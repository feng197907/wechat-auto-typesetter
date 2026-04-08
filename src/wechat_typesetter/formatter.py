from __future__ import annotations

from dataclasses import dataclass
import html
from pathlib import Path
import re

import markdown
from bs4 import BeautifulSoup


DEFAULT_CSS = """
:root {
  --bg: #f7f8fa;
  --card: #ffffff;
  --text: #1f2328;
  --muted: #57606a;
  --line: #d0d7de;
  --brand: #0f766e;
}
body {
  margin: 0;
  padding: 0;
  background: var(--bg);
  color: var(--text);
  font-family: "PingFang SC", "Microsoft YaHei", sans-serif;
}
.wechat-article {
  max-width: 760px;
  margin: 24px auto;
  background: var(--card);
  padding: 28px 24px;
  border-radius: 14px;
  box-shadow: 0 12px 30px rgba(16, 24, 40, 0.08);
}
.wechat-article h1,
.wechat-article h2,
.wechat-article h3 {
  line-height: 1.45;
  margin: 1.3em 0 0.6em;
}
.wechat-article h1 {
  font-size: 30px;
  border-bottom: 2px solid var(--brand);
  padding-bottom: 10px;
}
.wechat-article h2 {
  font-size: 24px;
  color: var(--brand);
}
.wechat-article h3 {
  font-size: 20px;
}
.wechat-article p,
.wechat-article blockquote p,
.wechat-article div {
  font-size: 16px;
  line-height: 1.9;
  margin: 1em 0;
}
.wechat-article ol,
.wechat-article ul {
  padding-left: 1.8em;
  margin: 1em 0;
  font-size: 16px;
}
.wechat-article li {
  margin: 0.4em 0;
  line-height: 1.9;
  font-size: 16px;
}
.wechat-article li p {
  margin: 0;
  display: inline;
  font-size: 16px;
}
/* 确保有序列表显示数字 */
.wechat-article ol li {
  list-style-type: decimal !important;
}
/* 确保无序列表显示圆点 */
.wechat-article ul li {
  list-style-type: disc !important;
}
.wechat-article blockquote {
  margin: 18px 0;
  padding: 10px 14px;
  border-left: 4px solid var(--brand);
  background: #f0fdfa;
  color: var(--muted);
}
.wechat-article code {
  padding: 2px 6px;
  border-radius: 6px;
  background: #eef2ff;
  font-family: Consolas, monospace;
}
.wechat-article pre {
  overflow-x: auto;
  padding: 12px;
  border-radius: 10px;
  background: #0f172a;
  color: #f8fafc;
}
.wechat-article pre code {
  background: transparent;
  color: inherit;
  padding: 0;
}
.wechat-article img {
  display: block;
  max-width: 100%;
  border-radius: 12px;
  margin: 16px auto;
}
.wechat-cover {
  margin: 10px 0 16px;
}
.wechat-cover img {
  width: 100%;
  max-height: 380px;
  object-fit: cover;
  border-radius: 12px;
}

.wechat-meta-author {
  margin: 0;
  font-size: 14px;
  color: var(--muted);
}
.wechat-meta-summary {
  margin: 8px 0 0;
  font-size: 15px;
  color: var(--text);
}
@media (max-width: 768px) {
  .wechat-article {
    margin: 0;
    border-radius: 0;
    padding: 18px 14px;
  }
  .wechat-article h1 {
    font-size: 26px;
  }
}
""".strip()

THEMES = {
    "default": DEFAULT_CSS,
    "minimal": """
:root {
  --bg: #ffffff;
  --card: #ffffff;
  --text: #333333;
  --muted: #666666;
  --line: #eeeeee;
  --brand: #222222;
}
body { background: var(--bg); color: var(--text); font-family: serif; }
.wechat-article { max-width: 700px; margin: 0 auto; padding: 40px 20px; box-shadow: none; }
.wechat-article h1 { font-size: 28px; text-align: center; border: none; }
.wechat-article h2 { font-size: 22px; border-left: 3px solid var(--brand); padding-left: 12px; }
.wechat-article p { font-size: 15px; line-height: 1.8; text-align: justify; }
.wechat-article blockquote { background: #f9f9f9; border: none; font-style: italic; border-left: 2px solid #ccc; }
    """.strip(),
    "elegant": """
:root {
  --bg: #fdf6e3;
  --card: #fdf6e3;
  --text: #586e75;
  --muted: #93a1a1;
  --line: #eee8d5;
  --brand: #b58900;
}
body { background: var(--bg); color: var(--text); }
.wechat-article { max-width: 740px; margin: 0 auto; padding: 30px; box-shadow: none; border: 1px solid var(--line); }
.wechat-article h1 { font-size: 32px; color: var(--brand); text-shadow: 1px 1px 1px rgba(0,0,0,0.05); }
.wechat-article h2 { font-size: 24px; color: #cb4b16; border-bottom: 1px dashed var(--brand); }
.wechat-article p { font-size: 17px; letter-spacing: 0.05em; }
.wechat-article blockquote { background: rgba(181, 137, 0, 0.05); border-color: var(--brand); }
    """.strip(),
    "dark": """
:root {
  --bg: #1a1a1a;
  --card: #2d2d2d;
  --text: #e0e0e0;
  --muted: #a0a0a0;
  --line: #404040;
  --brand: #3b82f6;
}
body { background: var(--bg); color: var(--text); }
.wechat-article { max-width: 760px; margin: 20px auto; background: var(--card); padding: 30px; border-radius: 12px; }
.wechat-article h1 { color: #fff; border-bottom-color: var(--brand); }
.wechat-article h2 { color: var(--brand); }
.wechat-article code { background: #404040; color: #ff79c6; }
.wechat-article blockquote { background: #363636; border-color: var(--brand); }
    """.strip()
}


@dataclass(slots=True)
class FormatOptions:
    title: str = ""
    custom_css: str = ""
    author: str = ""
    summary: str = ""
    cover_image_url: str = ""
    auto_extract_meta: bool = True
    summary_max_chars: int = 120
    # Fallbacks if extraction and manual input both fail
    default_author: str = ""
    default_summary: str = ""
    default_cover_image_url: str = ""
    theme: str = "default"


class WechatFormatter:
    """Convert Markdown content into WeChat-friendly HTML."""

    def __init__(self, options: FormatOptions | None = None) -> None:
        self.options = options or FormatOptions()

    def format_markdown(self, markdown_text: str) -> str:
        markdown_text = self._normalize_list_blocks(markdown_text)
        body_html = markdown.markdown(
            markdown_text,
            extensions=["extra", "tables", "fenced_code", "sane_lists"],
        )

        soup = BeautifulSoup(body_html, "html.parser")
        self._convert_inline_dash_list_paragraphs(soup)

        # Ensure external links open a new tab in web preview.
        for link in soup.find_all("a"):
            link["target"] = "_blank"
            link["rel"] = "noopener noreferrer"

        # Priority: Manual Option > Auto Extraction
        title = self.options.title.strip()
        if not title and self.options.auto_extract_meta:
            title = self._extract_title(markdown_text)
        if not title:
            title = "未命名文章"
        self.options.title = title # Update option for caller to see

        # Priority: Manual Option > Auto Extraction > Default Config
        author = self.options.author.strip()
        cover_url = self.options.cover_image_url.strip()
        summary = self.options.summary.strip()

        # Try extraction if manual is empty
        extracted_author = ""
        if self.options.auto_extract_meta:
            extracted_author = self._extract_author(markdown_text)
        
        # If we found an author in the text, we MUST remove it from body
        # regardless of whether we use it or manual input.
        if extracted_author:
            self._remove_author_paragraph(soup, extracted_author)
            if not author:
                author = extracted_author
        
        # If still no author, use default from config
        if not author:
            author = self.options.default_author
        
        self.options.author = author # Update option

        # Remove the title header from the body if it matches
        self._remove_title_header(soup, title)

        # Handle introduction replacement if summary is provided
        if self.options.summary.strip():
            self._replace_introduction(soup, self.options.summary.strip())

        if not cover_url and self.options.auto_extract_meta:
            cover_url = self._extract_cover_url(soup)
        if not cover_url:
            cover_url = self.options.default_cover_image_url
        self.options.cover_image_url = cover_url # Update option

        if not summary and self.options.auto_extract_meta:
            summary = self._extract_summary_text(soup, author)
        if not summary:
            summary = self.options.default_summary
        self.options.summary = summary # Update option

        meta_html = self._build_meta_html(cover_url, author, summary)

        html_body = str(soup)
        
        # Merge CSS: Selected theme as base, custom_css as overrides
        base_css = THEMES.get(self.options.theme, DEFAULT_CSS)
        custom = self.options.custom_css.strip()
        css = f"{base_css}\n{custom}" if custom else base_css
        
        safe_title = html.escape(title)

        return f"""<!doctype html>
<html lang=\"zh-CN\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>{safe_title}</title>
  <style>{css}</style>
</head>
<body>
  <article class=\"wechat-article\">
    <h1>{safe_title}</h1>
    {meta_html}
    {html_body}
  </article>
</body>
</html>
"""

    def _normalize_list_blocks(self, markdown_text: str) -> str:
        """Ensure list markers are parsed as lists even when users omit a blank line."""
        lines = markdown_text.splitlines()
        if not lines:
            return markdown_text

        normalized: list[str] = []
        list_marker = re.compile(r"^\s{0,3}(?:[-*+]\s+|\d+[.)]\s+)")

        for line in lines:
            if list_marker.match(line):
                prev_non_empty = ""
                for prev in reversed(normalized):
                    if prev.strip():
                        prev_non_empty = prev
                        break

                if prev_non_empty and not list_marker.match(prev_non_empty):
                    prev_stripped = prev_non_empty.strip()
                    if not prev_stripped.startswith(("#", ">", "|", "```", "~~~")):
                        if normalized and normalized[-1].strip():
                            normalized.append("")

            normalized.append(line)

        return "\n".join(normalized)

    def _build_meta_html(self, cover_url: str, author: str, summary: str) -> str:
        blocks: list[str] = []
        if cover_url:
            blocks.append(
                f'<div class="wechat-cover"><img src="{html.escape(cover_url)}" alt="cover" /></div>'
            )

        # Author as plain paragraph (no special style)
        if author:
            blocks.append(f'<p>作者：{html.escape(author)}</p>')

        return "".join(blocks)

    def _convert_inline_dash_list_paragraphs(self, soup: BeautifulSoup) -> None:
        """Convert patterns like '说明： - 项1 - 项2' into a real unordered list."""
        for paragraph in list(soup.find_all("p")):
            text = paragraph.get_text(" ", strip=True)
            if text.count(" - ") < 2:
                continue

            parts = [part.strip() for part in text.split(" - ") if part.strip()]
            if len(parts) < 3:
                continue

            intro_text = parts[0]
            item_texts = parts[1:]
            if not intro_text.endswith(("：", ":")):
                continue

            intro_tag = soup.new_tag("p")
            intro_tag.string = intro_text

            list_tag = soup.new_tag("ul")
            for item_text in item_texts:
                item_tag = soup.new_tag("li")
                item_tag.string = item_text
                list_tag.append(item_tag)

            paragraph.insert_before(intro_tag)
            intro_tag.insert_after(list_tag)
            paragraph.decompose()

    def _extract_cover_url(self, soup: BeautifulSoup) -> str:
        first_img = soup.find("img")
        if not first_img:
            return ""
        src = str(first_img.get("src", "")).strip()
        if src:
            first_img.decompose()
        return src

    def _extract_summary_text(self, soup: BeautifulSoup, author: str) -> str:
        # Get all paragraph text
        paragraphs = []
        for paragraph in soup.find_all("p"):
            text = paragraph.get_text(" ", strip=True)
            if not text:
                continue
            if self._matches_author_marker(text, author):
                continue
            # If it's a very short line (like a caption or separator), skip it
            if len(text) < 10:
                continue
            paragraphs.append(text)
        
        if not paragraphs:
            return ""
            
        # Combine the first few sentences to make a meaningful summary
        full_text = " ".join(paragraphs)
        return self._truncate(full_text, self.options.summary_max_chars)

    def _extract_author(self, markdown_text: str) -> str:
        for line in markdown_text.splitlines():
            # Matches "作者: xxx" or "## 作者: xxx" or "**作者**: xxx" etc.
            # Handles both colon types and optional markdown headers
            matched = re.search(r"(?:作者|Author)\s*[:：]\s*(.+?)\s*$", line, re.IGNORECASE)
            if matched:
                return matched.group(1).strip()
        return ""

    def _extract_title(self, markdown_text: str) -> str:
        for line in markdown_text.splitlines():
            matched = re.match(r"^\s*#\s+(.+?)\s*$", line)
            if matched:
                return matched.group(1).strip()
        return ""

    def _remove_title_header(self, soup: BeautifulSoup, title: str) -> None:
        # Since we always render <h1>{title}</h1> at the very top of the article,
        # we should remove the first <h1> found in the Markdown body to avoid duplication,
        # especially when the user manually provides a different title.
        first_h1 = soup.find("h1")
        if first_h1:
            first_h1.decompose()

    def _replace_introduction(self, soup: BeautifulSoup, summary: str) -> None:
        # 1. Try to find a header that looks like "Introduction" or "引言"
        intro_header = None
        for tag in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
            text = tag.get_text(strip=True)
            if "引言" in text or "Introduction" in text or "摘要" in text:
                intro_header = tag
                break
        
        if intro_header:
            # Found the header! Now replace the content until the next header
            new_intro = soup.new_tag("p")
            new_intro.string = summary
            
            # Remove siblings until next header
            current = intro_header.next_sibling
            while current and current.name not in ["h1", "h2", "h3", "h4", "h5", "h6"]:
                next_node = current.next_sibling
                current.extract()
                current = next_node
            
            # Replace the header itself or just insert after it?
            # User says "直接覆盖引言部分", so let's replace the content under the header.
            intro_header.insert_after(new_intro)
        else:
            # No specific intro header found, prepend at the very beginning of article body
            new_intro = soup.new_tag("p")
            new_intro.string = summary
            soup.insert(0, new_intro)

    def _remove_author_paragraph(self, soup: BeautifulSoup, author: str) -> None:
        # Look for author in various block-level elements
        for tag_name in ["p", "h1", "h2", "h3", "div"]:
            for tag in soup.find_all(tag_name):
                text = tag.get_text(" ", strip=True)
                if self._matches_author_marker(text, author):
                    tag.decompose()
                    return

    def _matches_author_marker(self, text: str, author: str) -> bool:
        matched = re.match(r"^(?:作者|Author)\s*[:：]\s*(.+?)\s*$", text.strip())
        if not matched:
            return False
        if not author:
            return True
        # If manual author is provided, check if it matches the content in the paragraph
        content = matched.group(1).strip()
        return content == author.strip() or author.strip() in content or content in author.strip()

    def _truncate(self, text: str, limit: int) -> str:
        if limit <= 0 or len(text) <= limit:
            return text
        return text[: limit - 1].rstrip() + "…"

    @staticmethod
    def load_text(path: str | Path) -> str:
        return Path(path).read_text(encoding="utf-8")

    @staticmethod
    def save_text(path: str | Path, text: str) -> None:
        Path(path).write_text(text, encoding="utf-8")
