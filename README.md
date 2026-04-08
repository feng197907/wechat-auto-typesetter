# 微信公众号文章自动排版系统 (WeChat Auto Typesetter)

这是一个基于 Python 的微信公众号文章自动排版工具，旨在将 Markdown 文档快速转换为符合微信公众号后台样式要求的 HTML 页面。支持 AI 润色、批量处理以及直观的 Web 操作界面。

## 🌟 核心特性

- **Markdown 转 HTML**：内置适配移动端的精美排版样式，确保阅读体验。
- **Web 可视化控制台**：提供极简的交互界面，支持文件上传、参数配置、即时预览及下载。
- **AI 智能润色**：集成 Moonshot (Kimi) 大模型，支持排版前自动优化内容（需配置 API Key）。
- **元数据智能提取**：自动从正文中提取标题（H1）、作者、摘要及首图，支持手动覆盖。
- **灵活的优先级机制**：手动输入 > 命令行参数 > 环境变量 > 配置文件 > 默认值。
- **一键操作流**：支持一键复制 HTML 代码，无缝对接公众号后台。

## 📂 项目结构

```text
wechat-auto-typesetter/
├── src/wechat_typesetter/
│   ├── formatter.py    # 排版引擎核心逻辑
│   ├── web.py          # Flask Web 控制台实现
│   ├── kimi.py         # Kimi AI 润色集成
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

# 创建并激活虚拟环境
python -m venv .venv
source .venv/bin/activate  # Windows 使用 .venv\Scripts\activate

# 安装依赖及开发模式安装项目
pip install -r requirements.txt
pip install -e .
```

### 2. 启动 Web 控制台 (推荐)

这是最简单、直观的使用方式：

```bash
wechat-typesetter-web
```

启动后访问：`http://127.0.0.1:8765`

**Web 功能亮点：**
- **文件上传**：直接上传本地 `.md` 文件。
- **可选配置**：标题、作者、摘要、封面图均支持“留空自动提取”。
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

### AI 润色配置
若要启用 Kimi 润色，请设置环境变量或在 `pipeline.local.json` 中配置：
```bash
$env:KIMI_API_KEY="你的Kimi密钥"  # Windows PowerShell
export KIMI_API_KEY="你的Kimi密钥" # Linux/macOS
```

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
