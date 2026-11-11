"""Модуль 4. Нагрузки: прочность балки с учетом нагрева при пожаре."""
from __future__ import annotations

import math
import numpy as np
import streamlit as st
import sympy as sp

from core import num, plots, ru, storage
from core.ai_explainer import explain_block

MATERIALS = {"Сталь С245": 240.0, "Дерево": 13.0, "Железобетон": 25.0}

_F, _L, _b, _h = sp.symbols("F L b h", positive=True)
W_EXPR = _b * _h**2 / 6
M_EXPR = _F * _L / 4
SIGMA_EXPR = sp.simplify(M_EXPR / W_EXPR)

def get_temp_factor(material: str, temp: float) -> float:
    """Снижение прочности материала при нагреве."""
    if material == "Сталь С245":
        if temp >= 600: return 0.1  # сталь почти расплавилась
        if temp >= 500: return 0.5
        if temp >= 400: return 0.7
        return 1.0
    elif material == "Дерево":
        if temp >= 300: return 0.0  # дерево сгорело
        if temp >= 200: return 0.5  # обугливание
        return 1.0
    return 1.0  # ЖБК имеет лучшую огнестойкость

def calculate(span: float, force: float, width: float, height: float, material: str, temp: float) -> dict:
    if span <= 0 or force <= 0 or width <= 0 or height <= 0:
        raise ValueError("Все размеры и нагрузка должны быть больше нуля.")

    base_strength = MATERIALS[material]
    temp_factor = get_temp_factor(material, temp)
    current_strength = base_strength * temp_factor

    w_mm3 = float(W_EXPR.subs({_b: width, _h: height}))
    m_knm = float(M_EXPR.subs({_F: force, _L: span}))
    sigma = m_knm * 1.0e6 / w_mm3 
    factor = current_strength / sigma if sigma > 0 else 0

    status = "ok" if factor >= 1.2 else "limit" if factor >= 1.0 else "fail"
    
    return {
        "w_cm3": w_mm3 / 1000.0, "m_knm": m_knm, "sigma": sigma,
        "strength": current_strength, "factor": factor, "status": status, "temp_factor": temp_factor
    }

def moment_line(span: float, force: float, points: int = 101):
    x = np.linspace(0.0, span, points)
    moments = force / 2.0 * np.minimum(x, span - x)
    return x, moments

def render() -> None:
    st.header("🏗️ Нагрузки: выдержит ли балка в огне?")
    st.markdown(
        "При пожаре строительные конструкции теряют прочность. Сталь при 500 °C теряет половину несущей способности, "
        "а дерево обугливается. Узнайте, в какой момент балка обрушится."
    )

    c1, c2, c3, c4, c5 = st.columns(5)
    span = c1.number_input("Пролёт L, м", min_value=0.5, max_value=20.0, value=4.0, step=0.5, key="load_l")
    force = c2.number_input("Сила F, кН", min_value=0.1, max_value=1000.0, value=10.0, step=1.0, key="load_f")
    width = c3.number_input("Ширина b, мм", min_value=10.0, max_value=1000.0, value=100.0, step=10.0, key="load_b")
    height = c4.number_input("Высота h, мм", min_value=10.0, max_value=2000.0, value=200.0, step=10.0, key="load_h")
    material = c5.selectbox("Материал", list(MATERIALS.keys()), key="load_mat")

    temp = st.slider("🔥 Температура при пожаре, °C", min_value=20, max_value=1000, value=20, step=10, key="load_temp")

    try:
        res = calculate(span, force, width, height, material, temp)
        x, moments = moment_line(span, force)
    except (ValueError, ArithmeticError) as exc:
        st.error(f"Ошибка в данных: {exc}")
        return

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Напряжение σ", f"{ru(res['sigma'], 1)} МПа")
    m2.metric(f"Предел при {temp}°C", f"{ru(res['strength'], 1)} МПа")
    m3.metric("Коэффициент запаса", ru(res["factor"], 2))

    if res["status"] == "ok":
        st.success(f"✅ Прочность обеспечена. Запас {ru(res['factor'], 2)}. Балка выдержит даже при нагреве.")
    elif res["status"] == "limit":
        st.warning(f"⚠️ Критическое состояние! Запас всего {ru(res['factor'], 2)}. При дальнейшем нагреве — обрушение.")
    else:
        st.error(f"❌ ОБРУШЕНИЕ! Напряжение ({ru(res['sigma'], 1)} МПа) превысило предел прочности нагретого материала ({ru(res['strength'], 1)} МПа).")

    # Визуализация деградации
    st.markdown("---")
    st.subheader("📉 Влияние температуры на прочность материала")
    temps = np.linspace(20, 800, 100)
    strengths = [MATERIALS[material] * get_temp_factor(material, t) for t in temps]
    
    import plotly.graph_objects as go
    fig = go.Figure()
    
    # Линия прочности материала
    fig.add_trace(go.Scatter(
        x=temps, 
        y=strengths, 
        mode="lines", 
        name="Предел прочности", 
        line=dict(color="#F26A1B", width=3)
    ))
    
    # Красная линия напряжения
    fig.add_hline(
        y=res["sigma"], 
        line_dash="dash", 
        line_color="red", 
        annotation_text=f"Ваше напряжение ({ru(res['sigma'], 1)} МПа)",
        annotation_position="bottom right"
    )
    
    fig.update_layout(
        xaxis_title="Температура, °C", 
        yaxis_title="Предел прочности, МПа", 
        title=f"Деградация прочности: {material}",
        template="plotly_white",
        height=400
    )
    
    st.plotly_chart(fig, use_container_width="stretch")
    st.caption("Оранжевая линия — предел прочности материала. Как только она опускается ниже красной пунктирной линии (ваше напряжение) — конструкция обрушается.")
    prompt = (
        "Тема: огнестойкость конструкций.\n"
        f"Данные: балка {material}, нагрузка {force} кН, нагрев до {temp} °C.\n"
        f"Напряжение {res['sigma']:.1f} МПа, предел прочности {res['strength']:.1f} МПа. Вердикт: {res['status']}.\n"
        "Объясни курсанту, почему металл обрушается при пожаре и почему пожарные не заходят под конструкции без расчета."
    )
    explain_block(prompt, key="load")

    with st.expander("🚒 Как это в реальной работе", expanded=True):
        st.markdown(
            "- **Скрип металла.** Перед обрушением стальная балка издает характерный звук и прогибается. Это сигнал к немедленному отходу.\n"
            "- **Защита конструкций.** В зданиях стальные колонны покрывают специальными огнезащитными составами (красками или бетоном), чтобы они дольше не грелись.\n"
            "- **Дерево.** Деревянные балки долго горят и теряют прочность из-за уменьшения полезного сечения."
        )

    storage.save_calc_button("Нагрузки", {"материал": material, "T": temp}, {"σ": round(res["sigma"], 1), "запас": round(res["factor"], 2)}, key="load")