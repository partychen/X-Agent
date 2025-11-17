"""侧边栏组件模块 - 处理系统设置和配置"""
import streamlit as st
import os
from collections import deque

from constants import DEFAULT_USER_SYSTEM_PROMPT
from utility import compose_system_prompt


def _reset_conversation_history(prompt: str):
    st.session_state.conversation_history = deque(maxlen=20)
    st.session_state.conversation_history.append(
        ("system", compose_system_prompt(prompt))
    )


def _render_llm_provider_selector():
    """渲染LLM提供商选择器"""
    from llm_factory import LLMFactory
    
    # 初始化session state
    if "llm_provider" not in st.session_state:
        st.session_state.llm_provider = os.getenv("LLM_PROVIDER", "azure_openai")
    
    # 获取可用的提供商
    provider_names = LLMFactory.get_provider_display_names()
    provider_options = list(set(provider_names.values()))
    display_to_key = {v: k for k, v in provider_names.items()}
    
    current_display = provider_names.get(st.session_state.llm_provider, "Azure OpenAI")
    
    # 选择框
    selected_display = st.selectbox(
        "🤖 LLM 提供商",
        options=provider_options,
        index=provider_options.index(current_display) if current_display in provider_options else 0,
        help="选择要使用的大语言模型提供商"
    )
    
    # 获取选中的provider key
    selected_provider = next(k for k, v in provider_names.items() if v == selected_display)
    
    # 如果提供商改变，更新并清除缓存
    if selected_provider != st.session_state.llm_provider:
        st.session_state.llm_provider = selected_provider
        if "agent_executor" in st.session_state:
            del st.session_state.agent_executor
        st.success(f"✅ 已切换到 {selected_display}")
        st.rerun()


def _render_system_prompt_editor():
    """渲染系统提示词编辑器（内部函数）"""
    # 初始化自定义提示词
    if "custom_system_prompt" not in st.session_state:
        st.session_state.custom_system_prompt = DEFAULT_USER_SYSTEM_PROMPT
        _reset_conversation_history(st.session_state.custom_system_prompt)
    
    # 文本编辑区域
    new_system_prompt = st.text_area(
        "自定义补充提示词",
        value=st.session_state.custom_system_prompt,
        height=300,
        help="可选：为Agent添加额外的风格或分析要求，基础规则将始终保留"
    )
    
    # 更新提示词
    if new_system_prompt != st.session_state.custom_system_prompt:
        st.session_state.custom_system_prompt = new_system_prompt
        _reset_conversation_history(new_system_prompt)
        st.success("✅ 补充提示词已更新")


def _render_action_buttons():
    """渲染操作按钮（重置和清空）（内部函数）"""
    # 重置按钮
    if st.button("🔄 重置为默认提示词"):
        st.session_state.custom_system_prompt = DEFAULT_USER_SYSTEM_PROMPT
        _reset_conversation_history(DEFAULT_USER_SYSTEM_PROMPT)
        st.rerun()
    
    # 清空对话按钮
    if st.button("🗑️ 清空对话历史"):
        st.session_state.messages = []
        _reset_conversation_history(st.session_state.custom_system_prompt)
        st.rerun()


def render_sidebar():
    with st.sidebar:
        st.header("⚙️ 系统设置")
        
        _render_llm_provider_selector()
        st.divider()
        _render_system_prompt_editor()
        _render_action_buttons()
