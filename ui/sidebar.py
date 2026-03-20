"""侧边栏组件模块 - 处理系统设置和配置"""
from collections import deque

import streamlit as st

from core.prompts import DEFAULT_USER_SYSTEM_PROMPT, compose_system_prompt

FETCH_MODE_OPTIONS = {
    "auto": "🔄 自动（API 优先，失败回退爬虫）",
    "api_only": "🔑 仅 API",
    "scraper_only": "🕷️ 仅爬虫",
}


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


def _render_fetch_mode_selector():
    """渲染数据获取模式选择器"""
    if "fetch_mode" not in st.session_state:
        st.session_state.fetch_mode = "auto"

    st.subheader("数据获取方式")

    selected = st.radio(
        "选择推文获取模式",
        options=list(FETCH_MODE_OPTIONS.keys()),
        format_func=lambda k: FETCH_MODE_OPTIONS[k],
        index=list(FETCH_MODE_OPTIONS.keys()).index(st.session_state.fetch_mode),
        key="fetch_mode_radio",
        help="auto: 优先用 API，失败自动回退爬虫\n仅 API: 只用官方 API（需配置 Bearer Token）\n仅爬虫: 只用 Playwright/Nitter 爬虫",
    )

    if selected != st.session_state.fetch_mode:
        st.session_state.fetch_mode = selected
        st.toast(f"已切换为: {FETCH_MODE_OPTIONS[selected]}")


def render_sidebar():
    with st.sidebar:
        st.header("⚙️ 系统设置")
        _render_fetch_mode_selector()
        st.divider()
        _render_system_prompt_editor()
        _render_action_buttons()
