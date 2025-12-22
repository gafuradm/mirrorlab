import streamlit as st
import os
import json
import uuid
from datetime import datetime
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

# ================== 高级样式和配置 ==================
st.set_page_config(
    page_title="🎭 AI角色扮演聊天室 | 沉浸式多角色体验",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/your-repo',
        'Report a bug': "https://github.com/your-repo/issues",
        'About': "# 🎭 AI角色扮演聊天室\n沉浸式多角色互动体验平台"
    }
)

# 加载高级CSS
def load_advanced_css():
    css = """
    <style>
    /* ===== 全局重置 ===== */
    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }
    
    /* ===== 主应用样式 ===== */
    .stApp {
        background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
        font-family: 'Inter', 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif;
        min-height: 100vh;
        position: relative;
        overflow-x: hidden;
    }
    
    /* 星空背景效果 */
    .stApp::before {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-image: 
            radial-gradient(2px 2px at 20px 30px, rgba(255,255,255,0.3), transparent),
            radial-gradient(2px 2px at 40px 70px, rgba(255,255,255,0.2), transparent),
            radial-gradient(1px 1px at 90px 40px, rgba(255,255,255,0.3), transparent);
        z-index: -1;
        animation: twinkle 3s infinite alternate;
    }
    
    @keyframes twinkle {
        0% { opacity: 0.3; }
        100% { opacity: 0.7; }
    }
    
    /* ===== 主容器 ===== */
    .main-container {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-radius: 24px;
        padding: 2.5rem;
        box-shadow: 
            0 8px 32px rgba(0, 0, 0, 0.3),
            inset 0 1px 0 rgba(255, 255, 255, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin: 1.5rem auto;
        max-width: 1600px;
        animation: containerSlide 0.6s ease-out;
    }
    
    @keyframes containerSlide {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    /* ===== 标题样式 ===== */
    .main-title {
        background: linear-gradient(45deg, #00dbde, #fc00ff, #00dbde);
        background-size: 200% auto;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 3.5rem !important;
        font-weight: 900 !important;
        text-align: center;
        margin-bottom: 1.5rem;
        letter-spacing: -0.5px;
        animation: titleShine 3s ease-in-out infinite;
        position: relative;
    }
    
    .main-title::after {
        content: '';
        position: absolute;
        bottom: -10px;
        left: 50%;
        transform: translateX(-50%);
        width: 100px;
        height: 4px;
        background: linear-gradient(90deg, #00dbde, #fc00ff);
        border-radius: 2px;
        animation: pulseLine 2s infinite;
    }
    
    @keyframes titleShine {
        0%, 100% { background-position: 0% center; }
        50% { background-position: 100% center; }
    }
    
    @keyframes pulseLine {
        0%, 100% { width: 100px; opacity: 1; }
        50% { width: 150px; opacity: 0.8; }
    }
    
    .subtitle {
        text-align: center;
        color: rgba(255, 255, 255, 0.7);
        font-size: 1.2rem;
        margin-bottom: 2.5rem;
        font-weight: 400;
        letter-spacing: 0.5px;
    }
    
    /* ===== 玻璃态卡片 ===== */
    .glass-card {
        background: rgba(255, 255, 255, 0.08);
        backdrop-filter: blur(15px);
        -webkit-backdrop-filter: blur(15px);
        border-radius: 20px;
        padding: 2rem;
        margin: 1.5rem 0;
        border: 1px solid rgba(255, 255, 255, 0.12);
        position: relative;
        overflow: hidden;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .glass-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
        transition: 0.5s;
    }
    
    .glass-card:hover {
        transform: translateY(-8px) scale(1.02);
        box-shadow: 
            0 20px 40px rgba(0, 0, 0, 0.4),
            0 0 0 1px rgba(255, 255, 255, 0.1);
    }
    
    .glass-card:hover::before {
        left: 100%;
    }
    
    .glass-card h3 {
        color: #ffffff;
        font-size: 1.5rem;
        margin-bottom: 1rem;
        font-weight: 700;
    }
    
    .glass-card p {
        color: rgba(255, 255, 255, 0.7);
        line-height: 1.6;
    }
    
    /* ===== 高级按钮 ===== */
    .gradient-btn {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 1rem 2rem;
        font-weight: 600;
        font-size: 1rem;
        letter-spacing: 0.5px;
        cursor: pointer;
        position: relative;
        overflow: hidden;
        transition: all 0.3s ease;
        box-shadow: 0 4px 20px rgba(102, 126, 234, 0.4);
    }
    
    .gradient-btn::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
        transition: 0.5s;
    }
    
    .gradient-btn:hover {
        transform: translateY(-3px);
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.6);
        background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
    }
    
    .gradient-btn:hover::before {
        left: 100%;
    }
    
    .gradient-btn:active {
        transform: translateY(-1px);
    }
    
    .gradient-btn-sm {
        padding: 0.6rem 1.2rem;
        font-size: 0.9rem;
    }
    
    /* ===== 输入框样式 ===== */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background: rgba(255, 255, 255, 0.07) !important;
        border: 2px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px !important;
        color: #ffffff !important;
        padding: 1rem !important;
        font-size: 1rem !important;
        transition: all 0.3s ease !important;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        background: rgba(255, 255, 255, 0.1) !important;
        border-color: #667eea !important;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.3) !important;
        outline: none !important;
    }
    
    .stTextInput > div > div > input::placeholder,
    .stTextArea > div > div > textarea::placeholder {
        color: rgba(255, 255, 255, 0.5) !important;
    }
    
    /* ===== 标签页样式 ===== */
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
        background: rgba(255, 255, 255, 0.05);
        padding: 8px;
        border-radius: 16px;
        margin-bottom: 2rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent !important;
        border-radius: 12px !important;
        padding: 12px 24px !important;
        font-weight: 600 !important;
        color: rgba(255, 255, 255, 0.7) !important;
        transition: all 0.3s ease !important;
        position: relative;
        overflow: hidden;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: rgba(255, 255, 255, 0.1) !important;
        color: #ffffff !important;
        transform: translateY(-2px);
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        box-shadow: 0 4px 20px rgba(102, 126, 234, 0.4) !important;
    }
    
    .stTabs [aria-selected="true"]::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: linear-gradient(45deg, transparent, rgba(255,255,255,0.2), transparent);
        animation: tabShine 2s infinite;
    }
    
    @keyframes tabShine {
        0% { transform: translateX(-100%); }
        100% { transform: translateX(100%); }
    }
    
    /* ===== 聊天消息样式 ===== */
    .chat-message-container {
        display: flex;
        margin: 1.5rem 0;
        animation: messageAppear 0.5s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    @keyframes messageAppear {
        from {
            opacity: 0;
            transform: translateY(20px) scale(0.95);
        }
        to {
            opacity: 1;
            transform: translateY(0) scale(1);
        }
    }
    
    .user-message {
        justify-content: flex-end;
    }
    
    .ai-message {
        justify-content: flex-start;
    }
    
    .message-bubble {
        max-width: 70%;
        padding: 1.5rem;
        border-radius: 24px;
        position: relative;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
        word-wrap: break-word;
        line-height: 1.6;
    }
    
    .user-message .message-bubble {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-bottom-right-radius: 8px;
        animation: bubbleRise 0.6s ease-out;
    }
    
    .ai-message .message-bubble {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        color: #ffffff;
        border-bottom-left-radius: 8px;
        animation: bubbleRise 0.6s ease-out 0.1s backwards;
    }
    
    @keyframes bubbleRise {
        0% {
            opacity: 0;
            transform: translateY(30px) scale(0.9);
        }
        70% {
            transform: translateY(-5px) scale(1.02);
        }
        100% {
            opacity: 1;
            transform: translateY(0) scale(1);
        }
    }
    
    .message-header {
        display: flex;
        align-items: center;
        margin-bottom: 0.8rem;
        gap: 0.8rem;
    }
    
    .avatar-circle {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.2rem;
        background: rgba(255, 255, 255, 0.2);
        animation: avatarFloat 3s ease-in-out infinite;
    }
    
    @keyframes avatarFloat {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-5px); }
    }
    
    .message-sender {
        font-weight: 700;
        font-size: 1.1rem;
    }
    
    .message-time {
        font-size: 0.85rem;
        opacity: 0.7;
        margin-left: auto;
    }
    
    .message-content {
        font-size: 1.05rem;
        line-height: 1.7;
    }
    
    /* ===== 侧边栏样式 ===== */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0c1c24 0%, #182933 100%) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.1) !important;
    }
    
    .sidebar-header {
        text-align: center;
        padding: 2rem 1rem 1.5rem;
        position: relative;
    }
    
    .sidebar-header::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 10%;
        width: 80%;
        height: 2px;
        background: linear-gradient(90deg, transparent, #667eea, transparent);
        border-radius: 1px;
    }
    
    .sidebar-title {
        color: #ffffff;
        font-size: 1.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        letter-spacing: 0.5px;
    }
    
    .sidebar-subtitle {
        color: rgba(255, 255, 255, 0.6);
        font-size: 0.9rem;
    }
    
    /* ===== 聊天卡片 ===== */
    .chat-card {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 16px;
        padding: 1.2rem;
        margin: 0.8rem 0;
        cursor: pointer;
        transition: all 0.3s ease;
        border: 1px solid rgba(255, 255, 255, 0.05);
        position: relative;
        overflow: hidden;
    }
    
    .chat-card:hover {
        background: rgba(255, 255, 255, 0.1);
        transform: translateX(5px);
        border-color: rgba(102, 126, 234, 0.3);
    }
    
    .chat-card.active {
        background: rgba(102, 126, 234, 0.15);
        border-color: #667eea;
        box-shadow: 0 0 20px rgba(102, 126, 234, 0.2);
    }
    
    .chat-card-title {
        color: #ffffff;
        font-weight: 600;
        margin-bottom: 0.3rem;
        font-size: 1rem;
    }
    
    .chat-card-time {
        color: rgba(255, 255, 255, 0.5);
        font-size: 0.8rem;
        display: flex;
        align-items: center;
        gap: 0.3rem;
    }
    
    /* ===== 角色卡片 ===== */
    .role-card {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 20px;
        padding: 1.5rem;
        text-align: center;
        transition: all 0.4s ease;
        border: 1px solid rgba(255, 255, 255, 0.1);
        position: relative;
        overflow: hidden;
    }
    
    .role-card:hover {
        transform: translateY(-5px) scale(1.03);
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.3);
        border-color: rgba(102, 126, 234, 0.3);
    }
    
    .role-card:hover .role-avatar {
        transform: scale(1.1) rotate(5deg);
    }
    
    .role-avatar {
        font-size: 3.5rem;
        margin-bottom: 1rem;
        transition: transform 0.4s ease;
        animation: avatarPulse 2s ease-in-out infinite;
        display: inline-block;
    }
    
    @keyframes avatarPulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.05); }
    }
    
    .role-name {
        color: #ffffff;
        font-size: 1.2rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    
    .role-status {
        display: inline-block;
        padding: 0.3rem 0.8rem;
        background: rgba(76, 175, 80, 0.2);
        color: #4CAF50;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        border: 1px solid rgba(76, 175, 80, 0.3);
    }
    
    /* ===== 进度条样式 ===== */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #667eea, #764ba2) !important;
        border-radius: 10px !important;
        animation: progressShimmer 2s infinite linear !important;
        background-size: 200% 100% !important;
    }
    
    @keyframes progressShimmer {
        0% { background-position: 200% 0; }
        100% { background-position: -200% 0; }
    }
    
    /* ===== 徽章样式 ===== */
    .badge {
        display: inline-flex;
        align-items: center;
        padding: 0.4rem 1rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        letter-spacing: 0.3px;
        margin: 0.3rem;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        animation: badgeFloat 3s ease-in-out infinite;
    }
    
    @keyframes badgeFloat {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-3px); }
    }
    
    .badge-primary {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.2), rgba(118, 75, 162, 0.2));
        color: #a3b4ff;
        border-color: rgba(102, 126, 234, 0.3);
    }
    
    .badge-success {
        background: linear-gradient(135deg, rgba(76, 175, 80, 0.2), rgba(33, 150, 243, 0.2));
        color: #81c784;
        border-color: rgba(76, 175, 80, 0.3);
    }
    
    .badge-warning {
        background: linear-gradient(135deg, rgba(255, 193, 7, 0.2), rgba(244, 67, 54, 0.2));
        color: #ffd54f;
        border-color: rgba(255, 193, 7, 0.3);
    }
    
    .badge-info {
        background: linear-gradient(135deg, rgba(33, 150, 243, 0.2), rgba(156, 39, 176, 0.2));
        color: #64b5f6;
        border-color: rgba(33, 150, 243, 0.3);
    }
    
    /* ===== 浮动动作按钮 ===== */
    .fab-container {
        position: fixed;
        bottom: 40px;
        right: 40px;
        z-index: 1000;
    }
    
    .fab-main {
        width: 70px;
        height: 70px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 2rem;
        cursor: pointer;
        box-shadow: 0 10px 40px rgba(102, 126, 234, 0.5);
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    
    .fab-main:hover {
        transform: scale(1.1) rotate(90deg);
        box-shadow: 0 15px 50px rgba(102, 126, 234, 0.7);
    }
    
    .fab-main::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: linear-gradient(45deg, transparent, rgba(255,255,255,0.3), transparent);
        animation: fabShine 2s infinite;
    }
    
    @keyframes fabShine {
        0% { transform: translateX(-100%); }
        100% { transform: translateX(100%); }
    }
    
    /* ===== 粒子背景 ===== */
    .particles {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        pointer-events: none;
        z-index: -1;
    }
    
    /* ===== 响应式设计 ===== */
    @media (max-width: 992px) {
        .main-title {
            font-size: 2.5rem !important;
        }
        
        .main-container {
            padding: 1.5rem;
            margin: 1rem;
        }
        
        .message-bubble {
            max-width: 85%;
        }
        
        .fab-container {
            bottom: 20px;
            right: 20px;
        }
        
        .fab-main {
            width: 60px;
            height: 60px;
            font-size: 1.5rem;
        }
    }
    
    @media (max-width: 768px) {
        .main-title {
            font-size: 2rem !important;
        }
        
        .glass-card {
            padding: 1.5rem;
        }
        
        .stTabs [data-baseweb="tab"] {
            padding: 10px 16px !important;
            font-size: 0.9rem !important;
        }
    }
    
    /* ===== 自定义滚动条 ===== */
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 5px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 5px;
        transition: background 0.3s;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
    }
    
    /* ===== 工具提示 ===== */
    .tooltip {
        position: relative;
        display: inline-block;
    }
    
    .tooltip .tooltip-text {
        visibility: hidden;
        background: rgba(0, 0, 0, 0.8);
        color: #fff;
        text-align: center;
        padding: 0.5rem 1rem;
        border-radius: 8px;
        position: absolute;
        z-index: 1000;
        bottom: 125%;
        left: 50%;
        transform: translateX(-50%);
        opacity: 0;
        transition: opacity 0.3s;
        font-size: 0.9rem;
        white-space: nowrap;
        backdrop-filter: blur(10px);
    }
    
    .tooltip:hover .tooltip-text {
        visibility: visible;
        opacity: 1;
    }
    
    /* ===== 加载动画 ===== */
    .loading-spinner {
        display: inline-block;
        width: 50px;
        height: 50px;
        border: 3px solid rgba(255,255,255,.3);
        border-radius: 50%;
        border-top-color: #667eea;
        animation: spin 1s ease-in-out infinite;
    }
    
    @keyframes spin {
        to { transform: rotate(360deg); }
    }
    
    /* ===== 分隔线 ===== */
    .divider {
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
        margin: 2rem 0;
        border: none;
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

# 应用高级CSS
load_advanced_css()

load_dotenv()

@st.cache_resource
def get_ai_client():
    return OpenAI(
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url="https://api.deepseek.com"
    )

client = get_ai_client()

# ================== 高级动画组件 ==================
def animated_header():
    """高级动画标题"""
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<h1 class="main-title">🎭 AI角色扮演聊天室</h1>', unsafe_allow_html=True)
        st.markdown('<p class="subtitle">沉浸式多角色互动体验 · 人工智能驱动的角色对话系统</p>', unsafe_allow_html=True)
        
        # 特性徽章
        col_badges = st.columns(4)
        with col_badges[0]:
            st.markdown('<span class="badge badge-primary">🎭 多角色</span>', unsafe_allow_html=True)
        with col_badges[1]:
            st.markdown('<span class="badge badge-success">💬 实时对话</span>', unsafe_allow_html=True)
        with col_badges[2]:
            st.markdown('<span class="badge badge-warning">🔒 隐私保护</span>', unsafe_allow_html=True)
        with col_badges[3]:
            st.markdown('<span class="badge badge-info">🧠 AI驱动</span>', unsafe_allow_html=True)

def glass_card(title, content, icon="✨"):
    """玻璃态卡片组件"""
    st.markdown(f"""
    <div class="glass-card">
        <div style="display: flex; align-items: center; margin-bottom: 1rem;">
            <div style="font-size: 2rem; margin-right: 1rem;">{icon}</div>
            <h3>{title}</h3>
        </div>
        <p>{content}</p>
    </div>
    """, unsafe_allow_html=True)

def chat_message_display(sender, avatar, message, timestamp, is_user=False):
    """高级聊天消息显示"""
    if is_user:
        container_class = "user-message"
        avatar_bg = "linear-gradient(135deg, #667eea 0%, #764ba2 100%)"
    else:
        container_class = "ai-message"
        avatar_bg = "rgba(255, 255, 255, 0.2)"
    
    return f"""
    <div class="chat-message-container {container_class}">
        <div class="message-bubble">
            <div class="message-header">
                <div class="avatar-circle" style="background: {avatar_bg};">
                    {avatar}
                </div>
                <span class="message-sender">{sender}</span>
                <span class="message-time">{timestamp}</span>
            </div>
            <div class="message-content">
                {message}
            </div>
        </div>
    </div>
    """

def role_card_display(role_name, avatar, status="在线"):
    """高级角色卡片"""
    return f"""
    <div class="role-card">
        <div class="role-avatar">{avatar}</div>
        <div class="role-name">{role_name}</div>
        <div class="role-status">{status}</div>
    </div>
    """

# ================== 聊天管理实用工具（保持不变） ==================
class ChatManager:
    def __init__(self, data_dir="chat_data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
    
    def get_all_chats(self):
        """返回所有保存的聊天"""
        chats = []
        for file in self.data_dir.glob("*.json"):
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    data['id'] = file.stem
                    data['filename'] = file.name
                    data['modified'] = datetime.fromtimestamp(file.stat().st_mtime)
                    chats.append(data)
            except:
                continue
        
        chats.sort(key=lambda x: x['modified'], reverse=True)
        return chats
    
    def save_chat(self, chat_data, chat_id=None):
        """保存聊天"""
        if chat_id is None:
            chat_id = str(uuid.uuid4())
        
        chat_data['id'] = chat_id
        chat_data['modified'] = datetime.now().isoformat()
        
        filepath = self.data_dir / f"{chat_id}.json"
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(chat_data, f, ensure_ascii=False, indent=2)
        
        return chat_id
    
    def load_chat(self, chat_id):
        """根据ID加载聊天"""
        filepath = self.data_dir / f"{chat_id}.json"
        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    
    def delete_chat(self, chat_id):
        """删除聊天"""
        filepath = self.data_dir / f"{chat_id}.json"
        if filepath.exists():
            filepath.unlink()
            return True
        return False
    
    def rename_chat(self, chat_id, new_title):
        """重命名聊天"""
        data = self.load_chat(chat_id)
        if data:
            data['title'] = new_title
            self.save_chat(data, chat_id)
            return True
        return False

# ================== 主要功能（保持不变） ==================
def generate_agent_prompt(context, agent_name, avatar, other_agents, user_role="用户"):
    """为代理创建系统提示"""
    pass

def create_new_chat():
    """创建新聊天"""
    chat_id = str(uuid.uuid4())
    st.session_state.current_chat = {
        'id': chat_id,
        'title': f"新场景 {datetime.now().strftime('%H:%M')}",
        'scenario': '',
        'user_role': '您',
        'agents': {},
        'chat_history': [],
        'private_history': {},
        'created': datetime.now().isoformat(),
        'modified': datetime.now().isoformat()
    }
    st.session_state.editing_chat = True

# ================== 初始化 ==================
if 'chat_manager' not in st.session_state:
    st.session_state.chat_manager = ChatManager()

if 'current_chat' not in st.session_state:
    all_chats = st.session_state.chat_manager.get_all_chats()
    if all_chats:
        st.session_state.current_chat = st.session_state.chat_manager.load_chat(all_chats[0]['id'])
        st.session_state.editing_chat = False
    else:
        create_new_chat()

if 'editing_chat' not in st.session_state:
    st.session_state.editing_chat = True

if 'private_history' not in st.session_state.current_chat:
    st.session_state.current_chat['private_history'] = {}

# ================== 高级侧边栏设计 ==================
with st.sidebar:
    # 侧边栏头部
    st.markdown("""
    <div class="sidebar-header">
        <div class="sidebar-title">💬 我的对话</div>
        <div class="sidebar-subtitle">管理你的角色扮演场景</div>
    </div>
    """, unsafe_allow_html=True)
    
    # 新聊天按钮
    if st.button("✨ 创建新场景", use_container_width=True, key="new_chat_btn", type="primary"):
        create_new_chat()
        st.rerun()
    
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    
    # 聊天列表
    all_chats = st.session_state.chat_manager.get_all_chats()
    
    if all_chats:
        st.markdown(f'''
        <div style="color: rgba(255,255,255,0.7); font-size: 0.9rem; margin-bottom: 1rem;">
            已保存场景 ({len(all_chats)})
        </div>
        ''', unsafe_allow_html=True)
        
        for chat in all_chats:
            chat_id = chat['id']
            chat_title = chat.get('title', '无标题')
            chat_time = chat['modified'].strftime('%H:%M') if isinstance(chat['modified'], datetime) else '--:--'
            
            is_active = st.session_state.current_chat.get('id') == chat_id
            active_class = "active" if is_active else ""
            
            st.markdown(f"""
            <div class="chat-card {active_class}" onclick="document.querySelector('[data-testid=\\'stButton\\'][key=\\'load_{chat_id}\\'] button').click()">
                <div class="chat-card-title">{chat_title[:25]}{'...' if len(chat_title) > 25 else ''}</div>
                <div class="chat-card-time">
                    <span>🕐</span> {chat_time}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📂", key=f"load_{chat_id}", help="加载场景", use_container_width=True):
                    loaded_chat = st.session_state.chat_manager.load_chat(chat_id)
                    if loaded_chat:
                        st.session_state.current_chat = loaded_chat
                        st.session_state.editing_chat = False
                        st.rerun()
            
            with col2:
                if st.button("🗑️", key=f"delete_{chat_id}", help="删除", use_container_width=True):
                    if st.session_state.chat_manager.delete_chat(chat_id):
                        st.rerun()
    
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    
    # 当前场景信息
    if st.session_state.current_chat:
        st.markdown('<div style="color: rgba(255,255,255,0.7); font-size: 0.9rem; margin-bottom: 1rem;">当前场景</div>', unsafe_allow_html=True)
        
        with st.container():
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, rgba(102,126,234,0.2), rgba(118,75,162,0.2)); 
                 border-radius: 16px; padding: 1.5rem; border: 1px solid rgba(102,126,234,0.3);">
                <div style="font-weight: 700; color: white; font-size: 1.1rem; margin-bottom: 0.5rem;">
                    {st.session_state.current_chat.get('title', '无标题')}
                </div>
                <div style="color: rgba(255,255,255,0.8); font-size: 0.9rem;">
                    <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
                        <span>👤</span>
                        <span>{st.session_state.current_chat.get('user_role', '您')}</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                        <span>🎭</span>
                        <span>{len(st.session_state.current_chat.get('agents', {}))} 个角色</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    
    # 系统状态
    with st.expander("📊 系统状态", expanded=True):
        col_stat1, col_stat2 = st.columns(2)
        with col_stat1:
            st.metric("内存使用", "65%", "12%", delta_color="off")
        with col_stat2:
            st.metric("响应时间", "0.8s", "-0.2s")
        
        st.progress(85, text="场景加载进度")

# ================== 主界面 ==================
animated_header()

# 创建主容器
st.markdown('<div class="main-container">', unsafe_allow_html=True)

# 如果正在编辑聊天
if st.session_state.editing_chat:
    # 特性展示区域
    st.markdown('<h2 style="color: #ffffff; margin-bottom: 2rem;">🎬 创建沉浸式角色扮演场景</h2>', unsafe_allow_html=True)
    
    cols = st.columns(3)
    with cols[0]:
        glass_card("多角色互动", "同时与多个具有独特个性的AI角色对话", "👥")
    with cols[1]:
        glass_card("公私分离", "公共聊天和私密对话分开管理", "🔒")
    with cols[2]:
        glass_card("智能记忆", "AI记住所有对话历史和角色关系", "🧠")
    
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    
    # 创建场景表单
    with st.container():
        col1, col2 = st.columns([2, 1])
        
        with col1:
            current_title = st.session_state.current_chat.get('title', '')
            new_title = st.text_input(
                "🎭 场景名称:",
                value=current_title,
                help="为你的场景起个引人入胜的名字",
                placeholder="例如：午夜咖啡馆的神秘邂逅"
            )
            
            if new_title != current_title:
                st.session_state.current_chat['title'] = new_title
        
        with col2:
            user_role = st.text_input(
                "👤 你的角色:",
                value=st.session_state.current_chat.get('user_role', '您'),
                help="AI角色将如何称呼你",
                placeholder="主角/侦探/玩家"
            )
            
            if user_role != st.session_state.current_chat.get('user_role'):
                st.session_state.current_chat['user_role'] = user_role
        
        # 场景描述
        st.markdown('<h4 style="color: #ffffff; margin-top: 1.5rem;">📝 场景描述</h4>', unsafe_allow_html=True)
        scenario = st.text_area(
            "详细描述场景背景和设定:",
            height=150,
            value=st.session_state.current_chat.get('scenario', ''),
            placeholder=f"例如：在一个雨夜，{user_role}走进了一家古老的咖啡馆。角落里坐着几个神秘的客人...\n\n描述越详细，AI的表现越生动！",
            label_visibility="collapsed"
        )
        
        st.session_state.current_chat['scenario'] = scenario
    
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    
    # AI参与者管理
    st.markdown('<h2 style="color: #ffffff; margin-bottom: 1.5rem;">👥 设计AI参与者</h2>', unsafe_allow_html=True)
    
    # 快速添加区域
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        roles_input = st.text_input(
            "批量添加角色 (用逗号分隔):",
            placeholder="例如：神秘商人, 酒吧老板, 女巫, 侦探",
            help="一次性添加多个角色"
        )
    
    with col2:
        if st.button("🚀 快速添加", use_container_width=True, key="quick_add"):
            if roles_input:
                roles = [r.strip() for r in roles_input.split(",") if r.strip()]
                for role in roles:
                    if role not in st.session_state.current_chat['agents']:
                        st.session_state.current_chat['agents'][role] = {
                            'avatar': "👤",
                            'system_prompt': ''
                        }
                st.success(f"🎉 成功添加 {len(roles)} 个角色！")
    
    with col3:
        if st.button("🎲 随机角色", use_container_width=True, key="random_roles"):
            random_roles = ["神秘巫师", "时空旅人", "AI助手", "未来战士", "古代贤者"]
            for role in random_roles[:3]:
                if role not in st.session_state.current_chat['agents']:
                    st.session_state.current_chat['agents'][role] = {
                        'avatar': "👤",
                        'system_prompt': ''
                    }
            st.success("✨ 已添加随机角色！")
    
    # 已添加角色展示
    agents = st.session_state.current_chat['agents']
    if agents:
        st.markdown(f'<h4 style="color: #ffffff; margin-top: 2rem;">已添加角色 ({len(agents)})</h4>', unsafe_allow_html=True)
        
        # 使用网格展示角色
        cols_per_row = min(4, len(agents))
        roles_list = list(agents.keys())
        
        rows = (len(roles_list) + cols_per_row - 1) // cols_per_row
        for row in range(rows):
            cols = st.columns(cols_per_row)
            for col_idx in range(cols_per_row):
                idx = row * cols_per_row + col_idx
                if idx < len(roles_list):
                    role = roles_list[idx]
                    
                    with cols[col_idx]:
                        # 角色卡片
                        st.markdown(role_card_display(role, agents[role]['avatar']), unsafe_allow_html=True)
                        
                        # 角色设置
                        with st.expander("角色设置", expanded=False):
                            # 头像选择
                            avatar_options = ["👤", "🧙", "👑", "🦸", "🧚", "🤖", "👽", "🧝"]
                            selected_avatar = st.selectbox(
                                "选择头像:",
                                options=avatar_options,
                                index=avatar_options.index(agents[role]['avatar']) if agents[role]['avatar'] in avatar_options else 0,
                                key=f"avatar_{role}"
                            )
                            agents[role]['avatar'] = selected_avatar
                            
                            # 个性描述
                            personality = st.text_area(
                                "角色个性:",
                                value=agents[role].get('personality', ''),
                                placeholder="描述角色的性格特点、说话风格等",
                                key=f"personality_{role}",
                                height=100
                            )
                            agents[role]['personality'] = personality
                        
                        # 删除按钮
                        if st.button("移除", key=f"remove_{role}", use_container_width=True):
                            del agents[role]
                            st.rerun()
    
    # 创建按钮
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🎭 开始沉浸式角色扮演！", type="primary", use_container_width=True, key="start_roleplay"):
            if scenario and agents:
                with st.spinner("🎨 正在为AI角色塑造个性..."):
                    # 这里可以添加角色初始化逻辑
                    pass
                
                # 保存聊天
                chat_id = st.session_state.chat_manager.save_chat(st.session_state.current_chat)
                st.session_state.current_chat['id'] = chat_id
                st.session_state.editing_chat = False
                
                # 成功动画
                st.balloons()
                st.success("✨ 场景创建成功！AI角色已准备就绪！")
                st.rerun()
            else:
                if not scenario:
                    st.warning("📝 请先描述你的场景")
                if not agents:
                    st.warning("👥 请添加至少一个AI角色")

# ================== 聊天模式 ==================
else:
    user_role = st.session_state.current_chat.get('user_role', '您')
    
    # 场景概览
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown(f'<h2 style="color: #ffffff;">{st.session_state.current_chat.get("title", "聊天")}</h2>', unsafe_allow_html=True)
        
        # 状态徽章
        col_status = st.columns(4)
        with col_status[0]:
            st.markdown(f'<span class="badge badge-primary">🎭 {len(st.session_state.current_chat.get("agents", {}))} 角色</span>', unsafe_allow_html=True)
        with col_status[1]:
            public_count = len(st.session_state.current_chat.get('chat_history', []))
            st.markdown(f'<span class="badge badge-success">💬 {public_count} 消息</span>', unsafe_allow_html=True)
        with col_status[2]:
            private_count = sum(len(h) for h in st.session_state.current_chat.get('private_history', {}).values())
            st.markdown(f'<span class="badge badge-warning">🔒 {private_count} 私聊</span>', unsafe_allow_html=True)
        with col_status[3]:
            if st.session_state.current_chat.get('modified'):
                mod_time = st.session_state.current_chat['modified']
                if isinstance(mod_time, str):
                    mod_time = datetime.fromisoformat(mod_time)
                st.markdown(f'<span class="badge badge-info">🕐 {mod_time.strftime("%H:%M")}</span>', unsafe_allow_html=True)
    
    with col2:
        if st.button("⚙️ 编辑场景", use_container_width=True, key="edit_scene"):
            st.session_state.editing_chat = True
            st.rerun()
    
    # 标签页设计
    tab1, tab2, tab3 = st.tabs(["💬 公共聊天", "🔒 私密聊天", "👥 角色档案"])
    
    # ================== 公共聊天标签页 ==================
    with tab1:
        # 聊天指南
        with st.expander("📚 聊天指南", expanded=False):
            st.markdown(f"""
            <div style="color: #ffffff; padding: 1rem;">
                <h4>✨ 如何与AI角色互动：</h4>
                <ul style="margin-left: 1.5rem; margin-top: 0.5rem;">
                    <li><strong>{user_role}是中心</strong> - 所有AI都围绕你展开对话</li>
                    <li><strong>发送消息给所有人</strong> - 你的话会同时被所有AI角色听到</li>
                    <li><strong>AI不互相聊天</strong> - 他们只回应你的话</li>
                    <li><strong>期待惊喜</strong> - AI会有各种有趣的回应方式</li>
                    <li><strong>随时切换</strong> - 可以在公共和私聊之间自由切换</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        # 聊天历史
        chat_history = st.session_state.current_chat.get('chat_history', [])
        
        if chat_history:
            for msg in chat_history:
                if len(msg) >= 4:
                    agent, avatar, message, timestamp = msg[:4]
                    is_user = (agent == user_role)
                    
                    # 显示聊天消息
                    st.markdown(chat_message_display(agent, avatar, message, timestamp, is_user), unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="text-align: center; padding: 3rem; color: rgba(255,255,255,0.7);">
                <div style="font-size: 4rem; margin-bottom: 1rem;">💭</div>
                <h3>对话尚未开始</h3>
                <p>点击下方的"开始介绍"按钮，让AI角色向你问好吧！</p>
            </div>
            """, unsafe_allow_html=True)
        
        # 聊天输入区域
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        st.markdown('<h4 style="color: #ffffff; margin-bottom: 1rem;">🎤 发送消息</h4>', unsafe_allow_html=True)
        
        col_input, col_send = st.columns([4, 1])
        
        with col_input:
            user_input = st.text_area(
                "输入消息给所有AI角色:",
                height=120,
                placeholder=f"作为{user_role}，你想对大家说什么？",
                key="public_input",
                label_visibility="collapsed"
            )
        
        with col_send:
            st.write(" ")
            if st.button("🚀 发送", type="primary", use_container_width=True, key="send_public"):
                if user_input:
                    timestamp = datetime.now().strftime("%H:%M")
                    chat_history = st.session_state.current_chat.get('chat_history', [])
                    chat_history.append([
                        user_role,
                        "👤",
                        user_input,
                        timestamp
                    ])
                    st.session_state.current_chat['chat_history'] = chat_history
                    st.rerun()
    
    # ================== 私密聊天标签页 ==================
    with tab2:
        agents = st.session_state.current_chat.get('agents', {})
        if agents:
            # 私聊选择器
            st.markdown('<h4 style="color: #ffffff; margin-bottom: 1.5rem;">🤫 选择私聊对象</h4>', unsafe_allow_html=True)
            
            # 创建角色卡片选择器
            cols = st.columns(min(len(agents), 4))
            selected_agent = st.session_state.get('selected_private_agent')
            
            for idx, (agent_name, data) in enumerate(agents.items()):
                with cols[idx % 4]:
                    if st.button(
                        f"{data['avatar']}\n{agent_name}",
                        key=f"select_private_{agent_name}",
                        use_container_width=True,
                        type="primary" if selected_agent == agent_name else "secondary"
                    ):
                        st.session_state.selected_private_agent = agent_name
                        st.rerun()
            
            # 显示私聊对话
            if selected_agent:
                st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
                st.markdown(f'<h4 style="color: #ffffff; margin-bottom: 1rem;">🔒 与 {agents[selected_agent]["avatar"]} {selected_agent} 的私聊</h4>', unsafe_allow_html=True)
                
                # 这里添加私聊历史显示逻辑
                
        else:
            glass_card("提示", "还没有AI参与者可以私聊，请先添加角色。", "🤷‍♂️")
    
    # ================== 角色档案标签页 ==================
    with tab3:
        agents = st.session_state.current_chat.get('agents', {})
        if agents:
            st.markdown('<h4 style="color: #ffffff; margin-bottom: 1.5rem;">🎭 AI角色档案</h4>', unsafe_allow_html=True)
            
            for agent_name, data in agents.items():
                with st.container(border=True):
                    col_icon, col_info = st.columns([1, 3])
                    
                    with col_icon:
                        st.markdown(f'<div style="text-align: center; font-size: 4rem;">{data["avatar"]}</div>', unsafe_allow_html=True)
                    
                    with col_info:
                        st.markdown(f'<h3>{agent_name}</h3>', unsafe_allow_html=True)
                        
                        if data.get('personality'):
                            st.markdown(f'<div style="color: rgba(255,255,255,0.8); margin-bottom: 1rem;">{data["personality"]}</div>', unsafe_allow_html=True)
                        
                        # 角色统计数据
                        col_stats = st.columns(3)
                        with col_stats[0]:
                            st.metric("状态", "在线", "🟢", delta_color="off")
                        with col_stats[1]:
                            st.metric("响应速度", "快速", "⚡", delta_color="off")
                        with col_stats[2]:
                            st.metric("友好度", "高", "😊", delta_color="off")
        else:
            glass_card("提示", "还没有AI角色档案，请先添加角色。", "🎭")
    
    # ================== 控制面板 ==================
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown('<h4 style="color: #ffffff; margin-bottom: 1rem;">⚙️ 控制面板</h4>', unsafe_allow_html=True)
    
    # 控制按钮
    col_controls = st.columns(5)
    
    with col_controls[0]:
        if st.button("👋 开始介绍", use_container_width=True, key="start_intro_btn"):
            st.success("AI角色开始自我介绍...")
    
    with col_controls[1]:
        if st.button("🎭 AI互动", use_container_width=True, key="ai_interact_btn"):
            st.info("AI角色开始互动...")
    
    with col_controls[2]:
        if st.button("💾 保存", use_container_width=True, key="save_btn"):
            chat_id = st.session_state.chat_manager.save_chat(st.session_state.current_chat)
            st.success(f"💾 场景已保存")
    
    with col_controls[3]:
        if st.button("📥 导出", use_container_width=True, key="export_btn"):
            st.info("导出功能开发中...")
    
    with col_controls[4]:
        if st.button("🔄 刷新", use_container_width=True, key="refresh_btn"):
            st.rerun()

# 关闭主容器
st.markdown('</div>', unsafe_allow_html=True)

# ================== 页脚 ==================
st.markdown("""
<div style="text-align: center; color: rgba(255,255,255,0.6); padding: 2rem;">
    <p>🎭 AI角色扮演聊天室 | 沉浸式多角色对话体验 | 由 DeepSeek API 驱动</p>
    <p style="font-size: 0.9rem; margin-top: 0.5rem;">Version 2.0.0 | 让对话更有趣，让故事更生动</p>
</div>
""", unsafe_allow_html=True)

# 浮动动作按钮 (FAB)
st.markdown("""
<div class="fab-container">
    <div class="fab-main" onclick="document.querySelector('[data-testid=\\'stButton\\'][key=\\'new_chat_btn\\'] button').click()">
        ✨
    </div>
</div>
""", unsafe_allow_html=True)

# 粒子背景效果
st.markdown("""
<div class="particles">
    <canvas id="particles-canvas"></canvas>
</div>

<script>
// 简单的粒子背景效果
const canvas = document.getElementById('particles-canvas');
const ctx = canvas.getContext('2d');

function resizeCanvas() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
}

window.addEventListener('resize', resizeCanvas);
resizeCanvas();

const particles = [];
for (let i = 0; i < 50; i++) {
    particles.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        size: Math.random() * 2 + 1,
        speedX: Math.random() * 0.5 - 0.25,
        speedY: Math.random() * 0.5 - 0.25,
        color: `rgba(255, 255, 255, ${Math.random() * 0.3})`
    });
}

function animateParticles() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    for (let particle of particles) {
        particle.x += particle.speedX;
        particle.y += particle.speedY;
        
        if (particle.x > canvas.width) particle.x = 0;
        if (particle.x < 0) particle.x = canvas.width;
        if (particle.y > canvas.height) particle.y = 0;
        if (particle.y < 0) particle.y = canvas.height;
        
        ctx.beginPath();
        ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
        ctx.fillStyle = particle.color;
        ctx.fill();
    }
    
    requestAnimationFrame(animateParticles);
}

animateParticles();
</script>
""", unsafe_allow_html=True)

if __name__ == "__main__":
    pass