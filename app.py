"""«Формула безопасности МЧС» — точка входа Streamlit-приложения."""
from __future__ import annotations

import pandas as pd
import streamlit as st
import urllib.parse
import streamlit.components.v1 as components
import base64
import os

from core import ai_explainer, storage
from modules import evacuation, fire_physics, hydraulics, loads, risk, trainer, dispatcher, sandbox, simulator

CUSTOM_CSS = """
<style>
/* Фон с легкой математической сеткой */
.stApp { 
    background-color: #F5F7FA !important; 
    background-image: 
        linear-gradient(rgba(11, 37, 69, 0.04) 1px, transparent 1px),
        linear-gradient(90deg, rgba(11, 37, 69, 0.04) 1px, transparent 1px);
    background-size: 25px 25px;
    background-position: center top;
}

/* Боковая панель */
[data-testid="stSidebar"] { background-color: #0B2545 !important; }
[data-testid="stSidebar"] * { color: #FFFFFF !important; }

/* Жесткий фикс текста в меню для темной темы */
[data-testid="stSidebar"] div[role="radiogroup"] *,
[data-testid="stSidebar"] [data-baseweb="radio"] *,
[data-testid="stSidebar"] [data-testid="stRadio"] * {
    color: #FFFFFF !important;
}
/* Возвращаем оранжевый цвет для активного пункта меню */
[data-testid="stSidebar"] div[role="radiogroup"] [aria-checked="true"] * {
    color: #F26A1B !important;
    font-weight: 700 !important;
}

[data-testid="stSidebar"] .fb-side-title { font-size: 1.25rem; font-weight: 700; margin-bottom: 0.5rem; }
[data-testid="stSidebar"] .fb-about {
    background: rgba(255, 255, 255, 0.1) !important;
    border-left: 4px solid #F26A1B;
    border-radius: 6px;
    padding: 10px 12px;
    font-size: 0.9rem;
    line-height: 1.4;
}
[data-testid="stSidebar"] .fb-slogan {
    color: #F26A1B !important;
    font-weight: 700;
    font-size: 1.05rem;
    text-align: center;
    margin-top: 14px;
}

/* Шапка */
.fb-header {
    background: linear-gradient(90deg, #0B2545 0%, #13315C 70%, #F26A1B 160%);
    border-radius: 10px;
    padding: 18px 24px;
    margin-bottom: 18px;
}
.fb-header .fb-title { color: #FFFFFF !important; font-size: 2rem; font-weight: 800; }
.fb-header .fb-subtitle { color: #FFD9C2 !important; font-size: 1.05rem; margin-top: 4px; }

/* Кнопки */
.stButton > button, .stFormSubmitButton > button {
    background-color: #F26A1B !important;
    color: #FFFFFF !important;
    border: none;
    border-radius: 8px;
    font-weight: 600;
    padding: 0.45rem 1.1rem;
}
.stButton > button:hover, .stFormSubmitButton > button:hover {
    background-color: #D4570F !important;
    color: #FFFFFF !important;
}
.stButton > button p, .stFormSubmitButton > button p { color: #FFFFFF !important; }

/* Метрики */
[data-testid="stMetric"], [data-testid="metric-container"] {
    background: #FFFFFF !important;
    border-left: 5px solid #F26A1B;
    border-radius: 8px;
    padding: 12px 16px;
    box-shadow: 0 1px 4px rgba(11, 37, 69, 0.12);
}
[data-testid="stMetricValue"], [data-testid="stMetricValue"] * { color: #0B2545 !important; }
[data-testid="stMetricLabel"], [data-testid="stMetricLabel"] * { color: #5A6A85 !important; }

/* Заголовки и обычный текст */
h1, h2, h3 { color: #0B2545 !important; }
[data-testid="stMarkdownContainer"] p, 
[data-testid="stMarkdownContainer"] li { color: #333333 !important; }

/* Карточка задачи в тренажёре */
.fb-task {
    background: #FFFFFF !important;
    border: 1px solid #D5DCE8;
    border-left: 5px solid #0B2545;
    border-radius: 8px;
    padding: 14px 18px;
    margin-bottom: 12px;
    font-size: 1.05rem;
    color: #0B2545 !important;
}

/* Красивая белая подложка для логотипа в сайдбаре */
[data-testid="stSidebar"] [data-testid="stImage"] img {
    background-color: #FFFFFF !important;
    border-radius: 50%;
    padding: 10px;
    box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.4);
    margin: 0 auto 15px auto;
    display: block;
    width: 100% !important;
    max-width: 260px;
    height: auto;
}

/* Карточки на главной странице */
.home-card {
    background: #FFFFFF !important;
    border: 1px solid #E8EDF5;
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 4px 15px rgba(11, 37, 69, 0.05);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    height: 175px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    margin-bottom: 10px;
}
.home-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 8px 25px rgba(242, 106, 27, 0.15);
    border-color: #F26A1B;
}
.home-card-icon { font-size: 2rem; margin-bottom: 10px; }
.home-card-title { color: #0B2545 !important; font-weight: 700; font-size: 1.1rem; margin-bottom: 5px; }
.home-card-text { color: #5A6A85 !important; font-size: 0.9rem; line-height: 1.4; }

/* Блок "Знаете ли вы" */
.fact-box {
    background: linear-gradient(135deg, #0B2545 0%, #13315C 100%) !important;
    color: #FFFFFF !important;
    border-radius: 10px;
    padding: 20px 25px;
    margin: 20px 0;
    border-left: 6px solid #F26A1B;
}
.fact-box b { color: #F26A1B !important; }
.fact-box * { color: #FFFFFF !important; }

/* Фикс для info, warning, success блоков (чтобы текст не пропадал в темной теме) */
[data-testid="stAlert"] * { color: #0B2545 !important; }


/* --- КРАСИВОЕ МЕНЮ В САЙДБАРЕ --- */

/* 1. Убираем стандартные кружочки радиокнопок */
[data-testid="stSidebar"] div[role="radiogroup"] label > div:first-child {
    display: none !important;
}

/* 2. Стилизуем сами пункты меню как кнопки */
[data-testid="stSidebar"] div[role="radiogroup"] label {
    padding: 12px 18px !important; /* Увеличили отступы для объема */
    margin-bottom: 6px !important; /* Расстояние между кнопками */
    border-radius: 8px !important;
    transition: all 0.2s ease !important;
    cursor: pointer !important;
    background-color: transparent;
    border: 1px solid transparent;
    align-items: center; /* Центрируем текст и иконку */
}

/* 3. Эффект при наведении мышки */
[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
    background-color: rgba(255, 255, 255, 0.1) !important;
    transform: translateX(5px); /* Легкий сдвиг вправо */
}

/* 4. Активный пункт (когда страница выбрана) */
[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {
    background-color: #F26A1B !important; /* Фирменный оранжевый */
    box-shadow: 0 4px 12px rgba(242, 106, 27, 0.4) !important;
    transform: translateX(0px) !important;
}

/* 5. Делаем текст крупнее и белым */
[data-testid="stSidebar"] div[role="radiogroup"] label p {
    font-size: 1.15rem !important; /* Увеличили размер шрифта */
    font-weight: 500 !important; /* Сделали текст чуть плотнее */
    color: #FFFFFF !important;
    margin: 0 !important;
}

/* 6. Делаем текст в активном пункте жирным */
[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) p {
    font-weight: 800 !important;
    color: #FFFFFF !important;
}

/* Убираем стандартный фокус (обводку) при клике */
[data-testid="stSidebar"] div[role="radiogroup"] label:focus-within {
    outline: none !important;
    box-shadow: none !important;
}



</style>
"""

ABOUT_HTML = """
<div style="margin-bottom: 5px;"><b>О проекте</b></div>
«Формула безопасности МЧС» — это тренажёр понимания, а не боевой инструмент
для расчётов во время пожара. Он показывает, как математика связана с профессией
спасателя, и помогает осознанно применять нормативы.

<div class="fb-slogan">Математика, которая спасает жизни</div>
"""


def render_header() -> None:
    import base64
    import streamlit.components.v1 as components

    # Функция для загрузки логотипа
    @st.cache_data(show_spinner=False)
    def get_logo_base64():
        try:
            with open("assets/logo.png", "rb") as img_file:
                return "data:image/jpeg;base64," + base64.b64encode(img_file.read()).decode()
        except FileNotFoundError:
            return ""

    logo_data = get_logo_base64()

    # --- СЛАЙДЕР-ШАПКА ---
    hero_slider_html = f"""
    <style>
    body {{ margin: 0; padding: 0; font-family: sans-serif; }}
    .hero-container {{
        position: relative;
        width: 100%;
        height: 220px; /* Высота шапки */
        border-radius: 12px;
        overflow: hidden;
        background: linear-gradient(135deg, #0B2545 0%, #13315C 100%);
        box-shadow: 0 8px 25px rgba(11, 37, 69, 0.2);
        margin-bottom: 25px;
    }}
    .hero-slide {{
        position: absolute;
        top: 0; left: 0; width: 100%; height: 100%;
        display: flex;
        flex-direction: row; /* Логотип слева, текст справа */
        align-items: center;
        justify-content: center;
        gap: 30px;
        opacity: 0;
        animation: heroFade 15s infinite;
        padding: 0 40px;
        box-sizing: border-box;
    }}
    .hero-slide img {{
        width: 110px;
        height: 110px;
        border-radius: 50%;
        background: white;
        padding: 5px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.4);
        object-fit: contain;
    }}
    .hero-text {{
        text-align: left;
        max-width: 700px;
    }}
    .hero-title {{
        color: #FFFFFF;
        font-size: 2rem;
        font-weight: 800;
        margin: 0 0 5px 0;
        text-shadow: 1px 1px 3px rgba(0,0,0,0.5);
    }}
    .hero-subtitle {{
        color: #F26A1B;
        font-size: 1.1rem;
        font-weight: 600;
        margin: 0;
        line-height: 1.3;
    }}
    
    .hero-slide:nth-child(1) {{ animation-delay: 0s; }}
    .hero-slide:nth-child(2) {{ animation-delay: 5s; }}
    .hero-slide:nth-child(3) {{ animation-delay: 10s; }}
    
    @keyframes heroFade {{
        0% {{ opacity: 0; transform: translateX(-10px); }}
        4% {{ opacity: 1; transform: translateX(0); }}
        29% {{ opacity: 1; transform: translateX(0); }}
        33% {{ opacity: 0; transform: translateX(10px); }}
        100% {{ opacity: 0; transform: translateX(10px); }}
    }}
    </style>
    
    <div class="hero-container">
        <div class="hero-slide">
            <img src="{logo_data}">
            <div class="hero-text">
                <h1 class="hero-title">Формула безопасности МЧС</h1>
                <p class="hero-subtitle">Интеллектуальный тренажёр по прикладной математике</p>
            </div>
        </div>
        <div class="hero-slide">
            <img src="{logo_data}">
            <div class="hero-text">
                <h1 class="hero-title">ГАПОУ «ТГКГЗ»</h1>
                <p class="hero-subtitle">Тетюшский государственный колледж гражданской защиты</p>
            </div>
        </div>
        <div class="hero-slide">
            <img src="{logo_data}">
            <div class="hero-text">
                <h1 class="hero-title">Математика, которая спасает</h1>
                <p class="hero-subtitle">Изучайте физику пожара, гидравлику и тактику</p>
            </div>
        </div>
    </div>
    """
    components.html(hero_slider_html, height=240)


def render_home() -> None:
    st.markdown(
        "<h2 style='color: #0B2545; margin-bottom: 5px;'>Добро пожаловать в тренажёр!</h2>"
        "<p style='font-size: 1.1rem; color: #5A6A85; margin-bottom: 25px;'>"
        "«Формула безопасности МЧС» — это интерактивная платформа, которая показывает, как математика помогает спасать жизни."
        "</p>",
        unsafe_allow_html=True
    )

    st.markdown("### 🧩 Выберите раздел для изучения")
    
    def draw_card(col, icon, title, text, nav_name):
        with col:
            st.markdown(
                f'<div class="home-card">'
                f'<div>'
                f'<div class="home-card-icon">{icon}</div>'
                f'<div class="home-card-title">{title}</div>'
                f'<div class="home-card-text">{text}</div>'
                f'</div>'
                f'</div>', unsafe_allow_html=True
            )
            st.button(
                "Перейти в раздел ➔", 
                key=f"btn_{nav_name}_card", 
                use_container_width=True,
                on_click=lambda n=nav_name: st.session_state.update(nav=n)
            )
            st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        draw_card(col1, "🔥", "Пожарная физика", "Логарифмы и производные. Как растёт температура и когда наступает вспышка.", "🔥 Пожарная физика")
        draw_card(col1, "🚪", "Эвакуация", "Обратная пропорциональность. Как ширина выходов влияет на время спасения.", "🚪 Эвакуация")

    with col2:
        draw_card(col2, "💧", "Гидравлика", "Линейные и квадратичные функции. Давление в рукавной линии.", "💧 Гидравлика")
        draw_card(col2, "⚠️", "Риск ЧС", "Показательная функция. Вероятность происшествий и надёжность техники.", "⚠️ Риск ЧС")

    with col3:
        draw_card(col3, "🏗️", "Нагрузки", "Степенные функции. Расчёт балок и оценка несущей способности.", "🏗️ Нагрузки")
        draw_card(col3, "🎯", "Тренажёр задач", "Проверка знаний. Задачи с подсказками, ответами и разбором.", "🎯 Тренажёр задач")

    # --- НОВЫЙ БЛОК "ЗНАЕТЕ ЛИ ВЫ?" (Слайдер фактов) ---
    import streamlit.components.v1 as components
    
    facts = [
        {"title": "Температура при пожаре", "text": "В закрытом помещении температура достигает <b>600 °C</b> уже к 6-й минуте. Это порог общей вспышки (flashover), после которого выжить без СИЗОД невозможно."},
        {"title": "Давление воды", "text": "Каждые <b>10 метров</b> подъема воды «съедают» 1 атмосферу давления. Чтобы подать ствол на 9-й этаж, насос должен создать минимум 3 атм только на преодоление высоты."},
        {"title": "Убийца — дым", "text": "Около <b>70%</b> людей на пожарах гибнут не от огня, а от отравления угарным газом (CO) и потери видимости в дыму. Дым распространяется со скоростью до 20 м/мин."},
        {"title": "Прочность металла", "text": "Сталь при нагреве до <b>500 °C</b> теряет половину своей несущей способности. Балка, которая спокойно держала вес, может внезапно обрушиться без видимого пламени."},
        {"title": "Правило эвакуации", "text": "Двери на путях эвакуации <b>всегда</b> открываются по направлению выхода (наружу). Если открыть их внутрь, паникующая толпа создаст затор и заблокирует проход."},
        {"title": "Сила воды", "text": "При тушении <b>1 литр</b> воды превращается в <b>1700 литров</b> пара. Этот пар вытесняет кислород и быстро охлаждает очаг возгорания, поэтому вода так эффективна."},
        {"title": "Волшебная пена", "text": "Из <b>1 литра</b> пенообразователя получается до <b>10 000 литров</b> готовой воздушно-механической пены, которая накрывает горящий бензин плотным одеялом."},
        {"title": "Математика огня", "text": "Стандартная кривая пожара ISO 834, по которой испытывают здания, рассчитывается через <b>десятичный логарифм</b>: T = T0 + 345 · lg(8t + 1)."},
        {"title": "Защита БОП", "text": "Боевая одежда пожарного (БОП) отражает до <b>90%</b> теплового излучения. Это дает драгоценные секунды, чтобы не воспламениться от жара открытого пламени."},
        {"title": "Жар молнии", "text": "Температура канала молнии достигает <b>30 000 °C</b>. Это в 5 раз горячее поверхности Солнца. При этом разряд длится доли секунды, но энергии хватает на разрушение."},
        {"title": "Дыхание в дыму", "text": "В баллоне дыхательного аппарата (ДАСВ) давление <b>300 атмосфер</b>. Этого хватает примерно на 45–60 минут тяжелой физической работы в непригодной для дыхания среде."},
        {"title": "Скорость сбора", "text": "Норматив надевания боевой одежды и снаряжения (БОП) на оценку «отлично» составляет всего <b>21 секунду</b>. В карауле счет идет на мгновения."}
    ]

    # Генерируем HTML
    total_facts = len(facts)
    time_per_fact = 10 # УВЕЛИЧИЛИ ВРЕМЯ ДО 10 СЕКУНД
    total_time = total_facts * time_per_fact
    
    slides_html = ""
    for i, fact in enumerate(facts):
        delay = i * time_per_fact
        slides_html += f"""
        <div class="fact-slide" style="animation-delay: {delay}s;">
            <div class="fact-icon">💡</div>
            <div class="fact-content">
                <div class="fact-title">{fact['title']}</div>
                <div class="fact-text">{fact['text']}</div>
            </div>
        </div>
        """

    # Процент времени на анимацию
    percentage = 100 / total_facts
    fade_in_end = 2
    fade_out_start = percentage - 2
    
    fact_box_html = f"""
    <style>
    .fact-container {{
        position: relative;
        width: 100%;
        height: 220px; /* Увеличили высоту блока */
        background: linear-gradient(135deg, #0B2545 0%, #13315C 100%);
        border-radius: 12px;
        border-left: 6px solid #F26A1B;
        box-shadow: 0 8px 25px rgba(11, 37, 69, 0.3);
        overflow: hidden;
        margin: 20px 0;
    }}
    
    .fact-slide {{
        position: absolute;
        top: 0; left: 0; width: 100%; height: 100%;
        display: flex;
        align-items: center;
        padding: 25px 35px; /* Чуть больше отступы */
        box-sizing: border-box;
        opacity: 0;
        animation: showFact {total_time}s infinite;
    }}
    
    .fact-icon {{
        font-size: 4rem; /* Увеличили иконку */
        margin-right: 30px;
        animation: pulseLight 2s infinite;
    }}
    
    .fact-content {{
        flex: 1;
        z-index: 2;
    }}
    
    .fact-title {{
        color: #F26A1B;
        font-size: 1.3rem; /* Увеличили заголовок */
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 8px;
    }}
    
    .fact-text {{
        color: #FFFFFF;
        font-size: 1.15rem; /* Увеличили основной текст */
        line-height: 1.6; /* Добавили воздуха между строками */
        text-shadow: 1px 1px 2px rgba(0,0,0,0.5); /* Тень для лучшей читаемости */
    }}
    
    /* Выделенный жирным текст делаем ярко-оранжевым и жирным */
    .fact-text b {{
        color: #F26A1B;
        font-weight: 800;
        font-size: 1.2rem;
    }}
    
    @keyframes pulseLight {{
        0% {{ transform: scale(1); filter: drop-shadow(0 0 5px rgba(242,106,27,0)); }}
        50% {{ transform: scale(1.1); filter: drop-shadow(0 0 20px rgba(242,106,27,0.8)); }}
        100% {{ transform: scale(1); filter: drop-shadow(0 0 5px rgba(242,106,27,0)); }}
    }}
    
    @keyframes showFact {{
        0% {{ opacity: 0; transform: translateY(15px); }}
        {fade_in_end}% {{ opacity: 1; transform: translateY(0); }}
        {fade_out_start}% {{ opacity: 1; transform: translateY(0); }}
        {percentage}% {{ opacity: 0; transform: translateY(-15px); }}
        100% {{ opacity: 0; transform: translateY(-15px); }}
    }}
    
    .fact-progress-bar {{
        position: absolute;
        bottom: 0; left: 0;
        height: 5px; /* Сделали полоску чуть толще */
        background-color: #F26A1B;
        width: 0%;
        animation: progress {time_per_fact}s linear infinite;
        z-index: 10;
    }}
    
    @keyframes progress {{
        0% {{ width: 0%; }}
        100% {{ width: 100%; }}
    }}
    </style>
    
    <div class="fact-container">
        {slides_html}
        <div class="fact-progress-bar"></div>
    </div>
    """
    components.html(fact_box_html, height=240) # Увеличили высоту компонента
    # -------------------------------------

    st.markdown("### 🚀 Как пользоваться тренажёром")
    c1, c2, c3 = st.columns(3)
    c1.info("**1. Выберите модуль**\n\nВ левом меню или по кнопкам выше найдите нужную тему.")
    c2.info("**2. Меняйте данные**\n\nВводите свои числа. Смотрите, как меняется график.")
    c3.info("**3. Учитесь с ИИ**\n\nНажимайте «Объясни как курсанту», чтобы понять смысл формул.")

    st.markdown("---")
    st.warning(
        "⚠️ **Важно:** Все модели в тренажёре учебные и упрощённые. Для реальных боевых расчётов "
        "используются действующие нормативные документы, справочники и методики."
    )


def render_history() -> None:
    st.header("📜 История")
    total, correct = storage.get_stats()
    col1, col2, col3 = st.columns(3)
    col1.metric("Попыток в тренажёре", str(total))
    col2.metric("Верных ответов", str(correct))
    col3.metric("Точность", f"{(100 * correct / total):.0f} %" if total else "—")

    tab_calc, tab_tasks = st.tabs(["Сохранённые расчёты", "Попытки в тренажёре"])
    with tab_calc:
        rows = storage.get_calculations()
        if rows:
            frame = pd.DataFrame(rows).rename(
                columns={"ts": "Время", "module": "Модуль", "inputs": "Исходные данные", "results": "Результаты"}
            )
            st.dataframe(frame, hide_index=True)
        else:
            st.info("Пока пусто. В любом модуле нажмите «Сохранить расчёт в историю».")
    with tab_tasks:
        rows = storage.get_attempts()
        if rows:
            frame = pd.DataFrame(rows)
            frame["is_correct"] = frame["is_correct"].map({1: "верно", 0: "неверно"})
            frame = frame.rename(
                columns={
                    "ts": "Время",
                    "topic": "Тема",
                    "task_id": "Задача",
                    "user_answer": "Ответ",
                    "correct_answer": "Эталон",
                    "is_correct": "Результат",
                }
            )
            st.dataframe(frame, hide_index=True)
        else:
            st.info("Пока нет решённых задач. Загляните в «Тренажёр задач».")
        st.markdown("---")
    st.subheader("📤 Экспорт данных для преподавателя")
    if rows:
        import io
        csv_buffer = io.StringIO()
        full_df = pd.DataFrame(storage.get_attempts(limit=10000))
        full_df.to_csv(csv_buffer, index=False, sep=';', encoding='utf-8-sig')
        st.download_button(
            label="📥 Скачать историю попыток (CSV)",
            data=csv_buffer.getvalue(),
            file_name="formula_bezopasnosti_history.csv",
            mime="text/csv",
            help="Файл можно открыть в Excel. Он содержит все попытки курсантов, что позволяет преподавателю проанализировать успеваемость."
        )
    if st.button("🗑️ Очистить историю", key="history_clear"):
        storage.clear_history()
        st.rerun()

def render_teacher_guide() -> None:
    st.header("👨‍🏫 Методический кабинет преподавателя")
    st.markdown(
        "Интерактивное пособие по интеграции тренажёра «Формула безопасности МЧС» "
        "в образовательный процесс. Разработано в соответствии с ФГОС СПО (срок обучения 3 г. 10 мес.)."
    )
    st.markdown("---")

    # Теперь 5 вкладок (убрали акт о внедрении)
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📖 Учебный план", 
        "📝 Конструктор урока", 
        "📊 Калькулятор оценок", 
        "🧠 Педагогика и ИИ",
        "📥 Скачать методичку"
    ])

    # ==========================================
    # ВКЛАДКА 1: УЧЕБНЫЙ ПЛАН (ФГОС)
    # ==========================================
    with tab1:
        st.subheader("Интеграция с рабочей программой (1–4 курс)")
        st.info("Тренажёр позволяет реализовать практическую часть дисциплин на протяжении всего срока обучения.")
        
        with st.expander("Карта соответствия модулей и тем (ФГОС СПО)", expanded=True):
            st.markdown(
                """
                | Модуль тренажёра | Курс | Дисциплина | Тема занятия |
                | :--- | :--- | :--- | :--- |
                | **Пожарная физика** | 1 курс | Математика / Физика | Логарифмы. Теплопередача и теплота сгорания. |
                | **Гидравлика** | 2 курс | Гидравлика / Механика | Линейные зависимости. Законы Паскаля и Бернулли. |
                | **Эвакуация** | 2 курс | БЖД / Тактика | Обратная пропорциональность. Расчет путей эвакуации. |
                | **Нагрузки** | 2 курс | Техническая механика | Степенные функции. Расчет балок на изгиб и нагрев. |
                | **Риск ЧС** | 3 курс | Математика / БЖД | Теория вероятностей. Показательные функции. |
                | **Тактика** | 3 курс | Пожарная тактика | Расчет сил и средств (площадь, расход, стволы). |
                | **ГДЗС** | 3 курс | Тактика / ГДЗС | Линейные уравнения. Расчет времени работы в СИЗОД. |
                | **Все модули** | 4 курс | ВКР (Диплом) | Выполнение расчетов для дипломного проекта, оформление приложений. |
                """
            )

        st.success("""
        **🎓 Специфика 4 курса (Выпускной):**
        *   **Дипломное проектирование:** Курсанты используют нормативную базу и тренажёр для обоснования инженерных решений в своих ВКР.
        *   **Стажировка в пожарных частях:** Преподаватель может давать задания на сравнение теоретических расчетов из тренажёра с реальными нормативами.
        """)

    # ==========================================
    # ВКЛАДКА 2: КОНСТРУКТОР УРОКА
    # ==========================================
    with tab2:
        st.subheader("Генератор плана занятия")
        st.markdown("Выберите параметры, и система сгенерирует готовый план урока (45 минут).")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            lesson_type = st.selectbox("Тип занятия", ["Практическое занятие", "Лабораторная работа", "Вводная лекция", "Контрольный срез"])
        with col2:
            module = st.selectbox("Основной модуль", ["Пожарная физика", "Гидравлика", "Эвакуация", "Нагрузки", "Риск ЧС", "Тактика", "ГДЗС"])
        with col3:
            target_group = st.selectbox("Курс", ["1 курс", "2 курс", "3 курс", "4 курс"])
            
        if st.button("📝 Сгенерировать план урока"):
            st.success(f"### План: {lesson_type} по модулю «{module}» ({target_group})")
            
            if "Практическое" in lesson_type:
                st.markdown(
                    f"""
                    **1. Орг. момент (5 мин):** Проверка присутствующих. Объявление темы.
                    **2. Актуализация (10 мин):** Разбор теории модуля «{module}» в левом меню тренажёра.
                    **3. Самостоятельная работа (20 мин):** Курсанты решают по 3 задачи из раздела «{module}» в тренажёре. Преподаватель консультирует.
                    **4. Разбор ошибок (5 мин):** Демонстрация на проекторе типичных ошибок с помощью кнопки «Объясни как курсанту».
                    **5. Домашнее задание (5 мин):** Пройти оставшиеся задачи в разделе «{module}», выгрузить CSV-отчет.
                    """
                )
            elif "Лабораторная" in lesson_type:
                st.markdown(
                    f"""
                    **1. Вводная часть (10 мин):** Инструктаж по технике безопасности при работе с ПК.
                    **2. Выполнение работы (25 мин):** Курсанты вводят параметры реального объекта в модуль «{module}».
                    **3. Оформление отчета (10 мин):** Скриншот расчета, вывод о соответствии нормативам.
                    """
                )
            else:
                st.markdown(f"**Цель занятия:** Сформировать понимание применения {module} в профессиональной деятельности спасателя.")

    # ==========================================
    # ВКЛАДКА 3: КАЛЬКУЛЯТОР ОЦЕНОК
    # ==========================================
    with tab3:
        st.subheader("Автоматизированная оценка знаний")
        st.markdown("Введите результаты курсанта из раздела «История», чтобы получить обоснованную оценку.")
        
        c1, c2, c3 = st.columns(3)
        with c1:
            total_tasks = st.number_input("Всего попыток", min_value=1, value=20)
        with c2:
            correct_tasks = st.number_input("Верных ответов", min_value=0, max_value=int(total_tasks), value=17)
        with c3:
            hints_used = st.number_input("Использовано подсказок / ИИ", min_value=0, value=1)
            
        percentage = (correct_tasks / total_tasks) * 100
        st.metric("Процент выполнения", f"{percentage:.0f} %")
        
        if percentage >= 90 and hints_used <= 2:
            st.success("Оценка: **5 (Отлично)**. Курсант показал глубокие знания и самостоятельность.")
        elif percentage >= 75 and hints_used <= 4:
            st.info("Оценка: **4 (Хорошо)**. Материал усвоен, но были неточности.")
        elif percentage >= 50:
            st.warning("Оценка: **3 (Удовлетворительно)**. Требуется повторение темы.")
        else:
            st.error("Оценка: **2 (Неудовлетворительно)**. Курсант не освоил материал.")

    # ==========================================
    # ВКЛАДКА 4: ПЕДАГОГИКА И ИИ
    # ==========================================
    with tab4:
        st.subheader("Педагогические технологии и ИИ")
        
        with st.expander("Как ИИ помогает преподавателю?", expanded=True):
            st.markdown(
                """
                *   **Экономия времени:** Вам не нужно вручную проверять тетради.
                *   **Индивидуальный подход:** Кнопка «Разобрать с ИИ» работает как личный репетитор 24/7.
                *   **Геймификация:** Система XP и званий повышает мотивацию.
                """
            )
            
        with st.expander("Работа с курсантами с ОВЗ (инклюзия)"):
            st.info(
                "Тренажёр поддерживает увеличение масштаба браузера и имеет высокий контраст шрифтов. "
                "Для слабовидящих доступен режим экранного диктора (Narrator)."
            )
            
        with st.expander("Метод проектов (PBL) для 3-4 курсов"):
            st.markdown(
                "Предложите курсантам в качестве курсовой работы **дополнить тренажёр новой задачей**. "
                "Они должны написать математическую модель, рассчитать ответ и оформить это в виде Python-кода. Это развивает IT-компетенции."
            )

    # ==========================================
    # ВКЛАДКА 5: СКАЧАТЬ МЕТОДИЧКУ
    # ==========================================
    with tab5:
        st.subheader("Экспорт учебно-методического комплекса (УМК)")
        st.markdown("Скачайте полный текст методических рекомендаций для приложения к пояснительной записке.")
        
        method_text = """
        МЕТОДИЧЕСКИЕ РЕКОМЕНДАЦИИ ПО ИСПОЛЬЗОВАНИЮ ТРЕНАЖЁРА "ФОРМУЛА БЕЗОПАСНОСТИ МЧС"

        1. Общие положения
        Тренажёр предназначен для курсантов СПО (специальности 20.02.04 и 20.02.02, срок обучения 3 г. 10 мес.).
        Цель: Визуализация математических и физических процессов, происходящих при пожаре и ЧС.

        2. Структура тренажёра
        Включает 9 модулей (Пожарная физика, Гидравлика, Эвакуация, Нагрузки, Риск ЧС, Тактика, ГДЗС, Первая помощь, Тесты).
        База задач содержит более 180 кейсов и расчетных задач.

        3. Методика проведения занятий
        - 1-2 курс: Вводные и практические занятия по математике и физике.
        - 3 курс: Практикумы по тактике и гидравлике.
        - 4 курс: Использование нормативной базы и расчетов для ВКР и стажировок.

        4. Критерии оценивания
        - Оценка "5": >90% верных ответов, без подсказок.
        - Оценка "4": 75-89% верных ответов.
        - Оценка "3": 50-74% верных ответов.

        5. Технические требования
        Браузер Chrome/Edge/Firefox, наличие интернета (для работы ИИ).

        Авторы: Миннивалиев Т.М., Емелин В.М.
        """
        
        st.download_button(
            label="📥 Скачать УМК (TXT)",
            data=method_text,
            file_name="UMK_Formula_Bezopasnosti.txt",
            mime="text/plain",
            use_container_width=True
        )
        
        st.success("✅ После скачивания файл можно конвертировать в PDF или Word для приложения к диплому.")


def render_norms() -> None:
    st.header("📚 Абсолютная энциклопедия спасателя")
    st.markdown(
        "Полный инженерный и правовой справочник: от законодательных актов и классификации зданий "
        "до тактических расчетов РТП и оказания первой помощи. Данные основаны на действующих ФЗ, СП, ГОСТ и Приказах МЧС России."
    )
    st.markdown("---")

    # 7 вкладок для максимального охвата
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "⚖️ Законодательство", 
        "🔥 Пожарная безопасность", 
        "🚪 Эвакуация и СОУЭ", 
        "🧯 Техника и ГАСИ", 
        "📊 Тактика и ГДЗС",
        "☢️ Гражданская защита",
        "🚑 Первая помощь"
    ])

    # ==========================================
    # ВКЛАДКА 1: ЗАКОНОДАТЕЛЬСТВО
    # ==========================================
    with tab1:
        st.subheader("ФЗ № 69-ФЗ «О пожарной безопасности»")
        with st.expander("Статья 1. Основные понятия", expanded=True):
            st.markdown(
                """
                *   **Пожарная безопасность** — состояние защищенности личности, имущества, общества и государства от пожаров.
                *   **Пожар** — неконтролируемое горение, причиняющее материальный ущерб, вред жизни и здоровью граждан.
                *   **Нарушение требований пожарной безопасности** — невыполнение или ненадлежащее выполнение требований.
                *   **Государственный пожарный надзор** — деятельность по проверке соблюдения требований пожарной безопасности.
                """
            )
        with st.expander("Статья 22. Тушение пожаров"):
            st.markdown(
                """
                *   Тушение пожаров осуществляется **на безвозмездной основе**.
                *   При тушении проводятся **аварийно-спасательные работы**, связанные со спасением людей и имущества.
                *   **РТП (Руководитель тушения пожара)** — должностное лицо, прибывшее на пожар. Его указания обязательны для всех граждан.
                """
            )
        with st.expander("Статья 34. Права и обязанности граждан"):
            col1, col2 = st.columns(2)
            with col1:
                st.success("**Граждане имеют ПРАВО на:**")
                st.markdown(
                    """
                    *   Защиту жизни, здоровья и имущества при пожаре.
                    *   Возмещение ущерба.
                    *   Получение информации по вопросам пожарной безопасности.
                    *   Участие в добровольной пожарной охране.
                    """
                )
            with col2:
                st.error("**Граждане ОБЯЗАНЫ:**")
                st.markdown(
                    """
                    *   Соблюдать требования пожарной безопасности.
                    *   Иметь первичные средства пожаротушения.
                    *   Немедленно уведомлять пожарную охрану при обнаружении пожара.
                    *   Оказывать содействие пожарной охране.
                    """
                )

        st.subheader("ФЗ № 68-ФЗ «О защите населения от ЧС»")
        with st.expander("Основные понятия и обязанности"):
            st.markdown(
                """
                *   **ЧС** — обстановка, сложившаяся в результате аварии или катастрофы, повлекшая жертвы и ущерб.
                *   **Предупреждение ЧС** — мероприятия, направленные на уменьшение риска.
                *   **Граждане обязаны:** изучать способы защиты, выполнять правила поведения при ЧС, оказывать содействие спасателям.
                """
            )

        st.subheader("ФЗ № 151-ФЗ «Об аварийно-спасательных службах»")
        with st.expander("Статья 27. Обязанности спасателя"):
            st.error(
                """
                *   Быть готовым к участию в ликвидации ЧС.
                *   Совершенствовать физическую и психологическую подготовку.
                *   Активно вести поиск пострадавших, оказывать первую помощь.
                *   Неукоснительно выполнять приказы руководителей.
                *   Соблюдать меры безопасности.
                """
            )

    # ==========================================
    # ВКЛАДКА 2: ПОЖАРНАЯ БЕЗОПАСНОСТЬ
    # ==========================================
    with tab2:
        st.subheader("Категории помещений по взрывопожарной опасности (СП 12.13130)")
        st.dataframe(
            {
                "Категория": ["А", "Б", "В1-В4", "Г", "Д"],
                "Опасность": ["Повышенная взрывопожароопасность", "Взрывопожароопасность", "Пожароопасность", "Умеренная", "Пониженная"],
                "Характеристика": [
                    "Горючие газы, ЛВЖ с t вспышки < 28°C",
                    "Горючие пыли, ЛВЖ с t вспышки > 28°C",
                    "Горючие жидкости, твердые вещества",
                    "Негорючие вещества в раскаленном состоянии",
                    "Негорючие вещества в холодном состоянии"
                ]
            },
            hide_index=True,
            use_container_width=True
        )

        st.subheader("Классификация пожаров (123-ФЗ, Ст. 8)")
        st.dataframe(
            {
                "Класс": ["A", "B", "C", "D", "E", "F"],
                "Материал": ["Твердые вещества", "Горючие жидкости", "Газы", "Металлы", "Электроустановки", "Ядерные материалы"],
                "Примеры": ["Дерево, бумага", "Бензин, масла", "Пропан, метан", "Магний, натрий", "Под напряжением", "Радиоактивные отходы"],
                "Способ тушения": ["Вода, пена", "Пена, порошок", "Порошок, объем", "Спецпорошки", "CO2, порошок", "Спецсоставы"]
            },
            hide_index=True,
            use_container_width=True
        )

        st.subheader("Предельные значения ОФП (ГОСТ 12.1.004-91)")
        col1, col2, col3 = st.columns(3)
        col1.metric("Температура", "70 °C", help="Предельная для человека")
        col2.metric("Тепловой поток", "1,4 кВт/м²", help="Болевой порог кожи")
        col3.metric("Потеря видимости", "20 м", help="Из-за задымления")
        col1.metric("Угарный газ (CO)", "0,1 %", help="По объему")
        col2.metric("Углекислый газ (CO2)", "6 %", help="По объему")
        col3.metric("Кислород (O2)", "14 %", help="Понижение (норма 21%)")

    # ==========================================
    # ВКЛАДКА 3: ЭВАКУАЦИЯ И СОУЭ
    # ==========================================
    with tab3:
        st.subheader("СП 3.13130.2009 «Системы оповещения (СОУЭ)»")
        st.dataframe(
            {
                "Тип СОУЭ": ["1-й", "2-й", "3-й", "4-й", "5-й"],
                "Способ оповещения": ["Звуковой (сирена)", "Звуковой + световые знаки", "Речевой + световые знаки", "Речевой + разделение на зоны", "Речевой + управление эвакуацией"],
                "Применение": ["Небольшие здания", "Гостиницы, школы", "ТЦ, больницы", "Многофункциональные", "Высотные здания"]
            },
            hide_index=True,
            use_container_width=True
        )

        st.subheader("СП 1.13130.2020 «Эвакуационные пути»")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(
                """
                *   **Ширина выхода:** 0,8 м (при < 50 чел.).
                *   **Ширина выхода (> 50 чел.):** 1,2 м.
                *   **Высота в свету:** не менее 1,9 м.
                *   **Пороги:** не более 3 см.
                *   **Двери:** открываются наружу.
                """
            )
        with col2:
            st.markdown(
                """
                *   **Ширина лестничного марша:** 1,35 м (> 50 чел.).
                *   **Уклон лестниц:** не более 1:2 (26°).
                *   **Высота ограждений:** не менее 1,2 м.
                *   **Незадымляемые лестницы:** Н1 (через балконы), Н2 (подпор воздуха), Н3 (тамбур-шлюзы).
                """
            )

    # ==========================================
    # ВКЛАДКА 4: ТЕХНИКА И ГАСИ
    # ==========================================
    with tab4:
        st.subheader("Пожарные автомобили (ПА)")
        st.dataframe(
            {
                "Тип": ["АЦ", "АЛ", "АКП", "АГ", "АСА"],
                "Расшифровка": ["Автоцистерна", "Автолестница", "Автоколенчатый подъемник", "Автогидрант", "Аварийно-спасательный"],
                "Назначение": ["Вода + пенообразователь", "Спасение с высоты", "Спасение с высоты", "Крупные пожары", "ДТП, ГАСИ"]
            },
            hide_index=True,
            use_container_width=True
        )

        st.subheader("Пожарные стволы и рукава")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(
                """
                **Стволы:**
                *   **РСК-50:** Расход 3,5 л/с, насадок 13 мм.
                *   **РС-70:** Расход 7,4 л/с, насадок 19 мм.
                *   **ГПС-600:** Пена средней кратности, расход 6 л/с р-ра.
                *   **СВП-4:** Пена низкой кратности.
                """
            )
        with col2:
            st.markdown(
                """
                **Рукава:**
                *   **51 мм:** Рабочий (внутри зданий).
                *   **66 мм:** Рабочий (для РС-70).
                *   **77 мм:** Магистральный (снижает потери).
                *   **89–150 мм:** Для перекачки больших объемов.
                """
            )

        st.subheader("СИЗОД и ГАСИ")
        st.markdown(
            """
            *   **ДАСВ (сжатый воздух):** Время 45–120 мин, баллоны 300 атм. Команда «Выход» при 70 атм.
            *   **ДАСК (сжатый кислород):** Время до 4 часов, 200 атм. Для подвалов и метро.
            *   **ГАСИ:** Расширители (до 10 тонн), Кусачки (арматура), Домкраты, Бензорезы.
            """
        )

    # ==========================================
    # ВКЛАДКА 5: ТАКТИКА И ГДЗС
    # ==========================================
    with tab5:
        st.subheader("Тактические расчеты РТП")
        col1, col2 = st.columns(2)
        with col1:
            st.latex(r"S_{\text{п}} = a \cdot b \quad \text{или} \quad \pi \cdot R^2")
            st.caption("Площадь пожара")
            st.latex(r"S_{\text{т}} = P \cdot h")
            st.caption("Площадь тушения (\(h\) = 5 м для ручных стволов)")
            st.latex(r"Q_{\text{тр}} = S_{\text{т}} \cdot I_{\text{тр}}")
            st.caption("Требуемый расход воды")
        with col2:
            st.latex(r"N_{\text{ст}} = \frac{Q_{\text{тр}}}{q_{\text{ст}}}")
            st.caption("Количество стволов")
            st.latex(r"V_{\text{в}} = Q_{\text{тр}} \cdot t_{\text{расч}} \cdot 60")
            st.caption("Объем воды для тушения")
            st.latex(r"Q_{\text{ф}} = N_{\text{ст}} \cdot q_{\text{ст}}")
            st.caption("Фактический расход (должен быть \(\geq Q_{\text{тр}}\))")

        st.subheader("Интенсивность подачи воды (\(I_{тр}\))")
        st.dataframe(
            {
                "Объект": ["Жилые здания, офисы", "Склады, библиотеки", "ЛВЖ (бензин)", "Производственные цеха", "Гаражи, депо"],
                "Интенсивность (л/с·м²)": ["0,1", "0,2", "0,15 (пеной)", "0,1 - 0,3", "0,1"]
            },
            hide_index=True,
            use_container_width=True
        )

        st.subheader("Расчет работы в ДАСВ")
        st.latex(r"T_{общ} = \frac{V \cdot (P_{вх} - P_{вых})}{Q_{ср}}")
        st.markdown("Время возврата = \(T_{общ} / 2\). Состав звена: минимум 3 человека.")

    # ==========================================
    # ВКЛАДКА 6: ГРАЖДАНСКАЯ ЗАЩИТА
    # ==========================================
    with tab6:
        st.subheader("☢️ Радиационная безопасность")
        col1, col2 = st.columns(2)
        with col1:
            st.info("**Приборы разведки:**")
            st.markdown(
                """
                *   **ДП-5В:** Радиометр (измерение гамма/бета).
                *   **ИД-1:** Индивидуальный дозиметр.
                *   **ДП-22В:** Комплект войсковых дозиметров.
                """
            )
        with col2:
            st.warning("**Степени лучевой болезни:**")
            st.markdown(
                """
                *   1 Зв — легкая (тошнота).
                *   2-4 Зв — средняя (госпитализация).
                *   > 6 Зв — смертельная (без помощи).
                *   Безопасно: до 1 мЗв/год.
                """
            )

        st.subheader("☣️ АХОВ (Химическая защита)")
        st.dataframe(
            {
                "Вещество": ["Аммиак (NH3)", "Хлор (Cl2)", "Ртуть (Hg)"],
                "Свойства": ["Легче воздуха", "Тяжелее воздуха", "Жидкий металл"],
                "Защита": ["5% лимонная кислота", "2% сода", "Демеркуризация"],
                "Эвакуация": ["Верхние этажи", "Верхние этажи", "Проветривание"]
            },
            hide_index=True,
            use_container_width=True
        )

    # ==========================================
    # ВКЛАДКА 7: ПЕРВАЯ ПОМОЩЬ
    # ==========================================
    with tab7:
        st.subheader("🚑 Сердечно-легочная реанимация (СЛР)")
        st.success("**Алгоритм:** Безопасность -> Проверка дыхания (10 сек) -> Вызов 112 -> 30 компрессий (5-6 см) -> 2 вдоха -> Цикл.")
        
        st.subheader("Виды кровотечений")
        st.dataframe(
            {
                "Вид": ["Артериальное", "Венозное", "Капиллярное"],
                "Признак": ["Алая кровь, фонтан", "Темная кровь, поток", "Сочится"],
                "Помощь": ["Жгут выше раны (до 1 часа)", "Давящая повязка", "Стерильная повязка"]
            },
            hide_index=True,
            use_container_width=True
        )

        st.subheader("Правило ладони и девяток (Ожоги)")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(
                """
                *   **Ладонь:** 1% тела.
                *   **Голова:** 9%.
                *   **Рука:** 9%.
                """
            )
        with col2:
            st.markdown(
                """
                *   **Нога:** 18%.
                *   **Грудь:** 18%.
                *   **Спина:** 18%.
                """
            )
        st.info("Ожог > 10% — тяжелая травма. Охлаждать водой 10-20 мин, не мазать маслом!")



def render_about_college() -> None:
    st.header("🏛️ О колледже")
    
    @st.cache_data(show_spinner=False)
    def get_base64_image(image_path):
        try:
            with open(image_path, "rb") as img_file:
                return "data:image/jpeg;base64," + base64.b64encode(img_file.read()).decode()
        except FileNotFoundError:
            return ""

    img1 = get_base64_image("assets/college_photos/1.jpg")
    img2 = get_base64_image("assets/college_photos/2.jpg")
    img3 = get_base64_image("assets/college_photos/3.jpg")
    img4 = get_base64_image("assets/college_photos/4.jpg")

    slider_html = f"""
    <style>
    body {{ margin: 0; padding: 0; font-family: sans-serif; }}
    .slider-container {{ position: relative; width: 100%; height: 500px; border-radius: 15px; overflow: hidden; box-shadow: 0 10px 30px rgba(11, 37, 69, 0.2); }}
    .slide {{ position: absolute; top: 0; left: 0; width: 100%; height: 100%; opacity: 0; animation: fade 20s infinite; }}
    .slide img {{ width: 100%; height: 100%; object-fit: cover; }}
    .slide:nth-child(1) {{ animation-delay: 0s; }}
    .slide:nth-child(2) {{ animation-delay: 5s; }}
    .slide:nth-child(3) {{ animation-delay: 10s; }}
    .slide:nth-child(4) {{ animation-delay: 15s; }}
    
    @keyframes fade {{
        0% {{ opacity: 0; }}
        3% {{ opacity: 1; }}
        22% {{ opacity: 1; }}
        25% {{ opacity: 0; }}
        100% {{ opacity: 0; }}
    }}
    
    .college-overlay {{
        position: absolute;
        bottom: 30px;
        right: 30px;
        background: rgba(11, 37, 69, 0.85);
        backdrop-filter: blur(8px);
        color: white;
        padding: 25px 30px;
        border-left: 6px solid #F26A1B;
        border-radius: 10px;
        max-width: 500px;
        z-index: 10;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }}
    </style>
    
    <div class="slider-container">
        <div class="slide"><img src="{img1}"></div>
        <div class="slide"><img src="{img2}"></div>
        <div class="slide"><img src="{img3}"></div>
        <div class="slide"><img src="{img4}"></div>
        
        <div class="college-overlay">
            <h3 style="margin-top: 0; color: #F26A1B; font-weight: 800; font-size: 1.3rem;">ГАПОУ «ТГКГЗ»</h3>
            <p style="margin-bottom: 0; font-size: 1.05rem; line-height: 1.4;">
                Кузница кадров для системы МЧС. Здесь соединились богатая история, 
                славные традиции и современные технологии обучения.
            </p>
        </div>
    </div>
    """
    components.html(slider_html, height=520)
    
    st.markdown(
        """
        <div style="background-color: white; padding: 25px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); margin-bottom: 30px;">
        <h3 style="color: #0B2545; margin-top: 0;">Наша история и миссия</h3>
        <p>Колледж основан <b>в 1917 году</b> как профессиональное учреждение педагогического профиля. С 2014 года в колледже началась подготовка кадров среднего звена в сфере гражданской защиты населения для <b>системы МЧС</b>.</p>
        <p>В 2015 г. колледж переименован в ГАПОУ «Тетюшский государственный колледж гражданской защиты».</p>
        <p>Мы — <b>единственное</b> профессиональное образовательное учреждение в Республике Татарстан среди государственных, реализующих специальности СПО для системы МЧС, а также единственное в юго-западном регионе республики, осуществляющее подготовку педагогических кадров.</p>
        <p>Ежегодно колледж открывает двери для тех, кто ценит <b>качественное образование</b>, качество которого проверено временем и доказывается <b>успешностью выпускников</b>, получивших универсальные знания и самореализовавшихся в различных областях профессиональной деятельности.</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    st.subheader("🎓 Специальности")
    st.markdown("Колледж готовит специалистов по следующим направлениям:")
    
    @st.cache_data(show_spinner=False)
    def get_spec_img(image_name):
        path = f"assets/college_photos/specialties/{image_name}"
        try:
            with open(path, "rb") as img_file:
                return "data:image/jpeg;base64," + base64.b64encode(img_file.read()).decode()
        except FileNotFoundError:
            return "https://via.placeholder.com/400x200?text=Нет+фото"

    def render_card(col, img_path, code, title, icon):
        img_data = get_spec_img(img_path)
        html = f"""
        <div style="background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.08); margin-bottom: 25px; transition: transform 0.3s;">
            <img src="{img_data}" style="width: 100%; height: 180px; object-fit: cover;">
            <div style="padding: 15px;">
                <div style="color: #F26A1B; font-weight: bold; font-size: 0.9rem;">{code}</div>
                <div style="color: #0B2545; font-weight: bold; font-size: 1.05rem; margin-top: 5px; line-height: 1.3;">
                    {icon} {title}
                </div>
            </div>
        </div>
        """
        with col:
            st.markdown(html, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    render_card(col1, "1.jpg", "20.02.02", "Защита в чрезвычайных ситуациях", "🚒")
    render_card(col2, "2.jpg", "49.02.01", "Физическая культура", "🏃")
    render_card(col3, "3.jpg", "25.02.08", "Эксплуатация беспилотных авиационных систем", "🛸")

    col4, col5, col6 = st.columns(3)
    render_card(col4, "4.jpg", "09.02.07", "Информационные системы и программирование", "💻")
    render_card(col5, "5.jpg", "20.02.05", "Организация оперативного (экстренного) реагирования в ЧС", "📞")
    render_card(col6, "6.png", "09.02.13", "Интеграция решений с применением технологий ИИ", "🤖")

    col7, col8, col9 = st.columns(3)
    render_card(col8, "7.jpg", "20.02.04", "Пожарная безопасность", "🔥")
    st.markdown("---")

    st.subheader("📍 Контакты")
    
    col_addr, col_contacts = st.columns(2)
    
    with col_addr:
        st.markdown(
            """
            <div style="background-color: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); min-height: 405px; border-top: 5px solid #F26A1B; display: flex; flex-direction: column; justify-content: space-between;">
                <div>
                    <h4 style="color: #0B2545; margin-top: 0; margin-bottom: 20px;">🏢 Как нас найти</h4>
                    <p style="color: #5A6A85; line-height: 1.6; margin-bottom: 15px;">
                        <b>Адрес:</b><br>
                        422370, Республика Татарстан,<br>
                        г. Тетюши, ул. Фрунзе, д. 23
                    </p>
                </div>
                <p style="color: #5A6A85; line-height: 1.6; margin-bottom: 15px;">
                    <b>Официальный сайт:</b><br>
                        <a href="https://tetushi-tpu.ru" target="_blank" style="color: #F26A1B; text-decoration: none; font-weight: bold;">tetushi-tpu.ru</a>
                    </p>
                <p style="color: #5A6A85; line-height: 1.6; margin-bottom: 0;">
                    <b>Электронная почта:</b><br>
                    <a href="mailto:Tetyush.GKGZ@tatar.ru" style="color: #F26A1B; text-decoration: none; font-weight: bold;">Tetyush.GKGZ@tatar.ru</a>
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
    with col_contacts:
        st.markdown(
            """
            <div style="background-color: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); min-height: 380px; border-top: 5px solid #0B2545;">
                <h4 style="color: #0B2545; margin-top: 0; margin-bottom: 20px;">📞 Телефоны для связи</h4>
                <ul style="list-style-type: none; padding-left: 0; color: #5A6A85; line-height: 1.8;">
                    <li style="margin-bottom: 10px;">
                        <b style="color: #0B2545;">+7 (843) 732-56-36</b><br>
                        <span style="font-size: 0.9em;">Адаева Татьяна Юрьевна <i>(Директор)</i></span>
                    </li>
                    <li style="margin-bottom: 10px;">
                        <b style="color: #0B2545;">+7 (843) 732-56-10</b><br>
                        <span style="font-size: 0.9em;">Клюева Екатерина Олеговна <i>(Зам. директора по УМР)</i></span>
                    </li>
                    <li style="margin-bottom: 10px;">
                        <b style="color: #0B2545;">+7 (843) 732-56-27</b><br>
                        <span style="font-size: 0.9em;">2-е здание</span>
                    </li>
                    <li>
                        <b style="color: #0B2545;">+7 (843) 732-56-29</b><br>
                        <span style="font-size: 0.9em;">Бухгалтерия</span>
                    </li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True
        )

def render_feedback() -> None:
    st.header("💬 Обратная связь")
    st.markdown(
        "Нашли ошибку в расчётах, обнаружили баг или у вас есть предложение по улучшению тренажёра? "
        "Напишите нам! Мы обязательно учтём ваши пожелания."
    )
    
    with st.form("feedback_form"):
        name = st.text_input("Ваше имя (или группа)")
        message = st.text_area("Ваше сообщение")
        submit = st.form_submit_button("📨 Подготовить письмо")
        
        if submit:
            if not name or not message:
                st.warning("Пожалуйста, заполните оба поля, чтобы мы знали, от кого письмо.")
            else:
                subject = urllib.parse.quote(f"Обратная связь: Формула безопасности МЧС ({name})")
                body = urllib.parse.quote(f"Имя/Группа: {name}\n\nСообщение:\n{message}")
                
                target_email = "tayfun23432@mail.ru" 
                mailto_link = f"mailto:{target_email}?subject={subject}&body={body}"
                
                st.success("✅ Текст письма сформирован! Нажмите на кнопку ниже, чтобы открыть ваш почтовый клиент.")
                st.markdown(
                    f'<a href="{mailto_link}" target="_blank" style="display: inline-block; padding: 10px 20px; background-color: #F26A1B; color: white; text-decoration: none; border-radius: 8px; font-weight: bold;">Открыть почту и отправить</a>',
                    unsafe_allow_html=True
                )
                st.caption("Если почтовая программа не открылась, просто скопируйте ваше сообщение и отправьте его нам вручную.")

PAGES = {
    "🏠 Главная": render_home,
    "🔥 Пожарная физика": fire_physics.render,
    "💧 Гидравлика": hydraulics.render,
    "🚪 Эвакуация": evacuation.render,
    "🏗️ Нагрузки": loads.render,
    "⚠️ Риск ЧС": risk.render,
    "🎯 Тренажёр задач": trainer.render,
    "📞 Диспетчер 112": dispatcher.render,
    "📈 Песочница": sandbox.render,
    "🎮 Симулятор спасателя": simulator.render,
    "📜 История": render_history,
    "📚 Нормативная база": render_norms,
    "👨‍🏫 Преподавателю": render_teacher_guide,
    "🏛️ О колледже": render_about_college,
    "💬 Обратная связь": render_feedback,
}


def render_sidebar() -> str:
    with st.sidebar:
        col1, col2, col3 = st.columns([1, 15, 1])
        with col2:
            try:
                st.image("assets/logo.png", use_container_width=True)
            except Exception:
                pass
            
        st.markdown(
            '<div style="text-align: center; font-size: 1.05rem; font-weight: 600; margin-bottom: 25px; line-height: 1.3; color: #FFD9C2;">'
            'ГАПОУ «Тетюшский государственный<br>колледж гражданской защиты»'
            '</div>',
            unsafe_allow_html=True
        )

        choice = st.radio("Разделы", list(PAGES.keys()), key="nav")
        st.markdown("---")
        
        st.markdown(ABOUT_HTML, unsafe_allow_html=True)
        st.markdown("---")
        
        st.markdown(
            '<div class="fb-about" style="border-left-color: #F26A1B;">'
            '<b>Авторы проекта:</b><br><br>'
            '<span style="font-size: 1.05rem;">Миннивалиев Тимур Марсельевич</span><br>'
            '<span style="font-size: 0.85rem; color: #FFD9C2;">Основной разработчик</span><br><br>'
            '<span style="font-size: 1.05rem;">Емелин Вячеслав Максимович</span><br>'
            '<span style="font-size: 0.85rem; color: #FFD9C2;">Дизайн и оформление</span><br><br>'
            'Курсанты 105 группы'
            '</div>',
            unsafe_allow_html=True
        )
        
        st.markdown("---")
        if ai_explainer.is_demo_mode():
            st.caption("ИИ: демо-режим (ключ не задан)")
        else:
            st.caption("ИИ: OpenAI подключен")
    return choice


def main() -> None:
    st.set_page_config(page_title="Формула безопасности МЧС", page_icon="🛡️", layout="wide")
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    storage.init_db()
    choice = render_sidebar()
    render_header()
    try:
        PAGES[choice]()
    except Exception as exc:
        st.error("В модуле произошла непредвиденная ошибка. Проверьте исходные данные и попробуйте снова.")
        st.exception(exc)


if __name__ == "__main__":
    main()