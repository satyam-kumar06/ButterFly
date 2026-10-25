"""SandboxManager: the only code in Fork that talks to Nebius Sandboxes (task B1).

Everything else (orchestrator, simulation runner, flip search) calls these seven
methods and never imports the Contree SDK directly:

    base()                      -> checkpoint id of the base image (Python + numpy + forklib)
    fork(checkpoint_id)         -> Sandbox starting from that checkpoint
    write(sb, path, content)    -> stage a file; it is uploaded with the next run
    run(sb, cmd, timeout_s)     -> RunResult(stdout, stderr, exit_code, seconds)
    read(sb, path)              -> file contents after the last run
    checkpoint(sb, label)       -> id of sb's current filesystem, reusable by fork()
    discard(sb)                 -> forget sb (a failed attempt is simply never reused)

How this maps onto Nebius Sandboxes (contree-sdk 0.3.6): every run is an operation
that starts fresh compute from an immutable image. Running with disposable=False
returns a NEW image version; that version id is our checkpoint. Two runs from the
same image are independent branches, so "fork" costs nothing until a run happens.
Checkpoints keep files only, never processes, so every step is a fresh command.

Paths are always relative to the work directory (/work in a real sandbox), e.g.
"spec.json" or "out/shard_A_0.json". Commands run with that directory as cwd.

LocalManager has the same interface over plain folders. It exists so forklib,
packs and the runner can be developed and tested offline. It must NEVER run
agent-written code: make_manager() only picks it when FORK_SANDBOX=local, and a
deployment sets FORK_REQUIRE_REMOTE_SANDBOX=1 to disable it completely.
"""

from __future__ import annotations

import asyncio
import hashlib
import itertools
import os
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any, Protocol

WORKDIR = "/work"
REPO_ROOT = Path(__file__).resolve().parents[3]


class SandboxError(RuntimeError):
    """Raised when the platform fails (not when a command exits non-zero)."""


@dataclass
class RunResult:
    stdout: str
    stderr: str
    exit_code: int
    seconds: float

    @property
    def ok(self) -> bool:
        return self.exit_code == 0


@dataclass
class Sandbox:
    """A handle on one line of work. `state` is the latest checkpoint id; it moves
    forward after every successful-or-not run, because the run produced files."""

    id: str
    parent: str
    state: str
    pending: dict[str, bytes] = field(default_factory=dict)
    discarded: bool = False
    _last: Any = None  # backend object for reads (Contree image) - private


def _rel(path: str) -> str:
    p = PurePosixPath(path)
    if p.is_absolute():
        try:
            p = p.relative_to(WORKDIR)
        except ValueError as e:
            raise ValueError(f"paths must be inside {WORKDIR}: {path}") from e
    if ".." in p.parts:
        raise ValueError(f"path escapes the work directory: {path}")
    return str(p)


class SandboxManager(Protocol):
    async def base(self) -> str: ...
    async def fork(self, checkpoint_id: str) -> Sandbox: ...
    def write(self, sb: Sandbox, path: str, content: str | bytes) -> None: ...
    async def run(self, sb: Sandbox, cmd: str, timeout_s: int = 60) -> RunResult: ...
    async def read(self, sb: Sandbox, path: str) -> str: ...
    async def checkpoint(self, sb: Sandbox, label: str) -> str: ...
    def discard(self, sb: Sandbox) -> None: ...


def forklib_files() -> dict[str, bytes]:
    """The trusted library that goes into the base checkpoint, keyed by work path."""
    files = {}
    for p in sorted((REPO_ROOT / "forklib").rglob("*.py")):
        if "__pycache__" in p.parts or p.name.startswith("test_"):
            continue
        files[str(PurePosixPath("forklib") / p.relative_to(REPO_ROOT / "forklib").as_posix())] = (
            p.read_bytes()
        )
    runtime = REPO_ROOT / "sandbox_runtime"
    for name in ("setup_base.sh", "run_shard.py"):
        if (runtime / name).exists():
            files[name] = (runtime / name).read_bytes()
    return files


def files_digest(files: dict[str, bytes]) -> str:
    h = hashlib.sha256()
    for k in sorted(files):
        h.update(k.encode())
        h.update(files[k])
    return h.hexdigest()[:12]


_ids = itertools.count(1)


def _new_id(prefix: str) -> str:
    return f"{prefix}_{next(_ids):04d}"


# ---------------------------------------------------------------------------
# Nebius Sandboxes (Contree)
# ---------------------------------------------------------------------------


class ContreeManager:
    """SandboxManager over Nebius Sandboxes.

    max_parallel caps simultaneous operations (beta docs list 50 per project; set it
    from the measured value in docs/platform-notes.md). Platform errors such as
    timeouts, transport errors and 429s are retried with backoff; a command that
    exits non-zero is NOT retried - that is a real result for the caller.
    """

    def __init__(
        self,
        client: Any | None = None,
        *,
        base_image: str | None = None,
        max_parallel: int | None = None,
        retries: int = 2,
        backoff_s: float = 1.0,
    ) -> None:
        self._client = client
        self.base_image = base_image or os.environ.get(
            "SANDBOX_BASE_IMAGE_PY", "docker://docker.io/library/python:3.12-slim"
        )
        self.sem = asyncio.Semaphore(
            max_parallel or int(os.environ.get("SANDBOX_MAX_CONCURRENCY", "4"))
        )
        self.retries = retries
        self.backoff_s = backoff_s
        self._images: dict[str, Any] = {}
        self._base_id: str | None = None

    @property
    def client(self) -> Any:
        if self._client is None:
            from contree_sdk import Contree
            from contree_sdk.auth import IAMAuth
            from contree_sdk.config import ContreeConfig

            env = os.environ
            auth = IAMAuth(
                token=env["SANDBOX_API_KEY"],
                project_id=env["NEBIUS_PROJECT_ID"],
                base_url=env.get(
                    "SANDBOX_BASE_URL", "https://api.tokenfactory.nebius.com/sandboxes"
                ).rstrip("/"),
            )
            # short polling cap: shard runs take seconds, not minutes
            self._client = Contree(
                config=ContreeConfig(auth=auth, operation_timeout=300, operation_poll_secs_max=1.0)
            )
        return self._client

    def _retryable(self, exc: BaseException) -> bool:
        try:
            from contree_sdk.sdk.exceptions.api import (
                ApiTimeoutError,
                ContreeTransportError,
                TooManyRequestsError,
            )
        except ImportError:  # pragma: no cover - SDK missing
            return False
        return isinstance(exc, ApiTimeoutError | ContreeTransportError | TooManyRequestsError)

    async def _with_retries(self, make_coro):
        delay = self.backoff_s
        for attempt in itertools.count():
            try:
                async with self.sem:
                    return await make_coro()
            except Exception as exc:  # noqa: BLE001
                if attempt >= self.retries or not self._retryable(exc):
                    raise SandboxError(f"sandbox operation failed: {exc!r}") from exc
                await asyncio.sleep(delay)
                delay *= 2

    async def _image(self, checkpoint_id: str) -> Any:
        if checkpoint_id not in self._images:
            self._images[checkpoint_id] = await self.client.images.use(checkpoint_id, strict=True)
        return self._images[checkpoint_id]

    async def base(self) -> str:
        """Python + numpy + pytest + forklib, built once and reused by tag."""
        if self._base_id:
            return self._base_id
        files = forklib_files()
        tag = f"fork-base-{files_digest(files)}"
        try:
            img = await self.client.images.use(tag, strict=True)
        except Exception:  # noqa: BLE001 - not built yet
            src = await self._with_retries(lambda: self.client.images.oci(self.base_image))
            upload = {f"{WORKDIR}/{k}": v for k, v in files.items()}
            img = await self._with_retries(
                lambda: src.run(
                    shell=f"mkdir -p {WORKDIR} && cd {WORKDIR} && sh setup_base.sh",
                    files=upload,
                    disposable=False,
                    tag=tag,
                    timeout=600,
                )
            )
            if img.exit_code != 0 or img.uuid is None:
                raise SandboxError(f"base setup failed: {str(img.stderr)[-500:]}") from None
        self._base_id = str(img.uuid)
        self._images[self._base_id] = img
        return self._base_id

    async def fork(self, checkpoint_id: str) -> Sandbox:
        await self._image(checkpoint_id)
        return Sandbox(id=_new_id("fk"), parent=checkpoint_id, state=checkpoint_id)

    def write(self, sb: Sandbox, path: str, content: str | bytes) -> None:
        if sb.discarded:
            raise SandboxError("sandbox was discarded")
        sb.pending[_rel(path)] = content.encode() if isinstance(content, str) else content

    async def run(self, sb: Sandbox, cmd: str, timeout_s: int = 60) -> RunResult:
        if sb.discarded:
            raise SandboxError("sandbox was discarded")
        img = await self._image(sb.state)
        upload = {f"{WORKDIR}/{k}": v for k, v in sb.pending.items()}
        t = time.perf_counter()
        res = await self._with_retries(
            lambda: img.run(
                shell=cmd,
                cwd=WORKDIR,
                files=upload or None,
                disposable=False,
                timeout=timeout_s,
            )
        )
        secs = time.perf_counter() - t
        sb.pending.clear()
        if res.uuid is not None:
            sb.state = str(res.uuid)
            self._images[sb.state] = res
        sb._last = res
        return RunResult(str(res.stdout or ""), str(res.stderr or ""), int(res.exit_code), secs)

    async def read(self, sb: Sandbox, path: str) -> str:
        img = sb._last if sb._last is not None else await self._image(sb.state)
        data = await self._with_retries(lambda: img.read(f"{WORKDIR}/{_rel(path)}"))
        return data.decode() if isinstance(data, bytes) else str(data)

    async def checkpoint(self, sb: Sandbox, label: str) -> str:
        if sb.pending:
            # files must be inside the image before it can be a checkpoint
            res = await self.run(sb, "true", timeout_s=60)
            if not res.ok:
                raise SandboxError("could not flush staged files before checkpoint")
        img = await self._image(sb.state)
        try:
            await img.tag_as(label)
        except Exception:  # noqa: BLE001 - tags are a convenience; the uuid is the id
            pass
        return sb.state

    def discard(self, sb: Sandbox) -> None:
        sb.discarded = True
        sb.pending.clear()
        sb._last = None


# ---------------------------------------------------------------------------
# Local folders (development and tests only)
# ---------------------------------------------------------------------------


class LocalManager:
    """Same interface over temp folders. Trusted code only: forklib, template models,
    the runner and tests. Checkpoints are frozen copies; a fork copies one."""

    def __init__(
        self, root: str | Path | None = None, *, max_parallel: int = 4, python: str | None = None
    ):
        if os.environ.get("FORK_REQUIRE_REMOTE_SANDBOX") == "1":
            raise SandboxError("LocalManager is disabled in this environment")
        self.root = Path(root) if root else Path(tempfile.mkdtemp(prefix="fork-local-"))
        self.root.mkdir(parents=True, exist_ok=True)
        self.sem = asyncio.Semaphore(max_parallel)
        self.python = python or sys.executable
        self._base_id: str | None = None

    def _ckpt_dir(self, checkpoint_id: str) -> Path:
        d = self.root / "checkpoints" / checkpoint_id
        if not d.is_dir():
            raise SandboxError(f"unknown checkpoint {checkpoint_id}")
        return d

    def _work(self, sb: Sandbox) -> Path:
        return self.root / "forks" / sb.id

    async def base(self) -> str:
        if self._base_id:
            return self._base_id
        files = forklib_files()
        cid = f"base-{files_digest(files)}"
        d = self.root / "checkpoints" / cid
        if not d.exists():
            for k, v in files.items():
                (d / k).parent.mkdir(parents=True, exist_ok=True)
                (d / k).write_bytes(v)
        self._base_id = cid
        return cid

    async def fork(self, checkpoint_id: str) -> Sandbox:
        src = self._ckpt_dir(checkpoint_id)
        sb = Sandbox(id=_new_id("lfk"), parent=checkpoint_id, state=checkpoint_id)
        await asyncio.to_thread(shutil.copytree, src, self._work(sb))
        return sb

    def write(self, sb: Sandbox, path: str, content: str | bytes) -> None:
        if sb.discarded:
            raise SandboxError("sandbox was discarded")
        sb.pending[_rel(path)] = content.encode() if isinstance(content, str) else content

    def _flush(self, sb: Sandbox) -> None:
        for k, v in sb.pending.items():
            p = self._work(sb) / k
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(v)
        sb.pending.clear()

    async def run(self, sb: Sandbox, cmd: str, timeout_s: int = 60) -> RunResult:
        if sb.discarded:
            raise SandboxError("sandbox was discarded")
        self._flush(sb)
        env = {**os.environ, "PYTHONPATH": str(self._work(sb)), "PYTHONDONTWRITEBYTECODE": "1"}
        cmd = cmd.replace("python ", f'"{self.python}" ', 1) if cmd.startswith("python ") else cmd
        t = time.perf_counter()
        async with self.sem:
            try:
                proc = await asyncio.to_thread(
                    subprocess.run,
                    cmd,
                    shell=True,
                    cwd=self._work(sb),
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=timeout_s,
                )
                out, err, code = proc.stdout, proc.stderr, proc.returncode
            except subprocess.TimeoutExpired as e:
                out, err, code = str(e.stdout or ""), f"timed out after {timeout_s}s", 124
        return RunResult(out, err, code, time.perf_counter() - t)

    async def read(self, sb: Sandbox, path: str) -> str:
        p = self._work(sb) / _rel(path)
        if not p.exists():
            raise SandboxError(f"no such file in sandbox: {path}")
        return p.read_text()

    async def checkpoint(self, sb: Sandbox, label: str) -> str:
        self._flush(sb)
        cid = f"{label}-{sb.id}"
        dest = self.root / "checkpoints" / cid
        await asyncio.to_thread(
            shutil.copytree, self._work(sb), dest, ignore=shutil.ignore_patterns("__pycache__")
        )
        sb.state = cid
        return cid

    def discard(self, sb: Sandbox) -> None:
        sb.discarded = True
        sb.pending.clear()
        shutil.rmtree(self._work(sb), ignore_errors=True)


def make_manager() -> SandboxManager:
    """Nebius when credentials exist; LocalManager only when explicitly asked for."""
    if os.environ.get("SANDBOX_API_KEY") and os.environ.get("NEBIUS_PROJECT_ID"):
        return ContreeManager()
    if os.environ.get("FORK_SANDBOX") == "local":
        return LocalManager()
    raise SandboxError(
        "No sandbox configured: set SANDBOX_API_KEY and NEBIUS_PROJECT_ID, "
        "or FORK_SANDBOX=local for trusted-code development only."
    )
