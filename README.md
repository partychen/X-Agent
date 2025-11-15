# X-Agent

一个基于 AI 的 Twitter 用户行为分析工具，可以自动抓取和分析 Twitter 用户的推文内容。

## 功能特点

- 🤖 **多 LLM 支持**：支持 Azure OpenAI、DeepSeek、Kimi、豆包等多种大语言模型
- 🔍 **自动抓取推文**：通过 Playwright 自动抓取用户推文（无头模式，后台运行）
- 💬 **对话式交互**：通过 Streamlit 界面进行自然语言对话
- 📊 **行为洞察**：分析用户兴趣、情感倾向、活跃时间等特征
- 🔄 **灵活切换**：在界面中可随时切换不同的 LLM 提供商

## 环境要求

- Python 3.13+
- 以下至少一种 LLM 服务账号：
  - Azure OpenAI
  - DeepSeek
  - Kimi (Moonshot)
  - 豆包 (Doubao/字节跳动)
- Chrome 浏览器（用于 Playwright）

## 安装步骤

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

复制 `.env.example` 为 `.env` 并根据使用的 LLM 提供商配置相应变量：

**选择 LLM 提供商**（在 `.env` 中设置）：
```env
LLM_PROVIDER=azure_openai  # 可选: azure_openai, deepseek, kimi, doubao
```

**Azure OpenAI 配置**：
```env
AZURE_OPENAI_ENDPOINT=your_azure_endpoint
AZURE_OPENAI_DEPLOYMENT_NAME=your_deployment_name
AZURE_OPENAI_API_VERSION=2024-12-01-preview
```

**DeepSeek 配置**：
```env
DEEPSEEK_API_KEY=your-deepseek-api-key
DEEPSEEK_MODEL=deepseek-chat
```

**Kimi (Moonshot) 配置**：
```env
KIMI_API_KEY=your-kimi-api-key
KIMI_MODEL=moonshot-v1-8k
```

**豆包 (Doubao) 配置**：
```env
DOUBAO_API_KEY=your-doubao-api-key
DOUBAO_MODEL=doubao-pro-4k
```

详细配置请参考 `.env.example` 文件。

## 启动应用

```bash
uv run streamlit run app.py
```

应用将在浏览器中自动打开（默认端口：8501）

## 使用方法

1. 启动应用后，在左侧边栏选择要使用的 LLM 提供商
2. 在聊天框中输入你想分析的 Twitter 用户
3. 例如：`分析一下 @elonmusk 的推文内容`
4. AI 会自动抓取该用户的推文并进行分析
5. 你可以继续提问以获取更深入的分析
6. 可以随时在边栏切换不同的 LLM 提供商

## 技术栈

- **Streamlit**：Web 界面
- **LangChain**：AI Agent 框架
- **多 LLM 支持**：Azure OpenAI、DeepSeek、Kimi、豆包
- **Playwright**：浏览器自动化
- **Python 3.13**：开发语言

## LLM 提供商说明

### Azure OpenAI
- 需要 Azure 订阅和 OpenAI 服务
- 使用 Azure CLI 凭据进行身份验证
- 支持多种 GPT 模型

### DeepSeek
- 访问 [deepseek.com](https://www.deepseek.com) 获取 API Key
- 提供高性价比的模型服务
- 使用 OpenAI 兼容的 API

### Kimi (Moonshot)
- 访问 [moonshot.cn](https://www.moonshot.cn) 获取 API Key
- 由月之暗面科技提供
- 支持超长上下文

### 豆包 (Doubao)
- 字节跳动旗下的 AI 服务
- 访问火山引擎获取 API Key
- 支持多种模型规格

## 许可证

MIT License
