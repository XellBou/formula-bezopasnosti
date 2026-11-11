"""Модуль 4. Нагрузки: прочность балки на двух опорах с силой в середине пролёта."""
from __future__ import annotations

import math

import numpy as np
import streamlit as st
import sympy as sp

from core import num, plots, ru, storage
from core.ai_explainer import explain_block

# Расчётные сопротивления, МПа (учебные значения)
MATERIALS = {
    "Сталь С245": 240.0,
    "Дерево": 13.0,
    "Железобетон": 25.0,
}
SAFE_FACTOR = 1.2  # при запасе ≥ 1,2 считаем прочность обеспеченной

_F, _L, _b, _h = sp.symbols("F L b h", positive=True)
W_EXPR = _b * _h**2 / 6
M_EXPR = _F * _L / 4
SIGMA_EXPR = sp.simplify(M_EXPR / W_EXPR)  # 3·F·L / (2·b·h²)


def calculate(span: float, force: float, width: float, height: float, material: str) -> dict:
    if material not in MATERIALS:
        raise ValueError(f"неизвестный материал: {material}.")
    if span <= 0 or force <= 0:
        raise ValueError("пролёт и сила должны быть больше нуля.")
    if width <= 0 or height <= 0:
        raise ValueError("размеры сечения должны быть больше нуля.")

    strength = MATERIALS[material]
    w_mm3 = float(W_EXPR.subs({_b: width, _h: height}))  # мм³
    m_knm = float(M_EXPR.subs({_F: force, _L: span}))  # кН·м
    sigma = m_knm * 1.0e6 / w_mm3  # Н·мм / мм³ = МПа
    factor = strength / sigma
    if factor >= SAFE_FACTOR:
        status = "ok"
    elif factor >= 1.0:
        status = "limit"
    else:
        status = "fail"
    h_min = math.sqrt(6.0 * m_knm * 1.0e6 / (width * strength))
    return {
        "w_mm3": w_mm3,
        "w_cm3": w_mm3 / 1000.0,
        "m_knm": m_knm,
        "sigma": sigma,
        "strength": strength,
        "factor": factor,
        "status": status,
        "h_min": h_min,
    }


def moment_line(span: float, force: float, points: int = 101):
    """Эпюра моментов: M(x) = F·x/2 до середины пролёта и симметрично после."""
    x = np.linspace(0.0, span, points)
    moments = force / 2.0 * np.minimum(x, span - x)
    return x, moments


def render() -> None:
    st.header("🏗️ Нагрузки: выдержит ли балка")
    st.markdown(
        "Балка лежит на двух опорах, сила приложена в середине пролёта. Сравниваем напряжение "
        "в сечении с тем, что способен выдержать материал."
    )
    st.latex(r"W = \dfrac{b h^2}{6}, \qquad M = \dfrac{F L}{4}, \qquad \sigma = \dfrac{M}{W}")

    c1, c2, c3, c4, c5 = st.columns(5)
    span = c1.number_input("Пролёт L, м", min_value=0.5, max_value=20.0, value=4.0, step=0.5, key="load_l")
    force = c2.number_input("Сила F, кН", min_value=0.1, max_value=1000.0, value=10.0, step=1.0, key="load_f")
    width = c3.number_input("Ширина сечения b, мм", min_value=10.0, max_value=1000.0, value=100.0, step=10.0, key="load_b")
    height = c4.number_input("Высота сечения h, мм", min_value=10.0, max_value=2000.0, value=200.0, step=10.0, key="load_h")
    material = c5.selectbox("Материал", list(MATERIALS.keys()), key="load_mat")

    try:
        res = calculate(span, force, width, height, material)
        x, moments = moment_line(span, force)
    except (ValueError, ArithmeticError) as exc:
        st.error(f"Ошибка в исходных данных: {exc}")
        return

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Момент сопротивления W", f"{ru(res['w_cm3'], 1)} см³")
    m2.metric("Изгибающий момент M", f"{ru(res['m_knm'], 2)} кН·м")
    m3.metric("Напряжение σ", f"{ru(res['sigma'], 1)} МПа")
    m4.metric("Коэффициент запаса", ru(res["factor"], 2))

    strength_s = ru(res["strength"], 0)
    if res["status"] == "ok":
        st.success(
            f"Прочность обеспечена: σ = {ru(res['sigma'], 1)} МПа при допустимых {strength_s} МПа, "
            f"запас {ru(res['factor'], 2)}."
        )
    elif res["status"] == "limit":
        st.warning(
            f"На грани: σ = {ru(res['sigma'], 1)} МПа почти равно допустимым {strength_s} МПа "
            f"(запас всего {ru(res['factor'], 2)})."
        )
    else:
        st.error(
            f"Не выдержит: σ = {ru(res['sigma'], 1)} МПа больше допустимых {strength_s} МПа. "
            f"При ширине {ru(width, 0)} мм нужна высота сечения не менее {ru(res['h_min'], 0)} мм."
        )

    with st.expander("🧮 Пошаговый расчёт", expanded=True):
        w_s = f"{res['w_mm3']:,.0f}".replace(",", r"\,")
        st.markdown("**Шаг 1.** Момент сопротивления прямоугольного сечения:")
        st.latex(
            rf"W = \dfrac{{b h^2}}{{6}} = \dfrac{{{num(width, 1)}\cdot {num(height, 1)}^2}}{{6}} "
            rf"\approx {w_s}\ \text{{мм}}^3 = {num(res['w_cm3'], 1)}\ \text{{см}}^3"
        )
        st.markdown("**Шаг 2.** Наибольший изгибающий момент (под силой, в середине пролёта):")
        st.latex(
            rf"M = \dfrac{{F L}}{{4}} = \dfrac{{{num(force, 2)}\cdot {num(span, 2)}}}{{4}} "
            rf"= {num(res['m_knm'], 2)}\ \text{{кН}}\cdot\text{{м}}"
        )
        st.markdown("**Шаг 3.** Напряжение (1 кН·м = 10⁶ Н·мм, тогда ответ сразу в МПа):")
        st.latex(
            rf"\sigma = \dfrac{{M}}{{W}} = \dfrac{{{num(res['m_knm'], 2)}\cdot 10^6}}{{{w_s}}} "
            rf"\approx {num(res['sigma'], 1)}\ \text{{МПа}}"
        )
        st.markdown("В общем виде (упрощение выполнено в SymPy):")
        st.latex(r"\sigma = " + sp.latex(SIGMA_EXPR))
        st.markdown("**Шаг 4.** Коэффициент запаса:")
        st.latex(
            rf"n = \dfrac{{R}}{{\sigma}} = \dfrac{{{num(res['strength'], 0)}}}{{{num(res['sigma'], 1)}}} "
            rf"\approx {num(res['factor'], 2)}"
        )
        st.caption(
            "Упрощения тренажёра: собственный вес балки не учитывается; железобетон рассматривается как "
            "однородный материал с условным сопротивлением 25 МПа; границы вердикта: запас ≥ 1,2 — обеспечена, "
            "1,0–1,2 — на грани, < 1,0 — не выдержит."
        )

    plots.show_chart(plots.moment_diagram(x, moments, span, res["m_knm"]))

    prompt = (
        "Тема: нагрузки, прочность балки на двух опорах с силой в середине пролёта.\n"
        f"Данные: пролёт {span:g} м, сила {force:g} кН, сечение {width:g}×{height:g} мм, материал — {material}.\n"
        f"Результат: напряжение {res['sigma']:.1f} МПа при допустимых {res['strength']:g} МПа, "
        f"коэффициент запаса {res['factor']:.2f}.\n"
        "Объясни курсанту, что такое напряжение и запас прочности и почему высота сечения важнее ширины."
    )
    explain_block(prompt, key="load")

    with st.expander("🚒 Как это в реальной работе", expanded=True):
        st.markdown(
            "- **Аварийно-спасательные работы.** При разборе завалов ставят временные крепления и подпорки: "
            "брус «на ребро» держит в разы больше, чем плашмя, потому что высота сечения входит в формулу в квадрате.\n"
            "- **Оценка перекрытий.** На перекрытие действуют вес людей, оборудования и пролитой воды — "
            "спасатель должен понимать, откуда берётся запас прочности и когда он исчезает.\n"
            "- **Связь с пожаром.** Сталь при нагреве до 500–550 °C теряет примерно половину прочности: "
            "балка, которая в обычных условиях держит нагрузку с запасом, в пожаре может обрушиться."
        )

    storage.save_calc_button(
        "Нагрузки",
        {"L, м": span, "F, кН": force, "b, мм": width, "h, мм": height, "материал": material},
        {"σ, МПа": round(res["sigma"], 2), "запас": round(res["factor"], 2)},
        key="load",
    )