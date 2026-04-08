from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from .formatter import WechatFormatter, FormatOptions
from .kimi import (
    DEFAULT_KIMI_BASE_URL,
    DEFAULT_KIMI_MODEL,
    polish_markdown_with_kimi,
)


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


def process_file(
    md_path: Path,
    out_dir: Path,
    options: FormatOptions,
    *,
    polish: bool = False,
    kimi_api_key: str = "",
    kimi_model: str = DEFAULT_KIMI_MODEL,
    kimi_base_url: str = DEFAULT_KIMI_BASE_URL,
) -> Path:
    text = md_path.read_text(encoding="utf-8")
    if polish:
        text = polish_markdown_with_kimi(
            text,
            api_key=kimi_api_key,
            model=kimi_model,
            base_url=kimi_base_url,
        )
    html = WechatFormatter(options).format_markdown(text)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / (md_path.stem + ".html")
    out_path.write_text(html, encoding="utf-8")
    return out_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="批量将 Markdown 转为微信样式 HTML")
    parser.add_argument("--in-dir", default="batch_input", help="输入 Markdown 文件目录（默认: batch_input）")
    parser.add_argument("--out-dir", default="batch_output", help="输出 HTML 目录（默认: batch_output）")
    parser.add_argument("--config", help="可选 JSON 配置文件（包含 custom_css 字段）")
    parser.add_argument("--title-template", default="{name}", help="标题模板，支持 {name} 占位符（默认: 文件名）")
    parser.add_argument("--author-template", default="", help="作者模板，支持 {name} 占位符")
    parser.add_argument("--summary", default=None, help="批量指定摘要，留空则自动提取")
    parser.add_argument("--cover", dest="cover_image_url", default=None, help="批量指定封面图 URL，留空则自动提取首图")
    parser.add_argument("--polish", action="store_true", help="调用 Kimi 对每篇 Markdown 先润色再排版")
    parser.add_argument("--kimi-api-key", help="Kimi API Key（默认读取环境变量 KIMI_API_KEY）")
    parser.add_argument("--kimi-model", default=None, help="Kimi 模型名")
    parser.add_argument("--kimi-base-url", default=None, help="Kimi API Base URL")
    args = parser.parse_args(argv)

    in_dir = Path(args.in_dir)
    out_dir = Path(args.out_dir)

    if not in_dir.exists():
        raise FileNotFoundError(f"输入目录不存在: {in_dir}")

    config = _load_config(args.config)
    custom_css = config.get("custom_css", "")
    summary = args.summary if args.summary is not None else config.get("summary", "")
    cover_image_url = (
        args.cover_image_url
        if args.cover_image_url is not None
        else config.get("cover_image_url", "")
    )

    processed = []
    kimi_api_key = args.kimi_api_key or os.getenv("KIMI_API_KEY", "") or config.get("kimi_api_key", "")
    kimi_model = args.kimi_model or config.get("kimi_model", "") or DEFAULT_KIMI_MODEL
    kimi_base_url = (
        args.kimi_base_url
        or config.get("kimi_base_url", "")
        or DEFAULT_KIMI_BASE_URL
    )

    for md in sorted(in_dir.glob("*.md")):
        title = args.title_template.format(name=md.stem)
        if args.author_template:
            author = args.author_template.format(name=md.stem)
        else:
            author = config.get("author", "")

        options = FormatOptions(
            title=title,
            custom_css=custom_css,
            author=author,
            summary=summary,
            cover_image_url=cover_image_url,
        )
        out_path = process_file(
            md,
            out_dir,
            options,
            polish=args.polish,
            kimi_api_key=kimi_api_key,
            kimi_model=kimi_model,
            kimi_base_url=kimi_base_url,
        )
        processed.append(out_path)
        print(f"已生成: {out_path}")

    if not processed:
        print("未找到任何 .md 文件。")
    else:
        print(f"批量处理完成，共生成 {len(processed)} 个文件。")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
