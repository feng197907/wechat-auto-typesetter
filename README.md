# 微信公众号文章自动排版系统 (WeChat Auto Typesetter)

这是一个基于 Python 的微信公众号文章自动排版工具，旨在将 Markdown 文档快速转换为符合微信公众号后台样式要求的 HTML 页面。支持 AI 润色、热点追踪、内容建议以及直观的 Web 操作界面。

## 🌟 核心特性

- **Markdown 转 HTML**：内置适配移动端的精美排版样式，确保阅读体验。
- **Web 可视化控制台**：提供极简的交互界面，支持文件上传、参数配置、即时预览及下载。
- **AI 智能润色**：集成 Moonshot (Kimi) 大模型，支持排版前自动优化内容（需配置 API Key）。
- **实时热点分析**：
    - **多源抓取**：支持 百度、微博、**抖音**、知乎、微信、头条等多平台热点实时抓取。
    - **AI 内容建议**：基于当前热点，由 AI 自动生成 3-4 条极具实操性的公众号选题与切入建议。
    - **可视化报告**：包含关键词聚焦、话题结构分析及 Top 10 热点列表。
- **元数据智能提取**：自动从正文中提取标题（H1）、作者、摘要及首图，支持手动覆盖。
- **高安全性设计**：API Key 在 Web 界面隐藏显示，且在报告页面通过异步安全请求获取，不在 URL 中明文暴露。
- **流畅交互体验**：热点分析过程增加 Loading 加载动画，彻底消除白屏等待焦虑。

## 📂 项目结构

```text
wechat-auto-typesetter/
├── src/wechat_typesetter/
│   ├── formatter.py    # 排版引擎核心逻辑
│   ├── web.py          # Flask Web 控制台 & 爬虫分析逻辑
│   ├── kimi.py         # Kimi AI 集成 (润色 & 聊天)
│   ├── batch.py        # 批量处理逻辑
│   └── cli.py          # 命令行工具入口
├── examples/           # 示例文件与配置模板
├── tests/              # 单元测试
├── pyproject.toml      # 项目打包与入口定义
└── requirements.txt    # 依赖列表
```

## 🚀 快速开始

### 1. 安装环境

```bash
# 克隆仓库并进入目录
cd wechat-auto-typesetter

# 安装依赖及开发模式安装项目
pip install -r requirements.txt
pip install -e .
```

### 2. 启动 Web 控制台 (推荐)

```bash
wechat-typesetter-web
```

启动后访问：`http://127.0.0.1:8765`

**Web 功能亮点：**
- **热点看板**：一键抓取全网热点，AI 专家为您提供创作灵感。
- **文件上传**：直接上传本地 `.md` 文件。
- **AI 润色**：勾选“启用 Kimi AI 润色”即可在排版前优化文字。
- **操作闭环**：排版成功后支持 **新窗口预览**、**复制 HTML** 及 **下载到本地**。

---

### 3. 命令行使用

#### 单文件处理
```bash
wechat-typesetter -i article.md -o output.html --author "你的名字" --polish
```

#### 批量处理
将 MD 文件放入 `batch_input` 目录，执行：
```bash
wechat-typesetter-batch --in-dir batch_input --out-dir batch_output
```

## 🛠️ 配置说明

### AI 配置 (Kimi API)
若要启用 AI 润色或热点建议，请在 `pipeline.local.json` 中配置：
```json
{
  "kimi_api_key": "你的Kimi密钥"
}
```
或者设置环境变量：`KIMI_API_KEY="你的Kimi密钥"`。

### 自定义样式 (theme.json)
你可以通过 JSON 文件自定义 CSS 样式：
```json
{
  "custom_css": "h1 { color: #ff5722; } ...",
  "author": "默认署名"
}
```

## 🧪 运行测试

```bash
pip install pytest
pytest
```

## 📝 许可证

本项目采用 MIT 许可证。

---
*由 [Trae](https://www.trae.ai/) 辅助开发完成*
