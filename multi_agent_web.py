import streamlit as st
import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime

# ================== НАСТРОЙКА ==================
st.set_page_config(page_title="Multi-Agent Chat", layout="wide")
load_dotenv()

@st.cache_resource
def get_ai_client():
    return OpenAI(
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url="https://api.deepseek.com"
    )

client = get_ai_client()

# ================== СОСТОЯНИЕ ==================
if "scenario" not in st.session_state:
    st.session_state.scenario = None
if "agents" not in st.session_state:
    st.session_state.agents = {}  # {имя: {аватар, system_prompt}}
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []  # [(агент, аватар, сообщение)]
if "conversation_started" not in st.session_state:
    st.session_state.conversation_started = False

# ================== ФУНКЦИИ ==================
def generate_agent_prompt(context, agent_name, avatar, other_agents):
    """Создает системный промпт для агента"""
    
    other_names = ", ".join(other_agents)
    
    prompt = f"""
    Контекст: {context}
    
    Ты {agent_name} (аватар: {avatar}).
    
    Другие участники: {other_names}
    
    Создай описание своего персонажа:
    1. Твой характер (3 черты)
    2. Твои цели в этой ситуации
    3. Как ты относишься к другим участникам
    4. Твой стиль речи
    
    Ответь ТОЛЬКО в JSON:
    {{
        "personality": "твой характер",
        "goals": ["цель 1", "цель 2"],
        "speech_style": "как ты говоришь"
    }}
    """
    
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "Ты создаешь персонажей для ролевой игры. Отвечай только в JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        result = response.choices[0].message.content
        # Чистим JSON от лишнего текста
        if "```json" in result:
            result = result.split("```json")[1].split("```")[0]
        elif "```" in result:
            result = result.split("```")[1].split("```")[0]
        
        agent_data = json.loads(result.strip())
        
        # Создаем финальный системный промпт
        system_prompt = f"""
        Ты {agent_name} в ситуации: {context}
        Твой аватар: {avatar}
        
        Твой характер: {agent_data['personality']}
        Твои цели: {', '.join(agent_data['goals'])}
        Твой стиль речи: {agent_data['speech_style']}
        
        Другие участники: {other_names}
        
        Правила:
        1. Всегда оставайся в роли {agent_name}
        2. Реагируй естественно на других
        3. Помни о своих целях
        4. Говори как реальный человек
        5. Не говори что ты ИИ
        """
        
        return system_prompt
        
    except Exception as e:
        st.error(f"Ошибка создания агента {agent_name}: {e}")
        return None

def create_agents(context, agents_info):
    """Создает всех агентов"""
    st.session_state.agents = {}
    
    for agent_name, avatar in agents_info.items():
        other_agents = [name for name in agents_info.keys() if name != agent_name]
        system_prompt = generate_agent_prompt(context, agent_name, avatar, other_agents)
        
        if system_prompt:
            st.session_state.agents[agent_name] = {
                "avatar": avatar,
                "system_prompt": system_prompt
            }
    
    st.session_state.scenario = context
    st.session_state.conversation_started = True
    st.session_state.chat_history = []

def get_agent_response(agent_name, history_for_agent):
    """Получает ответ от агента"""
    
    agent = st.session_state.agents[agent_name]
    messages = [{"role": "system", "content": agent["system_prompt"]}]
    
    # Добавляем историю
    for other_agent, avatar, msg in history_for_agent:
        role = "user" if other_agent == agent_name else "assistant"
        messages.append({"role": role, "content": f"{other_agent}: {msg}"})
    
    # Просим ответить
    messages.append({"role": "user", "content": f"Что скажешь сейчас, {agent_name}?"})
    
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            temperature=0.7,
            max_tokens=300
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Ошибка: {e}"

def start_conversation():
    """Начинает диалог между агентами"""
    if not st.session_state.agents:
        return
    
    # Первый раунд - все представляются
    for agent_name in st.session_state.agents.keys():
        history = st.session_state.chat_history[-3:] if st.session_state.chat_history else []
        response = get_agent_response(agent_name, history)
        
        st.session_state.chat_history.append((
            agent_name,
            st.session_state.agents[agent_name]["avatar"],
            response
        ))

# ================== ИНТЕРФЕЙС ==================
st.title("🤖 Multi-Agent Chat Simulator")
st.markdown("Создай сценарий и наблюдай как AI-агенты общаются между собой!")

# Шаг 1: Создание сценария
if not st.session_state.conversation_started:
    st.header("🎬 Шаг 1: Создай сценарий")
    
    # Ввод контекста
    context = st.text_area(
        "Опиши ситуацию:",
        height=100,
        placeholder="Пример: Бандит в подворотне пытается ограбить девушку. Появляется полицейский. Я - случайный прохожий."
    )
    
    st.divider()
    
    # Ввод ролей и аватаров
    st.header("👥 Шаг 2: Добавь участников")
    
    # Сначала вводим имена ролей
    roles_input = st.text_input(
        "Имена участников через запятую:",
        placeholder="Бандит, Девушка, Полицейский, Я, Прохожий"
    )
    
    agents_info = {}
    
    if roles_input:
        roles = [r.strip() for r in roles_input.split(",") if r.strip()]
        
        # Для каждой роли выбираем аватар
        for role in roles:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**{role}**")
            with col2:
                # Простой выбор аватара
                avatars = ["👤", "👨", "👩", "👮", "😈", "🚶", "🦸", "🧙", "🤖", "👽"]
                selected = st.selectbox(
                    "Аватар:",
                    avatars,
                    index=0,
                    key=f"avatar_{role}",
                    label_visibility="collapsed"
                )
                agents_info[role] = selected
    
    st.divider()
    
    # Кнопка создания
    if st.button("🚀 Создать агентов и начать!", type="primary"):
        if context and agents_info:
            with st.spinner("Создаю AI-агентов..."):
                create_agents(context, agents_info)
            st.rerun()
        else:
            st.error("Заполни все поля!")

# Шаг 2: Чат агентов
else:
    # Сайдбар управления
    with st.sidebar:
        st.header("⚙️ Управление")
        
        st.write("**Сценарий:**")
        st.info(st.session_state.scenario[:100] + "...")
        
        st.write("**Участники:**")
        for name, data in st.session_state.agents.items():
            st.write(f"{data['avatar']} {name}")
        
        st.divider()
        
        if st.button("▶️ Начать диалог", use_container_width=True):
            start_conversation()
            st.rerun()
        
        if st.button("🔄 Еще один раунд", use_container_width=True):
            # Каждый агент отвечает на последние сообщения
            for agent_name in st.session_state.agents.keys():
                history = st.session_state.chat_history[-5:] if st.session_state.chat_history else []
                response = get_agent_response(agent_name, history)
                st.session_state.chat_history.append((
                    agent_name,
                    st.session_state.agents[agent_name]["avatar"],
                    response
                ))
            st.rerun()
        
        if st.button("🗑️ Очистить чат", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()
        
        if st.button("🔄 Новый сценарий", use_container_width=True):
            for key in ["scenario", "agents", "chat_history", "conversation_started"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
    
    # Основная область - чат
    st.header("💬 Диалог агентов")
    
    if st.session_state.chat_history:
        for agent_name, avatar, message in st.session_state.chat_history:
            with st.chat_message("user" if agent_name == "Я" else "assistant", avatar=avatar):
                st.markdown(f"**{agent_name}:** {message}")
    else:
        st.info("Нажми 'Начать диалог' в сайдбаре 👈")
    
    # Ручное вмешательство
    st.divider()
    st.subheader("🎤 Вмешаться в диалог")
    
    user_msg = st.text_input("Скажи что-то агентам:", placeholder="Эй, что здесь происходит?")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📢 Сказать всем", use_container_width=True):
            if user_msg:
                # Добавляем сообщение пользователя
                st.session_state.chat_history.append(("Вы", "👤", user_msg))
                
                # Каждый агент реагирует
                for agent_name in st.session_state.agents.keys():
                    history = st.session_state.chat_history[-5:] if st.session_state.chat_history else []
                    history.append(("Вы", "👤", user_msg))
                    
                    response = get_agent_response(agent_name, history)
                    st.session_state.chat_history.append((
                        agent_name,
                        st.session_state.agents[agent_name]["avatar"],
                        response
                    ))
                st.rerun()
    
    with col2:
        selected_agent = st.selectbox(
            "Выбрать агента:",
            list(st.session_state.agents.keys()),
            label_visibility="collapsed"
        )
        
        if st.button(f"🎯 Ответить {selected_agent}", use_container_width=True):
            if user_msg:
                # Добавляем сообщение пользователя
                st.session_state.chat_history.append(("Вы", "👤", user_msg))
                
                # Только выбранный агент отвечает
                history = st.session_state.chat_history[-5:] if st.session_state.chat_history else []
                history.append(("Вы", "👤", user_msg))
                
                response = get_agent_response(selected_agent, history)
                st.session_state.chat_history.append((
                    selected_agent,
                    st.session_state.agents[selected_agent]["avatar"],
                    response
                ))
                st.rerun()
    
    # Инфо
    st.caption(f"📊 Сообщений: {len(st.session_state.chat_history)} | Агентов: {len(st.session_state.agents)}")

if __name__ == "__main__":
    pass