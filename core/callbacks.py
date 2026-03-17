"""Streamlit 回调处理器 - 实时显示 Agent 执行过程"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List

import streamlit as st
from langchain_core.callbacks import BaseCallbackHandler
from streamlit.errors import NoSessionContext

logger = logging.getLogger(__name__)

_ST_ERRORS = (NoSessionContext, AttributeError, RuntimeError)


class StreamlitCallbackHandler(BaseCallbackHandler):
    """在 Streamlit 界面中实时展示 Agent 的思考和工具调用过程"""

    def __init__(self, parent_container=None):
        self.parent_container = parent_container or st
        self.details_placeholder = self.parent_container.empty()
        self.details: list[str] = []
        self.current_tool_name: str | None = None

    @staticmethod
    def _now() -> str:
        return datetime.now().strftime("%H:%M:%S")

    @staticmethod
    def _truncate(text: str, limit: int = 100) -> str:
        return f"{text[:limit]}..." if len(text) > limit else text

    def _update_display(self):
        try:
            if self.details:
                with self.details_placeholder.container():
                    for detail in self.details:
                        st.markdown(detail)
        except _ST_ERRORS:
            pass

    def _append(self, line: str):
        self.details.append(line)
        self._update_display()

    def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs) -> None:
        try:
            logger.info("🤔 LLM 开始调用")
            self._append(f"- ⏰ `{self._now()}` 正在理解你的问题...")
        except _ST_ERRORS:
            pass

    def on_llm_end(self, response, **kwargs) -> None:
        try:
            logger.info("✅ LLM 调用结束")
            self._append(f"- ✅ `{self._now()}` LLM 分析完成")
        except _ST_ERRORS:
            pass

    def on_tool_start(self, serialized: Dict[str, Any], input_str: str, **kwargs) -> None:
        try:
            tool_name = serialized.get("name", "Unknown Tool")
            self.current_tool_name = tool_name
            logger.info(f"🔧 工具开始执行: {tool_name}")
            self._append(f"- 🔧 `{self._now()}` 调用工具: `{tool_name}`")
            self._append(f"  - 参数: `{self._truncate(input_str)}`")
        except _ST_ERRORS:
            pass

    def on_tool_end(self, output: Any, **kwargs) -> None:
        try:
            logger.info("✅ 工具执行完成")
            output_str = str(output.content) if hasattr(output, "content") else str(output)
            self._append(f"- ✅ `{self._now()}` 工具执行完成")

            if self.current_tool_name == "fetch_user_tweets":
                self._render_tweets(output_str)
            else:
                self._append(f"  - 返回: `{self._truncate(output_str)}`")
        except _ST_ERRORS:
            pass

    def _render_tweets(self, output_str: str):
        """解析并展示推文列表"""
        try:
            posts = json.loads(output_str)
            if not isinstance(posts, list) or not posts:
                raise ValueError("empty")

            display_posts = sorted(posts, key=lambda x: x.get("created_at", ""), reverse=True)
            self._append(f"  - 获取到 `{len(posts)}` 条推文:")
            for i, post in enumerate(display_posts, 1):
                created_at = post.get("created_at", "Unknown")
                text = post.get("text", "").replace("\n", " ")
                self._append(f"    {i}. **{created_at}** - {self._truncate(text, 80)}")
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as e:
            logger.warning(f"解析推文数据失败: {e}")
            self._append(f"  - 返回: `{self._truncate(output_str)}`")

    def on_tool_error(self, error: Exception, **kwargs) -> None:
        try:
            logger.error(f"❌ 工具执行失败: {error}")
            self._append(f"- ❌ `{self._now()}` 错误: {error}")
        except _ST_ERRORS:
            pass

    def clear_display(self):
        try:
            self.details_placeholder.empty()
        except _ST_ERRORS:
            pass
