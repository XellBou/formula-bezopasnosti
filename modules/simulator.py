"""Модуль 10. Ролевой симулятор спасателя (Hardcore mode)."""
import streamlit as st
import os
import random
import json

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from gigachat import GigaChat
from gigachat.models import Chat, Messages, MessagesRole

# Безопасное получение ключа
try:
    GIGA_CREDENTIALS = st.secrets["GIGACHAT_CREDENTIALS"]
except Exception:
    GIGA_CREDENTIALS = os.getenv("GIGACHAT_CREDENTIALS")

def generate_scenario():
    """Генерирует случайную вводную с жесткими скрытыми угрозами."""
    prompt = """
    Ты — генератор сценариев для игры "Симулятор спасателя" в режиме Хардкор.
    Придумай ситуацию (пожар, ДТП, обрушение, химическая авария, спасение на воде).
    ВАЖНО: Придумай СКРЫТУЮ УГРОЗУ, которую игрок не увидит сразу. (например: газовый баллон, обрыв провода под водой, взрывчатка, больной COVID, запертая решетка на окне).
    
    Верни ответ СТРОГО в формате JSON без markdown:
    {
        "scenario_name": "Короткое название (например: Пожар в подвале)",
        "situation": "Текст вводной для игрока (2-3 предложения)."
    }
    """
    try:
        with GigaChat(
            credentials=GIGA_CREDENTIALS,
            base_url="https://api.giga.chat/v1",
            model="GigaChat-3-Ultra",
            scope="GIGACHAT_API_PERS",
            verify_ssl_certs=False
        ) as giga:
            messages = [Messages(role=MessagesRole.USER, content=prompt)]
            response_data = giga.chat(Chat(messages=messages, model="GigaChat-3-Ultra"))
            raw_text = response_data.choices[0].message.content.strip()
            
            if raw_text.startswith("```json"):
                raw_text = raw_text[7:-3]
            elif raw_text.startswith("```"):
                raw_text = raw_text[3:-3]
                
            data = json.loads(raw_text.strip())
            return data["scenario_name"], data["situation"]
    except Exception:
        return "Пожар в высотном здании", "Горит 5-й этаж. Из окон валит дым. Внутри могут быть люди. На балконе замечен газовый баллон."

def init_game():
    """Инициализирует новую игру."""
    if "sim_health" not in st.session_state:
        st.session_state.sim_health = 1 # Всего 1 ошибка - и конец игры
    
    if "sim_messages" not in st.session_state or st.session_state.sim_health <= 0:
        scenario_name, situation = "Инициализация...", "Загрузка..."
        
        if GIGA_CREDENTIALS:
            with st.spinner("Генерация нового вызова..."):
                scenario_name, situation = generate_scenario()
        else:
            scenario_name, situation = "Тестовый вызов", "Тестовый сценарий (ключ GigaChat не найден)."
            
        st.session_state.sim_scenario = scenario_name
        st.session_state.sim_health = 1
        
        system_prompt = f"""
        Ты — ведущий текстового симулятора спасателя в режиме ХАРДКОР. Сценарий: {scenario_name}.
        {situation}
        
        ПРАВИЛА ИГРЫ:
        1. Игрок — командир отделения. Он пишет свои действия.
        2. Ты строгий, придирчивый. Ты наказываешь за нарушение техники безопасности.
        3. Если игрок вбегает в очаг БЕЗ СИЗОД, не отключает электричество перед тушением, не выставляет пост безопасности, не проверяет скрытые угрозы (газовый баллон, взрывчатка, решетки) — напиши в начале ответа тег **[ОШИБКА]**, опиши, как он пострадал, и напиши, что игра окончена.
        4. Если игрок выполняет ВСЕ действия по уставу (проверка СИЗОД, разведка, пост безопасности) — напиши **[УСПЕХ]**.
        5. Если игрок задает правильный вопрос (например, "есть ли в здании газовые баллоны?" или "отключено ли электричество?") — раскрой ему скрытую угрозу и дай шанс ее устранить.
        6. Будь краток (2-3 предложения). Всегда спрашивай: "Что делаете дальше?".
        """
        
        st.session_state.sim_messages = [
            {"role": "system", "content": system_prompt},
            {"role": "assistant", "content": f"🚨 **Вызов: {scenario_name}**\n\n{situation}\n\n**Ваши первые действия, командир?**"}
        ]

def evaluate_game():
    """ИИ выставляет оценку."""
    eval_prompt = """
    Ты — начальник караула. Оцени действия курсанта по 5-балльной шкале.
    Если он потерпел поражение (получил ошибку) — ставь 2. 
    Если спас людей без ошибок — ставь 5.
    Ответь в формате: **Оценка: [X]** \n**Разбор:** [Что сделано верно, что упущено]
    """
    history = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.sim_messages if m['role'] != 'system'])
    
    try:
        with GigaChat(
            credentials=GIGA_CREDENTIALS,
            base_url="https://api.giga.chat/v1",
            model="GigaChat-3-Ultra",
            scope="GIGACHAT_API_PERS",
            verify_ssl_certs=False
        ) as giga:
            messages = [
                Messages(role=MessagesRole.SYSTEM, content=eval_prompt),
                Messages(role=MessagesRole.USER, content=f"Диалог:\n{history}")
            ]
            response_data = giga.chat(Chat(messages=messages, model="GigaChat-3-Ultra"))
            return response_data.choices[0].message.content
    except Exception as e:
        return f"Ошибка оценки: {e}"

def send_action(action_text):
    """Отправляет действие в ИИ и обновляет жизни."""
    st.session_state.sim_messages.append({"role": "user", "content": action_text})
    
    try:
        with GigaChat(
            credentials=GIGA_CREDENTIALS,
            base_url="https://api.giga.chat/v1",
            model="GigaChat-3-Ultra",
            scope="GIGACHAT_API_PERS",
            verify_ssl_certs=False
        ) as giga:
            giga_messages = []
            for m in st.session_state.sim_messages:
                role = MessagesRole.SYSTEM if m["role"] == "system" else MessagesRole.USER if m["role"] == "user" else MessagesRole.ASSISTANT
                giga_messages.append(Messages(role=role, content=m["content"]))
            
            payload = Chat(messages=giga_messages, model="GigaChat-3-Ultra")
            response_data = giga.chat(payload)
            response = response_data.choices[0].message.content
            
            # Если ИИ нашел смертельную ошибку - конец игры
            if "[ОШИБКА]" in response:
                st.session_state.sim_health = 0
                eval_result = evaluate_game()
                st.session_state.sim_evaluation = eval_result
                
            st.session_state.sim_messages.append({"role": "assistant", "content": response})
    except Exception as e:
        st.session_state.sim_messages.append({"role": "assistant", "content": f"Ошибка связи: {e}"})

def render() -> None:
    st.header("🎮 Симулятор спасателя (Hardcore)")
    st.markdown(
        "Управляйте отделением. В этом режиме **у вас есть только ОДНА жизнь**. "
        "Любая ошибка в технике безопасности, игнорирование скрытых угроз или необдуманный шаг приведут к провалу миссии."
    )
    
    if not GIGA_CREDENTIALS:
        st.warning("⚠️ Ключи GigaChat не найдены. Симулятор недоступен.")
        return

    # Кнопка новой игры
    if st.button("🔄 Начать новую смену", use_container_width=True):
        for key in list(st.session_state.keys()):
            if key.startswith("sim_"):
                del st.session_state[key]
        st.rerun()

    # Инициализация
    init_game()

    # Отображение статуса
    col1, col2 = st.columns([3, 1])
    with col1:
        st.info(f"📍 **Сценарий:** {st.session_state.sim_scenario}")
    with col2:
        health = st.session_state.sim_health
        if health > 0:
            st.markdown("### 🟢 В строю")
        else:
            st.markdown("### 🔴 Выведен из строя")

    # Если игра окончена
    if st.session_state.sim_health <= 0 and "sim_evaluation" in st.session_state:
        st.error("🚨 **МИССИЯ ПРОВАЛЕНА**")
        st.success(st.session_state.sim_evaluation)
        return

    # История
    for msg in st.session_state.sim_messages:
        if msg["role"] != "system":
            with st.chat_message("assistant" if msg["role"] == "assistant" else "user"):
                st.markdown(msg["content"])

    # --- КНОПКИ БЫСТРЫХ ДЕЙСТВИЙ ---
    st.markdown("**Быстрые действия:**")
    c1, c2, c3, c4 = st.columns(4)
    if c1.button("🫁 Надеть СИЗОД", use_container_width=True):
        send_action("Надеваю СИЗОД, проверяю давление и герметичность.")
        st.rerun()
    if c2.button("🛡 Пост безопасности", use_container_width=True):
        send_action("Выставляю пост безопасности на входе.")
        st.rerun()
    if c3.button("⚡ Отключить свет", use_container_width=True):
        send_action("Отключаю электричество на вводе в здание.")
        st.rerun()
    if c4.button("👀 Разведка", use_container_width=True):
        send_action("Провожу разведку: ищу людей, оцениваю скрытые угрозы (газ, баллоны).")
        st.rerun()

    # Поле ввода
    if prompt := st.chat_input("Ваше действие (или используйте кнопки выше)..."):
        send_action(prompt)
        st.rerun()