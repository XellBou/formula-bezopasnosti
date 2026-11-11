"""Модуль 3. Эвакуация: время выхода и блокировка путей (ОФП)."""
from __future__ import annotations

import numpy as np
import streamlit as st
import sympy as sp

from core import num, plots, ru, storage
from core.ai_explainer import explain_block

T_NORM = 6.0

_N, _q, _b, _n, _tn = sp.symbols("N q b n t_n", positive=True)
TIME_EXPR = _N / (_q * _b * _n)
MIN_WIDTH_EXPR = sp.solve(sp.Eq(TIME_EXPR, _tn), _b)[0]

def calculate(people: int, width: float, capacity: float, exits: int, room_vol: float, smoke_rate: float) -> dict:
    if people <= 0 or width <= 0 or capacity <= 0 or exits < 1:
        raise ValueError("Проверьте корректность ввода людей, ширины и выходов.")
    
    values = {_N: people, _q: capacity, _b: width, _n: exits, _tn: T_NORM}
    time_min = float(TIME_EXPR.subs(values))
    min_width = float(MIN_WIDTH_EXPR.subs(values))
    
    # Время блокировки путей (упрощенно: V_помещения / (S_проема * V_дыма))
    # Допустим, дым заполняет помещение со скоростью 10 м/мин, площадь двери = 2 кв.м
    time_block = room_vol / (2.0 * smoke_rate)
    
    return {
        "time": time_min,
        "norm": T_NORM,
        "ok": time_min <= T_NORM,
        "min_width": min_width,
        "flow_total": capacity * width * exits,
        "time_block": time_block,
        "survive": time_min < time_block,
    }

def render() -> None:
    st.header("🚪 Эвакуация и опасные факторы пожара (ОФП)")
    st.markdown(
        "Расчёт времени эвакуации и сравнение его с временем блокировки путей эвакуации дымом. "
        "Если люди не успевают выйти до заполнения коридора дымом — это смертельно опасно."
    )
    st.latex(r"t = \dfrac{N}{q\cdot b\cdot n} \quad \text{и} \quad t_{ОФП} = \frac{V}{S \cdot v_{дыма}}")

    c1, c2, c3, c4 = st.columns(4)
    people = c1.number_input("Число людей N", min_value=1, max_value=20000, value=300, step=10, key="evac_n")
    width = c2.number_input("Ширина одного выхода b, м", min_value=0.6, max_value=6.0, value=1.2, step=0.1, key="evac_b")
    capacity = c3.number_input("Пропускная способность q, чел/(м·мин)", min_value=30, max_value=100, value=60, step=5, key="evac_q")
    exits = c4.number_input("Число выходов n", min_value=1, max_value=20, value=2, step=1, key="evac_exits")

    st.markdown("**Параметры помещения (для расчёта ОФП):**")
    c5, c6 = st.columns(2)
    room_vol = c5.number_input("Объём помещения V, м³", min_value=50, max_value=10000, value=500, step=50, key="evac_vol")
    smoke_rate = c6.number_input("Скорость распространения дыма, м/мин", min_value=5, max_value=20, value=10, step=1, key="evac_smoke")

    try:
        res = calculate(people, width, capacity, exits, room_vol, smoke_rate)
    except (ValueError, ArithmeticError) as exc:
        st.error(f"Ошибка: {exc}")
        return

    m1, m2, m3 = st.columns(3)
    m1.metric("Время эвакуации", f"{ru(res['time'], 2)} мин")
    m2.metric("Время блокировки (ОФП)", f"{ru(res['time_block'], 1)} мин")
    m3.metric("Успевают выйти?", "ДА" if res['survive'] else "НЕТ")

    if res["survive"] and res["ok"]:
        st.success(f"✅ Люди успевают выйти! Эвакуация {ru(res['time'], 1)} мин укладывается в норматив и меньше времени ОФП ({ru(res['time_block'], 1)} мин).")
    elif res["survive"] and not res["ok"]:
        st.warning(f"⚠️ Люди не погибнут от дыма, но нарушают норматив (эвакуация {ru(res['time'], 1)} мин > 6 мин).")
    else:
        st.error(f"❌ ЛЮДИ ПОГИБНУТ! Время эвакуации ({ru(res['time'], 1)} мин) больше времени заполнения помещения дымом ({ru(res['time_block'], 1)} мин).")

    # График
    widths = np.linspace(0.6, 6.0, 200)
    times = people / (capacity * widths * exits)
    plots.show_chart(plots.evacuation_curve(widths, times, width, res["time"], res["norm"]))
    st.caption("Кривая времени эвакуации. Помните: вы должны уложиться не только в норматив, но и успеть до того, как коридор заполнится смертельным дымом.")

    prompt = (
        "Тема: эвакуация и опасные факторы пожара.\n"
        f"Данные: {people} человек, {exits} вых. по {width} м. Объем помещения {room_vol} м3.\n"
        f"Результат: эвакуация {res['time']:.1f} мин, блокировка дымом {res['time_block']:.1f} мин. "
        f"Люди {'успевают' if res['survive'] else 'не успевают'}.\n"
        "Объясни курсанту, что такое ОФП и почему дым убивает быстрее огня."
    )
    explain_block(prompt, key="evac")

    with st.expander("🚒 Как это в реальной работе", expanded=True):
        st.markdown(
            "- **Дым — главный убийца.** 70% людей на пожарах гибнут не от огня, а от отравления угарным газом и потери видимости.\n"
            "- **Задача РТП.** Оценивая обстановку, руководитель тушения обязан прогнозировать время заполнения путей эвакуации. Если люди не успевают — вводится звено ГДЗС на защиту путей.\n"
            "- **Закрытые двери.** Если коридор заполнен дымом, это отрезает пути выхода. Поэтому противопожарные двери должны быть закрыты."
        )

    storage.save_calc_button("Эвакуация", {"N": people, "b": width}, {"t_эвак": round(res["time"], 2), "t_ОФП": round(res["time_block"], 1)}, key="evac")