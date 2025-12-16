import streamlit as st
import os
import json
import uuid
import tempfile
from datetime import datetime
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
import base64
from io import BytesIO

PDF_AVAILABLE = False
VOICE_AVAILABLE = False

# ================== 设置 ==================
st.set_page_config(
    page_title="终极聊天管理器 🚀",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

load_dotenv()

@st.cache_resource
def get_ai_client():
    return OpenAI(
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url="https://api.deepseek.com"
    )

client = get_ai_client()

# ================== 聊天管理实用工具 ==================
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
        
        # 按修改日期排序（新的在前）
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

# ================== 主要功能 ==================
def generate_agent_prompt(context, agent_name, avatar, other_agents, user_role="用户"):
    """为代理创建系统提示 - 重点: AI代理不互相聊天，只对用户说话"""
    
    other_names = ", ".join([f"{name} ({agents[name]})" for name in other_agents])
    
    prompt = f"""
    上下文: {context}
    
    你是 {agent_name} (头像: {avatar})。
    
    其他参与者: {other_names}
    
    ## 重要规则:
    1. 你不直接与其他AI代理聊天
    2. 你只与 {user_role} 交互
    3. 你基于场景和角色对 {user_role} 做出回应
    4. 如果其他AI代理说了什么，你只应把它作为场景的一部分，而不是直接回应他们
    5. 你的主要对话对象始终是 {user_role}
    
    创建你的角色描述包括:
    1. 性格 (3个关键特征)
    2. 在此情境下对 {user_role} 的目标
    3. 对 {user_role} 的态度
    4. 说话风格 (如何与 {user_role} 交流)
    5. 头像 {avatar} 如何反映你的性格
    
    仅以JSON格式回复:
    {{
        "personality": "性格描述",
        "goals": ["目标 1", "目标 2", "目标 3"],
        "user_attitude": "对用户的态度",
        "speech_style": "说话风格",
        "avatar_meaning": "头像含义",
        "interaction_style": "如何与用户互动"
    }}
    """
    
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你正在为角色扮演游戏创建角色。AI代理只与用户互动，不互相聊天。仅以JSON格式回复。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8,
            max_tokens=600
        )
        
        result = response.choices[0].message.content
        
        # 改进的JSON清理
        import re
        
        # 删除第一个 { 之前的所有内容
        result = re.sub(r'^[^{]*', '', result)
        # 删除最后一个 } 之后的所有内容
        result = re.sub(r'[^}]*$', '', result)
        
        # 修复JSON中的常见错误
        # 1. 未闭合的字符串
        result = re.sub(r',\s*\]', ']', result)  # ] 前的多余逗号
        result = re.sub(r',\s*}', '}', result)   # } 前的多余逗号
        
        # 2. 字符串中的引号
        result = re.sub(r'(?<!\\)"', '"', result)  # 标准化引号
        
        # 3. 省略号和特殊字符
        result = result.replace('...', '…')  # 替换省略号
        
        try:
            agent_data = json.loads(result.strip())
        except json.JSONDecodeError as e:
            # 如果无法解析，尝试修复
            st.warning(f"正在尝试修复 {agent_name} 的JSON...")
            
            # 尝试更积极地查找JSON
            json_match = re.search(r'\{.*\}', result, re.DOTALL)
            if json_match:
                result = json_match.group(0)
                # 删除数组/对象末尾的多余逗号
                result = re.sub(r',(\s*[}\]])', r'\1', result)
                
                try:
                    agent_data = json.loads(result)
                except:
                    # 创建备用数据
                    agent_data = {
                        "personality": f"角色 {agent_name}",
                        "goals": [f"与{user_role}互动", f"完成场景中的角色"],
                        "user_attitude": f"友好",
                        "speech_style": f"直接与{user_role}说话",
                        "avatar_meaning": f"头像 {avatar} 反映了角色的本质",
                        "interaction_style": f"专注回应{user_role}"
                    }
            else:
                # 如果根本找不到JSON，创建基本数据
                agent_data = {
                    "personality": f"角色 {agent_name}",
                    "goals": [f"与{user_role}互动", f"完成场景中的角色"],
                    "user_attitude": f"友好",
                    "speech_style": f"直接与{user_role}说话",
                    "avatar_meaning": f"头像 {avatar} 反映了角色的本质",
                    "interaction_style": f"专注回应{user_role}"
                }
        
        # 创建最终提示 - 强调只与用户互动
        system_prompt = f"""
        # 角色: {agent_name}
        # 头像: {avatar} ({agent_data.get('avatar_meaning', '')})
        
        ## 上下文:
        {context}
        
        ## 你的性格:
        {agent_data['personality']}
        
        ## 你的目标:
        {chr(10).join(['• ' + goal for goal in agent_data['goals']])}
        
        ## 你对用户的态度:
        {agent_data['user_attitude']}
        
        ## 你的说话风格:
        {agent_data['speech_style']}
        
        ## 互动方式:
        {agent_data['interaction_style']}
        
        ## 重要规则:
        1. 你只与{user_role}直接对话，不与其他AI代理聊天
        2. 始终保持{agent_name}的角色
        3. 如果其他角色说了什么，把它作为背景信息，但不是回应的对象
        4. 你的回应应针对{user_role}
        5. 使用自然的情绪和反应，但只面向{user_role}
        6. 不要打破"第四面墙"
        7. 等待{user_role}的输入来回应
        
        ## 其他AI代理 (不直接对话):
        {other_names}
        
        等待{user_role}开始互动!
        """
        
        return system_prompt
        
    except Exception as e:
        st.error(f"创建代理 {agent_name} 时出错: {str(e)}")
        st.code(f"原始响应: {result[:200]}...")
        return None

def create_new_chat():
    """创建新聊天"""
    chat_id = str(uuid.uuid4())
    st.session_state.current_chat = {
        'id': chat_id,
        'title': f"新聊天 {datetime.now().strftime('%H:%M')}",
        'scenario': '',
        'user_role': '您',  # 添加用户角色字段
        'agents': {},
        'chat_history': [],
        'created': datetime.now().isoformat(),
        'modified': datetime.now().isoformat()
    }
    st.session_state.editing_chat = True

# ================== 初始化 ==================
if 'chat_manager' not in st.session_state:
    st.session_state.chat_manager = ChatManager()

if 'current_chat' not in st.session_state:
    # 检查是否有保存的聊天
    all_chats = st.session_state.chat_manager.get_all_chats()
    if all_chats:
        # 加载最新聊天
        st.session_state.current_chat = st.session_state.chat_manager.load_chat(all_chats[0]['id'])
        st.session_state.editing_chat = False
    else:
        # 仅在没有保存的聊天时创建新聊天
        create_new_chat()

if 'editing_chat' not in st.session_state:
    st.session_state.editing_chat = True

# ================== 扩展的图标集 ==================
AVATAR_ICONS = {
    # 基本人物
    "👤": "中性人", "👨": "男人", "👩": "女人", "🧑": "成人", "👦": "男孩", "👧": "女孩",
    
    # 职业
    "👮": "警察", "👮‍♀️": "女警", "👨‍⚕️": "男医生", "👩‍⚕️": "女医生", "👨‍🍳": "厨师", 
    "👩‍🍳": "女厨师", "👨‍🎓": "学生", "👩‍🎓": "女学生", "👨‍🏫": "老师", "👩‍🏫": "女老师",
    "👨‍💼": "商务人士", "👩‍💼": "女商务", "👨‍🔧": "技工", "👩‍🔧": "女技工", "👨‍🚒": "消防员",
    "👩‍🚒": "女消防员", "👨‍✈️": "飞行员", "👩‍✈️": "女飞行员", "👨‍🚀": "宇航员", "👩‍🚀": "女宇航员",
    
    # 幻想/角色
    "🦸": "超级英雄", "🦸‍♀️": "女英雄", "🦹": "超级反派", "🦹‍♀️": "女反派",
    "🧙": "巫师", "🧙‍♀️": "女巫", "🧚": "仙子", "🧚‍♀️": "女仙子", "🧚‍♂️": "男仙子",
    "🧛": "吸血鬼", "🧛‍♀️": "女吸血鬼", "🧟": "僵尸", "🧟‍♀️": "女僵尸",
    
    # 表情/情感
    "😊": "微笑", "😎": "酷", "🤓": "书呆子", "🧐": "侦探", "🤠": "牛仔",
    "😈": "恶魔", "👿": "愤怒恶魔", "😇": "天使", "🤡": "小丑", "👺": "妖怪",
    "👹": "食人魔", "👻": "鬼魂", "💀": "骷髅", "🤖": "机器人", "👽": "外星人",
    "🎩": "魔术师", "🧢": "年轻人", "👑": "国王/女王", "💍": "贵族",
    
    # 动物/生物
    "🐶": "狗", "🐱": "猫", "🐭": "老鼠", "🐹": "仓鼠", "🐰": "兔子",
    "🦊": "狐狸", "🐻": "熊", "🐼": "熊猫", "🐨": "考拉", "🐯": "老虎",
    "🦁": "狮子", "🐮": "牛", "🐷": "猪", "🐸": "青蛙", "🐵": "猴子",
    "🐔": "鸡", "🐧": "企鹅", "🐦": "鸟", "🐴": "马", "🦄": "独角兽",
    "🐙": "章鱼", "🦑": "鱿鱼", "🦀": "螃蟹", "🐢": "乌龟", "🐍": "蛇",
    "🦖": "恐龙", "🐉": "龙", "🦅": "鹰", "🦉": "猫头鹰", "🦇": "蝙蝠",
    
    # 其他角色
    "🧍": "站立人", "🧍‍♂️": "站立男人", "🧍‍♀️": "站立女人", "🚶": "行人", 
    "🚶‍♂️": "行走男人", "🚶‍♀️": "行走女人", "🏃": "跑步者", "🏃‍♂️": "跑步男人",
    "🏃‍♀️": "跑步女人", "💂": "卫兵", "💂‍♀️": "女卫兵", "👷": "建筑工人",
    "👷‍♀️": "女建筑工", "🕵️": "侦探", "🕵️‍♀️": "女侦探", "👰": "新娘", "🤵": "新郎",
    
    # 神话/历史
    "👸": "公主", "🤴": "王子", "🧝": "精灵", "🧝‍♀️": "女精灵", "🧝‍♂️": "男精灵",
    "🧞": "精灵", "🧞‍♀️": "女精灵", "🧞‍♂️": "男精灵", "🧜": "美人鱼", "🧜‍♀️": "美人鱼",
    "🧜‍♂️": "男人鱼", "🧟‍♂️": "男僵尸", "⚔️": "武士", "🛡️": "骑士",
    
    # 现代/日常
    "👨‍💻": "程序员", "👩‍💻": "女程序员", "👨‍🎨": "艺术家", "👩‍🎨": "女艺术家",
    "👨‍🎤": "歌手", "👩‍🎤": "女歌手", "👨‍🎤": "音乐家", "👩‍🎤": "女音乐家",
    "🕺": "舞者", "💃": "女舞者", "👯": "兔子女郎", "👯‍♂️": "男兔子"
}

def get_avatar_suggestions(role_name):
    """根据角色名称建议图标"""
    role_lower = role_name.lower()
    
    suggestions = {
        # 警察相关
        "警察": ["👮", "👮‍♀️", "🚓", "⚖️"],
        "劫匪": ["😈", "🦹", "👿", "💀"],
        "医生": ["👨‍⚕️", "👩‍⚕️", "🏥", "💊"],
        "老师": ["👨‍🏫", "👩‍🏫", "📚", "✏️"],
        "学生": ["👨‍🎓", "👩‍🎓", "🎒", "📖"],
        "程序员": ["👨‍💻", "👩‍💻", "💻", "⌨️"],
        "厨师": ["👨‍🍳", "👩‍🍳", "🍳", "🔪"],
        # 添加更多映射...
    }
    
    for key, icons in suggestions.items():
        if key in role_lower:
            return icons
    
    # 默认返回一些常用图标
    return ["👤", "🧑", "😊", "🤔"]

# ================== 侧边栏 - 聊天列表 ==================
with st.sidebar:
    st.title("💬 我的聊天")
    
    # 新聊天按钮
    if st.button("➕ 新聊天", use_container_width=True):
        create_new_chat()
        st.rerun()
    
    st.divider()
    
    # 已保存聊天列表
    all_chats = st.session_state.chat_manager.get_all_chats()
    
    if all_chats:
        st.write(f"📁 已保存聊天: {len(all_chats)}")
        
        for chat in all_chats:
            chat_id = chat['id']
            chat_title = chat.get('title', '无标题')
            chat_time = chat['modified'].strftime('%H:%M') if isinstance(chat['modified'], datetime) else '--:--'
            
            # 一行内的简单字符串和按钮
            col1, col2, col3 = st.columns([6, 1, 1])
            
            with col1:
                # 主要的加载聊天按钮（宽）
                if st.button(
                    f"💬 {chat_title[:18]}{'...' if len(chat_title) > 18 else ''}",
                    key=f"load_{chat_id}",
                    help=f"加载聊天 (修改于: {chat_time})",
                    use_container_width=True
                ):
                    loaded_chat = st.session_state.chat_manager.load_chat(chat_id)
                    if loaded_chat:
                        st.session_state.current_chat = loaded_chat
                        st.session_state.editing_chat = False
                        st.rerun()
            
            with col2:
                # 重命名按钮（方形）
                if st.button(
                    "✏️",
                    key=f"rename_btn_{chat_id}",
                    help="重命名聊天",
                    use_container_width=True
                ):
                    st.session_state.renaming_chat = chat_id
                    st.rerun()
            
            with col3:
                # 删除按钮（方形）
                if st.button(
                    "🗑️",
                    key=f"delete_btn_{chat_id}",
                    help="删除聊天",
                    use_container_width=True
                ):
                    if st.session_state.chat_manager.delete_chat(chat_id):
                        st.rerun()
    
    else:
        st.info("📭 无保存的聊天")
    
    st.divider()
    
    # 重命名对话框
    if 'renaming_chat' in st.session_state:
        chat_id = st.session_state.renaming_chat
        chat = st.session_state.chat_manager.load_chat(chat_id)
        
        if chat:
            new_title = st.text_input(
                "新标题:",
                value=chat.get('title', ''),
                key=f"rename_input_{chat_id}"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ 保存", use_container_width=True):
                    if new_title:
                        st.session_state.chat_manager.rename_chat(chat_id, new_title)
                        if st.session_state.current_chat.get('id') == chat_id:
                            st.session_state.current_chat['title'] = new_title
                        del st.session_state.renaming_chat
                        st.rerun()
            
            with col2:
                if st.button("❌ 取消", use_container_width=True):
                    del st.session_state.renaming_chat
                    st.rerun()
    
    st.divider()
    
    # 当前聊天信息
    if st.session_state.current_chat:
        st.write("**当前聊天:**")
        st.info(f"📝 {st.session_state.current_chat.get('title', '无标题')}")
        
        agents = st.session_state.current_chat.get('agents', {})
        if agents:
            st.write("**参与者:**")
            for name, data in agents.items():
                st.write(f"{data.get('avatar', '👤')} {name}")
    
    st.divider()
    
    # 导出当前聊天
    if st.session_state.current_chat.get('chat_history'):
        st.write("**导出:**")
        
        # JSON导出
        json_data = json.dumps(st.session_state.current_chat, ensure_ascii=False, indent=2)
        st.download_button(
            label="📥 下载 JSON",
            data=json_data,
            file_name=f"chat_{st.session_state.current_chat['id']}.json",
            mime="application/json",
            use_container_width=True
        )

# ================== 主界面 ==================
st.title("🚀 终极聊天管理器")

# 如果正在编辑聊天
if st.session_state.editing_chat:
    st.header("🎬 创建新聊天")
    
    # 聊天标题
    current_title = st.session_state.current_chat.get('title', '')
    new_title = st.text_input(
        "聊天标题:",
        value=current_title,
        help="为保存起一个有意义的名字"
    )
    
    if new_title != current_title:
        st.session_state.current_chat['title'] = new_title
    
    # 用户角色名称
    user_role = st.text_input(
        "您在场景中的称呼:",
        value=st.session_state.current_chat.get('user_role', '您'),
        help="AI代理将如何称呼您（例如：玩家、主角、英雄等）"
    )
    
    if user_role != st.session_state.current_chat.get('user_role'):
        st.session_state.current_chat['user_role'] = user_role
    
    st.divider()
    
    # 场景
    scenario = st.text_area(
        "📝 描述场景:",
        height=150,
        placeholder=f"示例: 小巷里的劫匪试图抢劫女孩。警察出现了。{user_role}是一个目睹一切的随机路人...\n\n重点: 描述{user_role}的角色和AI代理如何与{user_role}互动",
        help="描述越详细，AI越能理解上下文。确保描述用户如何参与"
    )
    
    st.session_state.current_chat['scenario'] = scenario
    
    st.divider()
    
    # 参与者
    st.header("👥 添加参与者")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        roles_input = st.text_input(
            "AI参与者姓名 (用逗号分隔):",
            placeholder="劫匪, 女孩, 警察, 路人"
        )
    
    with col2:
        st.write(" ")
        st.write(" ")
        if st.button("➕ 添加参与者", use_container_width=True):
            if roles_input:
                roles = [r.strip() for r in roles_input.split(",") if r.strip()]
                
                for role in roles:
                    if role not in st.session_state.current_chat['agents']:
                        # 获取建议的图标
                        suggestions = get_avatar_suggestions(role)
                        avatar = suggestions[0] if suggestions else "👤"
                        st.session_state.current_chat['agents'][role] = {
                            'avatar': avatar,
                            'system_prompt': ''
                        }
    
    # 编辑参与者
    if st.session_state.current_chat['agents']:
        st.write("**配置AI参与者:**")
        st.caption(f"这些AI角色将与 {user_role} 互动，但不互相聊天")
        
        agents = st.session_state.current_chat['agents']
        roles_list = list(agents.keys())
        
        # 按行显示，每行最多3个
        for i in range(0, len(roles_list), 3):
            cols = st.columns(3)
            for col_idx in range(3):
                if i + col_idx < len(roles_list):
                    role = roles_list[i + col_idx]
                    
                    with cols[col_idx]:
                        with st.container(border=True):
                            st.write(f"**{role}**")
                            
                            # 获取建议的图标
                            suggestions = get_avatar_suggestions(role)
                            current_avatar = agents[role]['avatar']
                            
                            # 如果当前图标不在建议中，添加到列表开头
                            if current_avatar not in suggestions:
                                suggestions = [current_avatar] + suggestions
                            
                            # 限制显示的图标数量
                            display_icons = suggestions[:10]  # 最多显示10个
                            
                            # 图标选择器
                            selected_avatar = st.selectbox(
                                "选择头像:",
                                options=display_icons,
                                index=0,
                                key=f"avatar_{role}_{i}",
                                label_visibility="collapsed"
                            )
                            
                            # 或者使用更直观的图标选择器
                            st.write("快速选择:")
                            icon_cols = st.columns(5)
                            quick_icons = suggestions[:5]  # 快速选择前5个
                            
                            for idx, icon in enumerate(quick_icons):
                                with icon_cols[idx]:
                                    if st.button(
                                        icon,
                                        key=f"quick_{role}_{icon}",
                                        use_container_width=True
                                    ):
                                        selected_avatar = icon
                            
                            agents[role]['avatar'] = selected_avatar
                            
                            # 删除按钮
                            if st.button(f"🗑️ 删除 {role}", key=f"del_{role}_{i}", use_container_width=True):
                                del agents[role]
                                st.rerun()
    
    st.divider()
    
    # 创建代理
    if scenario and st.session_state.current_chat['agents']:
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            if st.button("🤖 创建AI代理并开始！", type="primary", use_container_width=True):
                with st.spinner("正在创建AI代理..."):
                    agents_info = st.session_state.current_chat['agents']
                    
                    # 添加进度条
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    for i, agent_name in enumerate(agents_info.keys()):
                        status_text.text(f"正在创建 {agent_name}...")
                        
                        other_agents = [name for name in agents_info.keys() if name != agent_name]
                        other_avatars = {name: agents_info[name]['avatar'] for name in other_agents}
                        
                        system_prompt = generate_agent_prompt(
                            scenario,
                            agent_name,
                            agents_info[agent_name]['avatar'],
                            other_avatars,
                            st.session_state.current_chat.get('user_role', '您')
                        )
                        
                        if system_prompt:
                            agents_info[agent_name]['system_prompt'] = system_prompt
                        
                        # 更新进度
                        progress_bar.progress((i + 1) / len(agents_info))
                    
                    # 清除指示器
                    status_text.empty()
                    progress_bar.empty()
                    
                    # 保存聊天
                    chat_id = st.session_state.chat_manager.save_chat(st.session_state.current_chat)
                    st.session_state.current_chat['id'] = chat_id
                    st.session_state.editing_chat = False
                    
                    st.success(f"✅ 代理已创建！现在{user_role}可以与AI角色互动了！")
                    st.rerun()

# ================== 聊天模式 ==================
else:
    user_role = st.session_state.current_chat.get('user_role', '您')
    
    # 标题
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.header(f"💬 {st.session_state.current_chat.get('title', '聊天')}")
        st.caption(f"**您的角色:** {user_role}")
    
    with col2:
        if st.button("✏️ 编辑", use_container_width=True):
            st.session_state.editing_chat = True
            st.rerun()
    
    # 显示场景
    with st.expander("📖 显示场景", expanded=False):
        scenario = st.session_state.current_chat.get('scenario', '无描述')
        st.write(scenario)
        
        # 显示参与者
        agents = st.session_state.current_chat.get('agents', {})
        if agents:
            st.write("\n**AI参与者:**")
            for name, data in agents.items():
                st.write(f"{data.get('avatar', '👤')} **{name}**")
    
    st.divider()
    
    # 重要提示框
    with st.container(border=True):
        st.info(f"""
        💡 **互动模式说明:**
        
        1. **{user_role}是场景的中心** - 所有AI角色都直接与您互动
        2. **AI角色不互相聊天** - 他们只对您的输入做出反应
        3. **集体响应** - 当您发送消息时，所有AI角色都会同时回应
        4. **保持您的参与** - 场景围绕您展开
        """)
    
    # 聊天历史
    chat_history = st.session_state.current_chat.get('chat_history', [])
    
    if chat_history:
        for agent, avatar, message, timestamp in chat_history:
            is_user = (agent == user_role)
            
            with st.chat_message("user" if is_user else "assistant", avatar=avatar):
                if is_user:
                    st.markdown(f"**{agent}:** {message}")
                else:
                    # 对于AI角色，突出显示
                    st.markdown(f"**{avatar} {agent}:**")
                    st.markdown(f"{message}")
                st.caption(timestamp)
    else:
        st.info(f"💡 点击'开始介绍'让AI角色向{user_role}自我介绍，然后开始对话！")
    
    # 对话管理
    st.divider()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("👋 开始介绍", use_container_width=True):
            # 让每个AI角色向用户自我介绍
            agents = st.session_state.current_chat['agents']
            
            for agent_name in agents.keys():
                response = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {"role": "system", "content": agents[agent_name]['system_prompt']},
                        {"role": "user", "content": f"场景开始。{user_role}在场。向{user_role}介绍你自己并开始互动。"}
                    ],
                    temperature=0.8,
                    max_tokens=200
                )
                
                message = response.choices[0].message.content
                timestamp = datetime.now().strftime('%H:%M:%S')
                
                chat_history.append((agent_name, agents[agent_name]['avatar'], message, timestamp))
            
            # 保存
            st.session_state.chat_manager.save_chat(st.session_state.current_chat)
            st.rerun()
    
    with col2:
        if st.button("🔁 请求回应", use_container_width=True):
            # 用户没有输入新消息，但想获取AI的回应
            if chat_history:
                agents = st.session_state.current_chat['agents']
                
                for agent_name in agents.keys():
                    # 获取最近的对话历史
                    recent_history = []
                    for h_agent, h_avatar, h_msg, h_time in chat_history[-5:]:  # 最后5条消息
                        role = "user" if h_agent == user_role else "assistant"
                        recent_history.append({"role": role, "content": f"{h_agent}: {h_msg}"})
                    
                    # 请求AI回应最近的对话
                    messages = [
                        {"role": "system", "content": agents[agent_name]['system_prompt']},
                        *recent_history,
                        {"role": "user", "content": f"基于最近的对话，{agent_name}，你想对{user_role}说什么？"}
                    ]
                    
                    response = client.chat.completions.create(
                        model="deepseek-chat",
                        messages=messages,
                        temperature=0.7,
                        max_tokens=250
                    )
                    
                    message = response.choices[0].message.content
                    timestamp = datetime.now().strftime('%H:%M:%S')
                    
                    chat_history.append((agent_name, agents[agent_name]['avatar'], message, timestamp))
                
                # 保存
                st.session_state.chat_manager.save_chat(st.session_state.current_chat)
                st.rerun()
            else:
                st.warning("请先开始对话！")
    
    with col3:
        if st.button("🗑️ 清除历史", use_container_width=True):
            st.session_state.current_chat['chat_history'] = []
            st.session_state.chat_manager.save_chat(st.session_state.current_chat)
            st.rerun()
    
    # 消息输入
    st.divider()
    st.subheader(f"🎤 {user_role}的消息")

    user_input = st.text_area(f"输入{user_role}的消息:", height=100, placeholder=f"作为{user_role}，你会说什么？")
    
    # 发送消息
    if user_input and st.button("📤 发送消息", type="primary", use_container_width=True):
        # 添加用户消息
        timestamp = datetime.now().strftime('%H:%M:%S')
        chat_history.append((user_role, "👤", user_input, timestamp))
        
        # 每个AI代理响应（集体响应）
        agents = st.session_state.current_chat['agents']
        
        for agent_name in agents.keys():
            # 构建历史记录（只关注用户和当前AI的互动）
            history_messages = []
            
            # 包括用户的消息
            history_messages.append({"role": "user", "content": f"{user_role}: {user_input}"})
            
            # 可能包括最近的其他AI回应作为上下文
            for h_agent, h_avatar, h_msg, h_time in chat_history[-4:-1]:  # 不包括最新的用户消息
                if h_agent == agent_name:
                    history_messages.append({"role": "assistant", "content": f"{h_agent}: {h_msg}"})
                elif h_agent == user_role:
                    history_messages.append({"role": "user", "content": f"{h_agent}: {h_msg}"})
            
            # 请求AI回应
            messages = [
                {"role": "system", "content": agents[agent_name]['system_prompt']},
                *history_messages,
                {"role": "user", "content": f"{user_role}刚刚说了：'{user_input}'。{agent_name}，你会如何回应{user_role}？"}
            ]
            
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=messages,
                temperature=0.7,
                max_tokens=300
            )
            
            message = response.choices[0].message.content
            timestamp = datetime.now().strftime('%H:%M:%S')
            
            chat_history.append((agent_name, agents[agent_name]['avatar'], message, timestamp))
        
        # 保存
        st.session_state.chat_manager.save_chat(st.session_state.current_chat)
        
        st.rerun()
    
    # 自动保存提示
    if chat_history:
        st.caption(f"💾 自动保存: {datetime.now().strftime('%H:%M:%S')}")

# ================== 页脚 ==================
st.divider()
col1, col2, col3 = st.columns(3)

with col1:
    st.caption(f"💬 消息数: {len(st.session_state.current_chat.get('chat_history', []))}")

with col2:
    st.caption(f"🤖 AI参与者数: {len(st.session_state.current_chat.get('agents', {}))}")

with col3:
    if st.session_state.current_chat.get('modified'):
        mod_time = st.session_state.current_chat['modified']
        if isinstance(mod_time, str):
            mod_time = datetime.fromisoformat(mod_time)
        st.caption(f"🕐 修改于: {mod_time.strftime('%H:%M')}")

if __name__ == "__main__":
    pass