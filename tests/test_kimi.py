import json
from urllib import request

import pytest

from wechat_typesetter.kimi import KimiAPIError, polish_markdown_with_kimi


class _FakeResponse:
    def __init__(self, payload: dict):
        self._payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self) -> bytes:
        return json.dumps(self._payload).encode("utf-8")


def test_polish_markdown_with_kimi_returns_text(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def _fake_urlopen(req: request.Request, timeout: int = 0):
        captured["url"] = req.full_url
        captured["auth"] = req.headers.get("Authorization")
        body = req.data.decode("utf-8") if req.data else "{}"
        captured["payload"] = json.loads(body)
        return _FakeResponse(
            {
                "choices": [
                    {
                        "message": {
                            "content": "# 标题\n\n润色后正文。",
                        }
                    }
                ]
            }
        )

    monkeypatch.setattr(request, "urlopen", _fake_urlopen)

    result = polish_markdown_with_kimi(
        "# 标题\n\n原始正文。",
        api_key="test-key",
        model="kimi-k2.5",
        base_url="https://api.moonshot.cn/v1",
    )

    assert result == "# 标题\n\n润色后正文。"
    assert captured["url"] == "https://api.moonshot.cn/v1/chat/completions"
    assert captured["auth"] == "Bearer test-key"
    assert isinstance(captured["payload"], dict)


def test_polish_markdown_with_kimi_requires_api_key() -> None:
    with pytest.raises(ValueError):
        polish_markdown_with_kimi("test", api_key="")


def test_polish_markdown_with_kimi_raises_on_invalid_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _fake_urlopen(req: request.Request, timeout: int = 0):
        return _FakeResponse({"choices": [{"message": {"content": ""}}]})

    monkeypatch.setattr(request, "urlopen", _fake_urlopen)

    with pytest.raises(KimiAPIError):
        polish_markdown_with_kimi("test", api_key="test-key")
