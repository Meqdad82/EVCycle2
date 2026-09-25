"""Rule-based conversion of route metadata to a one-second driving cycle."""

from __future__ import annotations

import numpy as np

from evcycle.models import DrivingCycle, RouteData, RouteInput


def traffic_factor(request: RouteInput, multiplier: float = 1.0) -> float:
    """Return the explicit time/day heuristic used by the offline workflow."""
    hour = request.departure_time.hour + request.departure_time.minute / 60
    if 7 <= hour < 9.5 or 16 <= hour < 19:
        value = 0.72
    elif 9.5 <= hour < 21:
        value = 0.88
    else:
        value = 0.97
    if request.day_of_week >= 6:
        value = min(1.0, value + 0.08)
    return float(np.clip(value * multiplier, 0.25, 1.5))


def _desired_idle_fraction(request: RouteInput, road_class: str) -> float:
    hour = request.departure_time.hour + request.departure_time.minute / 60
    if road_class == "highway":
        return 0.285
    if request.day_of_week >= 6:
        return 0.265
    if hour >= 21 or hour < 5:
        return 0.178
    if road_class == "urban" and (7 <= hour < 9.5 or 16 <= hour < 19):
        return 0.557
    if road_class == "suburban":
        return 0.233
    return 0.30


def _apply_stop_and_ramp_rules(
    speed: np.ndarray,
    request: RouteInput,
    road_class: str,
    rng: np.random.Generator,
) -> np.ndarray:
    result = speed.copy()
    n = len(result)
    result[:2] = 0.0
    result[-2:] = 0.0

    desired_zero = max(2, int(round(_desired_idle_fraction(request, road_class) * n)))
    dwell = 20
    block_count = max(1, int(np.ceil(desired_zero / dwell)))
    boundaries = np.linspace(dwell, max(dwell, n - dwell), block_count, dtype=int)
    remaining = desired_zero - 2
    for center in boundaries:
        if remaining <= 0:
            break
        current_dwell = min(dwell, remaining)
        left = max(0, center - dwell // 2)
        right = min(n, left + current_dwell)
        result[left:right] = 0.0
        remaining -= right - left

    zero = result <= 1e-12
    changes = np.diff(zero.astype(int), prepend=0, append=0)
    starts = np.flatnonzero(changes == 1)
    ends = np.flatnonzero(changes == -1)
    for start, end in zip(starts, ends):
        transition = 5 if road_class == "highway" else int(rng.integers(5, 21))
        for offset in range(1, transition + 1):
            fraction = offset / transition
            after = end - 1 + offset
            before = start - offset
            if after < n and not zero[after]:
                result[after] *= fraction
            if before >= 0 and not zero[before]:
                result[before] *= fraction
    return result


def _integrate_distance(speed_ms: np.ndarray) -> np.ndarray:
    increments = (speed_ms[:-1] + speed_ms[1:]) * 0.5
    return np.concatenate(([0.0], np.cumsum(increments)))


def _reconcile_distance(
    speed_ms: np.ndarray,
    target_distance_m: float,
    speed_limit_ms: float,
    tolerance_m: float,
) -> np.ndarray:
    result = speed_ms.copy()
    movable = result > 0
    for _ in range(80):
        distance = _integrate_distance(result)[-1]
        error = target_distance_m - distance
        if abs(error) <= tolerance_m:
            break
        if distance <= 0:
            raise ValueError("cannot reconcile distance for an all-zero profile")
        factor = target_distance_m / distance
        result[movable] = np.clip(result[movable] * factor, 0.0, speed_limit_ms)
        movable = (result > 0) & (result < speed_limit_ms - 1e-9)
        if not np.any(movable):
            break
    return result


def synthesize_cycle(
    route: RouteData,
    request: RouteInput,
    *,
    seed: int = 42,
    traffic_multiplier: float = 1.0,
    grade_coefficient: float = 1.0,
    elevation_offset_m: float = 0.0,
    distance_tolerance_m: float = 5.0,
) -> DrivingCycle:
    """Implement the documented stop, transition, mean, time, distance, and cap rules."""
    rng = np.random.default_rng(seed)
    n = max(3, int(round(route.duration_s)) + 1)
    time_s = np.arange(n, dtype=float)

    phase = np.linspace(0.0, 6.0 * np.pi, n)
    variation = 1.0 + 0.10 * np.sin(phase) + 0.04 * np.sin(phase * 2.7)
    target = route.nominal_speed_ms * traffic_factor(request, traffic_multiplier) * variation

    provisional_distance = np.linspace(0.0, route.distance_m, n)
    provisional_elevation = np.interp(
        provisional_distance,
        route.distance_samples_m,
        route.elevation_samples_m,
    )
    error_phase = (seed % 360) * np.pi / 180.0
    elevation_error = elevation_offset_m * np.sin(
        np.linspace(0.0, 4.0 * np.pi, n) + error_phase
    )
    provisional_elevation = provisional_elevation + elevation_error
    delta_d = np.diff(provisional_distance, prepend=provisional_distance[0])
    delta_h = np.diff(provisional_elevation, prepend=provisional_elevation[0])
    grade = np.zeros(n)
    valid = delta_d > 1e-9
    grade[valid] = 100.0 * delta_h[valid] / delta_d[valid]
    grade = np.clip(grade, -20.0, 20.0)
    target *= np.maximum(0.0, 1.0 - grade_coefficient * grade / 100.0)
    target = np.clip(target, 0.0, route.speed_limit_ms)

    speed_ms = _apply_stop_and_ramp_rules(target, request, route.road_class, rng)
    speed_ms = _reconcile_distance(
        speed_ms,
        route.distance_m,
        route.speed_limit_ms,
        distance_tolerance_m,
    )
    speed_ms[0] = 0.0
    speed_ms[-1] = 0.0

    distance_m = _integrate_distance(speed_ms)
    elevation_m = np.interp(
        np.minimum(distance_m, route.distance_m),
        route.distance_samples_m,
        route.elevation_samples_m,
    )
    normalized_distance = np.minimum(distance_m / max(route.distance_m, 1.0), 1.0)
    elevation_m = elevation_m + elevation_offset_m * np.sin(
        4.0 * np.pi * normalized_distance + error_phase
    )

    delta_d = np.diff(distance_m, prepend=distance_m[0])
    delta_h = np.diff(elevation_m, prepend=elevation_m[0])
    road_grade_pct = np.zeros(n)
    valid = delta_d > 0.5
    road_grade_pct[valid] = 100.0 * delta_h[valid] / delta_d[valid]
    road_grade_pct = np.clip(road_grade_pct, -20.0, 20.0)
    acceleration_ms2 = np.diff(speed_ms, prepend=speed_ms[0])

    return DrivingCycle(
        time_s=time_s,
        speed_ms=speed_ms,
        elevation_m=elevation_m,
        acceleration_ms2=acceleration_ms2,
        road_grade_pct=road_grade_pct,
        distance_m=distance_m,
        provider=route.provider,
    )