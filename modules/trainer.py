"""Модуль 6. Тренажёр задач с проверкой ответа, подсказками и разбором."""
from __future__ import annotations

import math
import pandas as pd
import streamlit as st

from core import ru, storage
from core.ai_explainer import explain

TOLERANCE = 0.05

# Каждая задача: id, type (numeric/choice), text, answer, unit, hint, solution, options (для choice)
TASKS = {
    "Тесты и Кейсы": [
        {
            "id": "case-1",
            "type": "choice",
            "text": "Вы прибыли на пожар в жилом доме. Из квартиры на 3 этаже идет густой черный дым. Ваши первые действия?",
            "options": [
                "1. Вбежать в квартиру и начать тушить водой",
                "2. Разбить окно для проветривания",
                "3. Звено ГДЗС: проверить дверь на ощупь, открыть осторожно, подать ствол на защиту",
                "4. Открыть дверь и крикнуть, чтобы выходили"
            ],
            "answer": "3. Звено ГДЗС: проверить дверь на ощупь, открыть осторожно, подать ствол на защиту",
            "hint": "Вспомните правила работы в непригодной для дыхания среде. Нельзя открывать дверь, не защитив себя.",
            "solution": "Правильный ответ: 3. При открытии двери произойдет подсос воздуха и вспышка. Нужно работать в СИЗОД и охлаждать дверь."
        },
        {
            "id": "test-1",
            "type": "choice",
            "text": "Какова минимальная ширина эвакуационного выхода при одновременном пребывании более 50 человек (СП 1.13130.2020)?",
            "options": ["А) 0,8 м", "Б) 1,0 м", "В) 1,2 м", "Г) 1,5 м"],
            "answer": "В) 1,2 м",
            "hint": "Это число часто встречается в нормативах для широких проходов.",
            "solution": "Согласно п. 4.2.19 СП 1.13130.2020, минимальная ширина составляет 1,2 м."
        },
        {
            "id": "case-2",
            "type": "choice",
            "text": "На человеке загорелась одежда. Что категорически нельзя делать?",
            "options": [
                "1. Сбить пламя, используя плотную ткань",
                "2. Заставить человека бежать в сторону выхода",
                "3. Повалить человека на землю",
                "4. Облить водой"
            ],
            "answer": "2. Заставить человека бежать в сторону выхода",
            "hint": "Бег создает дополнительный приток кислорода.",
            "solution": "Нельзя позволять человеку бежать — это усиливает горение. Нужно повалить его на землю и тушить."
        },
        {
            "id": "test-2",
            "type": "choice",
            "text": "Какой огнетушитель нельзя использовать для тушения электроустановок под напряжением?",
            "options": ["А) Углекислотный (ОУ)", "Б) Порошковый (ОП)", "В) Воздушно-пенный (ОВ)", "Г) Хладоновый (ОХ)"],
            "answer": "В) Воздушно-пенный (ОВ)",
            "hint": "В составе этого огнетушителя есть вода, которая проводит ток.",
            "solution": "Воздушно-пенные огнетушители содержат воду и не подходят для класса Е (электроустановки)."
        },
        {
            "id": "test-3",
            "type": "choice",
            "text": "Какое опасное значение температуры считается предельным для человека в помещении при пожаре?",
            "options": ["А) 50 °C", "Б) 70 °C", "В) 100 °C", "Г) 120 °C"],
            "answer": "Б) 70 °C",
            "hint": "При этой температуре человек быстро теряет сознание.",
            "solution": "Согласно ГОСТ 12.1.004-91, критическая температура для человека — 70 °C."
        }
    ],
    "Пожарная физика": [
        {
            "id": "fire-1",
            "type": "numeric",
            "text": "Пожар развивается по стандартной кривой ISO 834: T(t) = T₀ + 345·lg(8t + 1). Начальная температура 20 °C. Найдите температуру в помещении через 30 минут.",
            "answer": 841.8,
            "unit": "°C",
            "hint": "Подставьте t = 30: сначала вычислите 8·30 + 1, затем десятичный логарифм.",
            "solution": "1. 8·30 + 1 = 241.\n2. lg 241 ≈ 2,382.\n3. T = 20 + 345·2,382 ≈ 841,8 °C.",
        },
        {
            "id": "fire-2",
            "type": "numeric",
            "text": "По стандартной кривой ISO 834 при начальной температуре 20 °C найдите температуру через 5 минут после начала пожара.",
            "answer": 576.4,
            "unit": "°C",
            "hint": "T = 20 + 345·lg(8·5 + 1). Логарифм 41 чуть больше 1,6.",
            "solution": "1. 8·5 + 1 = 41.\n2. lg 41 ≈ 1,613.\n3. T = 20 + 345·1,613 ≈ 576,4 °C.\n4. Вывод: всего за 5 минут температура подходит к 600 °C.",
        },
        {
            "id": "fire-3",
            "type": "numeric",
            "text": "Начальная температура 20 °C. Через сколько минут по кривой ISO 834 температура достигнет 600 °C (порог общей вспышки)?",
            "answer": 5.87,
            "unit": "мин",
            "hint": "Решите уравнение 600 = 20 + 345·lg(8t + 1): выразите lg(8t + 1), затем возведите 10 в эту степень.",
            "solution": "1. lg(8t + 1) = (600 − 20)/345 ≈ 1,681.\n2. 8t + 1 = 10^1,681 ≈ 47,99.\n3. t = (47,99 − 1)/8 ≈ 5,87 мин.",
        },
    ],
    "Гидравлика": [
        {
            "id": "hyd-1",
            "type": "numeric",
            "text": "Ствол подают на 9-й этаж, высота подъёма 27 м. Какое давление (в атм) нужно только на подъём воды? Примите ρ = 1000 кг/м³, g = 9,81 м/с², 1 атм ≈ 100 кПа.",
            "answer": 2.65,
            "unit": "атм",
            "hint": "P = ρ·g·h даёт паскали. Чтобы получить атмосферы, разделите на 100 000.",
            "solution": "1. P = 1000·9,81·27 = 264 870 Па.\n2. 264 870 / 100 000 ≈ 2,65 атм.",
        },
        {
            "id": "hyd-2",
            "type": "numeric",
            "text": "Рукавная линия диаметром 51 мм (k = 0,0015) длиной 80 м, расход 3,5 л/с. Найдите потери давления в линии по формуле P = k·L·Q² (в атм).",
            "answer": 1.47,
            "unit": "атм",
            "hint": "Сначала возведите расход в квадрат: 3,5² = 12,25.",
            "solution": "1. Q² = 3,5² = 12,25.\n2. P = 0,0015·80·12,25 = 1,47 атм.",
        },
        {
            "id": "hyd-3",
            "type": "numeric",
            "text": "Ствол работает на высоте 30 м, линия 51 мм (k = 0,0015) длиной 100 м, расход 3,5 л/с. На стволе нужно 3 атм. Какое давление должен развивать насос? (1 атм ≈ 100 кПа, g = 9,81 м/с².)",
            "answer": 7.78,
            "unit": "атм",
            "hint": "Сложите три слагаемых: давление на стволе, давление на подъём и потери в рукавах.",
            "solution": "1. Подъём: 1000·9,81·30 / 100 000 ≈ 2,94 атм.\n2. Потери: 0,0015·100·3,5² ≈ 1,84 атм.\n3. Насос: 3 + 2,94 + 1,84 ≈ 7,78 атм.",
        },
    ],
    "Эвакуация": [
        {
            "id": "evac-1",
            "type": "numeric",
            "text": "В актовом зале 300 человек. Есть 2 выхода шириной по 1,2 м, удельная пропускная способность 60 чел/(м·мин). За сколько минут люди покинут зал?",
            "answer": 2.08,
            "unit": "мин",
            "hint": "t = N / (q·b·n). Сначала найдите, сколько человек в минуту проходит через все выходы.",
            "solution": "1. Через все выходы: 60·1,2·2 = 144 чел/мин.\n2. t = 300 / 144 ≈ 2,08 мин.",
        },
        {
            "id": "evac-2",
            "type": "numeric",
            "text": "Из здания нужно эвакуировать 450 человек за 6 минут через 2 одинаковых выхода. Пропускная способность 50 чел/(м·мин). Какой должна быть минимальная ширина каждого выхода?",
            "answer": 0.75,
            "unit": "м",
            "hint": "Выразите ширину из формулы: b = N / (q·n·t).",
            "solution": "1. b = N / (q·n·t) = 450 / (50·2·6).\n2. b = 450 / 600 = 0,75 м.",
        },
    ],
    "Нагрузки": [
        {
            "id": "load-1",
            "type": "numeric",
            "text": "Деревянный брус имеет сечение: ширина 100 мм, высота 200 мм. Найдите момент сопротивления сечения W = b·h²/6. Ответ дайте в см³.",
            "answer": 666.7,
            "unit": "см³",
            "hint": "Удобно сразу перевести размеры в сантиметры: 10 см и 20 см.",
            "solution": "1. b = 10 см, h = 20 см.\n2. W = 10·20² / 6 = 4000 / 6 ≈ 666,7 см³.",
        },
        {
            "id": "load-2",
            "type": "numeric",
            "text": "Балка пролётом 4 м лежит на двух опорах, в середине приложена сила 10 кН. Сечение 100×200 мм (W ≈ 666 667 мм³). Найдите наибольшее напряжение в балке, МПа.",
            "answer": 15.0,
            "unit": "МПа",
            "hint": "M = F·L/4, затем σ = M/W. Переведите момент в Н·мм: 1 кН·м = 10⁶ Н·мм.",
            "solution": "1. M = 10·4 / 4 = 10 кН·м = 10·10⁶ Н·мм.\n2. σ = 10·10⁶ / 666 667 ≈ 15 МПа.",
        },
        {
            "id": "load-3",
            "type": "numeric",
            "text": "Деревянная балка (допустимое напряжение 13 МПа) сечением 150×200 мм перекрывает пролёт 3 м. Какую наибольшую силу в середине пролёта она выдержит? Ответ в кН.",
            "answer": 17.33,
            "unit": "кН",
            "hint": "Найдите W, затем допустимый момент M = σ·W и из M = F·L/4 выразите силу.",
            "solution": "1. W = 150·200² / 6 = 1 000 000 мм³.\n2. M = 13·1 000 000 = 13·10⁶ Н·мм = 13 кН·м.\n3. F = 4·M / L = 4·13 / 3 ≈ 17,33 кН.",
        },
    ],
    "Риск ЧС": [
        {
            "id": "risk-1",
            "type": "numeric",
            "text": "За 400 дежурных смен подразделение 18 раз выезжало на ДТП с деблокированием пострадавших. Оцените вероятность такого выезда за одну смену (ответ — десятичной дробью).",
            "answer": 0.045,
            "unit": "доля",
            "hint": "P = m / n: число событий делим на число наблюдений.",
            "solution": "1. P = 18 / 400.\n2. P = 0,045 (то есть 4,5 %).",
        },
        {
            "id": "risk-2",
            "type": "numeric",
            "text": "Интенсивность отказов мотопомпы λ = 0,002 1/ч. Найдите вероятность её безотказной работы в течение 100 часов: P(t) = e^(−λt).",
            "answer": 0.819,
            "unit": "доля",
            "hint": "Сначала найдите показатель степени: λ·t = 0,002·100.",
            "solution": "1. λ·t = 0,002·100 = 0,2.\n2. P = e^(−0,2) ≈ 0,819.",
        },
        {
            "id": "risk-3",
            "type": "numeric",
            "text": "Интенсивность отказов гидравлического инструмента λ = 0,0005 1/ч. Найдите среднюю наработку на отказ (в часах).",
            "answer": 2000.0,
            "unit": "ч",
            "hint": "Средняя наработка на отказ — величина, обратная интенсивности: T = 1/λ.",
            "solution": "1. T = 1 / λ = 1 / 0,0005.\n2. T = 2000 ч.",
        },
        {
            "id": "risk-4",
            "type": "numeric",
            "text": "Интенсивность отказов насоса λ = 0,001 1/ч. Через сколько часов вероятность безотказной работы снизится до 0,5 (медианная наработка)?",
            "answer": 693.0,
            "unit": "ч",
            "hint": "Решите уравнение e^(−λt) = 0,5: получится t = ln 2 / λ, где ln 2 ≈ 0,693.",
            "solution": "1. e^(−λt) = 0,5 → λt = ln 2 ≈ 0,693.\n2. t = 0,693 / 0,001 ≈ 693 ч.",
        },
    ],
}


def parse_number(raw: str) -> float | None:
    text = (raw or "").strip().replace(" ", "").replace("\u00a0", "").replace(",", ".")
    if not text:
        return None
    try:
        value = float(text)
    except ValueError:
        return None
    if math.isnan(value) or math.isinf(value):
        return None
    return value


def check_answer(user_answer, correct: float | str, task_type: str) -> bool:
    if task_type == "choice":
        return str(user_answer) == str(correct)
    else:
        if correct == 0:
            return abs(user_answer) <= TOLERANCE
        return abs(user_answer - correct) <= TOLERANCE * abs(correct)


def guess_error(user: float, correct: float) -> str:
    if correct != 0 and user != 0:
        ratio = user / correct
        if ratio < 0:
            return "Ответ отличается знаком — проверь, что из чего вычитается."
        power = round(math.log10(ratio))
        if power != 0 and abs(ratio / 10**power - 1) <= TOLERANCE:
            direction = "больше" if power > 0 else "меньше"
            return f"Твой ответ в {10 ** abs(power)} раз {direction} правильного. Ошибка в единицах измерения?"
        deviation = abs(ratio - 1) * 100
        return f"Отклонение — {ru(deviation, 1)} % (допуск 5%). Скорее всего, ошибка в формуле."
    return "Проверь, все ли данные подставлены в формулу."


def local_review(task: dict, result: dict | None) -> str:
    if task.get("type") == "choice":
        if result and result["ok"]:
            return f"Верно! {task['solution']}"
        return f"Правильный ответ: **{task['answer']}**.\n\n{task['solution']}"

    unit = task.get("unit", "")
    parts = []
    if result is None:
        parts.append("Ты пока не дал ответ, покажу ход решения.")
    elif result["ok"]:
        parts.append(f"Ответ {ru(result['user'], 4)} {unit} — верно (эталон: {ru(task['answer'], 4)} {unit}).")
    else:
        parts.append(f"Твой ответ: {ru(result['user'], 4)} {unit}, правильный: {ru(task['answer'], 4)} {unit}.")
        parts.append(guess_error(result["user"], task["answer"]))
    parts.append("**Решение:**\n\n" + task["solution"])
    return "\n\n".join(parts)


def build_review_prompt(topic: str, task: dict, result: dict | None) -> str:
    if result is None:
        answer_part = "Курсант ещё не дал ответ. Объясни, как подступиться к задаче."
    elif result["ok"]:
        answer_part = f"Ответ курсанта: '{result['user']}' — верный. Подтверди ход решения."
    else:
        answer_part = f"Ответ курсанта: '{result['user']}' — неверный. Объясни, в чем ошибка."
    
    return (
        f"Тема: тренажёр задач, раздел «{topic}».\n"
        f"Задача: {task['text']}\n"
        f"Правильный ответ: {task['answer']}.\n"
        f"Эталонное решение:\n{task['solution']}\n"
        f"{answer_part}"
    )


def _init_state() -> None:
    for key in ("trainer_idx", "trainer_hints", "trainer_results", "trainer_reviews"):
        if key not in st.session_state:
            st.session_state[key] = {}


def render() -> None:
    st.header("🎯 Тренажёр задач")
    st.markdown(
        "Решите задачу. Ответ засчитывается, если он отличается от правильного не более чем на **5 %** (для расчётных задач). "
        "Для кейсов и тестов нужно выбрать правильный вариант."
    )
    db_ok = storage.init_db()
    _init_state()

    topic = st.selectbox("Тема", list(TASKS.keys()), key="trainer_topic")
    tasks = TASKS[topic]
    idx = st.session_state["trainer_idx"].get(topic, 0) % len(tasks)
    task = tasks[idx]
    task_id = task["id"]
    task_type = task.get("type", "numeric")

    st.subheader(f"Задача {idx + 1} из {len(tasks)}")
    
    st.markdown(f'<div class="fb-task">{task["text"]}</div>', unsafe_allow_html=True)

    with st.form(key=f"trainer_form_{task_id}"):
        if task_type == "choice":
            user_choice = st.radio("Выберите вариант:", task["options"], key=f"trainer_ans_{task_id}")
            raw_answer = user_choice
        else:
            raw_answer = st.text_input(
                f"Ваш ответ ({task.get('unit', '')})", 
                key=f"trainer_ans_{task_id}", 
                placeholder="Например: 2,08"
            )
            
        submitted = st.form_submit_button("✅ Проверить")

    if submitted:
        st.session_state["trainer_reviews"].pop(task_id, None)
        
        if task_type == "choice":
            is_ok = check_answer(raw_answer, task["answer"], task_type)
            st.session_state["trainer_results"][task_id] = {"user": raw_answer, "ok": is_ok}
            if db_ok:
                storage.save_attempt(topic, task_id, 1.0 if is_ok else 0.0, 1.0, is_ok)
        else:
            value = parse_number(raw_answer)
            if value is None:
                st.session_state["trainer_results"].pop(task_id, None)
                st.error("Введите число, например 2,08 или 15.")
            else:
                is_ok = check_answer(value, task["answer"], task_type)
                st.session_state["trainer_results"][task_id] = {"user": value, "ok": is_ok}
                if db_ok:
                    storage.save_attempt(topic, task_id, value, task["answer"], is_ok)

    result = st.session_state["trainer_results"].get(task_id)
    if result is not None:
        if result["ok"]:
            st.success("Верно! Отличная работа.")
            with st.expander("Показать решение"):
                st.markdown(task["solution"])
        else:
            if task_type == "choice":
                st.error(f"Пока неверно. Вы выбрали: *{result['user']}*")
            else:
                st.error(f"Пока неверно: {ru(result['user'], 4)} {task.get('unit', '')}.")

    col_prev, col_next, col_hint, col_ai = st.columns(4)
    
    if col_prev.button("⬅️ Назад", key=f"trainer_prev_{task_id}", use_container_width=True):
        st.session_state["trainer_idx"][topic] = (idx - 1) % len(tasks)
        for k in ("trainer_hints", "trainer_results", "trainer_reviews"):
            st.session_state[k].pop(task_id, None)
        st.rerun()

    if col_next.button("Вперёд ➡️", key=f"trainer_next_{task_id}", use_container_width=True):
        st.session_state["trainer_idx"][topic] = (idx + 1) % len(tasks)
        for k in ("trainer_hints", "trainer_results", "trainer_reviews"):
            st.session_state[k].pop(task_id, None)
        st.rerun()

    if col_hint.button("💡 Подсказка", key=f"trainer_hint_{task_id}", use_container_width=True):
        st.session_state["trainer_hints"][task_id] = True
        
    ai_clicked = col_ai.button("🤖 Разбор с ИИ", key=f"trainer_ai_{task_id}", use_container_width=True)

    if st.session_state["trainer_hints"].get(task_id):
        st.info(f"💡 {task['hint']}")

    if ai_clicked:
        with st.spinner("Разбираю решение…"):
            st.session_state["trainer_reviews"][task_id] = explain(
                build_review_prompt(topic, task, result),
                fallback=local_review(task, result),
            )
    review = st.session_state["trainer_reviews"].get(task_id)
    if review:
        st.info(review)

    st.markdown("---")
    if db_ok:
        total, correct = storage.get_stats()
        if total:
            st.caption(f"Ваша статистика: верных ответов {correct} из {total} попыток ({100 * correct / total:.0f} %).")