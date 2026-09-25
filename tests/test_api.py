import numpy as np

from evcycle import generate_cycle


def _cycle(seed=42):
    return generate_cycle(
        lat_start=39.9042,
        lon_start=116.4074,
        lat_end=39.9592,
        lon_end=116.4584,
        departure_time="08:00",
        day_of_week="monday",
        month=1,
        router="mock",
        seed=seed,
    )


def test_offline_cycle_schema_and_bounds():
    frame = _cycle()
    assert list(frame.columns) == [
        "time_s",
        "speed_ms",
        "speed_kmh",
        "elevation_m",
        "acceleration_ms2",
        "road_grade_pct",
        "distance_m",
    ]
    assert len(frame) > 60
    assert np.allclose(np.diff(frame["time_s"]), 1.0)
    assert (frame["speed_ms"] >= 0).all()
    assert frame["speed_kmh"].max() <= 120.0 + 1e-6
    assert frame["distance_m"].is_monotonic_increasing


def test_cycle_is_deterministic_for_fixed_seed():
    first = _cycle(seed=7)
    second = _cycle(seed=7)
    assert np.allclose(first["speed_ms"], second["speed_ms"])
    assert np.allclose(first["elevation_m"], second["elevation_m"])


def test_distance_matches_router_target_within_three_percent():
    frame = _cycle()
    target = frame.attrs["target_distance_m"]
    actual = frame["distance_m"].iloc[-1]
    assert abs(actual - target) / target < 0.03
