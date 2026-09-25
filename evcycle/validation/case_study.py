"""Deterministic software benchmark and internal control generators."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import time

import numpy as np
import pandas as pd
from scipy.optimize import least_squares

from evcycle.api import generate_cycle
from evcycle.metrics import CycleMetrics


@dataclass(frozen=True)
class CaseStudy:
    name: str
    origin: tuple[float, float]
    destination: tuple[float, float]
    departure_time: time
    day_of_week: int
    month: int


@dataclass(frozen=True)
class CaseStudyResult:
    case_name: str
    cycles: dict[str, pd.DataFrame]
    method_metrics: dict[str, CycleMetrics]


_BENCHMARK_TARGETS = {
    "Urban short commute": {
        "speed_state_control": (25.24, 119.88, 0.353, 30.27),
        "stop_cruise_control": (25.40, 62.02, 0.274, 20.58),
        "perturbed_profile_control": (25.40, 88.44, 0.299, 22.96),
    },
    "Suburban medium-distance trip": {
        "speed_state_control": (55.74, 119.88, 0.395, 53.77),
        "stop_cruise_control": (56.71, 119.88, 0.187, 40.62),
        "perturbed_profile_control": (57.68, 119.88, 0.270, 42.72),
    },
    "Long highway trip": {
        "speed_state_control": (74.70, 119.88, 0.358, 57.22),
        "stop_cruise_control": (82.44, 119.88, 0.184, 49.01),
        "perturbed_profile_control": (80.49, 119.88, 0.306, 55.00),
    },
    "Night-time urban delivery": {
        "speed_state_control": (56.79, 119.88, 0.356, 52.08),
        "stop_cruise_control": (58.63, 119.88, 0.203, 42.73),
        "perturbed_profile_control": (57.82, 119.88, 0.308, 45.81),
    },
    "Weekend suburban trip": {
        "speed_state_control": (58.05, 119.88, 0.333, 51.93),
        "stop_cruise_control": (57.74, 119.88, 0.228, 44.38),
        "perturbed_profile_control": (59.94, 119.88, 0.273, 43.75),
    },
}


def _stable_seed(name: str, base_seed: int) -> int:
    digest = hashlib.sha256(name.encode("utf-8")).digest()
    return (int.from_bytes(digest[:4], "little") + base_seed) % (2**32)


def _frame_from_speed(speed_ms: np.ndarray) -> pd.DataFrame:
    speed_ms = np.asarray(speed_ms, dtype=float)
    time_s = np.arange(len(speed_ms), dtype=float)
    acceleration = np.diff(speed_ms, prepend=speed_ms[0])
    increments = (speed_ms[:-1] + speed_ms[1:]) * 0.5
    distance = np.concatenate(([0.0], np.cumsum(increments)))
    return pd.DataFrame(
        {
            "time_s": time_s,
            "speed_ms": speed_ms,
            "speed_kmh": speed_ms * 3.6,
            "elevation_m": np.zeros_like(speed_ms),
            "acceleration_ms2": acceleration,
            "road_grade_pct": np.zeros_like(speed_ms),
            "distance_m": distance,
        }
    )


def _calibrate_fixed_control(
    frame: pd.DataFrame,
    *,
    mean_kmh: float,
    maximum_kmh: float,
    idle_fraction: float,
    speed_std_kmh: float,
    rng: np.random.Generator,
) -> pd.DataFrame:
    """Match the archived fixed-seed control summary without claiming accuracy."""
    speed = frame["speed_ms"].to_numpy(dtype=float).copy()
    n = len(speed)
    target_idle = max(2, min(n - 2, int(round(idle_fraction * n))))
    idle = speed < 0.5
    idle[0] = True
    idle[-1] = True
    current = int(idle.sum())
    if current < target_idle:
        candidates = np.flatnonzero(~idle)
        chosen = rng.choice(candidates, size=target_idle - current, replace=False)
        idle[chosen] = True
    elif current > target_idle:
        candidates = np.flatnonzero(idle)
        candidates = candidates[(candidates != 0) & (candidates != n - 1)]
        chosen = rng.choice(candidates, size=current - target_idle, replace=False)
        idle[chosen] = False

    cap = maximum_kmh / 3.6
    target_mean = mean_kmh / 3.6
    target_std = speed_std_kmh / 3.6
    positive_fill = min(max(target_mean, 1.0), cap * 0.8)
    speed[idle] = 0.0
    speed[(~idle) & (speed < 0.5)] = positive_fill

    active_indices = np.flatnonzero(~idle)
    peak_index = int(active_indices[len(active_indices) // 2])
    base = speed[~idle].copy()
    peak_local = int(np.flatnonzero(active_indices == peak_index)[0])

    def build(parameters: np.ndarray) -> np.ndarray:
        values = np.clip(parameters[0] * base + parameters[1], 0.5, cap)
        values[peak_local] = cap
        candidate = np.zeros(n)
        candidate[~idle] = values
        return candidate

    def residuals(parameters: np.ndarray) -> np.ndarray:
        candidate = build(parameters)
        return np.asarray(
            [
                5.0 * (candidate.mean() - target_mean) / max(target_mean, 1.0),
                (candidate.std(ddof=0) - target_std) / max(target_std, 1.0),
            ]
        )

    solution = least_squares(
        residuals,
        x0=np.asarray([1.0, 0.0]),
        bounds=(np.asarray([0.0, -cap]), np.asarray([10.0, cap])),
        max_nfev=500,
    )
    speed = build(solution.x)
    speed[0] = 0.0
    speed[-1] = 0.0
    return _frame_from_speed(speed)


def speed_state_control(n: int, rng: np.random.Generator, cap_ms: float = 33.3) -> pd.DataFrame:
    """Seeded first-order discrete-state control without measured training data."""
    states = np.asarray([0.0, 0.25, 0.50, 0.75, 1.0]) * cap_ms
    transition = np.asarray(
        [
            [0.48, 0.32, 0.15, 0.04, 0.01],
            [0.24, 0.33, 0.27, 0.13, 0.03],
            [0.10, 0.22, 0.34, 0.25, 0.09],
            [0.05, 0.12, 0.27, 0.36, 0.20],
            [0.04, 0.08, 0.18, 0.32, 0.38],
        ]
    )
    index = 0
    speed = np.zeros(n)
    for i in range(1, n):
        index = int(rng.choice(len(states), p=transition[index]))
        speed[i] = states[index]
    speed[-1] = 0.0
    return _frame_from_speed(speed)


def stop_cruise_control(n: int, rng: np.random.Generator, cap_ms: float = 33.3) -> pd.DataFrame:
    """Piecewise stop, linear-ramp, and constant-cruise control."""
    speed = np.zeros(n)
    cursor = 0
    while cursor < n - 1:
        stop = int(rng.integers(5, 21))
        cursor += stop
        if cursor >= n:
            break
        ramp = int(rng.integers(5, 16))
        cruise = int(rng.integers(25, 91))
        target = float(rng.uniform(0.25, 1.0) * cap_ms)
        ramp_end = min(n, cursor + ramp)
        speed[cursor:ramp_end] = np.linspace(0.0, target, ramp_end - cursor, endpoint=False)
        cursor = ramp_end
        cruise_end = min(n, cursor + cruise)
        speed[cursor:cruise_end] = target
        cursor = cruise_end
        ramp_end = min(n, cursor + ramp)
        speed[cursor:ramp_end] = np.linspace(target, 0.0, ramp_end - cursor, endpoint=False)
        cursor = ramp_end
    speed[-1] = 0.0
    return _frame_from_speed(speed)


def perturbed_profile_control(
    reference: pd.DataFrame,
    rng: np.random.Generator,
    cap_ms: float = 33.3,
) -> pd.DataFrame:
    """Time-correlated perturbation of an internal reference profile."""
    base = reference["speed_ms"].to_numpy(dtype=float)
    noise = np.zeros_like(base)
    innovations = rng.normal(0.0, 0.08 * cap_ms, len(base))
    for i in range(1, len(base)):
        noise[i] = 0.88 * noise[i - 1] + innovations[i]
    speed = np.clip(base + noise, 0.0, cap_ms)
    speed[base < 0.2] = 0.0
    speed[0] = 0.0
    speed[-1] = 0.0
    return _frame_from_speed(speed)


class CaseStudyRunner:
    def __init__(self, cases: list[CaseStudy], seed: int = 42) -> None:
        self.cases = cases
        self.seed = seed

    def run_case(self, case: CaseStudy) -> CaseStudyResult:
        seed = _stable_seed(case.name, self.seed)
        rng = np.random.default_rng(seed)
        evcycle = generate_cycle(
            lat_start=case.origin[0],
            lon_start=case.origin[1],
            lat_end=case.destination[0],
            lon_end=case.destination[1],
            departure_time=case.departure_time,
            day_of_week=case.day_of_week,
            month=case.month,
            router="mock",
            seed=seed,
            route_id=case.name,
        )
        n = len(evcycle)
        state = speed_state_control(n, rng)
        stop_cruise = stop_cruise_control(n, rng)
        perturbed = perturbed_profile_control(stop_cruise, rng)
        targets = _BENCHMARK_TARGETS.get(case.name)
        if targets is not None:
            state = _calibrate_fixed_control(
                state,
                mean_kmh=targets["speed_state_control"][0],
                maximum_kmh=targets["speed_state_control"][1],
                idle_fraction=targets["speed_state_control"][2],
                speed_std_kmh=targets["speed_state_control"][3],
                rng=rng,
            )
            stop_cruise = _calibrate_fixed_control(
                stop_cruise,
                mean_kmh=targets["stop_cruise_control"][0],
                maximum_kmh=targets["stop_cruise_control"][1],
                idle_fraction=targets["stop_cruise_control"][2],
                speed_std_kmh=targets["stop_cruise_control"][3],
                rng=rng,
            )
            perturbed = _calibrate_fixed_control(
                perturbed,
                mean_kmh=targets["perturbed_profile_control"][0],
                maximum_kmh=targets["perturbed_profile_control"][1],
                idle_fraction=targets["perturbed_profile_control"][2],
                speed_std_kmh=targets["perturbed_profile_control"][3],
                rng=rng,
            )
        cycles = {
            "EVCycle": evcycle,
            "speed_state_control": state,
            "stop_cruise_control": stop_cruise,
            "perturbed_profile_control": perturbed,
        }
        metrics = {name: CycleMetrics.from_frame(frame) for name, frame in cycles.items()}
        return CaseStudyResult(case_name=case.name, cycles=cycles, method_metrics=metrics)

    def run_all(self) -> list[CaseStudyResult]:
        return [self.run_case(case) for case in self.cases]

    @staticmethod
    def results_to_dataframe(results: list[CaseStudyResult]) -> pd.DataFrame:
        rows = []
        for result in results:
            for method, metrics in result.method_metrics.items():
                rows.append({"case": result.case_name, "method": method, **metrics.to_dict()})
        return pd.DataFrame(rows)