from pathlib import Path

from wechat_typesetter.web import create_app


def test_web_index_loads() -> None:
    app = create_app()
    client = app.test_client()

    resp = client.get("/")

    assert resp.status_code == 200
    assert "微信公众号排版控制台" in resp.get_data(as_text=True)


def test_web_single_run_generates_file(tmp_path: Path) -> None:
    md_path = tmp_path / "article.md"
    out_path = tmp_path / "article.html"
    md_path.write_text("# 标题\n\n正文", encoding="utf-8")

    app = create_app()
    client = app.test_client()

    resp = client.post(
        "/run",
        data={
            "mode": "single",
            "config_path": "",
            "input_path": str(md_path),
            "output_path": str(out_path),
            "title": "测试标题",
            "title_template": "{name}",
            "author": "",
            "author_template": "",
            "summary": "",
            "cover_image_url": "",
            "kimi_api_key": "",
            "kimi_model": "kimi-k2.5",
            "kimi_base_url": "https://api.moonshot.cn/v1",
        },
    )

    assert resp.status_code == 200
    assert out_path.exists()
    html = out_path.read_text(encoding="utf-8")
    assert "测试标题" in html
