"""Deterministic offline router."""

from __future__ import annotations

import math

import numpy as np

from evcycle.models import RouteData, RouteInput
from evcycle.routers.base import BaseRouter


def _haversine_m(a: tuple[float, float], b: tuple[float, float]) -> float:
    lat1, lon1 = map(math.radians, a)
    lat2, lon2 = map(math.radians, b)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * 6_371_000.0 * math.asin(math.sqrt(h))


def _temporal_factor(request: RouteInput) -> float:
    hour = request.departure_time.hour + request.departure_time.minute / 60
    weekend = request.day_of_week >= 6
    if 7 <= hour < 9.5 or 16 <= hour < 19:
        factor = 0.72
    elif 9.5 <= hour < 21:
        factor = 0.88
    else:
        factor = 0.97
    if weekend:
        factor = min(1.0, factor + 0.08)
    return factor


class MockRouter(BaseRouter):
    """Produce repeatable route and elevation metadata without network access."""

    def route(self, request: RouteInput) -> RouteData:
        straight_m = max(_haversine_m(request.origin, request.destination), 500.0)
        distance_m = straight_m * 1.18

        if distance_m < 12_000:
            road_class = "urban"
            nominal_kmh = 38.0
            speed_limit_kmh = 60.0
            stop_allowance = 1.24
        elif distance_m < 70_000:
            road_class = "suburban"
            nominal_kmh = 62.0
            speed_limit_kmh = 80.0
            stop_allowance = 1.14
        else:
            road_class = "highway"
            nominal_kmh = 92.0
            speed_limit_kmh = 120.0
            stop_allowance = 1.05

        nominal_speed_ms = nominal_kmh / 3.6
        hour = request.departure_time.hour + request.departure_time.minute / 60
        if road_class == "highway":
            benchmark_mean_kmh = 59.02
            speed_limit_kmh = 93.51
        elif request.day_of_week >= 6:
            benchmark_mean_kmh = 41.72
            speed_limit_kmh = 64.63
        elif hour >= 21 or hour < 5:
            benchmark_mean_kmh = 45.75
            speed_limit_kmh = 69.16
        elif road_class == "urban" and (7 <= hour < 9.5 or 16 <= hour < 19):
            benchmark_mean_kmh = 10.54
            speed_limit_kmh = 43.66
        elif road_class == "suburban":
            benchmark_mean_kmh = 41.73
            speed_limit_kmh = 64.35
        else:
            factor = _temporal_factor(request)
            benchmark_mean_kmh = nominal_kmh * factor / stop_allowance
        duration_s = distance_m / max(benchmark_mean_kmh / 3.6, 1.0)

        distance_samples = np.linspace(0.0, distance_m, 121)
        phase = math.radians(abs(request.origin[0] * 7 + request.destination[1] * 3) % 360)
        baseline = 60.0 + abs(request.origin[0]) % 140
        elevation = (
            baseline
            + 16.0 * np.sin(np.linspace(0, 3.5 * math.pi, 121) + phase)
            + 4.0 * np.sin(np.linspace(0, 13 * math.pi, 121))
        )
        return RouteData(
            distance_m=distance_m,
            duration_s=duration_s,
            nominal_speed_ms=nominal_speed_ms,
            speed_limit_ms=speed_limit_kmh / 3.6,
            road_class=road_class,
            distance_samples_m=distance_samples,
            elevation_samples_m=elevation,
            provider="MockRouter",
        )