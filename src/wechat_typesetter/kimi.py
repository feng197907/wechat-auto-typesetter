from __future__ import annotations

import json
from typing import Any
from urllib import request


DEFAULT_KIMI_BASE_URL = "https://api.moonshot.cn/v1"
DEFAULT_KIMI_MODEL = "moonshot-v1-8k"


SYSTEM_PROMPT = (
    "你是微信公众号写作助手。请润色用户提供的 Markdown 文章，要求："
    "1) 保留原始事实与结构，不编造信息；"
    "2) 语句更清晰流畅，适合公众号阅读；"
    "3) 保留 Markdown 语法（标题、列表、代码块、链接、图片）；"
    "4) 不要输出解释，只输出润色后的完整 Markdown。"
)

REWRITE_PROMPT = (
    "你是微信公众号写作助手。请在不改变事实与结构的前提下，"
    "对用户提供的 Markdown 做明显可感知的语言升级："
    "1) 句式重写，减少口语重复；"
    "2) 语气更有节奏与感染力；"
    "3) 保留 Markdown 语法（标题、列表、代码块、链接、图片）；"
    "4) 不要输出解释，只输出润色后的完整 Markdown。"
)


class KimiAPIError(RuntimeError):
    """Raised when Kimi API returns invalid or error response."""


def chat_with_kimi(
    prompt: str,
    system_prompt: str,
    *,
    api_key: str,
    model: str = DEFAULT_KIMI_MODEL,
    base_url: str = DEFAULT_KIMI_BASE_URL,
    temperature: float = 0.5,
    timeout_seconds: int = 90,
) -> str:
    """Generic chat with Kimi model."""
    if not api_key.strip():
        raise ValueError("Kimi API Key 不能为空。")

    url = base_url.rstrip("/") + "/chat/completions"
    payload = {
        "model": model,
        "temperature": temperature,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
    }
    req = request.Request(
        url=url,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )

    try:
        with request.urlopen(req, timeout=timeout_seconds) as resp:
            raw = resp.read().decode("utf-8")
        data: dict[str, Any] = json.loads(raw)
        choices = data.get("choices") or []
        first = choices[0] if choices else {}
        message = first.get("message") or {}
        content = message.get("content", "")
        
        if isinstance(content, str):
            return content.strip()
        return str(content)
    except Exception as exc:
        raise KimiAPIError(f"调用 Kimi API 失败: {exc}") from exc


def polish_markdown_with_kimi(
    markdown_text: str,
    *,
    api_key: str,
    model: str = DEFAULT_KIMI_MODEL,
    base_url: str = DEFAULT_KIMI_BASE_URL,
    timeout_seconds: int = 90,
) -> str:
    """Polish markdown text with Kimi model and return polished markdown."""
    if not api_key.strip():
        raise ValueError("Kimi API Key 不能为空，请设置 KIMI_API_KEY 或通过参数传入。")

    def _request_once(system_prompt: str, temperature: float) -> str:
        url = base_url.rstrip("/") + "/chat/completions"
        payload = {
            "model": model,
            "temperature": temperature,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": markdown_text},
            ],
        }
        req = request.Request(
            url=url,
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )

        try:
            with request.urlopen(req, timeout=timeout_seconds) as resp:
                raw = resp.read().decode("utf-8")
        except request.HTTPError as exc:
            err_body = exc.read().decode("utf-8")
            try:
                err_data = json.loads(err_body)
                err_msg = err_data.get("error", {}).get("message", err_body)
            except Exception:
                err_msg = err_body
            raise KimiAPIError(f"调用 Kimi API 失败 ({exc.code}): {err_msg}") from exc
        except Exception as exc:  # pragma: no cover - network exception path
            raise KimiAPIError(f"调用 Kimi API 失败: {exc}") from exc

        try:
            data: dict[str, Any] = json.loads(raw)
            choices = data.get("choices") or []
            first = choices[0] if choices else {}
            message = first.get("message") or {}
            content = message.get("content", "")
        except Exception as exc:
            raise KimiAPIError("Kimi API 返回格式无效。") from exc

        if isinstance(content, str) and content.strip():
            return content.strip()

        if isinstance(content, list):
            # Compatible with tool/content-array style response.
            text_parts = [
                str(item.get("text", ""))
                for item in content
                if isinstance(item, dict) and item.get("type") in {"text", None}
            ]
            merged = "\n".join(part for part in text_parts if part).strip()
            if merged:
                return merged

        raise KimiAPIError("Kimi API 未返回可用文本内容。")

    polished = _request_once(SYSTEM_PROMPT, 0.4)
    if polished.strip() != markdown_text.strip():
        return polished

    # If output is unchanged, retry once with stronger rewrite intent.
    return _request_once(REWRITE_PROMPT, 0.7)
