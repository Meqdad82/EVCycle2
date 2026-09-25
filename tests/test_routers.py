from datetime import time

import numpy as np

from evcycle.models import RouteInput
from evcycle.routers import MockRouter


def test_mock_router_is_deterministic():
    request = RouteInput(
        origin=(39.9042, 116.4074),
        destination=(39.9592, 116.4584),
        departure_time=time(8, 0),
        day_of_week=1,
        month=1,
    )
    first = MockRouter().route(request)
    second = MockRouter().route(request)
    assert first.distance_m == second.distance_m
    assert first.duration_s == second.duration_s
    assert np.allclose(first.elevation_samples_m, second.elevation_samples_m)
