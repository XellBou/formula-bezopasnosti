"""Самопроверка расчётов: запустите `python selfcheck.py` из корня проекта."""
from __future__ import annotations

import math

from modules import evacuation, fire_physics, hydraulics, loads, risk, trainer


def close(value: float, expected: float, tol: float = 0.01) -> bool:
    return abs(value - expected) <= tol


def main() -> None:
    # Пожарная физика
    fire = fire_physics.calculate(20.0, 30.0, 40.0, 3.0)
    assert close(fire["temp_end"], 841.8, 0.1), fire
    assert close(fire["t_flash"], 5.87), fire
    assert close(fire["t_flash"], fire["t_flash_numeric"], 1e-6), fire

    # Гидравлика: контрольный пример из ТЗ
    hyd = hydraulics.calculate(30.0, 100.0, 3.5, 51)
    assert close(hyd["p_lift"], 2.94), hyd
    assert close(hyd["p_loss"], 1.84), hyd
    assert close(hyd["p_pump"], 7.78), hyd
    x, pressure = hydraulics.pressure_profile(30.0, 100.0, 3.5, 51)
    assert close(float(pressure[0]), hyd["p_pump"], 1e-9)
    assert close(float(pressure[-1]), hydraulics.P_NOZZLE, 1e-9)

    # Эвакуация
    evac = evacuation.calculate(300, 1.2, 60, 2)
    assert close(evac["time"], 2.083, 0.001) and evac["ok"], evac
    assert close(evacuation.calculate(450, 1.0, 50, 2)["min_width"], 0.75, 1e-9)

    # Нагрузки
    load = loads.calculate(4.0, 10.0, 100.0, 200.0, "Сталь С245")
    assert close(load["w_cm3"], 666.67), load
    assert close(load["m_knm"], 10.0, 1e-9), load
    assert close(load["sigma"], 15.0, 1e-6), load
    assert close(load["factor"], 16.0, 1e-6) and load["status"] == "ok", load
    assert loads.calculate(4.0, 10.0, 100.0, 200.0, "Дерево")["status"] == "fail"

    # Риск
    prob = risk.probability(18, 400)
    assert close(prob["p"], 0.045, 1e-9) and prob["level"] == "low", prob
    assert (prob["frac_num"], prob["frac_den"]) == (9, 200), prob
    rel = risk.reliability(0.001, 1000.0)
    assert close(rel["p"], math.exp(-1), 1e-9) and close(rel["p"], rel["p_check"], 1e-9), rel
    assert close(rel["mtbf"], 1000.0, 1e-6) and close(rel["median"], 693.147, 0.001), rel

    # Тренажёр: структура и ответы задач
    answers = {}
    for topic, tasks in trainer.TASKS.items():
        assert tasks, topic
        for task in tasks:
            for field in ("id", "text", "answer", "unit", "hint", "solution"):
                assert field in task, (topic, field)
            assert task["id"] not in answers, f"повтор id: {task['id']}"
            answers[task["id"]] = task["answer"]
    assert len(answers) >= 10

    ok = trainer.check_answer
    assert ok(float(fire_physics.temperature(30.0, 20.0)), answers["fire-1"])
    assert ok(float(fire_physics.temperature(5.0, 20.0)), answers["fire-2"])
    assert ok(fire_physics.time_to_reach(600.0, 20.0), answers["fire-3"])
    assert ok(hydraulics.calculate(27.0, 20.0, 1.0, 51)["p_lift"], answers["hyd-1"])
    assert ok(hydraulics.calculate(0.0, 80.0, 3.5, 51)["p_loss"], answers["hyd-2"])
    assert ok(hyd["p_pump"], answers["hyd-3"])
    assert ok(evac["time"], answers["evac-1"])
    assert ok(0.75, answers["evac-2"])
    assert ok(load["w_cm3"], answers["load-1"])
    assert ok(load["sigma"], answers["load-2"])
    assert ok(4 * 13.0 / 3.0, answers["load-3"])
    assert ok(prob["p"], answers["risk-1"])
    assert ok(risk.reliability(0.002, 100.0)["p"], answers["risk-2"])
    assert ok(risk.reliability(0.0005, 1.0)["mtbf"], answers["risk-3"])
    assert ok(rel["median"], answers["risk-4"])
    assert not ok(700.0, answers["fire-1"]) and trainer.parse_number("2,08") == 2.08

    print("Все проверки пройдены ✔")


if __name__ == "__main__":
    main()