"""Модуль 2. Гидравлика: давление на насосе и расчет пены."""
from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st
import sympy as sp

from core import num, plots, ru, storage
from core.ai_explainer import explain_block

RHO = 1000.0
G = 9.81
PA_PER_ATM = 100_000.0
P_NOZZLE = 3.0
P_PUMP_NOMINAL = 10.0
RESERVE_SHARE = 0.8

K_TABLE = {25: 0.06, 51: 0.0015, 66: 0.0004, 77: 0.00017, 89: 0.000045, 110: 0.000025}

_rho, _g, _h, _k, _L, _Q, _Ps = sp.symbols("rho g h k L Q P_s", positive=True)
P_LIFT_EXPR = _rho * _g * _h / sp.Integer(100000)
P_LOSS_EXPR = _k * _L * _Q**2
P_PUMP_EXPR = _Ps + P_LIFT_EXPR + P_LOSS_EXPR


def calculate(height: float, length: float, flow: float, diameter: int) -> dict:
    if diameter not in K_TABLE:
        raise ValueError(f"для диаметра {diameter} мм нет коэффициента k.")
    if height < 0:
        raise ValueError("высота подъёма не может быть отрицательной.")
    if length <= 0 or flow <= 0:
        raise ValueError("длина линии и расход должны быть больше нуля.")

    k = K_TABLE[diameter]
    values = {_rho: RHO, _g: G, _h: height, _k: k, _L: length, _Q: flow, _Ps: P_NOZZLE}
    p_lift = float(P_LIFT_EXPR.subs(values))
    p_loss = float(P_LOSS_EXPR.subs(values))
    p_pump = float(P_PUMP_EXPR.subs(values))

    if p_pump <= RESERVE_SHARE * P_PUMP_NOMINAL:
        status = "ok"
    elif p_pump <= P_PUMP_NOMINAL:
        status = "limit"
    else:
        status = "fail"

    available = P_PUMP_NOMINAL - P_NOZZLE - p_lift
    max_length = available / (k * flow**2) if available > 0 else 0.0
    return {
        "k": k,
        "p_lift": p_lift,
        "p_loss": p_loss,
        "p_pump": p_pump,
        "status": status,
        "max_length": max_length,
    }


def pressure_profile(height: float, length: float, flow: float, diameter: int, points: int = 101):
    res = calculate(height, length, flow, diameter)
    x = np.linspace(0.0, length, points)
    pressure = res["p_pump"] - res["k"] * x * flow**2 - res["p_lift"] * x / length
    return x, pressure


def _k_table_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Диаметр рукава, мм": [str(d) for d in K_TABLE],
            "k, атм/(м·(л/с)²)": [ru(k, 6) for k in K_TABLE.values()],
        }
    )


def render() -> None:
    st.header("💧 Гидравлика и пена")
    st.markdown("Расчёт давления в рукавных линиях и расчёт воздушно-механической пены для тушения ЛВЖ.")

    tab_water, tab_foam = st.tabs(["Тушение водой (Давление)", "Тушение пеной (ЛВЖ)"])

    with tab_water:
        st.markdown(
            "Чтобы ствол работал на высоте, насос должен преодолеть **подъём воды** и **трение в рукавах**, "
            "а на стволе должно остаться рабочее давление."
        )
        st.latex(r"P_{\text{насос}} = P_{\text{ствол}} + \underbrace{\frac{\rho g h}{10^5}}_{P_{\text{подъём}}} + \underbrace{k\cdot L\cdot Q^2}_{P_{\text{пот}}}")

        c1, c2, c3, c4 = st.columns(4)
        height = c1.number_input("Высота подъёма h, м", min_value=0.0, max_value=150.0, value=30.0, step=1.0, key="hyd_h")
        length = c2.number_input("Длина рукавной линии L, м", min_value=20.0, max_value=2000.0, value=100.0, step=20.0, key="hyd_l")
        flow = c3.number_input("Расход Q, л/с", min_value=0.5, max_value=40.0, value=3.5, step=0.1, key="hyd_q")
        diameters = list(K_TABLE.keys())
        diameter = c4.selectbox("Диаметр рукава, мм", diameters, index=diameters.index(51), key="hyd_d")

        try:
            res = calculate(height, length, flow, diameter)
            x, pressure = pressure_profile(height, length, flow, diameter)
        except (ValueError, ArithmeticError) as exc:
            st.error(f"Ошибка в исходных данных: {exc}")
            return

        m1, m2, m3 = st.columns(3)
        m1.metric("Давление на подъём", f"{ru(res['p_lift'], 2)} атм")
        m2.metric("Потери в рукавах", f"{ru(res['p_loss'], 2)} атм")
        m3.metric("Требуемое давление насоса", f"{ru(res['p_pump'], 2)} атм")

        nominal = ru(P_PUMP_NOMINAL, 1)
        if res["status"] == "ok":
            st.success(f"Давления достаточно: нужно {ru(res['p_pump'], 2)} атм при номинале насоса {nominal} атм — есть запас.")
        elif res["status"] == "limit":
            st.warning(f"Насос работает на пределе: нужно {ru(res['p_pump'], 2)} атм из {nominal} атм. Запаса почти нет.")
        else:
            st.error(
                f"Давления недостаточно: нужно {ru(res['p_pump'], 2)} атм, а номинал насоса — {nominal} атм. "
                "Варианты: рукава большего диаметра, меньший расход, подача в перекачку."
            )
        if res["max_length"] > 0:
            st.caption(
                f"При этих высоте, расходе и диаметре предельная длина линии для насоса {nominal} атм — "
                f"около {ru(res['max_length'], 0)} м."
            )
        else:
            st.caption("На такую высоту номинального давления насоса не хватает даже без потерь в рукавах.")

        with st.expander("🧮 Пошаговый расчёт", expanded=True):
            h_s, l_s, q_s = num(height, 1), num(length, 1), num(flow, 2)
            k_s = num(res["k"], 6)
            lift_s, loss_s, pump_s = num(res["p_lift"], 2), num(res["p_loss"], 2), num(res["p_pump"], 2)

            st.markdown("**Шаг 1.** Гидростатическое давление столба воды (переводим паскали в атмосферы):")
            st.latex(
                rf"P_{{\text{{подъём}}}} = \dfrac{{\rho g h}}{{10^5}} = "
                rf"\dfrac{{1000\cdot 9{{,}}81\cdot {h_s}}}{{100\,000}} \approx {lift_s}\ \text{{атм}}"
            )
            st.markdown(f"**Шаг 2.** Потери в рукавной линии диаметром {diameter} мм:")
            st.latex(
                rf"P_{{\text{{пот}}}} = k\cdot L\cdot Q^2 = {k_s}\cdot {l_s}\cdot {q_s}^2 \approx {loss_s}\ \text{{атм}}"
            )
            st.markdown("**Шаг 3.** Складываем три слагаемых:")
            st.latex(
                rf"P_{{\text{{насос}}}} = {num(P_NOZZLE, 1)} + {lift_s} + {loss_s} \approx {pump_s}\ \text{{атм}}"
            )
            st.markdown("Учебные коэффициенты потерь:")
            st.dataframe(_k_table_frame(), hide_index=True)
            st.caption(
                "Допущения тренажёра: 1 атм ≈ 100 кПа; коэффициенты k — учебные, а не справочные; "
                "давление на стволе 3 атм; номинал насоса 10 атм. Для реальных расчётов используют справочники РТП."
            )

        plots.show_chart(plots.pressure_profile(x, pressure, P_NOZZLE))
        st.caption("График построен в предположении, что высота набирается равномерно по длине линии.")

        prompt = (
            "Тема: гидравлика, расчёт давления на насосе для рукавной линии.\n"
            f"Данные: высота {height:g} м, длина линии {length:g} м, расход {flow:g} л/с, рукав {diameter} мм.\n"
            f"Результат: на подъём {res['p_lift']:.2f} атм, потери в рукавах {res['p_loss']:.2f} атм, "
            f"требуемое давление насоса {res['p_pump']:.2f} атм.\n"
            "Объясни курсанту, откуда берётся каждое слагаемое и почему потери зависят от квадрата расхода."
        )
        explain_block(prompt, key="hyd")

        with st.expander("🚒 Как это в реальной работе", expanded=True):
            st.markdown(
                "- **Правило «10 метров — 1 атмосфера».** Подавая ствол на 9-й этаж, водитель насоса сразу знает: "
                "почти 3 атм уйдёт только на подъём воды.\n"
                "- **Квадрат расхода.** Подключили второй ствол к той же линии — расход вырос вдвое, "
                "а потери в ней — вчетверо. Поэтому магистральную линию прокладывают рукавами 77 мм, "
                "а рабочие — 51 мм.\n"
                "- **Перекачка.** Если водоисточник далеко и одного насоса не хватает, машины ставят в цепочку — "
                "расчёт расстояния между ними основан на той же формуле потерь."
            )

        storage.save_calc_button(
            "Гидравлика",
            {"h, м": height, "L, м": length, "Q, л/с": flow, "d, мм": diameter},
            {
                "P подъём, атм": round(res["p_lift"], 2),
                "P пот, атм": round(res["p_loss"], 2),
                "P насос, атм": round(res["p_pump"], 2),
            },
            key="hyd",
        )

    with tab_foam:
        st.subheader("Расчёт воздушно-механической пены")
        st.markdown("Тушение легковоспламеняющихся жидкостей (ЛВЖ) водой невозможно — жидкость всплывает и продолжает гореть. Для этого используется пена.")
        st.latex(r"V_{пены} = V_{раствора} \cdot K")
        
        c1, c2, c3 = st.columns(3)
        area = c1.number_input("Площадь пожара S, м²", min_value=10.0, max_value=5000.0, value=50.0, step=10.0, key="foam_area")
        time = c2.number_input("Время тушения t, мин", min_value=5, max_value=60, value=10, step=1, key="foam_time")
        conc = c3.selectbox("Тип пенообразователя", ["4% (углеводороды)", "6% (спирты, полярные)"], key="foam_conc")

        conc_rate = 0.04 if conc.startswith("4%") else 0.06
        I_rate = 0.08 # Интенсивность подачи раствора (I) для ЛВЖ = 0.08 л/(с*м2)
        
        solution_total = area * I_rate * time * 60
        foam_concentrate = solution_total * conc_rate
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Объем раствора", f"{ru(solution_total, 0)} л")
        m2.metric("Нужно пенообразователя", f"{ru(foam_concentrate, 0)} л")
        m3.metric("Объем готовой пены (K=10)", f"{ru(solution_total * 10, 0)} л")

        st.info(
            f"Для тушения {ru(area, 0)} м² горящего бензина потребуется насос, подающий "
            f"**{ru(solution_total/60, 1)} л/с** раствора, и **{ru(foam_concentrate, 0)} л** концентрата."
        )
        
        st.warning(
            "**Важно:** Пенообразователь — это концентрат. В чистом виде он не тушит. "
            "Его смешивают с водой в специальных пропорциях (4% или 6%), и только потом подают через ствол ГПС или СВП."
        )
                # --- ДОБАВИТЬ ВОТ ЭТОТ БЛОК В КОНЕЦ ВКЛАДКИ tab_foam ---
        
        st.markdown("---")
        
        prompt = (
            "Тема: гидравлика, тушение легковоспламеняющихся жидкостей (ЛВЖ) пеной.\n"
            f"Данные: площадь пожара {area} м², время тушения {time} мин, выбран тип {conc}.\n"
            f"Результат: требуется {solution_total:.0f} л раствора и {foam_concentrate:.0f} л концентрата.\n"
            "Объясни курсанту, почему бензин нельзя тушить водой, как образуется воздушно-механическая пена и зачем нужен пенообразователь."
        )
        explain_block(prompt, key="foam")

        with st.expander("🚒 Как это в реальной работе", expanded=True):
            st.markdown(
                "- **Почему вода не работает.** Бензин легче воды и всплывает на поверхность, продолжая гореть. Более того, мощная струя воды может разбрызгать горящую жидкость, увеличив площадь пожара.\n"
                "- **Как работает пена.** Воздушно-механическая пена — это множество пузырьков, заполненных воздухом. Она накрывает очаг плотным «одеялом», перекрывая доступ кислорода и охлаждая поверхность.\n"
                "- **Стволы для пены.** Для подачи используются стволы ГПС (генератор пены средней кратности) или СВП (ствол воздушно-пенный).\n"
                "- **Кратность пены.** Это отношение объема пены к объему раствора. Бывает низкой (до 20), средней (21–200) и высокой (более 200). Для бензина обычно используют пену средней кратности."
            )