from evcycle import CycleMetrics, generate_cycle


def test_metrics_are_finite_and_consistent():
    frame = generate_cycle(
        lat_start=31.2304,
        lon_start=121.4737,
        lat_end=31.2904,
        lon_end=121.5937,
        departure_time="10:30",
        day_of_week=3,
        month=6,
        router="mock",
        seed=42,
    )
    metrics = CycleMetrics.from_frame(frame)
    assert metrics.avg_speed_kmh > 0
    assert metrics.max_speed_kmh >= metrics.avg_speed_kmh
    assert 0 <= metrics.idle_fraction <= 1
    assert metrics.total_distance_km > 0
    assert metrics.energy_proxy_kwh_per_100km >= 0
