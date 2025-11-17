"""聊天界面模块 - 处理消息显示和用户交互"""
import streamlit as st
import os
import logging
from langchain.agents import create_agent

from tools import get_user_post
from llm_factory import LLMFactory
from callbacks import CustomStreamlitCallbackHandler

logger = logging.getLogger(__name__)

def _initialize_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "agent_executor" not in st.session_state:
        current_provider = st.session_state.get("llm_provider", os.getenv("LLM_PROVIDER", "azure_openai"))
        st.session_state.agent_executor = create_agent(LLMFactory.create_llm(current_provider), [get_user_post])


def _display_chat_messages():
    """显示历史聊天消息（跳过系统消息）（内部函数）"""
    for message in st.session_state.messages:
        if message["role"] != "system":
            with st.chat_message(message["role"]):
                st.markdown(message["content"])


def _handle_user_input():
    if prompt := st.chat_input("请输入你想分析的Twitter用户行为问题..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.conversation_history.append(("user", prompt))
        
        # 显示用户消息
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # 生成助手响应
        _generate_assistant_response()


def _generate_assistant_response():
    """使用Agent生成助手响应（内部函数）"""
    with st.chat_message("assistant"):
        with st.spinner("AI 正在思考中..."):
            try:
                logger.info("开始调用 Agent 执行器...")
                
                # 创建自定义回调处理器
                callback_handler = CustomStreamlitCallbackHandler()
                
                response_result = st.session_state.agent_executor.invoke(
                    {"messages": list(st.session_state.conversation_history)},
                    {"callbacks": [callback_handler]}
                )
                
                # 清空状态显示
                callback_handler.clear_display()
                
                ai_message = response_result["messages"][-1].content
                logger.info(f"AI 结果生成: {len(ai_message)} 字符")

                # 添加AI响应到历史
                st.session_state.conversation_history.append(("assistant", ai_message))
                st.session_state.messages.append({"role": "assistant", "content": ai_message})
                
            except Exception as e:
                # 错误处理
                error_message = f"❌ 发生错误: {str(e)}"
                logger.error(f"Agent 执行失败: {str(e)}", exc_info=True)
                st.error(error_message)
                st.session_state.messages.append({"role": "assistant", "content": error_message})
            
            # 刷新界面
            st.rerun()

def render_chatbox():
    """渲染完整的聊天界面"""
    _initialize_session_state()
    _display_chat_messages()
    _handle_user_input()
