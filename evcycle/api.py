"""Public Python API."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, time

import pandas as pd

from evcycle.models import RouteInput
from evcycle.routers import get_router
from evcycle.synthesis import synthesize_cycle


_WEEKDAYS = {
    "monday": 1,
    "tuesday": 2,
    "wednesday": 3,
    "thursday": 4,
    "friday": 5,
    "saturday": 6,
    "sunday": 7,
}


def _parse_time(value: str | time) -> time:
    if isinstance(value, time):
        return value
    return datetime.strptime(value, "%H:%M").time()


def _parse_weekday(value: str | int) -> int:
    if isinstance(value, int):
        return value
    try:
        return _WEEKDAYS[value.strip().lower()]
    except KeyError as exc:
        raise ValueError(f"unknown weekday: {value}") from exc


def generate_cycle(
    *,
    lat_start: float,
    lon_start: float,
    lat_end: float,
    lon_end: float,
    departure_time: str | time,
    day_of_week: str | int,
    month: int,
    router: str = "mock",
    seed: int = 42,
    route_id: str = "route",
    traffic_multiplier: float = 1.0,
    grade_coefficient: float = 1.0,
    elevation_offset_m: float = 0.0,
) -> pd.DataFrame:
    """Generate a one-second cycle and return it as a DataFrame."""
    request = RouteInput(
        origin=(lat_start, lon_start),
        destination=(lat_end, lon_end),
        departure_time=_parse_time(departure_time),
        day_of_week=_parse_weekday(day_of_week),
        month=int(month),
        route_id=route_id,
    )
    route_data = get_router(router).route(request)
    if traffic_multiplier <= 0:
        raise ValueError("traffic_multiplier must be positive")
    # Treat the uncertain traffic multiplier as a travel-time modifier. This
    # makes its effect visible even though distance reconciliation is enforced.
    route_data = replace(
        route_data,
        duration_s=route_data.duration_s / traffic_multiplier,
    )
    cycle = synthesize_cycle(
        route_data,
        request,
        seed=seed,
        traffic_multiplier=1.0,
        grade_coefficient=grade_coefficient,
        elevation_offset_m=elevation_offset_m,
    )
    frame = cycle.to_frame()
    frame.attrs.update(
        {
            "route_id": route_id,
            "router": route_data.provider,
            "seed": seed,
            "target_distance_m": route_data.distance_m,
            "target_duration_s": route_data.duration_s,
        }
    )
    return frame