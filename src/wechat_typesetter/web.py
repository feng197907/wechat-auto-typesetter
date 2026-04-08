from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from flask import Flask, request, render_template_string, send_file
import io

from .formatter import FormatOptions, WechatFormatter
from .kimi import (
    DEFAULT_KIMI_BASE_URL,
    DEFAULT_KIMI_MODEL,
    polish_markdown_with_kimi,
)


PAGE_HTML = """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>微信文章排版控制台</title>
  <style>
    :root {
      --bg: radial-gradient(circle at 20% 10%, #fff4dc 0%, #f8f3e8 35%, #e9f1ee 100%);
      --panel: #fffdf8;
      --ink: #222018;
      --muted: #6b665a;
      --line: #d8d1c2;
      --brand: #c2410c;
      --brand-2: #0f766e;
      --ok: #17633e;
      --danger: #9f1239;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      color: var(--ink);
      background: var(--bg);
      font-family: "Microsoft YaHei", "PingFang SC", sans-serif;
    }
    .wrap {
      max-width: 1100px;
      margin: 28px auto;
      padding: 0 16px;
    }
    .hero {
      border: 1px solid var(--line);
      border-radius: 18px;
      padding: 18px 20px;
      background: linear-gradient(110deg, #fff7ed 0%, #ecfeff 100%);
      box-shadow: 0 10px 26px rgba(17, 24, 39, 0.08);
      margin-bottom: 16px;
    }
    h1 {
      margin: 0;
      font-size: 28px;
      letter-spacing: 0.4px;
      color: #7c2d12;
    }
    .sub {
      margin: 8px 0 0;
      color: var(--muted);
      font-size: 14px;
    }
    form {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 14px;
      padding: 16px;
      border: 1px solid var(--line);
      border-radius: 18px;
      background: var(--panel);
      box-shadow: 0 8px 20px rgba(2, 6, 23, 0.05);
    }
    .full { grid-column: 1 / -1; }
    label {
      display: block;
      font-size: 13px;
      color: var(--muted);
      margin: 0 0 6px;
    }
    input, select, textarea {
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 10px 12px;
      font-size: 14px;
      color: var(--ink);
      background: #fff;
      outline: none;
      font-family: inherit;
    }
    input:focus, select:focus, textarea:focus {
      border-color: var(--brand);
      box-shadow: 0 0 0 3px rgba(194, 65, 12, 0.14);
    }
    .inline {
      display: flex;
      align-items: center;
      gap: 8px;
      padding-top: 20px;
    }
    .inline input[type='checkbox'] {
      width: auto;
      transform: translateY(1px);
    }
    .btns {
      display: flex;
      gap: 10px;
      justify-content: flex-end;
    }
    button {
      border: 0;
      border-radius: 10px;
      padding: 10px 16px;
      font-size: 14px;
      cursor: pointer;
      color: #fff;
      background: linear-gradient(90deg, var(--brand) 0%, #ea580c 100%);
      box-shadow: 0 6px 16px rgba(194, 65, 12, 0.28);
    }
    button.secondary {
      background: linear-gradient(90deg, var(--brand-2) 0%, #14b8a6 100%);
      box-shadow: 0 6px 16px rgba(15, 118, 110, 0.28);
    }
    .status {
      margin: 14px 0 0;
      padding: 10px 12px;
      border-radius: 10px;
      font-size: 14px;
      border: 1px solid;
      white-space: pre-wrap;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .ok {
      color: var(--ok);
      border-color: #86efac;
      background: #f0fdf4;
    }
    .err {
      color: var(--danger);
      border-color: #fda4af;
      background: #fff1f2;
    }
    .status-text { flex: 1; }
    .status-btns { display: flex; gap: 8px; margin-left: 12px; }
    .btn-sm {
      padding: 4px 10px;
      font-size: 12px;
      border-radius: 6px;
      box-shadow: none;
    }
    /* Modal Styles */
    .modal-overlay {
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: rgba(0,0,0,0.5);
      display: flex;
      justify-content: center;
      align-items: center;
      z-index: 1000;
      backdrop-filter: blur(4px);
    }
    .modal-content {
      background: #fff;
      padding: 24px;
      border-radius: 18px;
      max-width: 400px;
      width: 90%;
      text-align: center;
      box-shadow: 0 20px 50px rgba(0,0,0,0.2);
      animation: modalSlide 0.3s ease-out;
    }
    @keyframes modalSlide {
      from { transform: translateY(20px); opacity: 0; }
      to { transform: translateY(0); opacity: 1; }
    }
    .modal-title {
      font-size: 20px;
      font-weight: bold;
      margin-bottom: 12px;
      color: var(--ink);
    }
    .modal-msg {
      font-size: 15px;
      color: var(--muted);
      margin-bottom: 24px;
      line-height: 1.6;
    }
    .modal-footer {
      display: flex;
      gap: 12px;
      justify-content: center;
    }
    .modal-btn {
      border: 0;
      border-radius: 10px;
      padding: 10px 20px;
      font-size: 14px;
      cursor: pointer;
      font-weight: 500;
    }
    .modal-btn.primary {
      color: #fff;
      background: linear-gradient(90deg, var(--brand) 0%, #ea580c 100%);
    }
    .modal-btn.secondary {
      color: var(--ink);
      background: #f3f4f6;
      border: 1px solid var(--line);
    }
    .modal-btn.success {
      color: #fff;
      background: linear-gradient(90deg, var(--brand-2) 0%, #14b8a6 100%);
    }
    /* Loading Overlay */
    .loading-overlay {
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: rgba(255,255,255,0.8);
      display: none;
      flex-direction: column;
      justify-content: center;
      align-items: center;
      z-index: 2000;
      backdrop-filter: blur(2px);
    }
    .spinner {
      width: 40px;
      height: 40px;
      border: 4px solid var(--line);
      border-top: 4px solid var(--brand-2);
      border-radius: 50%;
      animation: spin 1s linear infinite;
      margin-bottom: 16px;
    }
    @keyframes spin {
      0% { transform: rotate(0deg); }
      100% { transform: rotate(360deg); }
    }
    .loading-text {
      font-size: 16px;
      font-weight: bold;
      color: var(--brand-2);
    }
    .hint {
      margin-top: 16px;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: #fff;
      overflow: hidden;
    }
    .preview-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 10px 12px;
      border-bottom: 1px solid var(--line);
      background: #f8fafc;
    }
    .preview-header h2 {
      margin: 0;
      font-size: 14px;
      color: #374151;
    }
    iframe {
      width: 100%;
      height: 540px;
      border: 0;
      display: block;
    }
    .hint {
      margin-top: 8px;
      color: var(--muted);
      font-size: 12px;
    }
    @media (max-width: 900px) {
      form { grid-template-columns: 1fr; }
      .btns { justify-content: flex-start; }
      iframe { height: 420px; }
    }
  </style>
  <script>
    function openPreview() {
      const content = document.getElementById('preview-data').value;
      const win = window.open('', '_blank');
      win.document.write(content);
      win.document.close();
    }

    function closeModal() {
      const modal = document.getElementById('success-modal');
      if (modal) modal.style.display = 'none';
    }

    function downloadFile() {
      const content = document.getElementById('preview-data').value;
      const title = document.getElementById('download-filename').value;
      const filename = (title || 'wechat_article') + '.html';
      
      const blob = new Blob([content], { type: 'text/html;charset=utf-8' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      
      setTimeout(() => {
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
      }, 100);
    }

    function showLoading() {
      const isPolish = document.querySelector('input[name="polish"]').checked;
      const overlay = document.getElementById('loading-overlay');
      const text = document.getElementById('loading-text');
      
      if (isPolish) {
        text.innerText = "🚀 AI 正在润色并排版中，请稍候...";
      } else {
        text.innerText = "⚡ 正在排版中...";
      }
      
      overlay.style.display = 'flex';
      return true;
    }
  </script>
</head>
<body>
  <div id="loading-overlay" class="loading-overlay">
    <div class="spinner"></div>
    <div id="loading-text" class="loading-text">正在处理中...</div>
  </div>

  {% if ok and message %}
  <div id="success-modal" class="modal-overlay">
    <div class="modal-content">
      <div class="modal-title">✨ 排版成功</div>
      <div class="modal-msg">{{ message }}</div>
      <div class="modal-footer">
        <button class="modal-btn success" type="button" onclick="openPreview()">预览文章</button>
        <button class="modal-btn primary" type="button" onclick="downloadFile()">下载文件</button>
        <button class="modal-btn secondary" type="button" onclick="closeModal()">关闭</button>
      </div>
    </div>
  </div>
  
  <input type="hidden" id="download-filename" value="{{ values.title or 'wechat_article' }}">
  {% endif %}

  <div class="wrap">
    <section class="hero">
      <h1>微信公众号排版控制台</h1>
      <p class="sub">在页面里快速完成: 单文件排版 / 批量目录排版。</p>
    </section>

    <form method="post" action="/run" enctype="multipart/form-data" onsubmit="return showLoading()">
      <input type="hidden" name="config_path" value="{{ values.config_path }}" />
      <input type="hidden" name="input_path" value="{{ values.input_path }}" />
      <input type="hidden" name="output_path" value="{{ values.output_path }}" />
      <input type="hidden" name="in_dir" value="{{ values.in_dir }}" />
      <input type="hidden" name="out_dir" value="{{ values.out_dir }}" />

      <div class="full">
        <label>运行模式</label>
        <select name="mode" onchange="this.form.submit()">
          <option value="single" {% if values.mode == 'single' %}selected{% endif %}>单文件 (上传 MD)</option>
          <option value="batch" {% if values.mode == 'batch' %}selected{% endif %}>批处理目录 (服务器本地)</option>
        </select>
      </div>

      {% if values.mode == 'single' %}
      <div class="full">
        <label>上传 Markdown 文件</label>
        <input type="file" name="file" accept=".md" />
      </div>
      {% endif %}

      <div>
        <label>标题</label>
        {% if values.mode == 'single' %}
          <input name="title" value="{{ values.title }}" placeholder="留空自动提取" />
        {% else %}
          <input name="title_template" value="{{ values.title_template }}" placeholder="留空自动使用文件名" />
        {% endif %}
      </div>
      <div>
        <label>作者（可选）</label>
        <input name="author" value="{{ values.author }}" placeholder="留空自动提取" />
      </div>

      <div class="full">
        <label>引言 / 摘要（可选，填写后将覆盖正文引言）</label>
        <textarea name="summary" rows="3" placeholder="留空自动提取">{{ values.summary }}</textarea>
      </div>

      <div class="full">
        <label>封面图 URL（可选）</label>
        <input name="cover_image_url" value="{{ values.cover_image_url }}" placeholder="留空自动提取首图" />
      </div>

      <div class="full" style="border-top: 1px dashed var(--line); margin: 10px 0; padding-top: 10px;">
        <div class="inline">
          <input type="checkbox" name="polish" value="1" {% if values.polish %}checked{% endif %} />
          <label style="margin:0; font-weight: bold; color: var(--brand-2);">启用 Kimi AI 润色 (大模型)</label>
        </div>
        <input type="hidden" name="kimi_api_key" value="{{ values.kimi_api_key }}" />
      </div>

      <div class="full btns">
        <button type="submit">执行</button>
        <button class="secondary" type="button" onclick="location.href='/'">重置</button>
      </div>

      <div class="full hint">提示：将自动处理默认目录下的 Markdown 文件。</div>
    </form>

    {% if message %}
      {% if not ok %}
      <div class="status err">
        <div class="status-text">{{ message }}</div>
      </div>
      {% endif %}
    {% endif %}

    {% if preview_html %}
      <textarea id="preview-data" style="display:none;">{{ preview_html }}</textarea>
    {% endif %}
  </div>
</body>
</html>
"""


def _load_config(config_path: str) -> dict[str, str]:
    if not config_path.strip():
        return {}

    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_path}")

    data = json.loads(path.read_text(encoding="utf-8"))
    return {
        "custom_css": str(data.get("custom_css", "")),
        "author": str(data.get("author", "")),
        "summary": str(data.get("summary", "")),
        "cover_image_url": str(data.get("cover_image_url", "")),
        "kimi_api_key": str(data.get("kimi_api_key", "")),
        "kimi_model": str(data.get("kimi_model", "")),
        "kimi_base_url": str(data.get("kimi_base_url", "")),
    }


def _initial_values() -> dict[str, Any]:
    return {
        "mode": "single",
        "config_path": "examples/pipeline.config.json",
        "input_path": "examples/article.md",
        "output_path": "output.html",
        "in_dir": "batch_input",
        "out_dir": "batch_output",
        "title": "",
        "title_template": "",
        "author": "",
        "author_template": "",
        "summary": "",
        "cover_image_url": "",
        "polish": False,
        "kimi_api_key": "",
        "kimi_model": DEFAULT_KIMI_MODEL,
        "kimi_base_url": DEFAULT_KIMI_BASE_URL,
    }


def _get_kimi_fields(values: dict[str, Any], config: dict[str, str]) -> tuple[str, str, str]:
    api_key = (
        str(values.get("kimi_api_key", "")).strip()
        or os.getenv("KIMI_API_KEY", "")
        or config.get("kimi_api_key", "")
    )
    model = (
        str(values.get("kimi_model", "")).strip()
        or config.get("kimi_model", "")
        or DEFAULT_KIMI_MODEL
    )
    base_url = (
        str(values.get("kimi_base_url", "")).strip()
        or config.get("kimi_base_url", "")
        or DEFAULT_KIMI_BASE_URL
    )
    return api_key, model, base_url


def _run_single(values: dict[str, Any], config: dict[str, str], markdown_text: str | None = None) -> tuple[str, str]:
    if markdown_text is None:
        input_path = Path(str(values.get("input_path", "")).strip())
        if not input_path.exists():
            raise FileNotFoundError(f"输入文件不存在: {input_path}")
        markdown_text = WechatFormatter.load_text(input_path)

    output_path = Path(str(values.get("output_path", "")).strip())

    if values.get("polish"):
        api_key, model, base_url = _get_kimi_fields(values, config)
        markdown_text = polish_markdown_with_kimi(
            markdown_text,
            api_key=api_key,
            model=model,
            base_url=base_url,
        )

    custom_css = config.get("custom_css", "")
    
    # Pass manual values if provided, otherwise let formatter handle extraction and fallbacks
    author = str(values.get("author", "")).strip()
    summary = str(values.get("summary", "")).strip()
    cover_image_url = str(values.get("cover_image_url", "")).strip()
    title = str(values.get("title", "")).strip()

    formatter = WechatFormatter(
        FormatOptions(
            title=title,
            custom_css=custom_css,
            author=author,
            summary=summary,
            cover_image_url=cover_image_url,
            # Fallbacks from config
            default_author=config.get("author", ""),
            default_summary=config.get("summary", ""),
            default_cover_image_url=config.get("cover_image_url", ""),
        )
    )
    
    # Format and let it extract missing info
    html = formatter.format_markdown(markdown_text)
    
    # Update values with what was actually used (for UI feedback)
    values["title"] = formatter.options.title
    values["author"] = formatter.options.author
    values["cover_image_url"] = formatter.options.cover_image_url

    WechatFormatter.save_text(output_path, html)
    return "排版成功！", html


def _run_batch(values: dict[str, Any], config: dict[str, str]) -> tuple[str, str]:
    in_dir = Path(str(values.get("in_dir", "")).strip())
    out_dir = Path(str(values.get("out_dir", "")).strip())
    if not in_dir.exists():
        raise FileNotFoundError(f"输入目录不存在: {in_dir}")

    out_dir.mkdir(parents=True, exist_ok=True)
    md_files = sorted(in_dir.glob("*.md"))
    if not md_files:
        return "排版成功：未找到需要处理的 .md 文件", ""

    custom_css = config.get("custom_css", "")
    cover_image_url = str(values.get("cover_image_url", "")).strip() or config.get("cover_image_url", "")
    title_template = str(values.get("title_template", "")).strip()
    author_template = str(values.get("author_template", "")).strip()

    preview_html = ""
    outputs: list[str] = []

    api_key = model = base_url = ""
    if values.get("polish"):
        api_key, model, base_url = _get_kimi_fields(values, config)

    for md in md_files:
        markdown_text = md.read_text(encoding="utf-8")
        if values.get("polish"):
            markdown_text = polish_markdown_with_kimi(
                markdown_text,
                api_key=api_key,
                model=model,
                base_url=base_url,
            )

        author = (
            author_template.format(name=md.stem)
            if author_template
            else config.get("author", "")
        )
        title = title_template.format(name=md.stem)
        options = FormatOptions(
            title=title,
            custom_css=custom_css,
            author=author,
            summary=str(values.get("summary", "")).strip(),
            cover_image_url=cover_image_url,
        )

        html = WechatFormatter(options).format_markdown(markdown_text)
        out_path = out_dir / f"{md.stem}.html"
        out_path.write_text(html, encoding="utf-8")
        outputs.append(str(out_path))
        preview_html = html

    return f"批量排版成功！共处理 {len(outputs)} 个文件", preview_html


def create_app() -> Flask:
    app = Flask(__name__)

    @app.get("/")
    def index() -> str:
        return render_template_string(
            PAGE_HTML,
            values=_initial_values(),
            message="",
            ok=True,
            preview_html="",
        )

    @app.post("/run")
    def run_pipeline() -> str:
        # Get values from form
        form_values = request.form.to_dict()
        
        values = _initial_values()
        for key in values:
            if key == "polish":
                values[key] = request.form.get("polish") == "1"
            elif key in form_values:
                values[key] = form_values[key]

        # Handle uploaded file
        uploaded_file = request.files.get("file")
        markdown_text = None
        if uploaded_file and uploaded_file.filename:
            markdown_text = uploaded_file.read().decode("utf-8")
            # Only set title from filename if the user didn't provide one
            if not values.get("title"):
                values["title"] = "" # Clear default to trigger extraction from content


        try:
            config = _load_config(str(values.get("config_path", "")))
            if values.get("mode") == "batch":
                message, preview_html = _run_batch(values, config)
            else:
                message, preview_html = _run_single(values, config, markdown_text=markdown_text)
            ok = True
        except Exception as exc:
            message = f"排版失败：{exc}"
            preview_html = ""
            ok = False

        return render_template_string(
            PAGE_HTML,
            values=values,
            message=message,
            ok=ok,
            preview_html=preview_html,
        )

    @app.post("/download")
    def download_file() -> Any:
        html_content = request.form.get("html_content", "")
        # Get the actual title from form if available, otherwise fallback
        filename = request.form.get("filename", "wechat_article")
        if not filename.endswith(".html"):
            filename += ".html"
        
        # 使用内存文件流返回下载
        file_stream = io.BytesIO(html_content.encode("utf-8"))
        return send_file(
            file_stream,
            as_attachment=True,
            download_name=filename,
            mimetype="text/html"
        )

    return app


def main() -> int:
    app = create_app()
    app.run(host="127.0.0.1", port=8765, debug=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
