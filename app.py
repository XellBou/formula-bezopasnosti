"""«Формула безопасности» — точка входа Streamlit-приложения."""
from __future__ import annotations

import pandas as pd
import streamlit as st
import urllib.parse
import streamlit.components.v1 as components
import base64
import os

from core import ai_explainer, storage
from modules import evacuation, fire_physics, hydraulics, loads, risk, trainer

CUSTOM_CSS = """
<style>
.stApp { background-color: #F5F7FA; }

/* Боковая панель */
[data-testid="stSidebar"] { background-color: #0B2545; }
[data-testid="stSidebar"] * { color: #FFFFFF !important; }
[data-testid="stSidebar"] .fb-side-title { font-size: 1.25rem; font-weight: 700; margin-bottom: 0.5rem; }
[data-testid="stSidebar"] .fb-about {
    background: rgba(255, 255, 255, 0.08);
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
.fb-header .fb-title { color: #FFFFFF; font-size: 2rem; font-weight: 800; }
.fb-header .fb-subtitle { color: #FFD9C2; font-size: 1.05rem; margin-top: 4px; }

/* Кнопки */
.stButton > button, .stFormSubmitButton > button {
    background-color: #F26A1B;
    color: #FFFFFF;
    border: none;
    border-radius: 8px;
    font-weight: 600;
    padding: 0.45rem 1.1rem;
}
.stButton > button:hover, .stFormSubmitButton > button:hover {
    background-color: #D4570F;
    color: #FFFFFF;
}
.stButton > button p, .stFormSubmitButton > button p { color: #FFFFFF; }

/* Метрики */
[data-testid="stMetric"], [data-testid="metric-container"] {
    background: #FFFFFF;
    border-left: 5px solid #F26A1B;
    border-radius: 8px;
    padding: 12px 16px;
    box-shadow: 0 1px 4px rgba(11, 37, 69, 0.12);
}
[data-testid="stMetricValue"] { color: #0B2545; }

h1, h2, h3 { color: #0B2545; }

/* Карточка задачи в тренажёре */
.fb-task {
    background: #FFFFFF;
    border: 1px solid #D5DCE8;
    border-left: 5px solid #0B2545;
    border-radius: 8px;
    padding: 14px 18px;
    margin-bottom: 12px;
    font-size: 1.05rem;
    color: #0B2545;
}

/* Красивая белая подложка для логотипа в сайдбаре */
[data-testid="stSidebar"] [data-testid="stImage"] img {
    background-color: #FFFFFF;
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
    background: #FFFFFF;
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
.home-card-title { color: #0B2545; font-weight: 700; font-size: 1.1rem; margin-bottom: 5px; }
.home-card-text { color: #5A6A85; font-size: 0.9rem; line-height: 1.4; }

/* Блок "Знаете ли вы" */
.fact-box {
    background: linear-gradient(135deg, #0B2545 0%, #13315C 100%);
    color: #FFFFFF;
    border-radius: 10px;
    padding: 20px 25px;
    margin: 20px 0;
    border-left: 6px solid #F26A1B;
}
.fact-box b { color: #F26A1B; }



</style>
"""

ABOUT_HTML = """
<div style="margin-bottom: 5px;"><b>О проекте</b></div>
«Формула безопасности» — это тренажёр понимания, а не боевой инструмент
для расчётов во время пожара. Он показывает, как математика связана с профессией
спасателя, и помогает осознанно применять нормативы.

<div class="fb-slogan">Математика, которая спасает жизни</div>
"""


def render_header() -> None:
    col1, col2 = st.columns([3, 10])
    with col1:
        try:
            # Высота орла регулируется ТОЛЬКО здесь (width=340)
            st.image("assets/mchs.png", width=340)
        except Exception:
            st.markdown("## 🛡️")
    with col2:
        st.markdown(
            # ВЫСОТА БЛОКА РЕГУЛИРУЕТСЯ ЗДЕСЬ:
            # margin-top: 55px; -> опускает блок вниз (для выравнивания с орлом)
            # padding: 15px 25px; -> это рамка внутри блока. 
            #   15px — это отступ сверху и снизу (если уменьшить, блок станет ниже).
            #   25px — это отступ слева и справа.
            '<div class="fb-header" style="margin-top: 30px; margin-bottom: 0px; padding: 15px 25px;">'
            '<div class="fb-title" style="font-size: 1.9rem; margin-bottom: 5px;">Формула безопасности</div>'
            '<div class="fb-subtitle" style="font-size: 1.05rem; line-height: 1.4;">'
            'Интеллектуальный тренажёр по прикладной математике '
            'для курсантов ГАПОУ «Тетюшский государственный колледж гражданской защиты»'
            '</div>'
            '</div>',
            unsafe_allow_html=True,
        )


def render_home() -> None:
    st.markdown(
        "<h2 style='color: #0B2545; margin-bottom: 5px;'>Добро пожаловать в тренажёр!</h2>"
        "<p style='font-size: 1.1rem; color: #5A6A85; margin-bottom: 25px;'>"
        "«Формула безопасности» — это интерактивная платформа, которая показывает, как математика помогает спасать жизни."
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
            # Вместо if st.button используем on_click.
            # lambda n=nav_name: ... запоминает правильное имя раздела для каждой кнопки
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

    # Блок "Знаете ли вы?"
    st.markdown(
        '<div class="fact-box">'
        '<div style="font-size: 1.2rem; font-weight: bold; margin-bottom: 8px;">💡 Знаете ли вы?</div>'
        'При пожаре в помещении температура растёт <b>экспоненциально</b>. Уже к 6-й минуте она достигает <b>600 °C</b> (порог общей вспышки). '
        'Именно поэтому нормативы требуют прибытия первого караула за 10 минут — математика здесь напрямую определяет шансы на спасение.'
        '</div>',
        unsafe_allow_html=True
    )

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
    if rows: # Используем переменную rows из вкладки попыток
        import io
        csv_buffer = io.StringIO()
        # Пересоздаём DataFrame, чтобы экспортировать все данные
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
    st.header("👨‍🏫 Методические указания")
    st.markdown(
        "Данный раздел предназначен для преподавателей математики и специальных дисциплин. "
        "Он содержит рекомендации по интеграции тренажёра в учебный процесс."
    )
    
    tab1, tab2, tab3 = st.tabs(["📖 Методика", "📊 Оценка знаний", "🛠️ Работа с ошибками"])
    
    with tab1:
        st.subheader("Как встроить тренажёр в пару")
        st.markdown(
            """
            **Цель использования:** Показать практическую значимость математики в профессии спасателя, автоматизировать рутинные расчёты.
            
            **Вариант 1. Вводное занятие (15 минут)**
            1. На главной странице покажите связь модулей с реальными процессами.
            2. В модуле «Пожарная физика» запустите расчет с параметрами 20°C и 30 мин. Покажите график логарифмического роста температуры.
            3. Задайте курсантам вопрос: «Почему норматив прибытия — 10 минут, а не 20?» (Ответ в математике: к 10-й минуте температура уже опасна для жизни).
            
            **Вариант 2. Практическая работа (45 минут)**
            1. Разделите группу на бригады.
            2. Модуль «Гидравлика»: каждая бригада рассчитывает требуемое давление насоса для 5-этажного, 9-этажного и 16-этажного дома. Обсуждаются различия.
            3. Модуль «Эвакуация»: курсанты вводят параметры своего учебного кабинета (число людей, ширина двери) и проверяют, соответствует ли кабинет требованиям СП 1.13130.2020.
            """
        )
        
    with tab2:
        st.subheader("Как система проверяет ответы")
        st.markdown(
            """
            В разделе «Тренажёр задач» реализован допуск на погрешность **5%** (константа `TOLERANCE` в коде).
            
            *   **Почему 5%?** В инженерных расчётах на месте нет времени считать до сотых долей. Ошибка в 1-2% считается нормой (например, из-за использования 1 атм ≈ 100 кПа вместо 101,3 кПа).
            *   **Пример:** Если правильный ответ `2.94`, то ответы от `2.79` до `3.09` будут засчитаны как верные.
            *   **Задачи на нормативы:** В задачах типа «Соответствует ли это СП?» допуска нет, ответ должен быть строго 1 или 0, так как нормативы — это закон.
            """
        )
        st.info("💡 **Совет:** В разделе «История» вы можете выгрузить CSV-файл с результатами группы и проанализировать, какие темы вызвали больше всего ошибок.")

    with tab3:
        st.subheader("Как тренажёр развивает критическое мышление")
        st.markdown(
            """
            Если курсант вводит неверный ответ, система не просто пишет «Ошибка». Включается эвристический анализ (функция `guess_error`):
            
            1.  **Поиск пропорциональности:** Если ответ отличается в 10, 100 или 1000 раз, система подсказывает: *«Похоже на ошибку в единицах измерения (мм ↔ см ↔ м)»*.
            2.  **Поиск знака:** Если получилось отрицательное число давления или времени, система намекает на неправильный порядок действий.
            3.  **ИИ-разбор:** Кнопка «Разобрать с ИИ» отправляет задачу, ответ курсанта и эталонное решение нейросети. ИИ пытается понять логику курсанта и объяснить, где именно он свернул не туда.
            """
        )

def render_norms() -> None:
    st.header("📚 Нормативная база и справочные данные")
    st.markdown(
        "В этом разделе собраны ключевые документы, регламенты и справочные таблицы, "
        "которые необходимы в профессиональной деятельности специалиста МЧС России."
    )
    st.markdown("---")

    # Добавили 5-ю вкладку!
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🚪 Эвакуация и защита", 
        "📜 Пожарная безопасность", 
        "🧯 Техника и рукава", 
        "📊 Справочник РТП",
        "☢️ Гражданская защита"
    ])

    # --- ВКЛАДКА 1: ЭВАКУАЦИЯ И ЗАЩИТА ---
    with tab1:
        st.subheader("СП 1.13130.2020 «Эвакуационные пути и выходы»")
        st.info("**Главный документ для модуля «Эвакуация».** Устанавливает требования к геометрии путей эвакуации.")
        with st.expander("Показать ключевые требования", expanded=True):
            st.markdown(
                """
                *   **Ширина выхода:** не менее **0,8 м** (в общем случае).
                *   **Ширина выхода (при >50 чел.):** не менее **1,2 м**.
                *   **Высота в свету:** не менее **1,9 м**.
                *   **Количество выходов:** не менее **двух** для помещений с пребыванием более **50 человек**.
                *   **Ширина коридора:** не менее **1,2 м** (при эвакуации более 50 чел.).
                """
            )
            
        st.subheader("СП 7.13130.2013 «Противодымная защита»")
        with st.expander("Показать требования к дымоудалению"):
            st.markdown(
                """
                *   В зданиях высотой более 28 метров обязательна система дымоудаления.
                *   Скорость движения дыма по коридорам достигает **10–15 м/мин**.
                *   Незадымляемые лестничные клетки бывают 3 типов (с подпором воздуха, с проходами через балконы и т.д.).
                """
            )

        st.subheader("СП 2.13130.2020 «Огнестойкость объектов»")
        with st.expander("Пределы огнестойкости строительных конструкций (REI)"):
            st.markdown(
                """
                Огнестойкость измеряется в минутах до потери несущей способности (R), целостности (E) или теплоизолирующей способности (I).
                *   **REI 15 / 30 / 45:** Здания V и IV степеней огнестойкости (деревянные, каркасные).
                *   **REI 60 / 90:** Здания III и II степеней (кирпич, бетон).
                *   **REI 120 / 150:** Здания I степени (высотные, крупные ТЦ).
                *   **REI 240 / 360:** Уникальные сооружения, тоннели, метро.
                """
            )

    # --- ВКЛАДКА 2: ПОЖАРНАЯ БЕЗОПАСНОСТЬ ---
    with tab2:
        st.subheader("ФЗ № 123-ФЗ «Технический регламент о требованиях пожарной безопасности»")
        st.info("**Базовый закон.** Устанавливает классификацию пожаров и опасные факторы.")
        
        with st.expander("Классификация пожаров по виду горючего материала (Статья 8)", expanded=True):
            st.markdown(
                """
                *   **Класс A** — горение твердых веществ (дерево, бумага, текстиль).
                *   **Класс B** — горение горючих жидкостей (бензин, масла).
                *   **Класс C** — горение газов (пропан, метан).
                *   **Класс D** — горение металлов (магний, натрий).
                *   **Класс E** — горение электроустановок под напряжением.
                *   **Класс F** — горение ядерных материалов.
                """
            )
        
        st.subheader("Опасные факторы пожара (ОФП)")
        st.warning("Это предельные значения, при которых человек может погибнуть или потерять сознание.")
        with st.expander("Показать критические значения (ГОСТ 12.1.004-91)"):
            st.markdown(
                """
                *   **Температура:** **70 °C**.
                *   **Тепловой поток:** **1,4 кВт/м²** (болевой порог кожи).
                *   **Потеря видимости:** до **20 метров** (задымление).
                *   **Понижение кислорода:** до **14 %** (в норме 21%).
                *   **Угарный газ (CO):** **0,1 %** по объему.
                *   **Углекислый газ (CO2):** **6 %** по объему.
                """
            )

        st.subheader("СП 484.1311500.2020 «Системы пожарной сигнализации»")
        with st.expander("Классификация огнетушителей по ОТВ"):
            st.markdown(
                """
                *   **ОВ (воздушно-пенные):** для класса A, B. Нельзя для E (поражение током).
                *   **ОУ (углекислотные):** для класса B, C, E. 
                *   **ОП (порошковые):** для A, B, C, D, E (универсальные).
                *   **ОХ (хладоновые):** для B, C, E (серверные, музеи).
                """
            )

    # --- ВКЛАДКА 3: ТЕХНИКА И РУКАВА ---
    with tab3:
        st.subheader("Пожарные рукава и гидравлика")
        st.info("**База для расчета гидравлики.**")
        with st.expander("Классификация рукавов (диаметры и применение)", expanded=True):
            st.markdown(
                """
                *   **Рукав 51 мм (РСК-50):** Рабочий рукав для тушения внутри зданий. Расход ~3,5 л/с.
                *   **Рукав 66 мм (РС-70):** Рабочий рукав для тушения крупных очагов. Расход ~7,4 л/с.
                *   **Рукав 77 мм:** Магистральный рукав для подачи воды от водоисточника к разветвлению.
                *   **Рукав 89–150 мм:** Используется для перекачки больших объемов воды.
                """
            )

        st.subheader("Пожарные лестницы и спасательные устройства")
        with st.expander("Типы ручных пожарных лестниц"):
            st.markdown(
                """
                *   **Лестница-палка (ЛП):** Для подъема на высоту до 3 метров.
                *   **Штурмовая лестница (ЛШ):** Для подъема на этажи зданий (до 4-го этажа).
                *   **Трехколенная лестница (Л-60):** Длина 10,7 метра. Для подъема на 3-й этаж или на крышу.
                """
            )
            
        st.subheader("СИЗОД (Средства индивидуальной защиты органов дыхания)")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(
                """
                **ДАСВ (сжатый воздух):**
                *   Время работы: **60–120 минут**.
                *   Баллоны: 300 атм.
                """
            )
        with col2:
            st.markdown(
                """
                **ДАСК (сжатый кислород):**
                *   Время работы: **до 4 часов**.
                *   Для работы в подземных сооружениях и метро.
                """
            )

    # --- ВКЛАДКА 4: СПРАВОЧНИК РТП (ТАКТИКА) ---
    with tab4:
        st.subheader("Формулы пожарной тактики (Справочник РТП)")
        
        st.markdown("**1. Площадь пожара (Sп)** — зона, в которой происходит горение.")
        st.latex(r"S_{\text{п}} = a \cdot b \quad \text{(прямоугольная форма)}")
        st.latex(r"S_{\text{п}} = \pi \cdot R^2 \quad \text{(круговая форма)}")
        st.caption("Где \(a\) и \(b\) — ширина и длина помещения, \(R\) — радиус распространения огня.")

        st.markdown("**2. Требуемый расход воды (Qтр)** для локализации пожара:")
        st.latex(r"Q_{\text{тр}} = S_{\text{п}} \cdot I_{\text{тр}}")
        st.caption(
            "Где \(I_{\text{тр}}\) — требуемая интенсивность подачи воды (справочная величина). "
            "Для твердых материалов \(I_{\text{тр}} \approx 0,1 \text{ л/(с} \cdot \text{м}^2)\)."
        )
        
        st.markdown("**3. Требуемое количество стволов (Nст):**")
        st.latex(r"N_{\text{ст}} = \frac{Q_{\text{тр}}}{q_{\text{ст}}}")
        st.caption("Где \(q_{\text{ст}}\) — расход одного ствола (РСК-50 = 3,5 л/с; РС-70 = 7,4 л/с).")

        st.markdown("---")
        st.subheader("Нормативы пожарно-строевой подготовки (ПСП)")
        with st.expander("Надевание боевой одежды и снаряжения (БОП)", expanded=True):
            st.markdown(
                """
                *   **Отлично:** 21 секунда.
                *   **Хорошо:** 24 секунды.
                *   **Удовлетворительно:** 27 секунд.
                *   **Норматив для караула:** выезд и сбор в полном составе — до 90 секунд.
                """
            )
            
        with st.expander("Вязка двойной спасательной петли (на пострадавшего)"):
            st.markdown(
                """
                *   **Отлично:** 15 секунд.
                *   **Хорошо:** 17 секунд.
                *   **Удовлетворительно:** 20 секунд.
                """
            )

    # --- ВКЛАДКА 5: ГРАЖДАНСКАЯ ЗАЩИТА ---
    with tab5:
        st.subheader("☢️ Радиационная безопасность")
        st.info("В колледже гражданской защиты этому уделяется особое внимание.")
        with st.expander("Единицы измерения и дозы", expanded=True):
            st.markdown(
                """
                *   **Грей (Гр)** — поглощенная доза (энергия, переданная веществу).
                *   **Зиверт (Зв)** — эквивалентная доза (влияние на живые организмы).
                *   *1 Гр = 1 Зв для гамма-излучения.*
                *   **Безопасная доза:** до 50 мЗв (миллизиверт) в год (для населения).
                *   **Лучевая болезнь:** развивается при облучении **> 1 Зв**.
                """
            )

        st.subheader("☣️ Химическая безопасность (АХОВ)")
        with st.expander("Действия при разливе аммиака и хлора"):
            st.markdown(
                """
                **Аммиак (NH3):**
                *   Легче воздуха (поднимается вверх).
                *   Защита: ватно-марлевая повязка, смоченная 5% раствором лимонной кислоты.
                *   Эвакуация: из нижних этажей (подвал опасен).

                **Хлор (Cl2):**
                *   Тяжелее воздуха (стелется по земле, скапливается в низинах).
                *   Защита: ватно-марлевая повязка, смоченная 2% раствором соды.
                *   Эвакуация: на верхние этажи зданий.
                """
            )
            
        st.subheader("Убежища и укрытия")
        with st.expander("Классы защитных сооружений"):
            st.markdown(
                """
                *   **Убежища (класс А):** Выдерживают избыточное давление до **500 кПа** (5 атм). Защищают от радиации, ОМП и АХОВ.
                *   **ПРУ (Противорадиационные укрытия):** Защищают от радиации и светового излучения. Ослабляют радиацию в 100–300 раз.
                *   **Простейшие укрытия:** Щели, подвалы, овраги.
                """
            )

def render_about_college() -> None:
    st.header("🏛️ О колледже")
    
    # Функция для кодирования картинок в Base64 с кэшированием
    @st.cache_data(show_spinner=False)
    def get_base64_image(image_path):
        try:
            with open(image_path, "rb") as img_file:
                return "data:image/jpeg;base64," + base64.b64encode(img_file.read()).decode()
        except FileNotFoundError:
            return ""

    # Загружаем 4 фотографии (убедись, что пути правильные!)
    img1 = get_base64_image("assets/college_photos/1.jpg")
    img2 = get_base64_image("assets/college_photos/2.jpg")
    img3 = get_base64_image("assets/college_photos/3.jpg")
    img4 = get_base64_image("assets/college_photos/4.jpg")

    # --- КРАСИВЫЙ СЛАЙДЕР С ФОТО ---
    slider_html = """
    <style>
    body { margin: 0; padding: 0; font-family: sans-serif; }
    .slider-container { position: relative; width: 100%; height: 500px; border-radius: 15px; overflow: hidden; box-shadow: 0 10px 30px rgba(11, 37, 69, 0.2); }
    .slide { position: absolute; top: 0; left: 0; width: 100%; height: 100%; opacity: 0; animation: fade 20s infinite; }
    .slide img { width: 100%; height: 100%; object-fit: cover; }
    .slide:nth-child(1) { animation-delay: 0s; }
    .slide:nth-child(2) { animation-delay: 5s; }
    .slide:nth-child(3) { animation-delay: 10s; }
    .slide:nth-child(4) { animation-delay: 15s; }
    
    @keyframes fade {
        0% { opacity: 0; }
        3% { opacity: 1; }
        22% { opacity: 1; }
        25% { opacity: 0; }
        100% { opacity: 0; }
    }
    
    .college-overlay {
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
    }
    </style>
    
    <div class="slider-container">
        <div class="slide"><img src="{IMG1}"></div>
        <div class="slide"><img src="{IMG2}"></div>
        <div class="slide"><img src="{IMG3}"></div>
        <div class="slide"><img src="{IMG4}"></div>
        
        <div class="college-overlay">
            <h3 style="margin-top: 0; color: #F26A1B; font-weight: 800; font-size: 1.3rem;">ГАПОУ «ТГКГЗ»</h3>
            <p style="margin-bottom: 0; font-size: 1.05rem; line-height: 1.4;">
                Кузница кадров для системы МЧС. Здесь соединились богатая история, 
                славные традиции и современные технологии обучения.
            </p>
        </div>
    </div>
    """
    
    # Подставляем закодированные картинки в HTML
    slider_html = slider_html.replace("{IMG1}", img1)
    slider_html = slider_html.replace("{IMG2}", img2)
    slider_html = slider_html.replace("{IMG3}", img3)
    slider_html = slider_html.replace("{IMG4}", img4)
    
    components.html(slider_html, height=520)
    
    # ... (дальше идет блок истории и контактов, он остается без изменений)
    
    # --- ИСТОРИЯ И МИССИЯ ---
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
    
    # ... (дальше идет блок специальностей и контактов, который у тебя уже есть)

    
    # --- БЛОК СПЕЦИАЛЬНОСТЕЙ С ФОТО ---
    st.subheader("🎓 Специальности")
    st.markdown("Колледж готовит специалистов по следующим направлениям:")
    
    # Функция для конвертации картинок в Base64 с кэшированием
    @st.cache_data(show_spinner=False)
    def get_spec_img(image_name):
        path = f"assets/college_photos/specialties/{image_name}"
        try:
            with open(path, "rb") as img_file:
                return "data:image/jpeg;base64," + base64.b64encode(img_file.read()).decode()
        except FileNotFoundError:
            return "https://via.placeholder.com/400x200?text=Нет+фото"

    # Шаблон красивой карточки
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

    # Ряд 1
    col1, col2, col3 = st.columns(3)
    render_card(col1, "1.jpg", "20.02.02", "Защита в чрезвычайных ситуациях", "🚒")
    render_card(col2, "2.jpg", "49.02.01", "Физическая культура", "🏃")
    render_card(col3, "3.jpg", "25.02.08", "Эксплуатация беспилотных авиационных систем", "🛸")

    # Ряд 2
    col4, col5, col6 = st.columns(3)
    render_card(col4, "4.jpg", "09.02.07", "Информационные системы и программирование", "💻")
    render_card(col5, "5.jpg", "20.02.05", "Организация оперативного (экстренного) реагирования в ЧС", "📞")
    render_card(col6, "6.png", "09.02.13", "Интеграция решений с применением технологий ИИ", "🤖")

    # Ряд 3 (по центру)
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
                subject = urllib.parse.quote(f"Обратная связь: Формула безопасности ({name})")
                body = urllib.parse.quote(f"Имя/Группа: {name}\n\nСообщение:\n{message}")
                
                # ВПИШИ СВОЮ ПОЧТУ ЗДЕСЬ:
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
    st.set_page_config(page_title="Формула безопасности", page_icon="🛡️", layout="wide")
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