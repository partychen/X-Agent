# X-Agent

一个基于 AI 的 Twitter 用户行为分析工具，可以自动抓取和分析 Twitter 用户的推文内容。

## 功能特点

- 🤖 **开源大模型**：通过 IP + 端口连接任意 OpenAI 兼容的模型服务
- 🔍 **自动抓取推文**：支持 X 官方 API 和 Playwright 自动抓取，具备自动 Fallback 机制
- 💬 **对话式交互**：通过 Streamlit 界面进行自然语言对话
- 📊 **行为洞察**：分析用户兴趣、情感倾向、活跃时间等特征

## 环境要求

- Python 3.12+
- 开源大模型服务地址（IP + 端口，需兼容 OpenAI API 格式）
- Chrome 浏览器（用于 Playwright）

## 安装步骤

### 0. 安装 uv（Python 包管理器）

本项目使用 [uv](https://docs.astral.sh/uv/) 作为包管理器，请先安装：

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

安装完成后验证：
```powershell
uv --version
```

> 💡 更多安装方式请参考 [uv 官方文档](https://docs.astral.sh/uv/getting-started/installation/)

1. **克隆项目**
```bash
git clone https://github.com/partychen/X-Agent.git
cd X-Agent
```

2. **安装依赖**
```bash
uv sync
```

3. **安装 Playwright 浏览器**
```bash
uv run playwright install chrome
```

4. **配置环境变量**

复制 `.env.example` 为 `.env` 并配置：

```bash
cp .env.example .env
```

**模型配置**：
```env
# 模型服务地址（填入提供的 IP + 端口）
LOCAL_LLM_BASE_URL=http://192.168.1.100:8000/v1
# 模型名称
LOCAL_LLM_MODEL=qwen2.5:7b
# API Key（如果服务方有要求则填写，否则保持默认）
LOCAL_LLM_API_KEY=not-needed
```

**Twitter/X 数据获取配置**：

推文获取支持两种模式，并具备**自动 Fallback 机制**：

| 优先级 | 模式 | 说明 |
|--------|------|------|
| 1️⃣ | X (Twitter) 官方 API | 配置了 `TWITTER_BEARER_TOKEN` 时优先使用 |
| 2️⃣ | Playwright + Nitter | API 不可用/Token 用尽时自动降级，或未配置 API 时直接使用 |

```env
# X (Twitter) API 配置 (可选)
# 配置了 Bearer Token 将优先使用官方 API
# API 失败（网络不通、Token 用尽 429、认证失败 401）时自动 Fallback 到 Playwright
TWITTER_BEARER_TOKEN=your_bearer_token_here

# Nitter 实例列表，用逗号分隔 (Playwright Fallback 使用)
NITTER_INSTANCES=https://nitter.net,https://nitter.privacydev.net

# 代理设置 (可选)，例如: http://127.0.0.1:1087
PROXY_URL=http://127.0.0.1:1087
```

详细配置请参考 `.env.example` 文件。

## 启动应用

```bash
uv run streamlit run app.py
```

应用将在浏览器中自动打开（默认端口：8501）

## 使用方法

1. 启动应用后，在聊天框中输入你想分析的 Twitter 用户
2. 例如：`分析一下 @elonmusk 的推文内容`
3. AI 会自动抓取该用户的推文并进行分析
4. 你可以继续提问以获取更深入的分析

## 技术栈

- **Streamlit**：Web 界面
- **LangChain**：AI Agent 框架
- **OpenAI 兼容 API**：连接开源大模型服务
- **Playwright**：浏览器自动化
- **Python 3.12**：开发语言

## 许可证

MIT License
