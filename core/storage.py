"""SQLite-хранилище: история расчётов и попыток в тренажёре (data/tasks.db)."""
from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path

import streamlit as st

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "tasks.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    topic TEXT NOT NULL,
    task_id TEXT NOT NULL,
    user_answer REAL NOT NULL,
    correct_answer REAL NOT NULL,
    is_correct INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS calculations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    module TEXT NOT NULL,
    inputs TEXT NOT NULL,
    results TEXT NOT NULL
);
"""


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), timeout=5)
    conn.row_factory = sqlite3.Row
    return conn


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _execute(sql: str, params: tuple = ()) -> bool:
    try:
        with closing(_connect()) as conn:
            with conn:
                conn.execute(sql, params)
        return True
    except (sqlite3.Error, OSError):
        return False


def _query(sql: str, params: tuple = ()) -> list[dict]:
    try:
        with closing(_connect()) as conn:
            rows = conn.execute(sql, params).fetchall()
        return [dict(row) for row in rows]
    except (sqlite3.Error, OSError):
        return []


def init_db() -> bool:
    """Создаёт файл базы и таблицы, если их ещё нет. Возвращает False, если база недоступна."""
    try:
        with closing(_connect()) as conn:
            with conn:
                conn.executescript(SCHEMA)
        return True
    except (sqlite3.Error, OSError):
        return False


def save_attempt(topic: str, task_id: str, user_answer: float, correct_answer: float, is_correct: bool) -> bool:
    return _execute(
        "INSERT INTO attempts (ts, topic, task_id, user_answer, correct_answer, is_correct) VALUES (?, ?, ?, ?, ?, ?)",
        (_now(), topic, task_id, float(user_answer), float(correct_answer), int(bool(is_correct))),
    )


def get_attempts(limit: int = 200) -> list[dict]:
    return _query(
        "SELECT ts, topic, task_id, user_answer, correct_answer, is_correct FROM attempts ORDER BY id DESC LIMIT ?",
        (int(limit),),
    )


def get_stats() -> tuple[int, int]:
    rows = _query("SELECT COUNT(*) AS total, COALESCE(SUM(is_correct), 0) AS correct FROM attempts")
    if not rows:
        return 0, 0
    return int(rows[0]["total"]), int(rows[0]["correct"])


def save_calculation(module: str, inputs: dict, results: dict) -> bool:
    return _execute(
        "INSERT INTO calculations (ts, module, inputs, results) VALUES (?, ?, ?, ?)",
        (
            _now(),
            module,
            json.dumps(inputs, ensure_ascii=False, default=str),
            json.dumps(results, ensure_ascii=False, default=str),
        ),
    )


def get_calculations(limit: int = 200) -> list[dict]:
    return _query("SELECT ts, module, inputs, results FROM calculations ORDER BY id DESC LIMIT ?", (int(limit),))


def clear_history() -> bool:
    ok_attempts = _execute("DELETE FROM attempts")
    ok_calcs = _execute("DELETE FROM calculations")
    return ok_attempts and ok_calcs


def save_calc_button(module: str, inputs: dict, results: dict, key: str) -> None:
    """Кнопка сохранения текущего расчёта в историю."""
    if st.button("💾 Сохранить расчёт в историю", key=f"save_calc_{key}"):
        if save_calculation(module, inputs, results):
            st.success("Расчёт сохранён. Его можно посмотреть в разделе «История».")
        else:
            st.warning("Не удалось сохранить расчёт: база данных недоступна.")