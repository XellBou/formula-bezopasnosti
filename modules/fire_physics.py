
"""Модуль 1. Пожарная физика: стандартный температурный режим ISO 834."""
from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st
import sympy as sp
from scipy.optimize import brentq

from core import num, plots, ru, storage
from core.ai_explainer import explain_block

T_FLASHOVER = 600.0  # условный порог общей вспышки, °C
T_SEVERE = 1000.0

_t, _T0, _Tc = sp.symbols("t T_0 T_c", real=True)
ISO834 = _T0 + 345 * sp.log(8 * _t + 1, 10)
ISO834_RATE = sp.diff(ISO834, _t)
TIME_TO_TEMP = (10 ** ((_Tc - _T0) / 345) - 1) / 8

_temperature = sp.lambdify((_t, _T0), ISO834, "numpy")
_rate = sp.lambdify(_t, ISO834_RATE, "numpy")


def temperature(t_min, t0):
    """Температура по ISO 834, °C. t_min — время в минутах (число или массив)."""
    return _temperature(t_min, t0)


def heating_rate(t_min):
    """Скорость роста температуры T'(t), °C/мин."""
    return _rate(t_min)


def time_to_reach(target: float, t0: float) -> float:
    """Время (мин), за которое температура достигает target при начальной t0."""
    if target <= t0:
        return 0.0
    return float(TIME_TO_TEMP.subs({_Tc: target, _T0: t0}))


def calculate(t0: float, duration: float, area: float, height: float) -> dict:
    if duration <= 0:
        raise ValueError("время должно быть больше нуля.")
    if area <= 0 or height <= 0:
        raise ValueError("площадь и высота помещения должны быть больше нуля.")
    t_flash = time_to_reach(T_FLASHOVER, t0)
    if t0 < T_FLASHOVER:
        # независимая численная проверка аналитической формулы
        t_flash_numeric = float(brentq(lambda x: float(temperature(x, t0)) - T_FLASHOVER, 0.0, 1.0e4))
    else:
        t_flash_numeric = 0.0
    return {
        "temp_end": float(temperature(duration, t0)),
        "t_flash": t_flash,
        "t_flash_numeric": t_flash_numeric,
        "t_severe": time_to_reach(T_SEVERE, t0),
        "volume": area * height,
        "rate_end": float(heating_rate(duration)),
    }


def render() -> None:
    st.header("🔥 Пожарная физика: стандартный пожар")
    st.markdown(
        "Стандартный температурный режим **ISO 834** — условная кривая, по которой испытывают "
        "строительные конструкции на огнестойкость. Она показывает главное: температура при пожаре "
        "растёт **по логарифму** — очень быстро в начале и медленнее потом."
    )
    st.latex(r"T(t) = T_0 + 345\cdot\lg(8t + 1)")

    c1, c2, c3, c4 = st.columns(4)
    t0 = c1.number_input("Начальная температура T₀, °C", min_value=-40.0, max_value=60.0, value=20.0, step=1.0, key="fire_t0")
    duration = c2.number_input("Время t, мин", min_value=1.0, max_value=240.0, value=30.0, step=1.0, key="fire_time")
    area = c3.number_input("Площадь помещения, м²", min_value=1.0, max_value=5000.0, value=40.0, step=1.0, key="fire_area")
    height = c4.number_input("Высота помещения, м", min_value=1.5, max_value=30.0, value=3.0, step=0.1, key="fire_height")

    try:
        res = calculate(t0, duration, area, height)
    except (ValueError, ArithmeticError) as exc:
        st.error(f"Ошибка в исходных данных: {exc}")
        return

    m1, m2, m3, m4 = st.columns(4)
    m1.metric(f"Температура через {ru(duration, 1)} мин", f"{ru(res['temp_end'], 0)} °C")
    m2.metric("До общей вспышки (600 °C)", f"{ru(res['t_flash'], 1)} мин")
    m3.metric("До 1000 °C", f"{ru(res['t_severe'], 0)} мин")
    m4.metric("Объём помещения", f"{ru(res['volume'], 1)} м³")

    if duration >= res["t_flash"]:
        st.error(
            f"К {ru(duration, 1)}-й минуте порог 600 °C уже пройден (≈ на {ru(res['t_flash'], 1)}-й минуте): "
            "по модели в помещении горит всё, что может гореть."
        )
    else:
        st.warning(
            f"Порог 600 °C ещё не достигнут: до общей вспышки остаётся ≈ {ru(res['t_flash'] - duration, 1)} мин."
        )

    with st.expander("🧮 Пошаговый расчёт", expanded=True):
        t_s, t0_s = num(duration, 1), num(t0, 1)
        t0_par = f"({t0_s})" if t0 < 0 else t0_s
        arg_s = num(8 * duration + 1, 1)
        temp_s = num(res["temp_end"], 1)
        flash_s = num(res["t_flash"], 2)

        st.markdown("**Шаг 1.** Подставляем время в формулу:")
        st.latex(
            rf"T({t_s}) = {t0_s} + 345\cdot\lg(8\cdot {t_s} + 1) = {t0_s} + 345\cdot\lg {arg_s} "
            rf"\approx {temp_s}\ ^\circ\mathrm{{C}}"
        )
        st.markdown("**Шаг 2.** Выражаем время из формулы (обратная функция к логарифму — показательная):")
        st.latex(r"T(t) = T_{\text{кр}} \;\Rightarrow\; t = \dfrac{10^{(T_{\text{кр}} - T_0)/345} - 1}{8}")
        st.latex(rf"t_{{600}} = \dfrac{{10^{{(600 - {t0_par})/345}} - 1}}{{8}} \approx {flash_s}\ \text{{мин}}")
        st.caption(
            f"Численная проверка методом Брента (SciPy): {ru(res['t_flash_numeric'], 2)} мин — совпадает с формулой."
        )
        st.markdown("**Шаг 3.** Скорость роста температуры — это производная:")
        st.latex(r"T'(t) = \dfrac{345\cdot 8}{(8t + 1)\ln 10}\ \ ^\circ\mathrm{C}/\text{мин}")
        st.caption(
            "Объём помещения V = S·H показан для справки: в стандартной кривой геометрия не участвует — "
            "это упрощение модели. В реальном пожаре объём и проёмы влияют на скорость прогрева и задымления."
        )

    t_plot = max(duration, 15.0)
    times = np.linspace(0.0, t_plot, 400)
    temps = temperature(times, t0)
    plots.show_chart(plots.fire_curve(times, temps, duration, res["temp_end"], res["t_flash"], T_FLASHOVER, T_SEVERE))

    st.subheader("Почему первые минуты критичны")
    marks = [1.0, 5.0, 10.0, 30.0, 60.0]
    table = pd.DataFrame(
        {
            "Время, мин": [ru(m, 0) for m in marks],
            "Температура, °C": [ru(float(temperature(m, t0)), 0) for m in marks],
            "Скорость роста, °C/мин": [ru(float(heating_rate(m)), 1) for m in marks],
        }
    )
    st.dataframe(table, hide_index=True)
    rise_first = float(temperature(5.0, t0)) - t0
    rise_next = float(temperature(30.0, t0)) - float(temperature(5.0, t0))
    st.markdown(
        f"За **первые 5 минут** температура вырастает на **{ru(rise_first, 0)} °C**, "
        f"а за следующие 25 минут — только на {ru(rise_next, 0)} °C. "
        "Так ведёт себя логарифм: самый крутой участок — в начале. Поэтому раннее обнаружение, "
        "быстрое сообщение и прибытие первого подразделения решают исход пожара."
    )

    prompt = (
        "Тема: пожарная физика, стандартная кривая пожара ISO 834 T(t) = T0 + 345·lg(8t + 1).\n"
        f"Данные: T0 = {t0:g} °C, время {duration:g} мин. "
        f"Результат: температура {res['temp_end']:.0f} °C, порог 600 °C (общая вспышка) "
        f"достигается через {res['t_flash']:.1f} мин.\n"
        "Объясни курсанту, что означают эти числа и почему первые минуты пожара самые важные."
    )
    explain_block(prompt, key="fire")

    with st.expander("🚒 Как это в реальной работе", expanded=True):
        st.markdown(
            "- **Время свободного развития пожара.** Руководитель тушения оценивает, сколько минут прошло "
            "от возникновения пожара до подачи первого ствола. Если прошло 8–10 минут, помещение, скорее всего, "
            "уже прошло общую вспышку — тактика и меры безопасности звена ГДЗС будут другими.\n"
            "- **Огнестойкость конструкций.** Обозначения вроде R 45 или REI 90 — это минуты, которые конструкция "
            "выдерживает именно при стандартном режиме нагрева.\n"
            "- **Важно:** реальный пожар зависит от пожарной нагрузки, проёмов и вентиляции. "
            "Стандартная кривая — учебная и испытательная модель, а не прогноз конкретного пожара."
        )

    storage.save_calc_button(
        "Пожарная физика",
        {"T0, °C": t0, "t, мин": duration, "S, м²": area, "H, м": height},
        {"T, °C": round(res["temp_end"], 1), "t до 600 °C, мин": round(res["t_flash"], 2)},
        key="fire",
    )