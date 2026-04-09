# 微信公众号文章自动排版系统 (WeChat Auto Typesetter)

这是一个基于 Python 的微信公众号文章全自动排版与创作工具。它不仅能将 Markdown 快速转换为精美的微信 HTML，还集成了全网热点追踪、AI 选题建议以及基于专业写作风格的 AI 自动化内容生成。

## 🌟 核心特性

- **Markdown 转 HTML**：内置多套适配微信后台的精美主题（Minimal, Elegant, Dark 等），支持自定义 CSS。
- **全网热点看板**：
    - **多源聚合**：实时抓取 **抖音**、百度、微博、知乎、头条、微信等平台的即时热搜。
    - **关键词聚焦**：自动提取当日热点的关键词云和话题结构分析。
- **交互式 AI 选题建议**：
    - **深度分析**：AI 专家基于当前热点，生成极具实操性的选题和切入角度。
    - **可视化卡片**：选题以精美卡片形式展示，支持**手动勾选**或**一键全选**。
- **AI 自动化文章创作**：
    - **一键生成**：选中选题后，AI 将根据选题背景自动创作完整的公众号初稿。
    - **风格注入**：严格遵循 [SKILL.md](file:///examples/SKILL.md) 写作指南，确保内容具有“真诚感”、“活人感”和“口语化”风格。
    - **自动归档**：生成的文章按日期自动存放在 `batch_input` 目录，方便后续批量排版。
- **高安全性与极致体验**：
    - **密钥安全**：API Key 在界面隐藏，数据传输不经过 URL，杜绝泄露风险。
    - **无感交互**：热点分析过程配有 Loading 动画，缓解等待焦虑；支持 Flask 热重载，修改即生效。

## 📂 项目结构

```text
wechat-auto-typesetter/
├── src/wechat_typesetter/
│   ├── formatter.py    # 排版引擎核心 (Markdown -> HTML)
│   ├── web.py          # 交互式 Web 控制台、爬虫分析 & 文章生成逻辑
│   ├── kimi.py         # Kimi AI 大模型集成
│   ├── batch.py        # 批量排版处理逻辑
│   └── cli.py          # 命令行入口
├── examples/           
│   ├── SKILL.md        # AI 写作风格指南（核心灵魂）
│   └── pipeline.config.json # 配置模板
├── batch_input/        # AI 生成文章的自动存放目录
├── tests/              # 单元测试
└── requirements.txt    # 依赖列表
```

## 🚀 快速开始

### 1. 安装环境

```bash
# 克隆仓库并安装
cd wechat-auto-typesetter
pip install -r requirements.txt
pip install -e .
```

### 2. 启动 Web 控制台 (推荐)

```bash
wechat-typesetter-web
```

访问：`http://127.0.0.1:8765`

### 3. 全自动化创作流程

1.  **抓取热点**：在页面顶部点击“抓取当前热点内容”。
2.  **挑选选题**：在弹出的报告中，勾选你感兴趣的选题卡片。
3.  **AI 生成**：点击底部的“🚀 AI 生成选中的公众号文章”。
4.  **排版发布**：在主页面选择生成的 `.md` 文件进行排版，一键复制代码至公众号后台。

## 🛠️ 配置说明

### 自动化配置
在项目根目录创建 `pipeline.local.json`，填入你的 Kimi API Key：
```json
{
  "kimi_api_key": "你的 sk-xxxx 密钥"
}
```
*系统启动时将自动加载此 Key，无需在页面重复输入。*

## 🧪 运行测试

```bash
pytest
```

