"""Общие утилиты проекта «Формула безопасности»."""
from __future__ import annotations


def _trim(value: float, digits: int) -> str:
    text = f"{float(value):.{digits}f}"
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    if text in ("-0", ""):
        text = "0"
    return text


def ru(value: float, digits: int = 2) -> str:
    """Число для обычного текста с десятичной запятой: 2.94 -> '2,94'."""
    return _trim(value, digits).replace(".", ",")


def num(value: float, digits: int = 2) -> str:
    """Число для LaTeX с десятичной запятой: 2.94 -> '2{,}94'."""
    return _trim(value, digits).replace(".", "{,}")