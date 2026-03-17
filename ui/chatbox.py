"""聊天界面模块 - 处理消息显示和用户交互"""
import logging

import streamlit as st

from core.agent import create_agent
from core.llm import create_llm
from core.twitter_tool import get_tools
from core.callbacks import StreamlitCallbackHandler

logger = logging.getLogger(__name__)


def _initialize_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "agent_executor" not in st.session_state:
        st.session_state.agent_executor = create_agent(create_llm(), get_tools())


def _display_chat_messages():
    """显示历史聊天消息（跳过系统消息）"""
    for message in st.session_state.messages:
        if message["role"] != "system":
            with st.chat_message(message["role"]):
                st.markdown(message["content"])


def _handle_user_input():
    if prompt := st.chat_input("请输入你想分析的Twitter用户行为问题..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.conversation_history.append(("user", prompt))

        with st.chat_message("user"):
            st.markdown(prompt)

        _generate_assistant_response()


def _generate_assistant_response():
    """使用 Agent 生成助手响应"""
    with st.chat_message("assistant"):
        with st.spinner("AI 正在思考中..."):
            try:
                logger.info("开始调用 Agent 执行器...")

                callback_handler = StreamlitCallbackHandler()

                response_result = st.session_state.agent_executor.invoke(
                    {"messages": list(st.session_state.conversation_history)},
                    {"callbacks": [callback_handler]},
                )

                callback_handler.clear_display()

                ai_message = response_result["output"]
                logger.info(f"AI 结果生成: {len(ai_message)} 字符")

                st.session_state.conversation_history.append(("assistant", ai_message))
                st.session_state.messages.append({"role": "assistant", "content": ai_message})

            except Exception as e:
                error_message = f"❌ 发生错误: {str(e)}"
                logger.error(f"Agent 执行失败: {e}", exc_info=True)
                st.error(error_message)
                st.session_state.messages.append({"role": "assistant", "content": error_message})

            st.rerun()


def render_chatbox():
    """渲染完整的聊天界面"""
    _initialize_session_state()
    _display_chat_messages()
    _handle_user_input()
