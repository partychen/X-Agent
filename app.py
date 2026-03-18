"""Twitter用户行为分析Agent - 主应用入口"""
import logging
from dotenv import load_dotenv

# ⚠️ 必须在所有业务模块 import 之前加载 .env，
# 否则模块顶层的 os.getenv() 读不到 .env 中的值
load_dotenv()

import streamlit as st
from ui.sidebar import render_sidebar
from ui.chatbox import render_chatbox

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)
st.set_page_config(
    page_title="Twitter用户行为分析Agent",
    page_icon="🤖",
    layout="wide"
)

def main():
    """主应用函数"""
    st.title("🤖 Twitter用户行为分析Agent")
    st.caption("使用大语言模型分析Twitter用户的行为模式和趋势")
    
    render_sidebar()
    render_chatbox()

if __name__ == "__main__":
    main()
