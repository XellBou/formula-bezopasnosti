"""Модуль 6. Тренажёр задач с проверкой ответа, подсказками и разбором."""
from __future__ import annotations

import math

import pandas as pd
import streamlit as st

from core import ru, storage
from core.ai_explainer import explain

TOLERANCE = 0.05  # допуск при проверке ответа: 5 %

# Каждая задача: id (уникальный), text, answer (число), unit, hint, solution.
TASKS = {
    "Нормативы (СП)": [
    {
        "id": "norm-1",
        "text": "В актовом зале планируется мероприятие на 80 человек. Проектом предусмотрен один эвакуационный выход шириной 1,0 м. "
                "Соответствует ли это требованиям СП 1.13130.2020? (Ответьте числом: 1 — да, 0 — нет)",
        "answer": 0.0,
        "unit": "0 или 1",
        "hint": "Обратите внимание на количество людей (больше 50?) и требуемую ширину выхода для такого числа людей.",
        "solution": "1. В зале более 50 человек, значит, ширина выхода должна быть не менее 1,2 м (п. 4.2.19).\n"
                    "2. Также требуется не менее двух выходов (п. 4.2.7).\n"
                    "3. Проект не соответствует нормативам. Правильный ответ: 0 (нет).",
    },
    {
        "id": "norm-2",
        "text": "Ширина коридора на путях эвакуации составляет 1,1 м. По коридору могут эвакуироваться 60 человек. "
                "Нарушает ли это СП 1.13130.2020? (1 — да (нарушает), 0 — нет)",
        "answer": 1.0,
        "unit": "0 или 1",
        "hint": "Для коридоров с эвакуацией более 50 человек ширина должна быть не менее 1,2 м.",
        "solution": "1. По коридору эвакуируются 60 человек, что больше 50.\n"
                    "2. Требуемая ширина — не менее 1,2 м (п. 4.3.3).\n"
                    "3. Фактическая ширина 1,1 м — это нарушение. Правильный ответ: 1 (да).",
    },
],
    "Пожарная физика": [
        {
            "id": "fire-1",
            "text": "Пожар развивается по стандартной кривой ISO 834: T(t) = T₀ + 345·lg(8t + 1). "
            "Начальная температура 20 °C. Найдите температуру в помещении через 30 минут.",
            "answer": 841.8,
            "unit": "°C",
            "hint": "Подставьте t = 30: сначала вычислите 8·30 + 1, затем десятичный логарифм.",
            "solution": "1. 8·30 + 1 = 241.\n2. lg 241 ≈ 2,382.\n3. T = 20 + 345·2,382 ≈ 841,8 °C.",
        },
        {
            "id": "fire-2",
            "text": "По стандартной кривой ISO 834 при начальной температуре 20 °C найдите температуру "
            "через 5 минут после начала пожара.",
            "answer": 576.4,
            "unit": "°C",
            "hint": "T = 20 + 345·lg(8·5 + 1). Логарифм 41 чуть больше 1,6.",
            "solution": "1. 8·5 + 1 = 41.\n2. lg 41 ≈ 1,613.\n3. T = 20 + 345·1,613 ≈ 576,4 °C.\n"
            "4. Вывод: всего за 5 минут температура подходит к 600 °C.",
        },
        {
            "id": "fire-3",
            "text": "Начальная температура 20 °C. Через сколько минут по кривой ISO 834 температура "
            "достигнет 600 °C (порог общей вспышки)?",
            "answer": 5.87,
            "unit": "мин",
            "hint": "Решите уравнение 600 = 20 + 345·lg(8t + 1): выразите lg(8t + 1), затем возведите 10 в эту степень.",
            "solution": "1. lg(8t + 1) = (600 − 20)/345 ≈ 1,681.\n2. 8t + 1 = 10^1,681 ≈ 47,99.\n"
            "3. t = (47,99 − 1)/8 ≈ 5,87 мин.",
        },
    ],
    "Гидравлика": [
        {
            "id": "hyd-1",
            "text": "Ствол подают на 9-й этаж, высота подъёма 27 м. Какое давление (в атм) нужно только "
            "на подъём воды? Примите ρ = 1000 кг/м³, g = 9,81 м/с², 1 атм ≈ 100 кПа.",
            "answer": 2.65,
            "unit": "атм",
            "hint": "P = ρ·g·h даёт паскали. Чтобы получить атмосферы, разделите на 100 000.",
            "solution": "1. P = 1000·9,81·27 = 264 870 Па.\n2. 264 870 / 100 000 ≈ 2,65 атм.",
        },
        {
            "id": "hyd-2",
            "text": "Рукавная линия диаметром 51 мм (k = 0,0015) длиной 80 м, расход 3,5 л/с. "
            "Найдите потери давления в линии по формуле P = k·L·Q² (в атм).",
            "answer": 1.47,
            "unit": "атм",
            "hint": "Сначала возведите расход в квадрат: 3,5² = 12,25.",
            "solution": "1. Q² = 3,5² = 12,25.\n2. P = 0,0015·80·12,25 = 1,47 атм.",
        },
        {
            "id": "hyd-3",
            "text": "Ствол работает на высоте 30 м, линия 51 мм (k = 0,0015) длиной 100 м, расход 3,5 л/с. "
            "На стволе нужно 3 атм. Какое давление должен развивать насос? (1 атм ≈ 100 кПа, g = 9,81 м/с².)",
            "answer": 7.78,
            "unit": "атм",
            "hint": "Сложите три слагаемых: давление на стволе, давление на подъём и потери в рукавах.",
            "solution": "1. Подъём: 1000·9,81·30 / 100 000 ≈ 2,94 атм.\n2. Потери: 0,0015·100·3,5² ≈ 1,84 атм.\n"
            "3. Насос: 3 + 2,94 + 1,84 ≈ 7,78 атм.",
        },
    ],
    "Эвакуация": [
        {
            "id": "evac-1",
            "text": "В актовом зале 300 человек. Есть 2 выхода шириной по 1,2 м, удельная пропускная способность "
            "60 чел/(м·мин). За сколько минут люди покинут зал?",
            "answer": 2.08,
            "unit": "мин",
            "hint": "t = N / (q·b·n). Сначала найдите, сколько человек в минуту проходит через все выходы.",
            "solution": "1. Через все выходы: 60·1,2·2 = 144 чел/мин.\n2. t = 300 / 144 ≈ 2,08 мин.",
        },
        {
            "id": "evac-2",
            "text": "Из здания нужно эвакуировать 450 человек за 6 минут через 2 одинаковых выхода. "
            "Пропускная способность 50 чел/(м·мин). Какой должна быть минимальная ширина каждого выхода?",
            "answer": 0.75,
            "unit": "м",
            "hint": "Выразите ширину из формулы: b = N / (q·n·t).",
            "solution": "1. b = N / (q·n·t) = 450 / (50·2·6).\n2. b = 450 / 600 = 0,75 м.",
        },
    ],
    "Нагрузки": [
        {
            "id": "load-1",
            "text": "Деревянный брус имеет сечение: ширина 100 мм, высота 200 мм. Найдите момент сопротивления "
            "сечения W = b·h²/6. Ответ дайте в см³.",
            "answer": 666.7,
            "unit": "см³",
            "hint": "Удобно сразу перевести размеры в сантиметры: 10 см и 20 см.",
            "solution": "1. b = 10 см, h = 20 см.\n2. W = 10·20² / 6 = 4000 / 6 ≈ 666,7 см³.",
        },
        {
            "id": "load-2",
            "text": "Балка пролётом 4 м лежит на двух опорах, в середине приложена сила 10 кН. "
            "Сечение 100×200 мм (W ≈ 666 667 мм³). Найдите наибольшее напряжение в балке, МПа.",
            "answer": 15.0,
            "unit": "МПа",
            "hint": "M = F·L/4, затем σ = M/W. Переведите момент в Н·мм: 1 кН·м = 10⁶ Н·мм.",
            "solution": "1. M = 10·4 / 4 = 10 кН·м = 10·10⁶ Н·мм.\n2. σ = 10·10⁶ / 666 667 ≈ 15 МПа.",
        },
        {
            "id": "load-3",
            "text": "Деревянная балка (допустимое напряжение 13 МПа) сечением 150×200 мм перекрывает пролёт 3 м. "
            "Какую наибольшую силу в середине пролёта она выдержит? Ответ в кН.",
            "answer": 17.33,
            "unit": "кН",
            "hint": "Найдите W, затем допустимый момент M = σ·W и из M = F·L/4 выразите силу.",
            "solution": "1. W = 150·200² / 6 = 1 000 000 мм³.\n2. M = 13·1 000 000 = 13·10⁶ Н·мм = 13 кН·м.\n"
            "3. F = 4·M / L = 4·13 / 3 ≈ 17,33 кН.",
        },
    ],
    "Риск ЧС": [
        {
            "id": "risk-1",
            "text": "За 400 дежурных смен подразделение 18 раз выезжало на ДТП с деблокированием пострадавших. "
            "Оцените вероятность такого выезда за одну смену (ответ — десятичной дробью).",
            "answer": 0.045,
            "unit": "доля",
            "hint": "P = m / n: число событий делим на число наблюдений.",
            "solution": "1. P = 18 / 400.\n2. P = 0,045 (то есть 4,5 %).",
        },
        {
            "id": "risk-2",
            "text": "Интенсивность отказов мотопомпы λ = 0,002 1/ч. Найдите вероятность её безотказной работы "
            "в течение 100 часов: P(t) = e^(−λt).",
            "answer": 0.819,
            "unit": "доля",
            "hint": "Сначала найдите показатель степени: λ·t = 0,002·100.",
            "solution": "1. λ·t = 0,002·100 = 0,2.\n2. P = e^(−0,2) ≈ 0,819.",
        },
        {
            "id": "risk-3",
            "text": "Интенсивность отказов гидравлического инструмента λ = 0,0005 1/ч. "
            "Найдите среднюю наработку на отказ (в часах).",
            "answer": 2000.0,
            "unit": "ч",
            "hint": "Средняя наработка на отказ — величина, обратная интенсивности: T = 1/λ.",
            "solution": "1. T = 1 / λ = 1 / 0,0005.\n2. T = 2000 ч.",
        },
        {
            "id": "risk-4",
            "text": "Интенсивность отказов насоса λ = 0,001 1/ч. Через сколько часов вероятность безотказной "
            "работы снизится до 0,5 (медианная наработка)?",
            "answer": 693.0,
            "unit": "ч",
            "hint": "Решите уравнение e^(−λt) = 0,5: получится t = ln 2 / λ, где ln 2 ≈ 0,693.",
            "solution": "1. e^(−λt) = 0,5 → λt = ln 2 ≈ 0,693.\n2. t = 0,693 / 0,001 ≈ 693 ч.",
        },
    ],
}


def parse_number(raw: str) -> float | None:
    """Преобразует ввод пользователя в число. Допускает запятую и пробелы. None — если это не число."""
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


def check_answer(user: float, correct: float, tolerance: float = TOLERANCE) -> bool:
    """Ответ верен, если отличается от эталона не более чем на 5 %."""
    if correct == 0:
        return abs(user) <= tolerance
    return abs(user - correct) <= tolerance * abs(correct)


def guess_error(user: float, correct: float) -> str:
    """Простая эвристика: на что похожа ошибка."""
    if correct != 0 and user != 0:
        ratio = user / correct
        if ratio < 0:
            return "Ответ отличается знаком — проверь, что из чего вычитается."
        power = round(math.log10(ratio))
        if power != 0 and abs(ratio / 10**power - 1) <= TOLERANCE:
            direction = "больше" if power > 0 else "меньше"
            return (
                f"Твой ответ в {10 ** abs(power)} раз {direction} правильного. Очень похоже на ошибку "
                "в единицах измерения (мм ↔ см ↔ м, Па ↔ атм, проценты ↔ доли)."
            )
        deviation = abs(ratio - 1) * 100
        return (
            f"Отклонение от правильного ответа — {ru(deviation, 1)} %, это больше допуска 5 %. "
            "Скорее всего, ошибка в формуле или в арифметике: сверь свои шаги с решением ниже."
        )
    return "Проверь, все ли данные подставлены в формулу."


def local_review(task: dict, result: dict | None) -> str:
    """Разбор без ИИ: сравнение ответа с эталоном и пошаговое решение."""
    unit = task["unit"]
    parts = []
    if result is None:
        parts.append("Ты пока не дал ответ, поэтому просто покажу ход решения.")
    elif result["ok"]:
        parts.append(
            f"Ответ {ru(result['user'], 4)} {unit} — верно (эталон: {ru(task['answer'], 4)} {unit})."
        )
    else:
        parts.append(
            f"Твой ответ: {ru(result['user'], 4)} {unit}, правильный: {ru(task['answer'], 4)} {unit}."
        )
        parts.append(guess_error(result["user"], task["answer"]))
    parts.append("**Решение по шагам:**\n\n" + task["solution"])
    return "\n\n".join(parts)


def build_review_prompt(topic: str, task: dict, result: dict | None) -> str:
    if result is None:
        answer_part = "Курсант ещё не дал ответ. Объясни, как подступиться к задаче и как её решить."
    elif result["ok"]:
        answer_part = (
            f"Ответ курсанта: {result['user']:g} {task['unit']} — верный. "
            "Кратко подтверди ход решения и объясни, почему этот способ работает."
        )
    else:
        answer_part = (
            f"Ответ курсанта: {result['user']:g} {task['unit']} — неверный. "
            "Предположи, где вероятнее всего ошибка (единицы измерения, формула, арифметика), "
            "и объясни, как решать правильно."
        )
    return (
        f"Тема: тренажёр задач, раздел «{topic}».\n"
        f"Задача: {task['text']}\n"
        f"Правильный ответ: {task['answer']:g} {task['unit']}.\n"
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
        "Выберите тему, решите задачу и введите ответ. Ответ засчитывается, если он отличается "
        "от правильного не более чем на **5 %**."
    )
    db_ok = storage.init_db()
    _init_state()

    topic = st.selectbox("Тема", list(TASKS.keys()), key="trainer_topic")
    tasks = TASKS[topic]
    idx = st.session_state["trainer_idx"].get(topic, 0) % len(tasks)
    task = tasks[idx]
    task_id = task["id"]

    st.subheader(f"Задача {idx + 1} из {len(tasks)}")
    st.markdown(f'{task["text"]}', unsafe_allow_html=True)

    with st.form(key=f"trainer_form_{task_id}"):
        raw = st.text_input(
            f"Ваш ответ ({task['unit']})", key=f"trainer_answer_{task_id}", placeholder="Например: 2,08"
        )
        submitted = st.form_submit_button("✅ Проверить")

    if submitted:
        st.session_state["trainer_reviews"].pop(task_id, None)
        value = parse_number(raw)
        if value is None:
            st.session_state["trainer_results"].pop(task_id, None)
            st.error("Введите число, например 2,08 или 15. Единицы измерения писать не нужно.")
        else:
            is_ok = check_answer(value, task["answer"])
            st.session_state["trainer_results"][task_id] = {"user": value, "ok": is_ok}
            if db_ok:
                storage.save_attempt(topic, task_id, value, task["answer"], is_ok)

    result = st.session_state["trainer_results"].get(task_id)
    if result is not None:
        if result["ok"]:
            st.success(
                f"Верно! Ваш ответ {ru(result['user'], 4)} {task['unit']}, "
                f"эталон — {ru(task['answer'], 4)} {task['unit']}."
            )
            with st.expander("Показать решение"):
                st.markdown(task["solution"])
        else:
            st.error(
                f"Пока неверно: {ru(result['user'], 4)} {task['unit']}. Попробуйте ещё раз, "
                "откройте подсказку или нажмите «Разобрать с ИИ»."
            )

        # Разделяем на 4 колонки для кнопок
    col_prev, col_next, col_hint, col_ai = st.columns(4)
    
    if col_prev.button("⬅️ Назад", key=f"trainer_prev_{task_id}", use_container_width=True):
        st.session_state["trainer_idx"][topic] = (idx - 1) % len(tasks)
        # Очищаем состояния для текущей задачи
        for state_key in ("trainer_hints", "trainer_results", "trainer_reviews"):
            st.session_state[state_key].pop(task_id, None)
        st.rerun()

    if col_next.button("Вперёд ➡️", key=f"trainer_next_{task_id}", use_container_width=True):
        st.session_state["trainer_idx"][topic] = (idx + 1) % len(tasks)
        for state_key in ("trainer_hints", "trainer_results", "trainer_reviews"):
            st.session_state[state_key].pop(task_id, None)
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
        with st.expander("📜 Последние попытки"):
            rows = storage.get_attempts(limit=20)
            if rows:
                frame = pd.DataFrame(rows)
                frame["is_correct"] = frame["is_correct"].map({1: "верно", 0: "неверно"})
                frame = frame.rename(
                    columns={
                        "ts": "Время",
                        "topic": "Тема",
                        "task_id": "Задача",
                        "user_answer": "Ответ",
                        "correct_answer": "Эталон",
                        "is_correct": "Результат",
                    }
                )
                st.dataframe(frame, hide_index=True)
            else:
                st.write("Пока нет попыток.")
    else:
        st.caption("История попыток недоступна: не удалось открыть базу данных data/tasks.db.")