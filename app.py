"""Twitter用户行为分析Agent - 主应用入口"""
import streamlit as st
import logging
from dotenv import load_dotenv

from ui.sidebar import render_sidebar
from ui.chatbox import render_chatbox

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

load_dotenv()
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
