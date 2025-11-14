# X-Agent

一个基于 AI 的 Twitter 用户行为分析工具，可以自动抓取和分析 Twitter 用户的推文内容。

## 功能特点

- 🤖 **AI 智能分析**：使用 Azure OpenAI 分析 Twitter 用户行为和特征
- 🔍 **自动抓取推文**：通过 Playwright 自动抓取用户推文（无头模式，后台运行）
- 💬 **对话式交互**：通过 Streamlit 界面进行自然语言对话
- 📊 **行为洞察**：分析用户兴趣、情感倾向、活跃时间等特征

## 环境要求

- Python 3.13+
- Azure OpenAI 服务账号
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

创建 `.env` 文件并配置以下变量：
```env
AZURE_OPENAI_ENDPOINT=your_azure_endpoint
AZURE_OPENAI_DEPLOYMENT_NAME=your_deployment_name
AZURE_OPENAI_API_VERSION=2024-12-01-preview
```

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

## 测试

运行测试脚本验证功能：
```bash
uv run python test_30_posts.py
```

## 技术栈

- **Streamlit**：Web 界面
- **LangChain**：AI Agent 框架
- **Azure OpenAI**：大语言模型
- **Playwright**：浏览器自动化
- **Python 3.13**：开发语言

## 许可证

MIT License
