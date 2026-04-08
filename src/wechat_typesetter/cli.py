from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from .formatter import FormatOptions, WechatFormatter
from .kimi import (
    DEFAULT_KIMI_BASE_URL,
    DEFAULT_KIMI_MODEL,
    polish_markdown_with_kimi,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="微信公众号文章自动排版工具")
    parser.add_argument("-i", "--input", required=True, help="输入 Markdown 文件路径")
    parser.add_argument("-o", "--output", required=True, help="输出 HTML 文件路径")
    parser.add_argument("-t", "--title", default="未命名文章", help="文章标题")
    parser.add_argument("-c", "--config", help="JSON 配置文件路径（可选）")
    parser.add_argument("--author", help="作者（可选，留空则自动提取）")
    parser.add_argument("--summary", help="摘要（可选，留空则自动提取）")
    parser.add_argument("--cover", dest="cover_image_url", help="封面图 URL（可选，留空则自动提取首图）")
    parser.add_argument("--polish", action="store_true", help="调用 Kimi 对 Markdown 先润色再排版")
    parser.add_argument("--kimi-api-key", help="Kimi API Key（默认读取环境变量 KIMI_API_KEY）")
    parser.add_argument("--kimi-model", default=None, help="Kimi 模型名")
    parser.add_argument("--kimi-base-url", default=None, help="Kimi API Base URL")
    return parser


def _load_config(config_path: str | None) -> dict[str, str]:
    def _pick_fields(raw: dict[str, object]) -> dict[str, str]:
        return {
            "custom_css": str(raw.get("custom_css", "")),
            "author": str(raw.get("author", "")),
            "summary": str(raw.get("summary", "")),
            "cover_image_url": str(raw.get("cover_image_url", "")),
            "kimi_api_key": str(raw.get("kimi_api_key", "")),
            "kimi_model": str(raw.get("kimi_model", "")),
            "kimi_base_url": str(raw.get("kimi_base_url", "")),
        }

    merged: dict[str, str] = {}

    if config_path:
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_path}")
        merged.update(_pick_fields(json.loads(path.read_text(encoding="utf-8"))))

    # 自动加载本地私有配置，覆盖公共配置中的同名字段（便于保存私钥）。
    local_path = Path("pipeline.local.json")
    if local_path.exists():
        local_cfg = _pick_fields(json.loads(local_path.read_text(encoding="utf-8")))
        for key, value in local_cfg.items():
            if value.strip():
                merged[key] = value

    return merged


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    markdown_text = WechatFormatter.load_text(args.input)
    config = _load_config(args.config)
    custom_css = config.get("custom_css", "")
    author = args.author if args.author is not None else config.get("author", "")
    summary = args.summary if args.summary is not None else config.get("summary", "")
    cover_image_url = (
        args.cover_image_url
        if args.cover_image_url is not None
        else config.get("cover_image_url", "")
    )

    if args.polish:
        api_key = args.kimi_api_key or os.getenv("KIMI_API_KEY", "") or config.get("kimi_api_key", "")
        kimi_model = args.kimi_model or config.get("kimi_model", "") or DEFAULT_KIMI_MODEL
        kimi_base_url = (
            args.kimi_base_url
            or config.get("kimi_base_url", "")
            or DEFAULT_KIMI_BASE_URL
        )
        markdown_text = polish_markdown_with_kimi(
            markdown_text,
            api_key=api_key,
            model=kimi_model,
            base_url=kimi_base_url,
        )

    formatter = WechatFormatter(
        FormatOptions(
            title=args.title,
            custom_css=custom_css,
            author=author,
            summary=summary,
            cover_image_url=cover_image_url,
        )
    )
    html = formatter.format_markdown(markdown_text)
    WechatFormatter.save_text(args.output, html)

    print(f"已生成排版文件: {args.output}")
    return 0
