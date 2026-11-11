"""Модуль 1. Пожарная физика: температурный режим с учетом пожарной нагрузки."""
from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st
import sympy as sp
from scipy.optimize import brentq

from core import num, plots, ru, storage
from core.ai_explainer import explain_block

T_FLASHOVER = 600.0
T_SEVERE = 1000.0

_t, _T0, _Tc = sp.symbols("t T_0 T_c", real=True)
ISO834 = _T0 + 345 * sp.log(8 * _t + 1, 10)
ISO834_RATE = sp.diff(ISO834, _t)
TIME_TO_TEMP = (10 ** ((_Tc - _T0) / 345) - 1) / 8

_temperature = sp.lambdify((_t, _T0), ISO834, "numpy")
_rate = sp.lambdify(_t, ISO834_RATE, "numpy")


def temperature_iso(t_min, t0):
    """Базовая температура по ISO 834, °C."""
    return _temperature(t_min, t0)


def heating_rate(t_min):
    """Скорость роста температуры T'(t), °C/мин (для фазы роста)."""
    return _rate(t_min)


def time_to_reach(target: float, t0: float) -> float:
    """Время (мин), за которое температура достигает target при начальной t0 (по ISO 834)."""
    if target <= t0:
        return 0.0
    return float(TIME_TO_TEMP.subs({_Tc: target, _T0: t0}))


def calculate(t0: float, duration: float, fire_load: float) -> dict:
    """Расчёт температуры с учётом выгорания пожарной нагрузки."""
    if duration <= 0 or fire_load < 0:
        raise ValueError("Время и нагрузка должны быть неотрицательными.")

    # Время выгорания нагрузки (эмпирически: 1 кг/м² дерева горит ~1.2 мин)
    t_burnout = fire_load * 1.2

    # Максимальная температура (в момент выгорания)
    temp_max = float(temperature_iso(t_burnout, t0))

    # Температура в конце заданного времени (с учетом фазы охлаждения)
    if duration <= t_burnout:
        temp_end = float(temperature_iso(duration, t0))
        rate_end = float(heating_rate(duration))
        phase = "Рост"
    else:
        # Упрощенная фаза охлаждения: -10 °C в минуту, но не ниже начальной
        temp_end = max(t0, temp_max - 10 * (duration - t_burnout))
        rate_end = -10.0
        phase = "Охлаждение"

    t_flash = time_to_reach(T_FLASHOVER, t0)
    
    return {
        "temp_end": temp_end,
        "temp_max": temp_max,
        "t_burnout": t_burnout,
        "t_flash": t_flash if fire_load >= 20 else None, # Если нагрузка мала, вспышки может не быть
        "t_severe": time_to_reach(T_SEVERE, t0),
        "rate_end": rate_end,
        "phase": phase,
        "reached_flash": temp_max >= T_FLASHOVER
    }


def render() -> None:
    st.header("🔥 Пожарная физика и пожарная нагрузка")
    st.markdown(
        "Стандартная кривая **ISO 834** показывает рост температуры при идеальных условиях. "
        "Однако реальный пожар зависит от того, **сколько горючих материалов** находится в помещении (пожарная нагрузка). "
        "Если нагрузка мала, пожар может затухнуть, не достигнув опасных температур."
    )
    st.latex(r"T(t) = T_0 + 345\cdot\lg(8t + 1) \quad \text{до момента выгорания нагрузки}")

    c1, c2, c3 = st.columns(3)
    t0 = c1.number_input("Начальная температура T₀, °C", min_value=-40.0, max_value=60.0, value=20.0, step=1.0, key="fire_t0")
    duration = c2.number_input("Время t, мин", min_value=1.0, max_value=240.0, value=60.0, step=1.0, key="fire_time")
    fire_load = c3.number_input("Пожарная нагрузка, кг/м² (экв. дерева)", min_value=1.0, max_value=150.0, value=40.0, step=5.0, key="fire_load")

    try:
        res = calculate(t0, duration, fire_load)
    except (ValueError, ArithmeticError) as exc:
        st.error(f"Ошибка в исходных данных: {exc}")
        return

    m1, m2, m3, m4 = st.columns(4)
    m1.metric(f"Температура через {ru(duration, 0)} мин", f"{ru(res['temp_end'], 0)} °C")
    m2.metric("Пиковая температура", f"{ru(res['temp_max'], 0)} °C")
    m3.metric("Время выгорания нагрузки", f"{ru(res['t_burnout'], 0)} мин")
    m4.metric("Фаза пожара", res['phase'])

    if not res['reached_flash']:
        st.warning(
            f"⚠️ Пожарная нагрузка слишком мала! Пиковая температура ({ru(res['temp_max'], 0)} °C) "
            f"не достигает порога общей вспышки (600 °C). Пожар затухнет сам."
        )
    elif res['phase'] == "Охлаждение":
        st.info(
            f"🔥 Пожарная нагрузка выгорела на {ru(res['t_burnout'], 0)}-й минуте. "
            f"С этого момента температура пошла на спад. Выгорание длилось {ru(res['t_burnout'], 0)} мин."
        )
    else:
        st.error(
            f"🔥 Пожар всё еще в активной фазе! Нагрузки хватит на {ru(res['t_burnout'], 0)} минут. "
            f"Порог 600 °C достигнут на {ru(res['t_flash'], 1)}-й минуте."
        )

    with st.expander("🧮 Пошаговый расчёт", expanded=True):
        st.markdown("**Шаг 1.** Определяем время, на которое хватит горючего материала:")
        st.latex(rf"t_{{\text{{выгор}}}} = q \cdot 1{{,}}2 = {num(fire_load, 0)} \cdot 1{{,}}2 = {num(res['t_burnout'], 1)}\ \text{{мин}}")
        
        st.markdown("**Шаг 2.** Рассчитываем максимальную температуру (в момент выгорания):")
        st.latex(rf"T_{{max}} = {num(t0, 0)} + 345\cdot\lg(8 \cdot {num(res['t_burnout'], 1)} + 1) \approx {num(res['temp_max'], 0)}\ ^\circ\text{{C}}")
        
        if duration > res['t_burnout']:
            st.markdown("**Шаг 3.** Пожар перешел в фазу охлаждения (температура падает на 10 °C в минуту):")
            st.latex(rf"T({num(duration, 0)}) = {num(res['temp_max'], 0)} - 10 \cdot ({num(duration, 0)} - {num(res['t_burnout'], 1)}) \approx {num(res['temp_end'], 0)}\ ^\circ\text{{C}}")
        else:
            st.markdown("**Шаг 3.** Пожар всё ещё в фазе роста, используем стандартную формулу:")
            st.latex(rf"T({num(duration, 0)}) = {num(t0, 0)} + 345\cdot\lg(8 \cdot {num(duration, 0)} + 1) \approx {num(res['temp_end'], 0)}\ ^\circ\text{{C}}")
            
        st.caption(
            "Допущения тренажёра: скорость выгорания 1 кг/м² в 1.2 минуты, скорость остывания 10 °C/мин. "
            "В реальности процесс зависит от вентиляции и типа материалов."
        )

    # График
    t_plot = max(duration, res['t_burnout']) + 20
    times = np.linspace(0.0, t_plot, 400)
    
    # Массивы температур
    temps_iso = temperature_iso(times, t0)
    temps_cool = np.maximum(t0, res['temp_max'] - 10 * (times - res['t_burnout']))
    temps = np.where(times <= res['t_burnout'], temps_iso, temps_cool)

    fig = plots.fire_curve(times, temps, duration, res['temp_end'], res['t_flash'] if res['reached_flash'] else None, T_FLASHOVER, T_SEVERE)
    
    # Добавляем вертикальную линию выгорания
    fig.add_vline(x=res['t_burnout'], line_dash="dot", line_color="orange", 
                  annotation_text="Выгорание нагрузки", annotation_position="top right")
    
    plots.show_chart(fig)

    # Таблица
    st.subheader("Как меняется температура (ключевые точки)")
    marks = [1.0, 5.0, 10.0, res['t_burnout'], res['t_burnout'] + 20, res['t_burnout'] + 40]
    marks = sorted(list(set([round(m, 1) for m in marks if m <= t_plot])))
    
    table_data = []
    for m in marks:
        if m <= res['t_burnout']:
            temp = float(temperature_iso(m, t0))
            phase = "Рост"
        else:
            temp = max(t0, res['temp_max'] - 10 * (m - res['t_burnout']))
            phase = "Охлаждение"
        
        table_data.append({
            "Время, мин": ru(m, 1),
            "Температура, °C": ru(temp, 0),
            "Фаза": phase
        })
    
    st.dataframe(pd.DataFrame(table_data), hide_index=True)

    prompt = (
        "Тема: пожарная физика, влияние пожарной нагрузки на температуру.\n"
        f"Данные: T0 = {t0:g} °C, время {duration:g} мин, нагрузка {fire_load:g} кг/м². "
        f"Результат: пиковая температура {res['temp_max']:.0f} °C, время выгорания {res['t_burnout']:.0f} мин. "
        f"Фаза на {duration}-й минуте: {res['phase']}.\n"
        "Объясни курсанту, почему в пустой комнате пожар может потухнуть сам, а в библиотеке будет гореть часами."
    )
    explain_block(prompt, key="fire")

    with st.expander("🚒 Как это в реальной работе", expanded=True):
        st.markdown(
            "- **Что такое пожарная нагрузка.** Это суммарное количество теплоты, которое может выделиться при сгорании всех материалов в помещении. Измеряется в кг/м² (в пересчете на дерево).\n"
            "- **Библиотеки и склады.** Там пожарная нагрузка огромна (бумага, стеллажи). Пожар будет гореть очень долго и достигнет температур свыше 1000 °C.\n"
            "- **Пустые квартиры или офисы.** Если выгорела мебель, пожар может прекратиться сам, не успев перекинуться на соседние здания.\n"
            "- **Роль вентиляции.** Открытое окно (приток кислорода) может резко увеличить интенсивность горения — это называется «эффектом печной трубы»."
        )

    storage.save_calc_button(
        "Пожарная физика",
        {"T0, °C": t0, "t, мин": duration, "нагрузка, кг/м²": fire_load},
        {"T, °C": round(res["temp_end"], 1), "T_пик, °C": round(res['temp_max'], 0), "выгорание, мин": round(res['t_burnout'], 1)},
        key="fire",
    )