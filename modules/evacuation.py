"""Модуль 3. Эвакуация: время выхода людей через эвакуационные выходы."""
from __future__ import annotations

import numpy as np
import streamlit as st
import sympy as sp

from core import num, plots, ru, storage
from core.ai_explainer import explain_block

T_NORM = 6.0  # учебное нормативное время для общественных зданий, мин

_N, _q, _b, _n, _tn = sp.symbols("N q b n t_n", positive=True)
TIME_EXPR = _N / (_q * _b * _n)
MIN_WIDTH_EXPR = sp.solve(sp.Eq(TIME_EXPR, _tn), _b)[0]  # N / (n·q·t_n)


def calculate(people: int, width: float, capacity: float, exits: int) -> dict:
    if people <= 0:
        raise ValueError("число людей должно быть больше нуля.")
    if width <= 0 or capacity <= 0:
        raise ValueError("ширина выхода и пропускная способность должны быть больше нуля.")
    if exits < 1:
        raise ValueError("должен быть хотя бы один выход.")
    values = {_N: people, _q: capacity, _b: width, _n: exits, _tn: T_NORM}
    time_min = float(TIME_EXPR.subs(values))
    min_width = float(MIN_WIDTH_EXPR.subs(values))
    return {
        "time": time_min,
        "norm": T_NORM,
        "ok": time_min <= T_NORM,
        "min_width": min_width,
        "flow_total": capacity * width * exits,
    }


def render() -> None:
    st.header("🚪 Эвакуация: успеют ли люди выйти")
    st.markdown(
        "Упрощённая модель: все выходы работают одновременно, а поток людей через каждый "
        "пропорционален его ширине."
    )
    st.latex(r"t = \dfrac{N}{q\cdot b\cdot n}")

    c1, c2, c3, c4 = st.columns(4)
    people = c1.number_input("Число людей N", min_value=1, max_value=20000, value=300, step=10, key="evac_n")
    width = c2.number_input("Ширина одного выхода b, м", min_value=0.6, max_value=6.0, value=1.2, step=0.1, key="evac_b")
    capacity = c3.slider("Пропускная способность q, чел/(м·мин)", min_value=30, max_value=100, value=60, step=5, key="evac_q")
    exits = c4.number_input("Число выходов n", min_value=1, max_value=20, value=2, step=1, key="evac_exits")

    try:
        res = calculate(people, width, capacity, exits)
    except (ValueError, ArithmeticError, IndexError) as exc:
        st.error(f"Ошибка в исходных данных: {exc}")
        return

    m1, m2, m3 = st.columns(3)
    m1.metric("Расчётное время эвакуации", f"{ru(res['time'], 2)} мин")
    m2.metric("Нормативное время", f"{ru(res['norm'], 1)} мин")
    m3.metric("Через все выходы", f"{ru(res['flow_total'], 0)} чел/мин")

    if res["ok"]:
        st.success(
            f"Успевают: {ru(res['time'], 2)} мин ≤ {ru(res['norm'], 1)} мин. "
            f"Запас по времени — {ru(res['norm'] - res['time'], 2)} мин."
        )
    else:
        st.error(
            f"Не успевают: {ru(res['time'], 2)} мин > {ru(res['norm'], 1)} мин. "
            f"Чтобы уложиться в норматив, ширина каждого из {exits} выходов должна быть "
            f"не меньше {ru(res['min_width'], 2)} м (или нужно больше выходов)."
        )

        # --- НОВЫЙ БЛОК: Проверка по СП 1.13130.2020 ---
    st.markdown("---")
    st.subheader("📋 Проверка на соответствие СП 1.13130.2020")
    
    width_ok = True
    if people > 50 and width < 1.2:
        st.error(
            f"**Нарушение!** При эвакуации более 50 человек ширина выхода должна быть **не менее 1,2 м** (п. 4.2.19 СП 1.13130.2020). "
            f"У вас: {width} м."
        )
        width_ok = False
    elif width < 0.8:
        st.error(
            f"**Нарушение!** Минимальная ширина эвакуационного выхода — **0,8 м** (п. 4.2.19 СП 1.13130.2020). "
            f"У вас: {width} м."
        )
        width_ok = False
        
    if exits < 2 and people > 50:
        st.error(
            "**Нарушение!** Помещения с одновременным пребыванием более 50 человек должны иметь **не менее двух** эвакуационных выходов (п. 4.2.7 СП 1.13130.2020)."
        )
        width_ok = False

    if width_ok:
        st.success("✅ Ширина выходов и их количество соответствуют требованиям СП 1.13130.2020.")

    with st.expander("🧮 Пошаговый расчёт", expanded=True):
        st.markdown("**Шаг 1.** Подставляем данные:")
        st.latex(
            rf"t = \dfrac{{N}}{{q\cdot b\cdot n}} = \dfrac{{{people}}}{{{capacity}\cdot {num(width, 2)}\cdot {exits}}} "
            rf"\approx {num(res['time'], 2)}\ \text{{мин}}"
        )
        st.markdown("**Шаг 2.** Сравниваем с нормативом и находим минимальную ширину выхода:")
        st.latex(
            rf"b_{{\min}} = \dfrac{{N}}{{q\cdot n\cdot t_{{\text{{норм}}}}}} = "
            rf"\dfrac{{{people}}}{{{capacity}\cdot {exits}\cdot {num(res['norm'], 1)}}} "
            rf"\approx {num(res['min_width'], 2)}\ \text{{м}}"
        )
        st.caption(
            "Норматив 6 минут — учебное значение для общественных зданий. В реальных расчётах учитывают "
            "также время начала эвакуации, длину путей, плотность и скорость людского потока."
        )

    widths = np.linspace(0.6, 6.0, 200)
    times = people / (capacity * widths * exits)
    plots.show_chart(plots.evacuation_curve(widths, times, width, res["time"], res["norm"]))
    st.caption("Кривая — гипербола: время обратно пропорционально ширине. Узкие выходы «стоят» особенно дорого.")

    prompt = (
        "Тема: эвакуация людей из здания, формула t = N / (q·b·n).\n"
        f"Данные: {people} человек, {exits} вых. шириной {width:g} м, пропускная способность {capacity} чел/(м·мин).\n"
        f"Результат: время эвакуации {res['time']:.2f} мин при нормативе {res['norm']:g} мин "
        f"({'успевают' if res['ok'] else 'не успевают'}).\n"
        "Объясни курсанту смысл формулы и что будет, если один из выходов окажется закрыт."
    )
    explain_block(prompt, key="evac")

    with st.expander("🚒 Как это в реальной работе", expanded=True):
        st.markdown(
            "- **Проверки объектов.** Инспектор обращает внимание на запертые и загромождённые выходы: "
            "из двух выходов остался один — время эвакуации удвоилось.\n"
            "- **Массовые мероприятия.** Перед концертом или линейкой оценивают, хватит ли выходов "
            "на фактическое число людей, а не на «обычную» загрузку зала.\n"
            "- **Учебные эвакуации.** Фактическое время на тренировке сравнивают с расчётным — "
            "расхождение показывает, где возникают заторы."
        )

    storage.save_calc_button(
        "Эвакуация",
        {"N": people, "b, м": width, "q": capacity, "n": exits},
        {"t, мин": round(res["time"], 2), "успевают": "да" if res["ok"] else "нет"},
        key="evac",
    )