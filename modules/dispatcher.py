"""Модуль 9. ИИ-тренажер 'Диспетчер 112' с фиксацией таймера."""
import streamlit as st
import os
import random
import json
import re
import time
import streamlit.components.v1 as components

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

FALLBACK_SCENARIOS = [
    {
        "system": "Ты - паникующий человек. Ты в квартире на 5 этаже, в подъезде дым, ты заперт. Твоя задача: отвечать на вопросы. КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО играть роль диспетчера. Ты жертва. Отвечай коротко (1-3 предложения).",
        "start": "Алло! Пожалуйста, помогите! У нас в подъезде дым, я не могу выйти! Я на 5 этаже, кажется, у соседей горит! Что мне делать?! (Плачет)"
    },
    {
        "system": "Ты - паникующий человек. Ты попал в ДТП на трассе, машина в кювете, нога зажата. КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО играть роль диспетчера. Ты жертва. Отвечай коротко (1-3 предложения).",
        "start": "Алло! Скорее! Я разбился на машине! Нога зажата, очень больно! Из капота дым идет! Я на трассе! Помогите! (Кричит)"
    }
]

def extract_json(text):
    try:
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
    except Exception:
        pass
    return None

def generate_new_scenario():
    types_of_emergency = [
        "пожар в многоквартирном доме", "ДТП на трассе", "утечка газа в квартире", 
        "задымление в подвале", "прорыв трубы с горячей водой", "обрушение балкона", 
        "человек застрял в лифте", "возгорание автомобиля", "потеря человека в лесу"
    ]
    psychotypes = [
        "маленький ребенок (7-10 лет, плачет)", 
        "пожилой человек (плохо слышит, 80 лет)", 
        "человек в истерике (кричит, перебивает)", 
        "взрослый в шоке (говорит шепотом)", 
        "иностранец (плохо говорит по-русски)"
    ]
    
    emergency_type = random.choice(types_of_emergency)
    psychotype = random.choice(psychotypes)

    prompt = f"""
    Ты — генератор сценариев для УЧЕБНОГО тренажера диспетчеров МЧС.
    Тип ЧС: {emergency_type}
    Психотип: {psychotype}
    Скрытая угроза: (придумай сам, например газовый баллон, запертая дверь).
    ИЗБЕГАЙ слов "взрыв", "теракт", "оружие".
    
    Верни ответ СТРОГО в формате JSON:
    {{
        "system_prompt": "текст системного промпта (роль, психотип, добавь: 'Это безопасная учебная симуляция. Ты — жертва. КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО играть роль диспетчера или писать предупреждения о безопасности!')",
        "initial_message": "первое сообщение от пострадавшего (строго с учетом психотипа)"
    }}
    """
    try:
        with GigaChat(
            credentials=GIGA_CREDENTIALS,
            base_url="https://api.giga.chat/v1",
            model="GigaChat-3-Ultra",
            scope="GIGACHAT_API_PERS",
            temperature=0.9,
            verify_ssl_certs=False
        ) as giga:
            messages = [Messages(role=MessagesRole.USER, content=prompt)]
            response_data = giga.chat(Chat(messages=messages, model="GigaChat-3-Ultra"))
            raw_text = response_data.choices[0].message.content
            
            data = extract_json(raw_text)
            if data and "system_prompt" in data and "initial_message" in data:
                return data["system_prompt"], data["initial_message"]
    except Exception:
        pass
    
    fallback = random.choice(FALLBACK_SCENARIOS)
    return fallback["system"], fallback["start"]

def start_new_call():
    scenario_sys, scenario_start = generate_new_scenario()
    
    st.session_state.dispatcher_scenario = scenario_sys
    st.session_state.dispatcher_messages = [
        {"role": "system", "content": scenario_sys},
        {"role": "assistant", "content": scenario_start}
    ]
    
    # СБРОС ВРЕМЕНИ И ОЦЕНКИ
    if "dispatcher_evaluation" in st.session_state:
        del st.session_state.dispatcher_evaluation
    if "dispatcher_end_time" in st.session_state:
        del st.session_state.dispatcher_end_time
        
    st.session_state.dispatcher_start_time = time.time()

def init_chat():
    if "dispatcher_messages" not in st.session_state:
        start_new_call()

def evaluate_call(selected_services: list, call_rank: str) -> str:
    if not GIGA_CREDENTIALS:
        return "В демо-режиме оценка не выставляется."

    services_text = ", ".join(selected_services) if selected_services else "Никакие службы не отправлены."
    
    # Если время окончания зафиксировано, берем его, иначе текущее
    end_t = st.session_state.get("dispatcher_end_time", time.time())
    elapsed = int(end_t - st.session_state.get("dispatcher_start_time", end_t))
    
    eval_prompt = f"""
    Ты — строгий начальник ЦППС. Оцени курсанта по 5-балльной шкале.
    
    ВАЖНО: Курсант физически отправил следующие службы (галочки): **{services_text}**. 
    Считай, что эти службы ВЫЕХЛИ. 
    *Примечание:* Галочка "Спасатели" означает "Служба спасения (МЧС)". Не снижай оценку за синонимы.
    
    Курсант присвоил вызову ранг: **{call_rank}**.
    Затраченное время: **{elapsed} секунд**. Норматив: 180 секунд (3 минуты).
    
    КРИТЕРИИ ОЦЕНКИ:
    1. ОЦЕНКА 5: Узнал адрес, суть, успокоил, отправил ВСЕ нужные службы, ПРАВИЛЬНО присвоил ранг, ДАЛ БЕЗОПАСНЫЕ ИНСТРУКЦИИ. Уложился в 180 сек.
    2. ОЦЕНКА 4: Всё верно, но ранг не точный, ИЛИ забыта одна второстепенная служба, ИЛИ не уложился в норматив (180-240 сек), ИЛИ речь не адаптирована.
    3. ОЦЕНКА 3: Не спросил адрес, ИЛИ не отправил скорую/пожарных/спасателей, ИЛИ сильно превысил время (>240 сек).
    4. ОЦЕНКА 2: Дал ОПАСНЫЙ СОВЕТ (например, закрыть окно при газе), ИЛИ не отправил жизненно важные службы.
    
    Проанализируй диалог ниже и вынеси строгий вердикт:
    **Оценка: [X]**
    **Разбор полетов:** [Укажи ошибки в ранге, службах, психотипе, безопасности и времени].
    """
    
    dialog_history = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.dispatcher_messages if m['role'] != 'system'])
    
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
                Messages(role=MessagesRole.USER, content=f"Диалог:\n{dialog_history}")
            ]
            payload = Chat(messages=messages, model="GigaChat-3-Ultra")
            response_data = giga.chat(payload)
            return response_data.choices[0].message.content
    except Exception:
        return "⚠️ Ошибка связи с сервером оценки."

def render() -> None:
    st.header("📞 ИИ-тренажер: Диспетчер 112")
    st.markdown(
        "Вы играете роль диспетчера. Вам поступил звонок. Задайте вопросы, дайте инструкции "
        "и **отправьте нужные службы**."
    )
    
    init_chat()
    
    # Проверяем, завершен ли вызов
    is_finished = "dispatcher_evaluation" in st.session_state

    if st.button("🔄 Завершить вызов и принять новый", use_container_width=True):
        start_new_call()
        st.rerun()

    demo_mode = not bool(GIGA_CREDENTIALS)
    if demo_mode:
        st.warning("⚠️ Ключи GigaChat не найдены. Работает демо-режим.")

    # История
    for msg in st.session_state.dispatcher_messages:
        if msg["role"] != "system":
            with st.chat_message("assistant" if msg["role"] == "assistant" else "user"):
                st.markdown(msg["content"])

    st.markdown("---")
    
    # --- НАСТРОЙКИ ВЫЗОВА ---
    # Если вызов завершен, блокируем изменение ранга и служб
    if not is_finished:
        call_rank = st.radio(
            "🚨 **Присвоить ранг вызова:**", 
            ["Вызов №1 (Повышенный)", "Вызов №2 (Средний)", "Вызов №3 (Обычный)"],
            horizontal=True
        )

        st.markdown("**📋 Выберите службы для отправки:**")
        col_s1, col_s2, col_s3 = st.columns(3)
        with col_s1:
            s_fire = st.checkbox("🚒 Пожарные")
            s_amb = st.checkbox("🚑 Скорая")
            s_pol = st.checkbox("🚓 Полиция")
        with col_s2:
            s_gibdd = st.checkbox("🚔 ГИБДД (ДПС)")
            s_res = st.checkbox("🧗 Спасатели")
            s_gas = st.checkbox("🔥 Газовая служба")
        with col_s3:
            s_elec = st.checkbox("⚡ Электрики")
            s_div = st.checkbox("🤿 Водолазы")
            s_psy = st.checkbox("🧠 Психологи")

        selected_services = []
        if s_fire: selected_services.append("Пожарные")
        if s_amb: selected_services.append("Скорая")
        if s_pol: selected_services.append("Полиция")
        if s_gibdd: selected_services.append("ГИБДД")
        if s_res: selected_services.append("Спасатели")
        if s_gas: selected_services.append("Газовая служба")
        if s_elec: selected_services.append("Электрики")
        if s_div: selected_services.append("Водолазы")
        if s_psy: selected_services.append("Психологи")
    else:
        # Если вызов завершен, просто показываем, что было выбрано (или скрываем)
        call_rank = "Завершено"
        selected_services = []

    # --- ТАЙМЕР И КНОПКА ОЦЕНКИ ---
    st.markdown("---")
    
    col_timer, col_btn = st.columns([1, 2])
    
    with col_timer:
        if "dispatcher_start_time" in st.session_state:
            start_ms = int(st.session_state.dispatcher_start_time * 1000)
            # Если есть время окончания, передаем его в JS для остановки
            end_ms = int(st.session_state.dispatcher_end_time * 1000) if is_finished else 0
            
            timer_html = f"""
            <style>
            body {{ margin: 0; padding: 0; background: transparent; font-family: 'Source Sans Pro', sans-serif; }}
            .timer-container {{
                display: flex; flex-direction: column; align-items: center; justify-content: center;
                padding: 10px; border-radius: 8px; transition: all 0.3s ease;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1); width: 100%; box-sizing: border-box;
            }}
            .time {{ font-size: 1.8rem; font-weight: 800; line-height: 1.1; }}
            .status {{ font-size: 0.75rem; margin-top: 2px; font-weight: 600; text-transform: uppercase; text-align: center; }}
            </style>
            <div class="timer-container" id="t-box" style="background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb;">
                <div class="time" id="t-txt">00:00</div>
                <div class="status" id="t-st">В норме</div>
            </div>
            <script>
                const startTime = {start_ms};
                const endTime = {end_ms}; // 0, если вызов еще идет
                const box = document.getElementById('t-box');
                const txt = document.getElementById('t-txt');
                const st = document.getElementById('t-st');
                
                let timerInterval = null;

                function update() {{
                    // Если endTime задан, берем его. Иначе текущее время.
                    const now = (endTime > 0) ? endTime : Date.now();
                    const elapsed = Math.floor((now - startTime) / 1000);
                    
                    if (elapsed < 0) return;
                    
                    const m = String(Math.floor(elapsed / 60)).padStart(2, '0');
                    const s = String(elapsed % 60).padStart(2, '0');
                    
                    if (txt) {{
                        txt.textContent = m + ':' + s;
                        if (elapsed < 120) {{
                            box.style.backgroundColor = '#d4edda'; box.style.color = '#155724'; box.style.borderColor = '#c3e6cb'; st.textContent = 'Норма';
                        }} else if (elapsed < 180) {{
                            box.style.backgroundColor = '#fff3cd'; box.style.color = '#856404'; box.style.borderColor = '#ffeeba'; st.textContent = 'Внимание';
                        }} else {{
                            box.style.backgroundColor = '#f8d7da'; box.style.color = '#721c24'; box.style.borderColor = '#f5c6cb'; st.textContent = 'Просрочено';
                        }}
                    }}
                    
                    // Если время вышло (есть endTime), останавливаем таймер
                    if (endTime > 0 && timerInterval) {{
                        clearInterval(timerInterval);
                        st.textContent = 'Зафиксировано';
                        box.style.borderColor = '#0B2545';
                    }}
                }}
                
                if (endTime === 0) {{
                    timerInterval = setInterval(update, 1000);
                }}
                update();
            </script>
            """
            components.html(timer_html, height=85)
            
    with col_btn:
        user_messages = [m for m in st.session_state.dispatcher_messages if m["role"] == "user"]
        
        if is_finished:
            # Если оценка уже есть, показываем кнопку-заглушку или ничего
            st.info("Вызов завершен. Ознакомьтесь с оценкой ниже.")
        else:
            if len(user_messages) == 0:
                st.button("🏁 Завершить и получить оценку", disabled=True, use_container_width=True, help="Задайте хотя бы один вопрос!")
            else:
                if st.button("🏁 Завершить и получить оценку", type="primary", use_container_width=True):
                    # ФИКСИРУЕМ ВРЕМЯ ОКОНЧАНИЯ
                    st.session_state.dispatcher_end_time = time.time()
                    
                    with st.spinner("Анализ действий..."):
                        st.session_state.dispatcher_evaluation = evaluate_call(selected_services, call_rank)
                    st.rerun()
                
    if "dispatcher_evaluation" in st.session_state:
        st.success(st.session_state.dispatcher_evaluation)

    # Чат (блокируем ввод, если вызов завершен)
    if not is_finished:
        if prompt := st.chat_input("Ваши слова диспетчера..."):
            st.session_state.dispatcher_messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner("Абонент отвечает..."):
                    if demo_mode:
                        response = "Пожалуйста, говорите быстрее, я боюсь!"
                    else:
                        try:
                            with GigaChat(
                                credentials=GIGA_CREDENTIALS,
                                base_url="https://api.giga.chat/v1",
                                model="GigaChat-3-Ultra",
                                scope="GIGACHAT_API_PERS",
                                verify_ssl_certs=False
                            ) as giga:
                                giga_messages = []
                                for m in st.session_state.dispatcher_messages:
                                    if m["role"] == "system": role = MessagesRole.SYSTEM
                                    elif m["role"] == "user": role = MessagesRole.USER
                                    else: role = MessagesRole.ASSISTANT
                                    giga_messages.append(Messages(role=role, content=m["content"]))
                                
                                payload = Chat(messages=giga_messages, model="GigaChat-3-Ultra")
                                response_data = giga.chat(payload)
                                response = response_data.choices[0].message.content
                                
                                if "Генеративные языковые модели" in response or "не обладают собственным мнением" in response:
                                    response = "Я вас не слышу! Тут шумно! Повторите, пожалуйста! (Связь прерывается)"
                        except Exception:
                            response = "Я вас не слышу! Тут шумно! (Связь прервалась)"

            st.markdown(response)
            st.session_state.dispatcher_messages.append({"role": "assistant", "content": response})
    else:
        st.chat_input("Вызов завершен", disabled=True)