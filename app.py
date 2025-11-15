import streamlit as st
import os
import logging
from dotenv import load_dotenv
from langchain.agents import create_agent
from tools import get_user_post
from llm_factory import LLMFactory
from constants import BASE_SYSTEM_PROMPT, DEFAULT_USER_SYSTEM_PROMPT


def compose_system_prompt(user_prompt: str | None) -> str:
    """Merge the non-editable base prompt with optional user instructions."""
    base_prompt = BASE_SYSTEM_PROMPT.strip()
    user_prompt = (user_prompt or "").strip()
    if user_prompt:
        return f"{base_prompt}\n\n{user_prompt}"
    return base_prompt

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
def get_llm(provider_name: str = None):
    """
    初始化LLM
    
    Args:
        provider_name: LLM提供商名称 (azure_openai, deepseek, kimi, doubao等)
                      如果为None，则从环境变量 LLM_PROVIDER 读取
    """
    return LLMFactory.create_llm(
        provider_name=provider_name,
        max_retries=3,
        temperature=0.1,
        top_p=0.9,
    )
# Display chat title
st.title("🤖 Twitter用户行为分析Agent")

# Add sidebar for system prompt configuration
with st.sidebar:
    st.header("⚙️ 系统设置")
    
    # Initialize LLM provider in session state
    if "llm_provider" not in st.session_state:
        st.session_state.llm_provider = os.getenv("LLM_PROVIDER", "azure_openai")
    
    # LLM Provider selection
    provider_names = LLMFactory.get_provider_display_names()
    provider_options = list(set(provider_names.values()))  # 去重显示名称
    # 创建反向映射
    display_to_key = {v: k for k, v in provider_names.items()}
    
    current_display = provider_names.get(st.session_state.llm_provider, "Azure OpenAI")
    
    selected_display = st.selectbox(
        "🤖 LLM 提供商",
        options=provider_options,
        index=provider_options.index(current_display) if current_display in provider_options else 0,
        help="选择要使用的大语言模型提供商"
    )
    
    # 获取选中的provider key（取第一个匹配的）
    selected_provider = next(k for k, v in provider_names.items() if v == selected_display)
    
    # Update LLM provider if changed
    if selected_provider != st.session_state.llm_provider:
        st.session_state.llm_provider = selected_provider
        # Clear cache to reinitialize LLM
        get_llm.clear()
        if "agent_executor" in st.session_state:
            del st.session_state.agent_executor
        st.success(f"✅ 已切换到 {selected_display}")
        st.rerun()
    
    st.divider()
    
    # Initialize custom system prompt segment in session state if not exists
    if "custom_system_prompt" not in st.session_state:
        st.session_state.custom_system_prompt = DEFAULT_USER_SYSTEM_PROMPT
    
    # System prompt text area
    new_system_prompt = st.text_area(
        "自定义补充提示词",
        value=st.session_state.custom_system_prompt,
        height=300,
        help="可选：为Agent添加额外的风格或分析要求，基础规则将始终保留"
    )
    
    # Update system prompt if changed
    if new_system_prompt != st.session_state.custom_system_prompt:
        st.session_state.custom_system_prompt = new_system_prompt
        composed_prompt = compose_system_prompt(new_system_prompt)
        if st.session_state.get("conversation_history") and st.session_state.conversation_history[0][0] == "system":
            st.session_state.conversation_history[0] = ("system", composed_prompt)
        st.success("✅ 补充提示词已更新")
    
    # Add reset button
    if st.button("🔄 重置为默认提示词"):
        st.session_state.custom_system_prompt = DEFAULT_USER_SYSTEM_PROMPT
        default_composed_prompt = compose_system_prompt(DEFAULT_USER_SYSTEM_PROMPT)
        if st.session_state.get("conversation_history") and st.session_state.conversation_history[0][0] == "system":
            st.session_state.conversation_history[0] = ("system", default_composed_prompt)
        st.rerun()
    
    # Add clear chat button
    if st.button("🗑️ 清空对话历史"):
        st.session_state.messages = []
        st.session_state.conversation_history = [("system", compose_system_prompt(st.session_state.custom_system_prompt))]
        st.rerun()

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []
    logger.info("初始化消息历史")
if "agent_executor" not in st.session_state:
    logger.info("正在创建 Agent...")
    current_provider = st.session_state.get("llm_provider", os.getenv("LLM_PROVIDER", "azure_openai"))
    st.session_state.agent_executor = create_agent(get_llm(current_provider), [get_user_post])
    logger.info(f"Agent 创建完成 - 使用 {current_provider}，已注册工具: get_user_post")
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = [("system", compose_system_prompt(st.session_state.custom_system_prompt))]
    logger.info("初始化对话历史")

# Display chat messages from history on app rerun (skip system message)
for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input("请输入你想分析的Twitter用户行为问题..."):
    
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
