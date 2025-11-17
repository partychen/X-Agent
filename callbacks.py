"""自定义回调处理器模块 - 用于显示Agent执行过程"""
import streamlit as st
import logging
from langchain_core.callbacks import BaseCallbackHandler
from typing import Any, Dict, List
from datetime import datetime
from streamlit.errors import NoSessionContext

logger = logging.getLogger(__name__)


class CustomStreamlitCallbackHandler(BaseCallbackHandler):
    """自定义的Streamlit回调处理器，显示Agent执行过程的不同阶段"""
    
    def __init__(self, parent_container=None):
        self.parent_container = parent_container or st
        self.details_placeholder = self.parent_container.empty()
        self.details = []
        self.current_tool_name = None
        
    def _update_display(self):
        """更新显示内容"""
        try:
            if self.details:
                with self.details_placeholder.container():
                    # 显示所有详情（推文列表可能很长）
                    for detail in self.details:
                        st.markdown(detail)
        except (NoSessionContext, AttributeError, RuntimeError):
            # 在后台线程中，Streamlit 上下文不可用，静默忽略
            pass
        
    def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs) -> None:
        """LLM开始调用时"""
        try:
            logger.info("🤔 LLM 开始调用")
            self.details.append(f"- ⏰ `{datetime.now().strftime('%H:%M:%S')}` 正在理解你的问题...")
            self._update_display()
        except (NoSessionContext, AttributeError, RuntimeError):
            pass
    
    def on_llm_end(self, response, **kwargs) -> None:
        """LLM调用结束时"""
        try:
            logger.info("✅ LLM 调用结束")
            self.details.append(f"- ✅ `{datetime.now().strftime('%H:%M:%S')}` LLM 分析完成")
            self._update_display()
        except (NoSessionContext, AttributeError, RuntimeError):
            pass
    
    def on_tool_start(self, serialized: Dict[str, Any], input_str: str, **kwargs) -> None:
        """工具开始执行时"""
        try:
            tool_name = serialized.get("name", "Unknown Tool")
            self.current_tool_name = tool_name
            logger.info(f"🔧 工具开始执行: {tool_name}")
            
            self.details.append(f"- 🔧 `{datetime.now().strftime('%H:%M:%S')}` 调用工具: `{tool_name}`")
            self.details.append(f"  - 参数: `{input_str[:100]}...`" if len(input_str) > 100 else f"  - 参数: `{input_str}`")
            self._update_display()
        except (NoSessionContext, AttributeError, RuntimeError):
            pass
    
    def on_tool_end(self, output: Any, **kwargs) -> None:
        """工具执行结束时"""
        try:
            import json
            logger.info("✅ 工具执行完成")
            
            # 处理不同类型的输出
            if hasattr(output, 'content'):
                output_str = str(output.content)
            else:
                output_str = str(output)
            
            self.details.append(f"- ✅ `{datetime.now().strftime('%H:%M:%S')}` 工具执行完成")
            
            # 仅对 get_user_post 工具解析并展示
            if self.current_tool_name == "get_user_post":
                try:
                    posts = json.loads(output_str)
                    if isinstance(posts, list) and len(posts) > 0:
                        # 按时间排序（假设 created_at 是可排序的字符串）
                        display_posts = sorted(posts, key=lambda x: x.get('created_at', ''), reverse=True)
                        self.details.append(f"  - 获取到 `{len(posts)}` 条推文:")
                        # 使用列表方式展示推文
                        for i, post in enumerate(display_posts, 1):
                            created_at = post.get('created_at', 'Unknown')
                            text = post.get('text', '').replace('\n', ' ')  # 移除换行符
                            text_preview = text[:80] + "..." if len(text) > 80 else text
                            self.details.append(f"    {i}. **{created_at}** - {text_preview}")
                    else:
                        output_preview = output_str[:100] + "..." if len(output_str) > 100 else output_str
                        self.details.append(f"  - 返回: `{output_preview}`")
                except (json.JSONDecodeError, KeyError, TypeError) as e:
                    logger.warning(f"解析推文数据失败: {e}")
                    output_preview = output_str[:100] + "..." if len(output_str) > 100 else output_str
                    self.details.append(f"  - 返回: `{output_preview}`")
            else:
                # 其他工具显示简短预览
                output_preview = output_str[:100] + "..." if len(output_str) > 100 else output_str
                self.details.append(f"  - 返回: `{output_preview}`")
            
            self._update_display()
        except (NoSessionContext, AttributeError, RuntimeError):
            pass
        
    def on_tool_error(self, error: Exception, **kwargs) -> None:
        """工具执行出错时"""
        try:
            logger.error(f"❌ 工具执行失败: {str(error)}")
            self.details.append(f"- ❌ `{datetime.now().strftime('%H:%M:%S')}` 错误: {str(error)}")
            self._update_display()
        except (NoSessionContext, AttributeError, RuntimeError):
            pass
    
    def clear_display(self):
        """清空显示内容"""
        try:
            self.details_placeholder.empty()
        except (NoSessionContext, AttributeError, RuntimeError):
            pass
