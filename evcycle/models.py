"""Core data structures for EVCycle."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import time

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class RouteInput:
    """Validated origin--destination and temporal input."""

    origin: tuple[float, float]
    destination: tuple[float, float]
    departure_time: time
    day_of_week: int
    month: int
    route_id: str = "route"

    def __post_init__(self) -> None:
        for lat, lon in (self.origin, self.destination):
            if not -90 <= lat <= 90:
                raise ValueError("latitude must be between -90 and 90")
            if not -180 <= lon <= 180:
                raise ValueError("longitude must be between -180 and 180")
        if not 1 <= self.day_of_week <= 7:
            raise ValueError("day_of_week must be in 1..7")
        if not 1 <= self.month <= 12:
            raise ValueError("month must be in 1..12")


@dataclass(frozen=True)
class RouteData:
    """Router output used by the synthesis module."""

    distance_m: float
    duration_s: float
    nominal_speed_ms: float
    speed_limit_ms: float
    road_class: str
    distance_samples_m: np.ndarray
    elevation_samples_m: np.ndarray
    provider: str

    def __post_init__(self) -> None:
        if self.distance_m <= 0 or self.duration_s <= 0:
            raise ValueError("route distance and duration must be positive")
        if len(self.distance_samples_m) != len(self.elevation_samples_m):
            raise ValueError("distance and elevation sample arrays must align")


@dataclass(frozen=True)
class DrivingCycle:
    """One-second speed, elevation, grade, and distance trajectory."""

    time_s: np.ndarray
    speed_ms: np.ndarray
    elevation_m: np.ndarray
    acceleration_ms2: np.ndarray
    road_grade_pct: np.ndarray
    distance_m: np.ndarray
    provider: str = "unknown"

    def to_frame(self) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "time_s": self.time_s,
                "speed_ms": self.speed_ms,
                "speed_kmh": self.speed_ms * 3.6,
                "elevation_m": self.elevation_m,
                "acceleration_ms2": self.acceleration_ms2,
                "road_grade_pct": self.road_grade_pct,
                "distance_m": self.distance_m,
            }
        )
