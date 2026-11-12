"""Модуль 9. ИИ-тренажер 'Диспетчер 112' с реалистичной генерацией."""
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

# РЕЗЕРВНЫЕ СЦЕНАРИИ
FALLBACK_SCENARIOS = [
    {
        "system": "Ты - паникующий человек, который звонит в службу спасения 112. Ты находишься в квартире на 5 этаже. В подъезде сильный запах дыма. Ты заперт. Твоя задача: отвечать на вопросы курсанта. КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО играть роль диспетчера, давать инструкции или вести себя спокойно. Ты в панике, ты не знаешь, что делать, ты ждешь указаний от курсанта. Если курсант спрашивает адрес, ты можешь назвать улицу, но путаться в номере дома. Твой ответ должен быть коротким (1-3 предложения).",
        "start": "Алло! Пожалуйста, помогите! У нас в подъезде дым, я не могу выйти! Я на 5 этаже, кажется, у соседей горит! Что мне делать?! (Плачет)"
    },
    {
        "system": "Ты - паникующий человек, который звонит в службу спасения 112. Ты попал в ДТП на трассе. Твоя машина в кювете, ты зажат, у тебя болит нога. Твоя задача: отвечать на вопросы курсанта. КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО играть роль диспетчера или давать инструкции. Ты в панике, кричишь от боли. Если курсант спрашивает адрес, скажи, что не знаешь точного километра, но видишь указатель. Твой ответ должен быть коротким (1-3 предложения).",
        "start": "Алло! Скорее! Я разбился на машине! Нога зажата, очень больно! Из капота дым идет! Я на трассе, не знаю где точно! Помогите! (Кричит)"
    },
    {
        "system": "Ты - паникующий человек, который звонит в службу спасения 112. Ты чувствуешь сильный запах газа в своей квартире. КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО играть роль диспетчера или давать инструкции. Ты в панике, шепчешь, боишься искры. Если курсант говорит не включать свет, открыть окна, перекрыть вентиль и выйти — успокаивайся. Твой ответ должен быть коротким (1-3 предложения).",
        "start": "Алло... помогите... у меня в квартире пахнет газом... Очень сильно... Я боюсь... Что делать? (Говорит шепотом)"
    },
    {
        "system": "Ты - паникующий человек, который звонит в службу спасения 112. Ты провалился под лед на реке. Ты держишься за кромку льда. КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО играть роль диспетчера или давать инструкции. Ты в панике, стучишь зубами. Если курсант говорит не барахтаться, широко раскинуть руки — делай это. Твой ответ должен быть коротким (1-3 предложения).",
        "start": "Спасите! Я под лед провалился! Очень холодно, руки замерзли! Я на пруду, возле лодочной станции! Вытащите меня! (Стучит зубами)"
    }
]

def generate_new_scenario():
    """Генерирует РЕАЛИСТИЧНЫЙ сценарий через GigaChat."""
    prompt = """
    Ты — генератор случайных чрезвычайных ситуаций для тренажера диспетчеров МЧС.
    Придумай РЕАЛИСТИЧНУЮ ситуацию (например: пожар в жилом доме, ДТП, утечка газа, прорыв трубы с горячей водой, обрушение балкона, потеря человека в лесу).
    КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО придумывать фантастику, бомбы с таймерами, хакеров, пентхаусы и прочий боевик.
    Опиши роль пострадавшего (кто он, где находится, что чувствует). 
    
    ГЛАВНОЕ ПРАВИЛО: Пострадавший НЕ ДОЛЖЕН быть диспетчером или спасателем. Он в панике, он не знает, что делать, он ждет указаний.
    
    Верни ответ СТРОГО в формате JSON без каких-либо других слов и форматирования (без ```json):
    {
        "system_prompt": "текст системного промпта для ИИ (описание роли пострадавшего, ОБЯЗАТЕЛЬНО добавь: 'КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО играть роль диспетчера или давать инструкции, ты жертва')",
        "initial_message": "первое паническое сообщение от пострадавшего"
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
            return data["system_prompt"], data["initial_message"]
    except Exception as e:
        st.error(f"Не удалось сгенерировать ситуацию: {e}")
        return None, None

def start_new_call():
    """Сбрасывает диалог и либо генерирует ситуацию ИИ, либо берет из резерва."""
    scenario_sys = None
    scenario_start = None

    if GIGA_CREDENTIALS:
        with st.spinner("Генерация новой случайной ситуации..."):
            scenario_sys, scenario_start = generate_new_scenario()
    
    if not scenario_sys or not scenario_start:
        scenario = random.choice(FALLBACK_SCENARIOS)
        scenario_sys = scenario["system"]
        scenario_start = scenario["start"]

    st.session_state.dispatcher_scenario = scenario_sys
    st.session_state.dispatcher_messages = [
        {"role": "system", "content": scenario_sys},
        {"role": "assistant", "content": scenario_start}
    ]
    
    if "dispatcher_evaluation" in st.session_state:
        del st.session_state.dispatcher_evaluation

def init_chat():
    if "dispatcher_messages" not in st.session_state:
        start_new_call()

def evaluate_call():
    """Отправляет диалог на оценку ИИ по строгим критериям."""
    if not GIGA_CREDENTIALS:
        return "В демо-режиме оценка не выставляется. Подключите ключ GigaChat."

    eval_prompt = """
    Ты — начальник караула пожарной части, принимающий экзамен у курсанта. 
    Ты крайне строгий, придирчивый и не терпишь халатности. Твоя цель — найти ошибки.
    
    Вот жесткие критерии оценивания (следуй им неукоснительно):
    
    1. ОЦЕНКА 5 (Отлично): Курсант узнал точный АДРЕС, выяснил, что произошло, есть ли угроза жизни. Дал ЧЕТКИЕ и БЕЗОПАСНЫЕ инструкции (например, при газе — открыть окна, не включать свет; при пожаре — закрыть щели тряпкой; при ДТП — не курить). Общался спокойно.
    2. ОЦЕНКА 4 (Хорошо): Курсант узнал адрес и суть, но забыл дать ОДНУ важную инструкцию по безопасности или задал мало уточняющих вопросов.
    3. ОЦЕНКА 3 (Удовл): Курсант забыл спросить точный адрес ИЛИ дал только одну инструкцию. (Если адрес не спрошен — выше 3 ставить ЗАПРЕЩЕНО).
    4. ОЦЕНКА 2 (Неудовл): Курсант не спросил адрес, задавал странные вопросы (про погоду, песни), ИЛИ дал опасный совет (например, включить свет при утечке газа, открыть окно при пожаре в подъезде), ИЛИ общался грубо. ИЛИ если курсант перепутал роли и начал сам давать инструкции, вместо того чтобы слушать пострадавшего.
    5. Если в диалоге НЕТ ни одного сообщения от курсанта (он просто нажал кнопку "Оценить"), напиши: "**Оценка: 2**. Вы не задали ни одного вопроса и бросили пострадавшего. Это халатность".
    
    Проанализируй диалог ниже и вынеси вердикт строго по формату:
    **Оценка: [X]**
    **Обоснование:** [Укажи, чего конкретно не хватило до оценки 5. Если 2 — укажи грубую ошибку].
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
                Messages(role=MessagesRole.USER, content=f"Вот диалог:\n{dialog_history}")
            ]
            payload = Chat(messages=messages, model="GigaChat-3-Ultra")
            response_data = giga.chat(payload)
            return response_data.choices[0].message.content
    except Exception as e:
        return f"Ошибка при выставлении оценки: {e}"

def render() -> None:
    st.header("📞 ИИ-тренажер: Диспетчер 112")
    st.markdown(
        "Вы играете роль диспетчера службы спасения. Вам поступил звонок от паникующего человека. "
        "Ваша задача — задать правильные вопросы и дать инструкции, чтобы спасти его жизнь. "
        "**Ситуации генерируются искусственным интеллектом случайным образом!**"
    )
    
    init_chat()
    
    if st.button("🔄 Завершить вызов и принять новый", use_container_width=True):
        start_new_call()
        st.rerun()

    demo_mode = not bool(GIGA_CREDENTIALS)
    if demo_mode:
        st.warning("⚠️ Ключи GigaChat не найдены. Используются базовые шаблонные ситуации.")

    for msg in st.session_state.dispatcher_messages:
        if msg["role"] != "system":
            with st.chat_message("assistant" if msg["role"] == "assistant" else "user"):
                st.markdown(msg["content"])

    st.markdown("---")
    
    user_messages = [m for m in st.session_state.dispatcher_messages if m["role"] == "user"]
    
    col_eval, col_empty = st.columns([1, 2])
    with col_eval:
        if len(user_messages) == 0:
            st.button("🏁 Завершить спасение и получить оценку", disabled=True, use_container_width=True, help="Сначала задайте хотя бы один вопрос!")
        else:
            if st.button("🏁 Завершить спасение и получить оценку", type="primary", use_container_width=True):
                with st.spinner("Экзаменатор анализирует ваши действия..."):
                    st.session_state.dispatcher_evaluation = evaluate_call()
                
    if "dispatcher_evaluation" in st.session_state:
        st.success(st.session_state.dispatcher_evaluation)

    if prompt := st.chat_input("Ваши слова диспетчера..."):
        st.session_state.dispatcher_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Абонент отвечает..."):
                if demo_mode:
                    p = prompt.lower()
                    if "адрес" in p or "где" in p: response = "Я не знаю точно! Тут темно и страшно!"
                    elif "скорую" in p or "спас" in p: response = "Да, да, вызовите! Скорее!"
                    else: response = "Пожалуйста, говорите быстрее, я боюсь! (Кашель/Плач)"
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
                                if m["role"] == "system":
                                    role = MessagesRole.SYSTEM
                                elif m["role"] == "user":
                                    role = MessagesRole.USER
                                else:
                                    role = MessagesRole.ASSISTANT
                                giga_messages.append(Messages(role=role, content=m["content"]))
                            
                            payload = Chat(messages=giga_messages, model="GigaChat-3-Ultra")
                            response_data = giga.chat(payload)
                            response = response_data.choices[0].message.content
                    except Exception as e:
                        response = f"⚠️ Ошибка связи с GigaChat: {e}. Попробуйте еще раз."

        st.markdown(response)
        st.session_state.dispatcher_messages.append({"role": "assistant", "content": response})