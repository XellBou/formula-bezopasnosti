"""Графики Plotly в фирменных цветах проекта."""
from __future__ import annotations

import inspect

import numpy as np
import plotly.graph_objects as go
import streamlit as st

NAVY = "#0B2545"
ORANGE = "#F26A1B"
RED = "#C0392B"
GREEN = "#2E8B57"
GRAY = "#8A94A6"


def show_chart(fig: go.Figure) -> None:
    """Вывод графика на всю ширину (совместимо со старыми и новыми версиями Streamlit)."""
    try:
        params = inspect.signature(st.plotly_chart).parameters
    except (TypeError, ValueError):
        params = {}
    if "width" in params:
        st.plotly_chart(fig, width="stretch")
    else:
        st.plotly_chart(fig, use_container_width=True)


def _style(fig: go.Figure, title: str, x_title: str, y_title: str) -> go.Figure:
    fig.update_layout(
        title=dict(text=title, font=dict(size=17)),
        xaxis_title=x_title,
        yaxis_title=y_title,
        template="plotly_white",
        height=440,
        margin=dict(l=60, r=30, t=60, b=40),
        legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="left", x=0),
        hovermode="x unified",
    )
    return fig


def fire_curve(times, temps, t_end, temp_end, t_flash, flash_level=600.0, severe_level=1000.0) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(x=times, y=temps, mode="lines", name="T(t) по ISO 834", line=dict(color=ORANGE, width=3))
    )
    fig.add_hline(
        y=flash_level,
        line_dash="dash",
        line_color=RED,
        annotation_text="600 °C — общая вспышка (flashover)",
        annotation_position="bottom right",
    )
    fig.add_hline(
        y=severe_level,
        line_dash="dot",
        line_color=NAVY,
        annotation_text="1000 °C",
        annotation_position="bottom right",
    )
    if t_flash is not None and 0 < t_flash <= float(times[-1]):
        fig.add_trace(
            go.Scatter(
                x=[t_flash],
                y=[flash_level],
                mode="markers",
                name=f"600 °C через ≈ {t_flash:.1f} мин",
                marker=dict(color=RED, size=12, symbol="x"),
            )
        )
    fig.add_trace(
        go.Scatter(
            x=[t_end],
            y=[temp_end],
            mode="markers",
            name=f"T({t_end:g} мин) ≈ {temp_end:.0f} °C",
            marker=dict(color=NAVY, size=11),
        )
    )
    y_min = min(0.0, float(np.min(temps)) - 20.0)
    y_max = max(1100.0, float(np.max(temps)) + 50.0)
    fig.update_yaxes(range=[y_min, y_max])
    return _style(fig, "Стандартный температурный режим пожара", "Время t, мин", "Температура T, °C")


def pressure_profile(x, pressure, p_nozzle) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=x,
            y=pressure,
            mode="lines",
            name="Давление в линии",
            line=dict(color=ORANGE, width=3),
            fill="tozeroy",
            fillcolor="rgba(242,106,27,0.15)",
        )
    )
    fig.add_hline(
        y=p_nozzle,
        line_dash="dash",
        line_color=NAVY,
        annotation_text=f"Требуется на стволе: {p_nozzle:g} атм",
        annotation_position="top left",
    )
    fig.add_trace(
        go.Scatter(
            x=[x[0], x[-1]],
            y=[pressure[0], pressure[-1]],
            mode="markers",
            name="Насос → ствол",
            marker=dict(color=NAVY, size=11),
        )
    )
    fig.update_yaxes(rangemode="tozero")
    return _style(fig, "Падение давления вдоль рукавной линии", "Расстояние от насоса, м", "Давление, атм")


def evacuation_curve(widths, times, b_current, t_current, t_norm) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(x=widths, y=times, mode="lines", name="t(b) — время эвакуации", line=dict(color=ORANGE, width=3))
    )
    fig.add_hline(
        y=t_norm,
        line_dash="dash",
        line_color=RED,
        annotation_text=f"Норматив: {t_norm:g} мин",
        annotation_position="top right",
    )
    fig.add_trace(
        go.Scatter(
            x=[b_current],
            y=[t_current],
            mode="markers",
            name=f"Сейчас: b = {b_current:g} м, t ≈ {t_current:.2f} мин",
            marker=dict(color=GREEN if t_current <= t_norm else RED, size=13),
        )
    )
    fig.update_yaxes(rangemode="tozero")
    return _style(fig, "Время эвакуации в зависимости от ширины выхода", "Ширина одного выхода b, м", "Время t, мин")


def moment_diagram(x, moments, span, m_max) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=x,
            y=moments,
            mode="lines",
            name="M(x)",
            line=dict(color=ORANGE, width=3),
            fill="tozeroy",
            fillcolor="rgba(242,106,27,0.25)",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[span / 2],
            y=[m_max],
            mode="markers+text",
            text=[f"Mmax = {m_max:.2f} кН·м"],
            textposition="top center",
            name="Максимум под силой F",
            marker=dict(color=NAVY, size=11),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[0, span],
            y=[0, 0],
            mode="markers",
            name="Опоры",
            marker=dict(color=NAVY, size=14, symbol="triangle-up"),
        )
    )
    fig.update_yaxes(autorange="reversed")
    return _style(
        fig,
        "Эпюра изгибающих моментов (отложена со стороны растянутых волокон)",
        "Координата вдоль балки x, м",
        "M, кН·м",
    )


def risk_gauge(probability, low=0.05, high=0.2) -> go.Figure:
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=probability * 100,
            number={"suffix": " %", "valueformat": ".1f"},
            title={"text": "Вероятность события"},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": NAVY},
                "steps": [
                    {"range": [0, low * 100], "color": "#BFE3C9"},
                    {"range": [low * 100, high * 100], "color": "#FCE0A6"},
                    {"range": [high * 100, 100], "color": "#F5B7B1"},
                ],
            },
        )
    )
    fig.update_layout(height=320, margin=dict(l=30, r=30, t=60, b=20))
    return fig


def reliability_curve(times, probs, t_max, p_max, mtbf, median) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(x=times, y=probs, mode="lines", name="P(t) = e^(−λt)", line=dict(color=ORANGE, width=3))
    )
    fig.add_trace(
        go.Scatter(
            x=[t_max],
            y=[p_max],
            mode="markers",
            name=f"P({t_max:g} ч) ≈ {p_max:.3f}",
            marker=dict(color=NAVY, size=11),
        )
    )
    fig.add_hline(y=0.5, line_dash="dot", line_color=GRAY, annotation_text="P = 0,5", annotation_position="top right")
    if median <= t_max:
        fig.add_vline(
            x=median, line_dash="dot", line_color=GRAY, annotation_text="медиана", annotation_position="top left"
        )
    if mtbf <= t_max:
        fig.add_vline(
            x=mtbf, line_dash="dash", line_color=RED, annotation_text="Tср = 1/λ", annotation_position="top right"
        )
    fig.update_yaxes(range=[0, 1.05])
    return _style(fig, "Вероятность безотказной работы", "Время работы t, ч", "P(t)")