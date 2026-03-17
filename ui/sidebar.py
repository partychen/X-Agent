"""侧边栏组件模块 - 处理系统设置和配置"""
from collections import deque

import streamlit as st

from core.prompts import DEFAULT_USER_SYSTEM_PROMPT, compose_system_prompt


def _reset_conversation_history(prompt: str):
    st.session_state.conversation_history = deque(maxlen=20)
    st.session_state.conversation_history.append(
        ("system", compose_system_prompt(prompt))
    )


def _render_system_prompt_editor():
    """渲染系统提示词编辑器"""
    if "custom_system_prompt" not in st.session_state:
        st.session_state.custom_system_prompt = DEFAULT_USER_SYSTEM_PROMPT
        _reset_conversation_history(st.session_state.custom_system_prompt)

    new_system_prompt = st.text_area(
        "自定义补充提示词",
        value=st.session_state.custom_system_prompt,
        height=300,
        help="可选：为Agent添加额外的风格或分析要求，基础规则将始终保留",
    )

    if new_system_prompt != st.session_state.custom_system_prompt:
        st.session_state.custom_system_prompt = new_system_prompt
        _reset_conversation_history(new_system_prompt)
        st.success("✅ 补充提示词已更新")


def _render_action_buttons():
    """渲染操作按钮（重置和清空）"""
    if st.button("🔄 重置为默认提示词"):
        st.session_state.custom_system_prompt = DEFAULT_USER_SYSTEM_PROMPT
        _reset_conversation_history(DEFAULT_USER_SYSTEM_PROMPT)
        st.rerun()

    if st.button("🗑️ 清空对话历史"):
        st.session_state.messages = []
        _reset_conversation_history(st.session_state.custom_system_prompt)
        st.rerun()


def render_sidebar():
    with st.sidebar:
        st.header("⚙️ 系统设置")
        _render_system_prompt_editor()
        _render_action_buttons()
