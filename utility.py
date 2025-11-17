"""工具函数模块 - 提供通用的辅助函数"""
from constants import BASE_SYSTEM_PROMPT

def compose_system_prompt(user_prompt: str | None) -> str:
    base_prompt = BASE_SYSTEM_PROMPT.strip()
    user_prompt = (user_prompt or "").strip()
    if user_prompt:
        return f"{base_prompt}\n\n{user_prompt}"
    return base_prompt
