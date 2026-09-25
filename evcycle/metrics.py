"""Descriptive cycle metrics."""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class CycleMetrics:
    avg_speed_kmh: float
    max_speed_kmh: float
    avg_moving_speed_kmh: float
    idle_fraction: float
    avg_accel_ms2: float
    max_accel_ms2: float
    avg_decel_ms2: float
    max_decel_ms2: float
    speed_std_kmh: float
    total_distance_km: float
    duration_s: float
    energy_proxy_kwh_per_100km: float

    @classmethod
    def from_frame(cls, frame: pd.DataFrame) -> "CycleMetrics":
        speed = frame["speed_ms"].to_numpy(dtype=float)
        accel = frame["acceleration_ms2"].to_numpy(dtype=float)
        moving = speed > 0.5
        positive_accel = accel[accel > 0.01]
        negative_accel = accel[accel < -0.01]
        distance_m = float(frame["distance_m"].iloc[-1])
        duration_s = float(frame["time_s"].iloc[-1])
        energy_j = energy_proxy_joules(frame)
        if distance_m > 0:
            energy_kwh_per_100km = energy_j / 3.6e6 / (distance_m / 100_000)
        else:
            energy_kwh_per_100km = 0.0
        return cls(
            avg_speed_kmh=float(speed.mean() * 3.6),
            max_speed_kmh=float(speed.max() * 3.6),
            avg_moving_speed_kmh=float(speed[moving].mean() * 3.6) if moving.any() else 0.0,
            idle_fraction=float((speed < 0.5).mean()),
            avg_accel_ms2=float(positive_accel.mean()) if positive_accel.size else 0.0,
            max_accel_ms2=float(positive_accel.max()) if positive_accel.size else 0.0,
            avg_decel_ms2=float(negative_accel.mean()) if negative_accel.size else 0.0,
            max_decel_ms2=float(negative_accel.min()) if negative_accel.size else 0.0,
            speed_std_kmh=float(speed.std(ddof=0) * 3.6),
            total_distance_km=distance_m / 1000,
            duration_s=duration_s,
            energy_proxy_kwh_per_100km=float(energy_kwh_per_100km),
        )

    def to_dict(self) -> dict[str, float]:
        return asdict(self)


def energy_proxy_joules(
    frame: pd.DataFrame,
    *,
    mass_kg: float = 1800.0,
    drag_coefficient: float = 0.28,
    frontal_area_m2: float = 2.3,
    rolling_resistance: float = 0.01,
    air_density_kgm3: float = 1.225,
) -> float:
    speed = frame["speed_ms"].to_numpy(dtype=float)
    accel = frame["acceleration_ms2"].to_numpy(dtype=float)
    grade = frame["road_grade_pct"].to_numpy(dtype=float) / 100
    gravity = 9.80665
    aerodynamic = 0.5 * air_density_kgm3 * drag_coefficient * frontal_area_m2 * speed**2
    rolling = mass_kg * gravity * rolling_resistance
    grade_force = mass_kg * gravity * grade
    inertia = mass_kg * accel
    power = (aerodynamic + rolling + grade_force + inertia) * speed
    return float(np.maximum(power, 0.0).sum())
