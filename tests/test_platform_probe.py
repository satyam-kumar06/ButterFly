import json

import httpx

from scripts.check_platform import config_status, safe_failure, token_probe


def test_missing_access_is_pending_not_passed():
    status = config_status({})
    assert status["token_factory"]["status"] == "pending"
    assert "TOKEN_FACTORY_API_KEY" in status["token_factory"]["missing"]
    assert status["sandboxes"]["status"] == "pending"


def test_model_probe_checks_catalog_before_inference_and_omits_secrets():
    calls = []

    def handler(request):
        calls.append(request)
        if request.url.path.endswith("/models"):
            return httpx.Response(
                200, json={"data": [{"id": "nvidia/nano"}, {"id": "nvidia/super"}]}
            )
        model = json.loads(request.content)["model"]
        if model.endswith("super"):
            return httpx.Response(429, json={"message": "private provider content"})
        return httpx.Response(200, json={"choices": [{"message": {"content": "FORK_OK"}}]})

    env = {
        "TOKEN_FACTORY_API_KEY": "fake-secret-must-not-leak",
        "MODEL_NANO": "nvidia/nano",
        "MODEL_SUPER": "nvidia/super",
        "MODEL_ULTRA": "nvidia/ultra",
    }
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        report = token_probe(env, client)
    assert len(calls) == 3  # catalog, Nano, Super; never call unavailable Ultra
    assert report["status"] == "failed"
    assert report["models"]["nano"]["status"] == "passed"
    assert report["models"]["super"]["http_status"] == 429
    assert report["models"]["ultra"]["status"] == "model_not_in_catalog"
    assert "fake-secret" not in json.dumps(report)
    assert "private provider content" not in json.dumps(report)


def test_failure_does_not_echo_sensitive_exception_message():
    assert safe_failure(RuntimeError("api_key=do-not-print")) == {
        "status": "failed",
        "error_type": "RuntimeError",
    }
