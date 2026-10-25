"""SandboxManager behaviour (task B1).

LocalManager is exercised for real. ContreeManager is exercised against a fake
client that mimics contree-sdk 0.3.6 semantics: images are immutable, a
non-disposable run returns a new image, runs from one image are independent.
"""

from __future__ import annotations

import asyncio
import json
import uuid

import pytest

from apps.api.sandbox import ContreeManager, LocalManager, SandboxError, make_manager


def run(coro):
    return asyncio.run(coro)


# ---------------------------------------------------------------------------
# LocalManager
# ---------------------------------------------------------------------------


@pytest.fixture()
def local(tmp_path):
    return LocalManager(tmp_path / "sbx", max_parallel=4)


def test_local_base_has_forklib(local):
    async def go():
        base = await local.base()
        sb = await local.fork(base)
        res = await local.run(sb, "python -c \"import forklib; print('ok')\"")
        return res

    res = run(go())
    assert res.ok, res.stderr
    assert res.stdout.strip() == "ok"


def test_local_write_run_read_and_checkpoint(local):
    async def go():
        sb = await local.fork(await local.base())
        local.write(sb, "spec.json", json.dumps({"n": 3}))
        local.write(
            sb,
            "/work/job.py",
            "import json;n=json.load(open('spec.json'))['n']\n"
            "open('out.txt','w').write(str(n*2))\n",
        )
        res = await local.run(sb, "python job.py")
        out = await local.read(sb, "out.txt")
        ck = await local.checkpoint(sb, "model-v1")
        child = await local.fork(ck)
        again = await local.read(child, "out.txt")
        return res, out, again

    res, out, again = run(go())
    assert res.ok and out == "6" and again == "6"


def test_local_forks_are_isolated_and_failed_attempt_rolls_back(local):
    async def go():
        ck = await local.checkpoint(await local.fork(await local.base()), "session")
        bad = await local.fork(ck)
        r = await local.run(bad, "echo broken > model.py && exit 3")
        local.discard(bad)
        good = await local.fork(ck)
        exists = await local.run(good, "test -e model.py && echo LEAK || echo CLEAN")
        return r, exists

    r, exists = run(go())
    assert r.exit_code == 3
    assert exists.stdout.strip() == "CLEAN"


def test_local_timeout_is_reported_not_raised(local):
    async def go():
        sb = await local.fork(await local.base())
        return await local.run(sb, 'python -c "import time; time.sleep(5)"', timeout_s=1)

    res = run(go())
    assert res.exit_code == 124 and "timed out" in res.stderr


def test_local_parallel_limit(tmp_path):
    mgr = LocalManager(tmp_path / "p", max_parallel=2)

    async def go():
        base = await mgr.base()
        sbs = [await mgr.fork(base) for _ in range(4)]
        return await asyncio.gather(
            *[mgr.run(sb, 'python -c "import time; time.sleep(0.4)"') for sb in sbs]
        )

    import time

    t = time.perf_counter()
    results = run(go())
    assert all(r.ok for r in results)
    assert time.perf_counter() - t >= 0.75  # 4 jobs, 2 at a time


def test_discarded_sandbox_cannot_be_used(local):
    async def go():
        sb = await local.fork(await local.base())
        local.discard(sb)
        with pytest.raises(SandboxError):
            await local.run(sb, "true")

    run(go())


def test_paths_cannot_escape_workdir(local):
    async def go():
        sb = await local.fork(await local.base())
        with pytest.raises(ValueError):
            local.write(sb, "../evil.py", "x")
        with pytest.raises(ValueError):
            local.write(sb, "/etc/passwd", "x")

    run(go())


def test_make_manager_requires_explicit_choice(monkeypatch):
    for k in ("SANDBOX_API_KEY", "NEBIUS_PROJECT_ID", "FORK_SANDBOX"):
        monkeypatch.delenv(k, raising=False)
    with pytest.raises(SandboxError):
        make_manager()
    monkeypatch.setenv("FORK_SANDBOX", "local")
    assert isinstance(make_manager(), LocalManager)
    monkeypatch.setenv("FORK_REQUIRE_REMOTE_SANDBOX", "1")
    with pytest.raises(SandboxError):
        make_manager()


# ---------------------------------------------------------------------------
# ContreeManager against a fake SDK
# ---------------------------------------------------------------------------


class FakeImage:
    store: dict[str, FakeImage] = {}

    def __init__(self, files=None, tag=None, exit_code=0, stdout="", stderr=""):
        self.uuid = uuid.uuid4()
        self.files = dict(files or {})
        self.tag = tag
        self.exit_code, self.stdout, self.stderr = exit_code, stdout, stderr
        FakeImage.store[str(self.uuid)] = self
        if tag:
            FakeImage.store[tag] = self

    async def run(self, shell, cwd=None, files=None, disposable=True, tag=None, timeout=None):
        new = dict(self.files)
        new.update({k: (v.encode() if isinstance(v, str) else v) for k, v in (files or {}).items()})
        code, out = 0, ""
        if shell.startswith("echo "):
            out = shell[5:]
        elif shell.startswith("fail"):
            code = 1
        elif shell.startswith("write "):
            _, path, text = shell.split(" ", 2)
            new[f"/work/{path}"] = text.encode()
        res = FakeImage(new, tag=tag, exit_code=code, stdout=out)
        if disposable:
            res.uuid = None
        return res

    async def read(self, path):
        if path not in self.files:
            raise FileNotFoundError(path)
        return self.files[path]

    async def tag_as(self, tag):
        FakeImage.store[tag] = self
        return self


class FakeImages:
    async def use(self, ref, strict=False):
        if ref not in FakeImage.store:
            raise LookupError(ref)
        return FakeImage.store[ref]

    async def oci(self, ref):
        return FakeImage({}, tag=None)


class FakeClient:
    images = FakeImages()


@pytest.fixture()
def remote(tmp_path):
    FakeImage.store = {}
    return ContreeManager(FakeClient(), max_parallel=3)


def test_contree_base_uploads_forklib_and_is_cached(remote):
    async def go():
        b1 = await remote.base()
        b2 = await remote.base()
        return b1, b2

    b1, b2 = run(go())
    assert b1 == b2
    img = FakeImage.store[b1]
    assert any(k.startswith("/work/forklib/") for k in img.files)
    assert img.tag and img.tag.startswith("fork-base-")


def test_contree_fork_write_run_read_checkpoint(remote):
    async def go():
        base = await remote.base()
        sb = await remote.fork(base)
        remote.write(sb, "spec.json", '{"a": 1}')
        res = await remote.run(sb, "write out.txt hello")
        text = await remote.read(sb, "out.txt")
        spec = await remote.read(sb, "spec.json")
        ck = await remote.checkpoint(sb, "model-v1")
        child = await remote.fork(ck)
        again = await remote.read(child, "out.txt")
        return res, text, spec, ck, again, base

    res, text, spec, ck, again, base = run(go())
    assert res.ok and text == "hello" and spec == '{"a": 1}' and again == "hello"
    assert ck != base  # new image version, base untouched
    assert "/work/out.txt" not in FakeImage.store[base].files


def test_contree_sibling_forks_do_not_see_each_other(remote):
    async def go():
        base = await remote.base()
        a, b = await remote.fork(base), await remote.fork(base)
        await remote.run(a, "write x.txt A")
        await remote.run(b, "write x.txt B")
        return await remote.read(a, "x.txt"), await remote.read(b, "x.txt")

    assert run(go()) == ("A", "B")


def test_contree_nonzero_exit_is_a_result_not_an_error(remote):
    async def go():
        sb = await remote.fork(await remote.base())
        return await remote.run(sb, "fail please")

    assert run(go()).exit_code == 1


def test_contree_retries_transient_errors(remote, monkeypatch):
    calls = {"n": 0}

    class Flaky(Exception):
        pass

    monkeypatch.setattr(remote, "_retryable", lambda exc: isinstance(exc, Flaky))
    remote.backoff_s = 0.01

    async def flaky():
        calls["n"] += 1
        if calls["n"] < 3:
            raise Flaky()
        return "done"

    assert run(remote._with_retries(flaky)) == "done"
    assert calls["n"] == 3

    async def always():
        raise Flaky()

    with pytest.raises(SandboxError):
        run(remote._with_retries(always))
