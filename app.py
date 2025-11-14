import streamlit as st
import os
import logging
from dotenv import load_dotenv
from azure.identity import AzureCliCredential, get_bearer_token_provider
from langchain_openai import AzureChatOpenAI
from langchain.agents import create_agent
from tools import get_user_post

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
logger.info("环境变量已加载")

# Set page config
st.set_page_config(page_title="Twitter用户行为分析Agent", page_icon="🤖", layout="wide")

# Initialize LLM
@st.cache_resource
def get_llm():
    logger.info("正在初始化 Azure OpenAI LLM...")
    token_provider = get_bearer_token_provider(
        AzureCliCredential(), "https://cognitiveservices.azure.com/.default"
    )
    llm = AzureChatOpenAI(
        azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview"),
        max_retries=3,
        temperature=0.1,
        top_p=0.9,
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        azure_ad_token_provider=token_provider,
    )
    logger.info(f"LLM 初始化完成 - 部署: {os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME')}")
    return llm


llm = get_llm()
SYSTEM_PROMPT = """你是一个Twitter用户行为分析专家。

重要工作流程：
1. 当用户要求分析某个Twitter用户时，你必须先使用get_user_post工具获取该用户的推文数据
2. 然后基于获取到的真实数据进行分析

你可以通过分析Twitter用户的推文内容来提供深入的用户行为洞察。
你的任务是帮助用户理解特定Twitter用户的兴趣、情感倾向、活跃时间段以及与粉丝的互动模式。
请根据提供的推文数据，生成详尽且有洞察力的分析报告，帮助用户更好地了解该Twitter用户的行为特点和趋势。"""

# Display chat title
st.title("🤖 Twitter用户行为分析Agent")

# Add sidebar for system prompt configuration
with st.sidebar:
    st.header("⚙️ 系统设置")
    
    # Initialize system_prompt in session state if not exists
    if "system_prompt" not in st.session_state:
        st.session_state.system_prompt = SYSTEM_PROMPT
    
    # System prompt text area
    new_system_prompt = st.text_area(
        "系统提示词 (System Prompt)",
        value=st.session_state.system_prompt,
        height=300,
        help="设置Agent的行为和角色定义"
    )
    
    # Update system prompt if changed
    if new_system_prompt != st.session_state.system_prompt:
        st.session_state.system_prompt = new_system_prompt
        # Update the first message in conversation history (system message)
        if st.session_state.conversation_history and st.session_state.conversation_history[0][0] == "system":
            st.session_state.conversation_history[0] = ("system", new_system_prompt)
        st.success("✅ 系统提示词已更新")
    
    # Add reset button
    if st.button("🔄 重置为默认提示词"):
        st.session_state.system_prompt = SYSTEM_PROMPT
        if st.session_state.conversation_history and st.session_state.conversation_history[0][0] == "system":
            st.session_state.conversation_history[0] = ("system", SYSTEM_PROMPT)
        st.rerun()
    
    # Add clear chat button
    if st.button("🗑️ 清空对话历史"):
        st.session_state.messages = []
        st.session_state.conversation_history = [("system", st.session_state.system_prompt)]
        st.rerun()

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []
    logger.info("初始化消息历史")
if "agent_executor" not in st.session_state:
    logger.info("正在创建 Agent...")
    st.session_state.agent_executor = create_agent(get_llm(), [get_user_post])
    logger.info("Agent 创建完成，已注册工具: get_user_post")
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []
    st.session_state.conversation_history.append(("system", SYSTEM_PROMPT))
    logger.info("初始化对话历史")

# Display chat messages from history on app rerun (skip system message)
for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input("请输入你想分析的Twitter用户行为问题..."):
    # Check if API key is configured
    if not llm:
        st.error("⚠️ 请先在 .env 文件中配置 Key")
        st.stop()
    
    logger.info("=" * 80)
    logger.info(f"用户输入: {prompt}")
    logger.info("=" * 80)
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.conversation_history.append(("user", prompt))
    
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Generate assistant response using LangChain
    with st.chat_message("assistant"):
        with st.spinner("思考中..."):
            try:
                logger.info("开始调用 Agent 执行器...")
                logger.info(f"对话历史长度: {len(st.session_state.conversation_history)}")
                
                response_result = st.session_state.agent_executor.invoke({
                    "messages": list(st.session_state.conversation_history)
                })
                
                logger.info("Agent 执行完成")
                logger.info(f"返回消息数量: {len(response_result['messages'])}")
                
                # Extract AI message content
                ai_message = response_result["messages"][-1].content
                logger.info(f"AI 結果生成: {len(ai_message)} 字符")
                
                # Add AI response to both histories
                st.session_state.conversation_history.append(("assistant", ai_message))
                st.session_state.messages.append({"role": "assistant", "content": ai_message})
                
                logger.info("=" * 80)
                
            except Exception as e:
                error_message = f"❌ 发生错误: {str(e)}"
                logger.error(f"Agent 执行失败: {str(e)}", exc_info=True)
                st.error(error_message)
                st.session_state.messages.append({"role": "assistant", "content": error_message})
                logger.info("=" * 80)

            st.rerun()
