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
def generate_agent_prompt(context, agent_name, avatar, other_agents):
    """为代理创建系统提示"""
    
    other_names = ", ".join([f"{name} ({agents[name]})" for name in other_agents])
    
    prompt = f"""
    上下文: {context}
    
    你是 {agent_name} (头像: {avatar})。
    
    其他参与者: {other_names}
    
    创建你的角色描述包括:
    1. 性格 (3个关键特征)
    2. 在此情境下的目标
    3. 对其他参与者的态度
    4. 说话风格
    5. 头像 {avatar} 如何反映你的性格
    
    仅以JSON格式回复:
    {{
        "personality": "性格描述",
        "goals": ["目标 1", "目标 2", "目标 3"],
        "relationships": {{"其他角色": "态度"}},
        "speech_style": "说话风格",
        "avatar_meaning": "头像含义"
    }}
    """
    
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你正在为角色扮演游戏创建角色。仅以JSON格式回复。"},
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
                        "goals": ["完成你的角色"],
                        "relationships": {},
                        "speech_style": "根据角色身份说话",
                        "avatar_meaning": f"头像 {avatar} 反映了角色的本质"
                    }
            else:
                # 如果根本找不到JSON，创建基本数据
                agent_data = {
                    "personality": f"角色 {agent_name}",
                    "goals": ["完成你的角色"],
                    "relationships": {},
                    "speech_style": "根据角色身份说话",
                    "avatar_meaning": f"头像 {avatar} 反映了角色的本质"
                }
        
        # 创建最终提示
        system_prompt = f"""
        # 角色: {agent_name}
        # 头像: {avatar} ({agent_data.get('avatar_meaning', '')})
        
        ## 上下文:
        {context}
        
        ## 你的性格:
        {agent_data['personality']}
        
        ## 你的目标:
        {chr(10).join(['• ' + goal for goal in agent_data['goals']])}
        
        ## 你的说话风格:
        {agent_data['speech_style']}
        
        ## 与他人的关系:
        {chr(10).join([f'• {other}: {relation}' for other, relation in agent_data.get('relationships', {}).items()])}
        
        ## 规则:
        1. 始终保持 {agent_name} 的角色
        2. 自然地回应其他参与者
        3. 记住你的目标和关系
        4. 像真人一样说话，不要像AI
        5. 使用自然的情绪和反应
        6. 不要打破"第四面墙"
        
        ## 其他参与者:
        {other_names}
        
        自然地开始对话!
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
                    key=f"rename_btn_{chat_id}",  # 已更改密钥！
                    help="重命名聊天",
                    use_container_width=True
                ):
                    st.session_state.renaming_chat = chat_id
                    st.rerun()
            
            with col3:
                # 删除按钮（方形）
                if st.button(
                    "🗑️",
                    key=f"delete_btn_{chat_id}",  # 已更改密钥！
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
    
    st.divider()
    
    # 场景
    scenario = st.text_area(
        "📝 描述场景:",
        height=150,
        placeholder="示例: 小巷里的劫匪试图抢劫女孩。警察出现了。我是一个目睹一切的随机路人...",
        help="描述越详细，AI越能理解上下文"
    )
    
    st.session_state.current_chat['scenario'] = scenario
    
    st.divider()
    
    # 参与者
    st.header("👥 添加参与者")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        roles_input = st.text_input(
            "参与者姓名 (用逗号分隔):",
            placeholder="劫匪, 女孩, 警察, 我, 路人"
        )
    
    with col2:
        st.write(" ")
        st.write(" ")
        if st.button("➕ 添加参与者", use_container_width=True):
            if roles_input:
                roles = [r.strip() for r in roles_input.split(",") if r.strip()]
                
                # 自动选择头像
                auto_avatars = {
                    "劫匪": "😈", "女孩": "👩", "警察": "👮",
                    "我": "👤", "路人": "🚶", "医生": "👨‍⚕️",
                    "老师": "👨‍🏫", "学生": "👦", "校长": "👔"
                }
                
                for role in roles:
                    if role not in st.session_state.current_chat['agents']:
                        avatar = auto_avatars.get(role, "👤")
                        st.session_state.current_chat['agents'][role] = {
                            'avatar': avatar,
                            'system_prompt': ''
                        }
    
    # 编辑参与者
    if st.session_state.current_chat['agents']:
        st.write("**配置参与者:**")
        
        agents = st.session_state.current_chat['agents']
        roles_list = list(agents.keys())
        
        cols = st.columns(min(3, len(roles_list)))
        
        for idx, role in enumerate(roles_list):
            col_idx = idx % len(cols)
            
            with cols[col_idx]:
                with st.container(border=True):
                    # 选择头像
                    current_avatar = agents[role]['avatar']
                    
                    # 常用头像
                    popular = ["👤", "👨", "👩", "👮", "😈", "🚶", "🦸", "🧙", "🤖", "👽"]
                    
                    selected_avatar = st.selectbox(
                        f"{role} 的头像:",
                        options=popular,
                        index=popular.index(current_avatar) if current_avatar in popular else 0,
                        key=f"avatar_{role}"
                    )
                    
                    agents[role]['avatar'] = selected_avatar
                    
                    # 删除按钮
                    if st.button(f"🗑️ 删除 {role}", key=f"del_{role}", use_container_width=True):
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
                            other_avatars
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
                    
                    st.success("✅ 代理已创建并聊天已保存！")
                    st.rerun()

# ================== 聊天模式 ==================
else:
    # 标题
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.header(f"💬 {st.session_state.current_chat.get('title', '聊天')}")
    
    with col2:
        if st.button("✏️ 编辑", use_container_width=True):
            st.session_state.editing_chat = True
            st.rerun()
    
    # 显示场景
    with st.expander("📖 显示场景", expanded=False):
        st.write(st.session_state.current_chat.get('scenario', '无描述'))
    
    # 聊天历史
    chat_history = st.session_state.current_chat.get('chat_history', [])
    
    if chat_history:
        for agent, avatar, message, timestamp in chat_history:
            with st.chat_message("user" if agent == "您" else "assistant", avatar=avatar):
                st.markdown(f"**{agent}:** {message}")
                st.caption(timestamp)
    else:
        st.info("💡 点击'开始对话'让代理开始交流！")
    
    # 对话管理
    st.divider()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("▶️ 开始对话", use_container_width=True):
            # 第一轮
            agents = st.session_state.current_chat['agents']
            
            for agent_name in agents.keys():
                # 准备开始消息
                response = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {"role": "system", "content": agents[agent_name]['system_prompt']},
                        {"role": "user", "content": "场景开始。自我介绍并自然地开始对话。"}
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
        if st.button("🔁 继续对话", use_container_width=True):
            # 继续对话
            agents = st.session_state.current_chat['agents']
            
            for agent_name in agents.keys():
                # 为代理构建历史记录
                history_messages = []
                for h_agent, h_avatar, h_msg, h_time in chat_history[-6:]:
                    role = "user" if h_agent == agent_name else "assistant"
                    history_messages.append({"role": role, "content": f"{h_agent}: {h_msg}"})
                
                # 请求响应
                messages = [
                    {"role": "system", "content": agents[agent_name]['system_prompt']},
                    *history_messages,
                    {"role": "user", "content": f"{agent_name}，现在你会说什么？"}
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
    
    with col3:
        if st.button("🗑️ 清除历史", use_container_width=True):
            st.session_state.current_chat['chat_history'] = []
            st.session_state.chat_manager.save_chat(st.session_state.current_chat)
            st.rerun()
    
    # 消息输入
    st.divider()
    st.subheader("🎤 您的消息")

    user_input = st.text_area("输入消息:", height=100)
    
    # 发送消息
    if user_input and st.button("📤 发送消息", type="primary", use_container_width=True):
        # 添加用户消息
        timestamp = datetime.now().strftime('%H:%M:%S')
        chat_history.append(("您", "👤", user_input, timestamp))
        
        # 每个代理响应
        agents = st.session_state.current_chat['agents']
        
        for agent_name in agents.keys():
            # 构建历史记录
            history_messages = []
            for h_agent, h_avatar, h_msg, h_time in chat_history[-8:]:
                role = "user" if h_agent == agent_name else "assistant"
                history_messages.append({"role": role, "content": f"{h_agent}: {h_msg}"})
            
            # 请求响应
            messages = [
                {"role": "system", "content": agents[agent_name]['system_prompt']},
                *history_messages,
                {"role": "user", "content": f"用户说: '{user_input}'。{agent_name}，你会如何回应？"}
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
    
    # 自动保存
    if chat_history:
        st.caption(f"💾 自动保存: {datetime.now().strftime('%H:%M:%S')}")

# ================== 页脚 ==================
st.divider()
col1, col2, col3 = st.columns(3)

with col1:
    st.caption(f"💬 消息数: {len(st.session_state.current_chat.get('chat_history', []))}")

with col2:
    st.caption(f"👥 参与者数: {len(st.session_state.current_chat.get('agents', {}))}")

with col3:
    if st.session_state.current_chat.get('modified'):
        mod_time = st.session_state.current_chat['modified']
        if isinstance(mod_time, str):
            mod_time = datetime.fromisoformat(mod_time)
        st.caption(f"🕐 修改于: {mod_time.strftime('%H:%M')}")

if __name__ == "__main__":
    pass