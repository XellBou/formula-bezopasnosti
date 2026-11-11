"""Модуль 5. Риск ЧС: вероятность, надёжность и статистика по Республике Татарстан."""
from __future__ import annotations

import numpy as np
import streamlit as st
import sympy as sp
from scipy.stats import binomtest, expon
import plotly.graph_objects as go
import pandas as pd

from core import num, plots, ru, storage
from core.ai_explainer import explain_block

LOW_RISK = 0.05
HIGH_RISK = 0.20

_lam, _t = sp.symbols("lambda t", positive=True)
RELIABILITY_EXPR = sp.exp(-_lam * _t)
MEDIAN_EXPR = sp.log(2) / _lam


def probability(events: int, observations: int) -> dict:
    events, observations = int(events), int(observations)
    if observations < 1:
        raise ValueError("Число наблюдений должно быть не меньше 1.")
    if events < 0:
        raise ValueError("Число событий не может быть отрицательным.")
    if events > observations:
        raise ValueError("Число событий m не может быть больше числа наблюдений n.")
    p = events / observations
    fraction = sp.Rational(events, observations)
    interval = binomtest(events, observations).proportion_ci(confidence_level=0.95, method="wilson")
    if p < LOW_RISK:
        level = "low"
    elif p < HIGH_RISK:
        level = "medium"
    else:
        level = "high"
    return {
        "p": p,
        "frac_num": int(fraction.p),
        "frac_den": int(fraction.q),
        "ci_low": float(interval.low),
        "ci_high": float(interval.high),
        "level": level,
    }


def reliability(rate: float, time_h: float) -> dict:
    if rate <= 0:
        raise ValueError("Интенсивность отказов λ должна быть больше нуля.")
    if time_h <= 0:
        raise ValueError("Время работы должно быть больше нуля.")
    p = float(RELIABILITY_EXPR.subs({_lam: rate, _t: time_h}))
    return {
        "p": p,
        "p_check": float(expon.sf(time_h, scale=1.0 / rate)),
        "mtbf": 1.0 / rate,
        "median": float(MEDIAN_EXPR.subs({_lam: rate})),
    }


def _render_probability() -> None:
    st.latex(r"P = \dfrac{m}{n}")
    c1, c2 = st.columns(2)
    events = c1.number_input("Число ЧС (событий) m", min_value=0, max_value=1_000_000, value=18, step=1, key="risk_m")
    observations = c2.number_input("Число наблюдений n", min_value=1, max_value=1_000_000, value=400, step=1, key="risk_n")

    try:
        res = probability(events, observations)
    except (ValueError, ArithmeticError) as exc:
        st.error(f"Ошибка в исходных данных: {exc}")
        return

    left, right = st.columns([1, 1])
    with left:
        st.metric("Вероятность события P", f"{ru(res['p'], 4)}  ({ru(res['p'] * 100, 2)} %)")
        if res["level"] == "low":
            st.success("Низкий риск (P < 0,05): событие редкое, но готовность всё равно нужна.")
        elif res["level"] == "medium":
            st.warning("Средний риск (0,05 ≤ P < 0,20): событие регулярно повторяется — нужны плановые меры.")
        else:
            st.error("Высокий риск (P ≥ 0,20): событие происходит часто — нужны усиленные меры и резервы.")

        if events > 0 and res["frac_den"] != observations:
            middle = rf" = \dfrac{{{res['frac_num']}}}{{{res['frac_den']}}}"
        else:
            middle = ""
        st.latex(
            rf"P = \dfrac{{m}}{{n}} = \dfrac{{{events}}}{{{observations}}}{middle} \approx {num(res['p'], 4)}"
        )
        st.caption(
            f"95 %-й доверительный интервал (метод Уилсона): от {ru(res['ci_low'], 4)} до {ru(res['ci_high'], 4)}. "
            "Чем меньше наблюдений, тем шире интервал и тем осторожнее нужно относиться к оценке."
        )
    with right:
        plots.show_chart(plots.risk_gauge(res["p"], LOW_RISK, HIGH_RISK))

    prompt = (
        "Тема: статистическая вероятность события P = m / n.\n"
        f"Данные: {events} событий за {observations} наблюдений. Результат: P = {res['p']:.4f}.\n"
        "Объясни курсанту, что означает это число и как его используют при планировании работы подразделения."
    )
    explain_block(prompt, key="risk_prob")

    storage.save_calc_button(
        "Риск ЧС: вероятность",
        {"m": events, "n": observations},
        {"P": round(res["p"], 4), "уровень": res["level"]},
        key="risk_prob",
    )


def _render_reliability() -> None:
    st.latex(r"P(t) = e^{-\lambda t}")
    c1, c2 = st.columns(2)
    rate = c1.number_input(
        "Интенсивность отказов λ, 1/ч", min_value=0.0001, max_value=1.0, value=0.001, step=0.0001, format="%.4f", key="risk_lam"
    )
    t_max = c2.number_input("Время работы t_max, ч", min_value=1.0, max_value=100000.0, value=1000.0, step=50.0, key="risk_t")

    try:
        res = reliability(rate, t_max)
    except (ValueError, ArithmeticError) as exc:
        st.error(f"Ошибка в исходных данных: {exc}")
        return

    m1, m2, m3 = st.columns(3)
    m1.metric(f"P({ru(t_max, 0)} ч)", ru(res["p"], 3))
    m2.metric("Средняя наработка 1/λ", f"{ru(res['mtbf'], 0)} ч")
    m3.metric("Медианная наработка ln2/λ", f"{ru(res['median'], 0)} ч")

    if res["p"] >= 0.9:
        st.success("Высокая надёжность на этом интервале: вероятность безотказной работы не ниже 0,9.")
    elif res["p"] >= 0.7:
        st.warning("Надёжность приемлемая, но отказ вполне возможен: предусмотрите резерв и обслуживание.")
    else:
        st.error("Надёжность низкая: без обслуживания и резерва рассчитывать на технику нельзя.")

    with st.expander("🧮 Пошаговый расчёт", expanded=True):
        lam_s, t_s = num(rate, 4), num(t_max, 1)
        st.latex(
            rf"P({t_s}) = e^{{-\lambda t}} = e^{{-{lam_s}\cdot {t_s}}} = e^{{-{num(rate * t_max, 3)}}} "
            rf"\approx {num(res['p'], 3)}"
        )
        st.latex(rf"T_{{\text{{ср}}}} = \dfrac{{1}}{{\lambda}} = \dfrac{{1}}{{{lam_s}}} \approx {num(res['mtbf'], 0)}\ \text{{ч}}")
        st.latex(
            rf"P(T_{{0{{,}}5}}) = 0{{,}}5 \;\Rightarrow\; T_{{0{{,}}5}} = \dfrac{{\ln 2}}{{\lambda}} "
            rf"\approx {num(res['median'], 0)}\ \text{{ч}}"
        )
        st.caption(
            f"Проверка через распределение scipy.stats.expon: P = {ru(res['p_check'], 3)}. "
            "К моменту средней наработки 1/λ исправными остаются лишь ≈ 37 % образцов."
        )

    times = np.linspace(0.0, t_max, 300)
    probs = np.exp(-rate * times)
    plots.show_chart(plots.reliability_curve(times, probs, t_max, res["p"], res["mtbf"], res["median"]))

    prompt = (
        "Тема: надёжность техники, показательный закон P(t) = e^(−λt).\n"
        f"Данные: λ = {rate:g} 1/ч, время работы {t_max:g} ч.\n"
        f"Результат: P = {res['p']:.3f}, средняя наработка {res['mtbf']:.0f} ч, медианная {res['median']:.0f} ч.\n"
        "Объясни курсанту, что означают эти величины и зачем технике нужны обслуживание и резерв."
    )
    explain_block(prompt, key="risk_rel")

    storage.save_calc_button(
        "Риск ЧС: надёжность",
        {"λ, 1/ч": rate, "t, ч": t_max},
        {"P": round(res["p"], 4), "1/λ, ч": round(res["mtbf"], 1), "ln2/λ, ч": round(res["median"], 1)},
        key="risk_rel",
    )


def _render_tatarstan_stats() -> None:
    st.subheader("📍 Оперативная обстановка в Республике Татарстан (2025 г.)")
    st.markdown("Данные основаны на отчетах ГУ МЧС России по Республике Татарстан.")
    
    # Ключевые метрики
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Всего пожаров", "3 758", "-10.9%")
    c2.metric("Погибло людей", "128", "+13 чел.")
    c3.metric("Травмировано", "177", "-12%")
    c4.metric("Погибло детей", "6", "в 2 раза")
    
    st.markdown("---")
    
    # --- ИНТЕРАКТИВНАЯ КАРТА РИСКОВ ---
    st.markdown("### 🗺️ Карта рисков: полная статистика по районам")
    st.markdown(
        "Выберите район из списка, чтобы увидеть детали. Районы, где зафиксирован рост гибели людей, "
        "выделены в таблице цветом."
    )

    # Полный список районов (43 района + 2 города)
    risk_data = {
        # --- РАЙОНЫ С РОСТОМ ГИБЕЛИ ---
        "Азнакаевский": {"status": "Рост", "delta": "+3 чел.", "details": "Рост гибели людей на пожарах."},
        "Альметьевский": {"status": "Рост", "delta": "с 3 до 6 чел.", "details": "Число погибших увеличилось вдвое."},
        "Бавлинский": {"status": "Рост", "delta": "есть случаи", "details": "Зафиксирован рост гибели людей."},
        "Верхнеуслонский": {"status": "Рост", "delta": "есть случаи", "details": "Зафиксирован рост гибели людей."},
        "Высокогорский": {"status": "Рост + дети", "delta": "есть случаи", "details": "Рост гибели, в т.ч. 2 детей."},
        "Дрожжановский": {"status": "Рост", "delta": "есть случаи", "details": "Зафиксирован рост гибели людей."},
        "Елабужский": {"status": "Рост", "delta": "есть случаи", "details": "Зафиксирован рост гибели людей."},
        "Кукморский": {"status": "Рост", "delta": "есть случаи", "details": "Зафиксирован рост гибели людей."},
        "Лаишевский": {"status": "Рост", "delta": "есть случаи", "details": "Зафиксирован рост гибели людей."},
        "Мензелинский": {"status": "Рост", "delta": "есть случаи", "details": "Зафиксирован рост гибели людей."},
        "Муслюмовский": {"status": "Рост", "delta": "есть случаи", "details": "Зафиксирован рост гибели людей."},
        "Нижнекамский": {"status": "Рост", "delta": "есть случаи", "details": "Рост гибели людей, много пожаров сухой травы."},
        "Новошешминский": {"status": "Рост", "delta": "есть случаи", "details": "Зафиксирован рост гибели людей."},
        "Пестречинский": {"status": "Рост", "delta": "есть случаи", "details": "Зафиксирован рост гибели людей."},
        "Спасский": {"status": "Рост", "delta": "есть случаи", "details": "Зафиксирован рост гибели людей."},
        "Тетюшский": {"status": "Рост", "delta": "есть случаи", "details": "Зафиксирован рост гибели людей."},
        "Тукаевский": {"status": "Рост", "delta": "есть случаи", "details": "Рост гибели людей, много пожаров сухой травы."},
        "Казань": {"status": "Рост + дети", "delta": "есть случаи", "details": "Рост гибели, в т.ч. 1 ребенок."},
        "Набережные Челны": {"status": "Рост", "delta": "есть случаи", "details": "Зафиксирован рост гибели людей."},
        
        # --- РАЙОНЫ С ГИБЕЛЬЮ ДЕТЕЙ ---
        "Зеленодольский": {"status": "Дети", "delta": "погиб ребенок", "details": "Трагедия с гибелью ребенка."},
        "Бугульминский": {"status": "Дети", "delta": "погиб ребенок", "details": "Трагедия с гибелью ребенка."},
        "Чистопольский": {"status": "Дети", "delta": "погибли 2 детей", "details": "Трагедия с гибелью 2 детей."},

        # --- СТАБИЛЬНЫЕ РАЙОНЫ ---
        "Агрызский": {"status": "Стабильно", "delta": "—", "details": "Роста гибели людей не зафиксировано."},
        "Аксубаевский": {"status": "Стабильно", "delta": "—", "details": "Роста гибели людей не зафиксировано."},
        "Актанышский": {"status": "Стабильно", "delta": "—", "details": "Роста гибели людей не зафиксировано."},
        "Алексеевский": {"status": "Стабильно", "delta": "—", "details": "Роста гибели людей не зафиксировано."},
        "Алькеевский": {"status": "Стабильно", "delta": "—", "details": "Роста гибели людей не зафиксировано."},
        "Апастовский": {"status": "Стабильно", "delta": "—", "details": "Роста гибели людей не зафиксировано."},
        "Арский": {"status": "Стабильно", "delta": "—", "details": "Роста гибели людей не зафиксировано."},
        "Атнинский": {"status": "Стабильно", "delta": "—", "details": "Роста гибели людей не зафиксировано."},
        "Балтасинский": {"status": "Стабильно", "delta": "—", "details": "Роста гибели людей не зафиксировано."},
        "Буинский": {"status": "Стабильно", "delta": "—", "details": "Роста гибели людей не зафиксировано."},
        "Заинский": {"status": "Стабильно", "delta": "—", "details": "Роста гибели людей не зафиксировано."},
        "Кайбицкий": {"status": "Стабильно", "delta": "—", "details": "Роста гибели людей не зафиксировано."},
        "Камско-Устьинский": {"status": "Стабильно", "delta": "—", "details": "Погибших на пожарах не зафиксировано (17 пожаров за год)."},
        "Лениногорский": {"status": "Стабильно", "delta": "—", "details": "Роста гибели людей не зафиксировано."},
        "Мамадышский": {"status": "Стабильно", "delta": "—", "details": "Роста гибели людей не зафиксировано."},
        "Менделеевский": {"status": "Стабильно", "delta": "—", "details": "Роста гибели людей не зафиксировано."},
        "Нурлатский": {"status": "Стабильно", "delta": "—", "details": "Роста гибели людей не зафиксировано."},
        "Рыбно-Слободский": {"status": "Стабильно", "delta": "—", "details": "Роста гибели людей не зафиксировано."},
        "Сабинский": {"status": "Стабильно", "delta": "—", "details": "Роста гибели людей не зафиксировано."},
        "Сармановский": {"status": "Стабильно", "delta": "—", "details": "Роста гибели людей не зафиксировано."},
        "Тюлячинский": {"status": "Стабильно", "delta": "—", "details": "Роста гибели людей не зафиксировано."},
        "Черемшанский": {"status": "Стабильно", "delta": "—", "details": "Роста гибели людей не зафиксировано."},
        "Ютазинский": {"status": "Стабильно", "delta": "—", "details": "Роста гибели людей не зафиксировано."},
    }

    # Преобразуем в DataFrame
    df_risk = pd.DataFrame([
        {"Район": k, "Статус": v["status"], "Динамика": v["delta"], "Детали": v["details"]}
        for k, v in risk_data.items()
    ])

    # Сортируем: сначала проблемные (Рост, Дети), потом Стабильно, внутри по алфавиту
    status_order = {"Дети": 1, "Рост + дети": 2, "Рост": 3, "Стабильно": 4}
    df_risk["sort_key"] = df_risk["Статус"].map(status_order)
    df_risk = df_risk.sort_values(by=["sort_key", "Район"]).drop(columns=["sort_key"]).reset_index(drop=True)

    # Выбор района для детального просмотра
    selected_district = st.selectbox("Выберите район для подробностей:", df_risk["Район"].tolist())
    info = risk_data[selected_district]

    col_info1, col_info2 = st.columns([1, 2])
    with col_info1:
        st.metric("Статус", info["status"])
        st.metric("Динамика", info["delta"])
    with col_info2:
        st.info(f"**{selected_district} район:** {info['details']}")
        if "дети" in info["status"].lower() or "дети" in info["details"].lower():
            st.error("⚠️ В районе зафиксирована гибель детей. Требуется усиленная профилактика с семьями.")
        elif info["status"] == "Рост":
            st.warning("⚠️ Рост гибели людей. Рекомендуется усилить профилактические рейды и проверку извещателей.")
        else:
            st.success("✅ Роста гибели людей не зафиксировано. Обстановка стабильная.")

    st.markdown("---")

    # --- ДЕТАЛЬНАЯ ТАБЛИЦА ПО РАЙОНАМ ---
    st.markdown("### 📊 Детальная таблица по районам")
    st.markdown("Проблемные районы (с ростом гибели и гибелью детей) находятся вверху списка.")

    def color_status(val):
        if "Дети" in val or "дети" in val:
            return "background-color: #FADBD8; color: #7B241C;"
        elif "Рост" in val:
            return "background-color: #FDEBD0; color: #7E5109;"
        return ""

    styled_df = df_risk.style.apply(lambda x: [color_status(v) for v in x], subset=["Статус"])
    st.dataframe(styled_df, use_container_width=True, hide_index=True)

    st.caption(
        "**Источник данных:** ГУ МЧС России по Республике Татарстан, итоги 2025 года. "
        "Представлены данные по 43 районам и 2 городским округам."
    )

    # --- КРУГОВАЯ ДИАГРАММА ПРИЧИН ---
    st.markdown("---")
    col_pie, col_water = st.columns([1, 1])
    with col_pie:
        st.markdown("### 🔥 Основные причины пожаров")
        labels = ['Неосторожное обращение с огнем', 'Электрооборудование', 'Печи', 'Прочее']
        values = [1712, 1185, 506, 355]
        fig = go.Figure(data=[go.Pie(
            labels=labels, values=values, hole=.4,
            marker_colors=['#F26A1B', '#0B2545', '#5A6A85', '#D5DCE8']
        )])
        fig.update_layout(margin=dict(t=20, b=20, l=0, r=0), height=350, showlegend=False)
        st.plotly_chart(fig, use_container_width="stretch")
        st.info(
            "**Главная причина — человек.** 45.6% пожаров происходят из-за неосторожного обращения с огнем. "
            "Профилактические беседы с населением — ключевая мера."
        )

    with col_water:
        st.markdown("### 🌊 Происшествия на водных объектах")
        st.warning(
            "За 2025 год на водных объектах РТ произошло **95** происшествий. "
            "Погибли **82** человека (в т.ч. 4 детей). Спасено 49 человек."
        )
        st.markdown("---")
        st.markdown("### 🏠 Профилактика (автономные извещатели)")
        st.success(
            "С 2016 года в Республике Татарстан установлено более **272 тыс.** автономных пожарных извещателей "
            "в **97 тыс.** домовладениях. Это позволило спасти жизнь **319** жителям, в том числе **104** детям."
        )

    # --- ЗАДАЧА ДЛЯ КУРСАНТОВ ---
    st.markdown("---")
    st.markdown("### 📝 Задача для курсантов (на основе реальных данных)")
    st.markdown(
        "По данным ГУ МЧС по РТ, в 2025 году **31,5%** пожаров произошли из-за нарушения правил эксплуатации "
        "электрооборудования. Всего произошло **3 758** пожаров. **Сколько пожаров возникло по этой причине?**"
    )
    with st.expander("Показать решение"):
        st.markdown(
            "1. Переведем проценты в доли: 31,5% = 0,315.\n"
            "2. Умножим общее количество на долю: 3758 × 0,315.\n"
            "3. Получаем: **1 183,77** (то есть примерно **1 184** пожара).\n\n"
            "*Проверка: в официальном отчете указано 1 185 пожаров. Разница в 1 пожар объясняется округлением.*"
        )


def render() -> None:
    st.header("⚠️ Риск ЧС: вероятность, надёжность и статистика")
    st.markdown(
        "Риск нельзя устранить полностью, но его можно **измерить**. Вероятность показывает, как часто "
        "случается событие, а закон надёжности — как долго можно рассчитывать на технику."
    )
    
    tab_prob, tab_rel, tab_rt = st.tabs([
        "Вероятность события", 
        "Надёжность техники",
        "📍 Статистика РТ"
    ])
    
    with tab_prob:
        _render_probability()
    with tab_rel:
        _render_reliability()
    with tab_rt:
        _render_tatarstan_stats()

    with st.expander("🚒 Как это в реальной работе", expanded=True):
        st.markdown(
            "- **Планирование сил и средств.** Статистика выездов по районам и сезонам показывает, "
            "где и когда вероятность ЧС выше — туда направляют профилактику и дополнительные наряды.\n"
            "- **Техническое обслуживание.** Мотопомпы, гидравлический инструмент, дыхательные аппараты "
            "обслуживают по регламенту именно потому, что надёжность падает со временем.\n"
            "- **Резервирование.** Если один насос работает безотказно с вероятностью 0,9, то хотя бы один "
            "из двух независимых — с вероятностью 1 − 0,1² = 0,99. Поэтому на ответственных участках ставят резерв."
        )