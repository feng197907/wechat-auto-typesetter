from wechat_typesetter import FormatOptions, WechatFormatter


def test_format_markdown_generates_article_html() -> None:
    formatter = WechatFormatter(FormatOptions(title="测试标题"))

    output = formatter.format_markdown("# 小节\n\n这是**正文**。")

    assert "<article class=\"wechat-article\">" in output
    assert "测试标题" in output
    assert "<strong>正文</strong>" in output


def test_auto_extract_cover_summary_author() -> None:
    formatter = WechatFormatter(FormatOptions(title="自动元信息"))
    md = """作者：小王

![封面](https://example.com/cover.png)

这是第一段摘要文本。

这是第二段正文。
"""

    output = formatter.format_markdown(md)

    assert 'class="wechat-cover"' in output
    assert 'src="https://example.com/cover.png"' in output
    assert "作者：小王" in output
    assert "摘要：这是第一段摘要文本。" in output
    assert "<p>作者：小王</p>" not in output


def test_manual_meta_overrides_auto_extract() -> None:
    formatter = WechatFormatter(
        FormatOptions(
            title="手动元信息",
            author="手动作者",
            summary="手动摘要",
            cover_image_url="https://example.com/manual-cover.png",
        )
    )
    md = """作者：自动作者

![封面](https://example.com/auto-cover.png)

自动摘要正文。
"""

    output = formatter.format_markdown(md)

    assert "作者：手动作者" in output
    assert "摘要：手动摘要" in output
    assert 'src="https://example.com/manual-cover.png"' in output
    assert "作者：自动作者" not in output


def test_inline_dash_sequence_converts_to_list() -> None:
    formatter = WechatFormatter(FormatOptions(title="列表修复"))
    md = "我开始盘点自己的核心能力： - 业务能力（产品思维、用户洞察） - 通用能力（项目管理、跨部门沟通） - 迁移能力（能不能复用到其他行业？）"

    output = formatter.format_markdown(md)

    assert "<p>我开始盘点自己的核心能力：</p>" in output
    assert "<ul>" in output
    assert "<li>业务能力（产品思维、用户洞察）</li>" in output
    assert "<li>通用能力（项目管理、跨部门沟通）</li>" in output
    assert "<li>迁移能力（能不能复用到其他行业？）</li>" in output
