"""Модуль 5. Риск ЧС: статистическая вероятность и надёжность техники."""
from __future__ import annotations

import numpy as np
import streamlit as st
import sympy as sp
from scipy.stats import binomtest, expon

from core import num, plots, ru, storage
from core.ai_explainer import explain_block

LOW_RISK = 0.05  # ниже — низкий риск
HIGH_RISK = 0.20  # выше или равно — высокий риск

_lam, _t = sp.symbols("lambda t", positive=True)
RELIABILITY_EXPR = sp.exp(-_lam * _t)
MEDIAN_EXPR = sp.log(2) / _lam


def probability(events: int, observations: int) -> dict:
    events, observations = int(events), int(observations)
    if observations < 1:
        raise ValueError("число наблюдений должно быть не меньше 1.")
    if events < 0:
        raise ValueError("число событий не может быть отрицательным.")
    if events > observations:
        raise ValueError("число событий m не может быть больше числа наблюдений n.")
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
        raise ValueError("интенсивность отказов λ должна быть больше нуля.")
    if time_h <= 0:
        raise ValueError("время работы должно быть больше нуля.")
    p = float(RELIABILITY_EXPR.subs({_lam: rate, _t: time_h}))
    return {
        "p": p,
        "p_check": float(expon.sf(time_h, scale=1.0 / rate)),  # независимая проверка через SciPy
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
            f"95 %-й доверительный интервал (метод Уилсона, SciPy): от {ru(res['ci_low'], 4)} до {ru(res['ci_high'], 4)}. "
            "Чем меньше наблюдений, тем шире интервал и тем осторожнее нужно относиться к оценке. "
            "Границы уровней риска (0,05 и 0,20) — учебные."
        )
    with right:
        plots.show_chart(plots.risk_gauge(res["p"], LOW_RISK, HIGH_RISK))

    prompt = (
        "Тема: статистическая вероятность события P = m / n.\n"
        f"Данные: {events} событий за {observations} наблюдений. Результат: P = {res['p']:.4f}.\n"
        "Объясни курсанту, что означает это число и как его используют при планировании работы подразделения."
    )
    explain_block(prompt, key="risk_prob")

        # --- НОВЫЙ БЛОК: Учебная карта рисков ---
    st.markdown("---")
    st.subheader("🗺️ Учебная карта рисков (демонстрация)")
    st.markdown("Выберите район, чтобы увидеть статистику выездов за год (данные вымышленные, для примера).")
    
    district = st.selectbox("Выберите район:", ["Центральный", "Северный", "Промышленный", "Зарёчный"])
    # Вымышленная статистика
    stats = {
        "Центральный": {"m": 45, "n": 365, "risk": "Средний"},
        "Северный": {"m": 12, "n": 365, "risk": "Низкий"},
        "Промышленный": {"m": 88, "n": 365, "risk": "Высокий"},
        "Зарёчный": {"m": 25, "n": 365, "risk": "Средний"},
    }
    data = stats[district]
    p = data["m"] / data["n"]
    
    col1, col2 = st.columns(2)
    col1.metric(f"Вероятность ЧС в {district} районе", f"{p:.4f}")
    col2.metric("Оценка уровня риска", data["risk"])
    
    if data["risk"] == "Высокий":
        st.warning("⚠️ В этом районе требуется усиленное профилактическое патрулирование.")
    else:
        st.info("ℹ️ Уровень риска в пределах нормы. Плановые мероприятия достаточны.")

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
        st.error("Надёжность низкая: без обслуживания и резерва рассчитывать на технику на таком интервале нельзя.")

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
            "Обратите внимание: к моменту средней наработки 1/λ исправными остаются лишь ≈ 37 % образцов."
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


def render() -> None:
    st.header("⚠️ Риск ЧС: вероятность и надёжность")
    st.markdown(
        "Риск нельзя устранить полностью, но его можно **измерить**. Вероятность показывает, как часто "
        "случается событие, а закон надёжности — как долго можно рассчитывать на технику."
    )
    tab_prob, tab_rel = st.tabs(["Вероятность события", "Надёжность техники"])
    with tab_prob:
        _render_probability()
    with tab_rel:
        _render_reliability()

    with st.expander("🚒 Как это в реальной работе", expanded=True):
        st.markdown(
            "- **Планирование сил и средств.** Статистика выездов по районам и сезонам показывает, "
            "где и когда вероятность ЧС выше — туда направляют профилактику и дополнительные наряды.\n"
            "- **Техническое обслуживание.** Мотопомпы, гидравлический инструмент, дыхательные аппараты "
            "обслуживают по регламенту именно потому, что надёжность падает со временем.\n"
            "- **Резервирование.** Если один насос работает безотказно с вероятностью 0,9, то хотя бы один "
            "из двух независимых — с вероятностью 1 − 0,1² = 0,99. Поэтому на ответственных участках ставят резерв."
        )