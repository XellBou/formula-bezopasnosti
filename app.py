"""«Формула безопасности» — точка входа Streamlit-приложения."""
from __future__ import annotations

import pandas as pd
import streamlit as st

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

    tab1, tab2, tab3, tab4 = st.tabs([
        "🚪 Эвакуация и спасение", 
        "📜 Пожарная безопасность", 
        "🧯 Техника и вооружение", 
        "📊 Справочные данные"
    ])

    # --- ВКЛАДКА 1: ЭВАКУАЦИЯ ---
    with tab1:
        st.subheader("СП 1.13130.2020 «Эвакуационные пути и выходы»")
        st.info("**Главный документ для модуля «Эвакуация».** Устанавливает требования к геометрии путей эвакуации и количеству выходов.")
        
        with st.expander("Показать ключевые требования", expanded=True):
            st.markdown(
                """
                *   **Ширина выхода:** не менее **0,8 м** (в общем случае).
                *   **Ширина выхода (при >50 чел.):** не менее **1,2 м**.
                *   **Высота в свету:** не менее **1,9 м**.
                *   **Количество выходов:** не менее **двух** для помещений с одновременным пребыванием более **50 человек**.
                *   **Ширина коридора:** не менее **1,2 м** (при эвакуации более 50 чел.).
                *   **Направление открытия дверей:** как правило, по направлению выхода из здания (кроме отдельных случаев).
                """
            )
        
        st.subheader("ГОСТ 12.1.004-91 «Пожарная безопасность. Общие требования»")
        st.warning("**Связь с модулем «Риск ЧС».** В ГОСТе описан методологический подход к расчету вероятности возникновения пожара и вероятности эвакуации людей.")
        with st.expander("Показать формулы вероятности эвакуации"):
            st.markdown(
                """
                Вероятность эвакуации людей по наружным лестницам принимается равной:
                *   **0,05** — в жилых зданиях.
                *   **0,03** — в остальных зданиях при наличии таких путей.
                
                *В тренажёре используется упрощённая статистическая модель, но она опирается на логику данного стандарта.*
                """
            )

    # --- ВКЛАДКА 2: ПОЖАРНАЯ БЕЗОПАСНОСТЬ ---
    with tab2:
        st.subheader("Федеральный закон № 123-ФЗ «Технический регламент о требованиях пожарной безопасности»")
        st.info("**Базовый закон.** Устанавливает классификацию пожаров и опасные факторы.")
        
        with st.expander("Классификация пожаров по виду горючего материала (Статья 8)", expanded=True):
            st.markdown(
                """
                *   **Класс A** — горение твердых веществ (дерево, бумага, текстиль).
                *   **Класс B** — горение горючих жидкостей или плавящихся твердых веществ (бензин, масла, парафин).
                *   **Класс C** — горение газов (пропан, метан, водород).
                *   **Класс D** — горение металлов (магний, натрий, алюминий).
                *   **Класс E** — горение электроустановок под напряжением.
                *   **Класс F** — горение ядерных материалов и радиоактивных отходов.
                """
            )
        
        with st.expander("Опасные факторы пожара (Статья 9)"):
            st.markdown(
                """
                1.  Пламя и искры.
                2.  Тепловой поток.
                3.  Повышенная температура окружающей среды.
                4.  Повышенная концентрация токсичных продуктов горения.
                5.  Пониженная концентрация кислорода.
                6.  Снижение видимости в дыму.
                """
            )

        st.subheader("СП 484.1311500.2020 «Системы пожарной сигнализации»")
        st.markdown(
            "Устанавливает нормы проектирования автоматических систем пожарной сигнализации (АПС). "
            "Определяет типы извещателей (дымовые, тепловые, пламени), расстояния между ними и алгоритмы срабатывания."
        )

    # --- ВКЛАДКА 3: ТЕХНИКА И ВООРУЖЕНИЕ ---
    with tab3:
        st.subheader("СИЗОД (Средства индивидуальной защиты органов дыхания)")
        st.info("**База для газодымозащитной службы (ГДЗС).**")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(
                """
                **Дыхательные аппараты со сжатым воздухом (ДАСВ):**
                *   Условное время защитного действия: **не менее 60 минут**.
                *   Рабочий диапазон температур: от **-40°C** до **+60°C**.
                *   Применяются повсеместно.
                """
            )
        with col2:
            st.markdown(
                """
                **Дыхательные аппараты со сжатым кислородом (ДАСК):**
                *   Время защитного действия: **не менее 4 часов** (240 минут).
                *   Применяются при длительных работах в подвалах, метро, высотных зданиях.
                """
            )

        st.subheader("Пожарно-техническое вооружение (ПТВ)")
        with st.expander("Пожарные стволы"):
            st.markdown(
                """
                *   **Ручные стволы:** РСК-50 (расход ~3,5 л/с), РС-70 (расход ~7,4 л/с).
                *   **Лафетные стволы:** Применяются для подачи больших объемов воды (более 20 л/с) на дальние расстояния.
                *   **Комбинированные стволы:** Позволяют регулировать подачу воды или пены.
                """
            )
        with st.expander("Пожарные краны (ПК)"):
            st.markdown(
                """
                *   **ПК-м (малорасходные):** расход от **0,2 до 1,5 л/с**.
                *   **ПК-с (среднерасходные):** расход **более 1,5 л/с**.
                *   Диаметр трубопровода: DN 50 (расход до 4 л/с) или DN 65 (большая производительность).
                """
            )

    # --- ВКЛАДКА 4: СПРАВОЧНЫЕ ДАННЫЕ ---
    with tab4:
        st.subheader("Нормативы пожарно-строевой подготовки")
        st.markdown("Время выполнения упражнений оценивается по трехбалльной системе.")
        
        with st.expander("Надевание боевой одежды и снаряжения (БОП)", expanded=True):
            st.markdown(
                """
                *   **Отлично:** 21 секунда.
                *   **Хорошо:** 24 секунды.
                *   **Удовлетворительно:** 27 секунд.
                *   **Норматив для караула:** выезд и сбор в полном составе — до 90 секунд.
                """
            )
        
        st.subheader("Практические правила для расчетов (Справочник РТП)")
        st.success(
            """
            **Правило гидравлики:**
            *   Каждые **10 метров** подъёма воды по вертикали «съедают» **1 атмосферу** давления.
            *   На каждые **100 метров** рукавной линии потери напора также составляют около **1 атмосферы**.
            *   Рабочее давление на стволе РСК-50 должно быть не менее **3 атм** (для компактной струи).
            """
        )
        
        st.latex(r"H_{\text{насоса}} = H_{\text{ствола}} + n \cdot S_{\text{рукава}} \cdot Q^2 \pm z \pm h_{\text{подъёма}}")
        st.caption("Тактико-техническая формула для расчета требуемого напора на насосе.")

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