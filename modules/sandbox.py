"""Модуль 8. Инженерная песочница (5 инструментов анализа)."""
import streamlit as st
import numpy as np
import sympy as sp
import plotly.graph_objects as go
import pandas as pd
from core.ai_explainer import explain_block

def render() -> None:
    st.header("📈 Инженерная песочница")
    st.markdown(
        "Профессиональный инструмент для анализа функций, 3D-моделирования, "
        "расчёта площадей (интегралов), обработки данных и баллистики."
    )
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Анализ 2D", 
        "⚖️ Сравнение", 
        "📉 Аппроксимация",
        "🌐 3D Поверхности",
        "🎯 Баллистика (Струя)"
    ])

    # ==========================================
    # ВКЛАДКА 1: АНАЛИЗ ФУНКЦИИ
    # ==========================================
    with tab1:
        st.markdown("Введите функцию, и система найдёт её корни, экстремумы, производную и **площадь под графиком (интеграл)**.")
        
        c1, c2 = st.columns([3, 1])
        with c1:
            func_str = st.text_input("Введите функцию f(x):", value="x**2 - 4*x + 3", key="f1")
        with c2:
            st.write("Диапазон X:")
            x_min = st.number_input("От", value=-10.0, step=1.0, key="xmin1")
            x_max = st.number_input("До", value=10.0, step=1.0, key="xmax1")

        if func_str:
            try:
                x = sp.Symbol('x')
                expr = sp.sympify(func_str.replace("^", "**"))
                
                derivative = sp.diff(expr, x)
                integral = sp.integrate(expr, (x, x_min, x_max))
                extrema = sp.solve(derivative, x)
                
                f_num = sp.lambdify(x, expr, "numpy")
                x_vals = np.linspace(x_min, x_max, 1000)
                
                with np.errstate(all='ignore'):
                    y_vals = f_num(x_vals)
                    y_vals = np.where(np.iscomplex(y_vals), np.nan, y_vals)
                    y_vals = np.where(np.abs(y_vals) > 10000, np.nan, y_vals) 

                fig = go.Figure()
                fig.add_trace(go.Scatter(x=x_vals, y=y_vals, mode='lines', name='f(x)', line=dict(color='#F26A1B', width=3)))
                fig.add_hline(y=0, line_color="black", line_width=1)
                fig.add_vline(x=0, line_color="black", line_width=1)
                fig.update_layout(title=f"График: y = {func_str}", template="plotly_white", height=450)
                st.plotly_chart(fig, use_container_width=True)
                
                col_a, col_b = st.columns(2)
                with col_a:
                    st.latex(rf"f'(x) = {sp.latex(derivative)}")
                    st.latex(rf"\int_{{{x_min}}}^{{{x_max}}} f(x)dx \approx {sp.N(integral, 3)}")
                with col_b:
                    if extrema:
                        st.write("**Экстремумы:**")
                        for e in extrema:
                            if e.is_real:
                                st.write(f"x = {sp.N(e, 2)}, y = {sp.N(expr.subs(x, e), 2)}")
                    
                prompt = f"Функция: f(x) = {func_str}. Интеграл на [{x_min}, {x_max}]: {sp.N(integral, 3)}. Объясни, что физически означает интеграл (например, если это скорость, то интеграл — путь). Приведи пример из МЧС."
                explain_block(prompt, key="sandbox_tab1")
            except Exception as e:
                st.error(f"Ошибка: {e}")

    # ==========================================
    # ВКЛАДКА 2: СРАВНЕНИЕ ФУНКЦИЙ
    # ==========================================
    with tab2:
        st.markdown("Сравните две функции и найдите точки их пересечения (например, точка разрушения конструкции или пересечение графиков нагрузок).")
        
        c1, c2 = st.columns(2)
        f1_str = c1.text_input("Функция f(x):", value="x**2 - 4", key="comp_f1")
        f2_str = c2.text_input("Функция g(x):", value="2*x + 1", key="comp_f2")
        
        if f1_str and f2_str:
            try:
                x = sp.Symbol('x')
                expr1 = sp.sympify(f1_str.replace("^", "**"))
                expr2 = sp.sympify(f2_str.replace("^", "**"))
                
                intersections = sp.solve(sp.Eq(expr1, expr2), x)
                
                f1_num = sp.lambdify(x, expr1, "numpy")
                f2_num = sp.lambdify(x, expr2, "numpy")
                x_vals = np.linspace(-10, 10, 1000)
                
                with np.errstate(all='ignore'):
                    y1 = f1_num(x_vals)
                    y2 = f2_num(x_vals)
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=x_vals, y=y1, mode='lines', name=f'f(x)', line=dict(color='#F26A1B', width=3)))
                fig.add_trace(go.Scatter(x=x_vals, y=y2, mode='lines', name=f'g(x)', line=dict(color='#0B2545', width=3)))
                
                for pt in intersections:
                    if pt.is_real:
                        y_pt = expr1.subs(x, pt)
                        fig.add_trace(go.Scatter(x=[pt], y=[y_pt], mode='markers', name=f'Пересечение x={sp.N(pt,2)}', marker=dict(color='red', size=10)))
                
                fig.update_layout(title="Сравнение функций", template="plotly_white", height=450)
                st.plotly_chart(fig, use_container_width=True)
                
                if intersections:
                    st.success(f"Найдены точки пересечения: x = {', '.join([str(sp.N(i, 2)) for i in intersections if i.is_real])}")
                else:
                    st.info("На заданном отрезке функции не пересекаются.")
                    
                prompt = f"Функции f(x) = {f1_str} и g(x) = {f2_str} пересекаются в точках {intersections}. Как инженер, объясни, что означает эта точка пересечения (например, когда нагрузка превышает прочность)."
                explain_block(prompt, key="sandbox_tab2")
            except Exception as e:
                st.error(f"Ошибка: {e}")

    # ==========================================
    # ВКЛАДКА 3: АППРОКСИМАЦИЯ ДАННЫХ
    # ==========================================
    with tab3:
        st.markdown("Введите экспериментальные данные, и инструмент построит линию тренда и выведет уравнение.")
        st.info("Вводите значения через запятую. Пример X: `1, 2, 3, 4, 5`. Пример Y: `10, 22, 35, 48, 60`.")
        
        c1, c2 = st.columns(2)
        x_input = c1.text_input("Данные X:", "1, 2, 3, 4, 5")
        y_input = c2.text_input("Данные Y:", "10, 22, 35, 48, 60")
        
        poly_degree = st.radio("Степень полинома:", [1, 2], format_func=lambda x: "Линейная" if x == 1 else "Квадратичная", horizontal=True)
        
        if x_input and y_input:
            try:
                x_vals = np.array([float(i) for i in x_input.replace(" ", "").split(",")])
                y_vals = np.array([float(i) for i in y_input.replace(" ", "").split(",")])
                
                if len(x_vals) == len(y_vals) and len(x_vals) >= 2:
                    coeffs = np.polyfit(x_vals, y_vals, poly_degree)
                    poly_func = np.poly1d(coeffs)
                    
                    x_plot = np.linspace(min(x_vals) - 1, max(x_vals) + 1, 100)
                    y_plot = poly_func(x_plot)
                    
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(x=x_vals, y=y_vals, mode='markers', name='Эксперимент', marker=dict(color='#F26A1B', size=12)))
                    fig.add_trace(go.Scatter(x=x_plot, y=y_plot, mode='lines', name='Тренд', line=dict(color='#0B2545', width=3, dash='dash')))
                    fig.update_layout(title="Аппроксимация данных", template="plotly_white", height=450)
                    st.plotly_chart(fig, use_container_width=True)
                    
                    if poly_degree == 1:
                        st.latex(rf"y = {coeffs[0]:.3f}x {coeffs[1]:+.3f}")
                    else:
                        st.latex(rf"y = {coeffs[0]:.3f}x^2 {coeffs[1]:+.3f}x {coeffs[2]:+.3f}")
                        
                    y_pred = poly_func(x_vals)
                    ss_res = np.sum((y_vals - y_pred)**2)
                    ss_tot = np.sum((y_vals - np.mean(y_vals))**2)
                    r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
                    
                    st.metric("Достоверность (R²)", f"{r_squared:.4f}")
                    
                    prompt = f"Данные: {x_vals}, {y_vals}. Тренд: y = {poly_func}. R² = {r_squared:.4f}. Объясни, что показывает этот тренд и можно ли доверять данным."
                    explain_block(prompt, key="sandbox_tab3")
                else:
                    st.error("Количество точек X и Y должно совпадать (минимум 2).")
            except Exception as e:
                st.error(f"Ошибка обработки данных: {e}.")

    # ==========================================
    # ВКЛАДКА 4: 3D-ПОВЕРХНОСТИ (НОВОЕ)
    # ==========================================
    with tab4:
        st.markdown(
            "Постройте 3D-поверхность для функции от двух переменных. "
            "Это полезно для визуализации распределения температуры, давления или нагрузки по площади."
        )
        
        func_3d = st.text_input("Введите функцию f(x, y):", value="sin(sqrt(x**2 + y**2))", key="f3d")
        st.info("💡 Примеры: `x**2 + y**2`, `sin(x)*cos(y)`, `exp(-(x**2 + y**2))`")
        
        if func_3d:
            try:
                x, y = sp.symbols('x y')
                expr = sp.sympify(func_3d.replace("^", "**"))
                f_num = sp.lambdify((x, y), expr, "numpy")
                
                # Создаем сетку
                x_vals = np.linspace(-5, 5, 100)
                y_vals = np.linspace(-5, 5, 100)
                X, Y = np.meshgrid(x_vals, y_vals)
                
                with np.errstate(all='ignore'):
                    Z = f_num(X, Y)
                    Z = np.where(np.iscomplex(Z), np.nan, Z)
                    Z = np.where(np.abs(Z) > 1000, np.nan, Z)
                
                fig = go.Figure(data=[go.Surface(z=Z, x=X, y=Y, colorscale='Viridis')])
                fig.update_layout(
                    title=f"3D Поверхность: z = {func_3d}",
                    scene=dict(xaxis_title='X', yaxis_title='Y', zaxis_title='Z'),
                    height=600,
                    margin=dict(l=0, r=0, b=0, t=40)
                )
                st.plotly_chart(fig, use_container_width=True)
                
                prompt = f"Функция двух переменных: f(x,y) = {func_3d}. Как инженер, объясни, что это за поверхность. Если по осям X и Y отложены координаты помещения, а Z — температура или давление, как это поможет спасателю?"
                explain_block(prompt, key="sandbox_tab4")
            except Exception as e:
                st.error(f"Ошибка: {e}")

    # ==========================================
    # ВКЛАДКА 5: БАЛЛИСТИКА (НОВОЕ)
    # ==========================================
    with tab5:
        st.markdown(
            "Расчет траектории полета струи воды из пожарного ствола или осколков. "
            "Мы пренебрегаем сопротивлением воздуха для простоты (идеальная баллистика)."
        )
        
        c1, c2, c3 = st.columns(3)
        v0 = c1.number_input("Начальная скорость V₀, м/с", min_value=1.0, max_value=100.0, value=30.0)
        angle = c2.number_input("Угол наклона ствола α, °", min_value=0.0, max_value=90.0, value=45.0)
        h0 = c3.number_input("Начальная высота ствола h₀, м", min_value=0.0, max_value=100.0, value=0.0)
        
        g = 9.81
        a_rad = np.radians(angle)
        
        # Время полета
        t_flight = (v0 * np.sin(a_rad) + np.sqrt((v0 * np.sin(a_rad))**2 + 2 * g * h0)) / g
        t_vals = np.linspace(0, t_flight, 200)
        
        # Координаты
        x_vals = v0 * np.cos(a_rad) * t_vals
        y_vals = h0 + v0 * np.sin(a_rad) * t_vals - 0.5 * g * t_vals**2
        
        # Дальность и макс высота
        L = x_vals[-1]
        H_max = np.max(y_vals)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=x_vals, y=y_vals, mode='lines', name='Траектория', line=dict(color='#0B2545', width=3)))
        # Отмечаем максимум
        fig.add_trace(go.Scatter(x=[x_vals[np.argmax(y_vals)]], y=[H_max], mode='markers', name='Макс. высота', marker=dict(color='#F26A1B', size=10)))
        # Земля
        fig.add_hline(y=0, line_color="green", line_width=2)
        
        fig.update_layout(
            title=f"Траектория струи (Дальность: {L:.1f} м, Высота: {H_max:.1f} м)",
            xaxis_title="Расстояние, м",
            yaxis_title="Высота, м",
            template="plotly_white",
            height=500
        )
        st.plotly_chart(fig, use_container_width=True)
        
        c_m1, c_m2, c_m3 = st.columns(3)
        c_m1.metric("Дальность полета", f"{L:.1f} м")
        c_m2.metric("Максимальная высота", f"{H_max:.1f} м")
        c_m3.metric("Время полета", f"{t_flight:.2f} с")
        
        prompt = f"Баллистика. Начальная скорость {v0} м/с, угол {angle}°, высота {h0} м. Дальность {L:.1f} м, макс высота {H_max:.1f} м. Объясни, как спасатель использует эти расчеты при подаче воды из ствола (например, чтобы достать до окна на высоте)."
        explain_block(prompt, key="sandbox_tab5")