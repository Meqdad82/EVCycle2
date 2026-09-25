"""Small uncertainty-interface demonstration."""

from pathlib import Path
import sys
from datetime import datetime, timedelta

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from evcycle import CycleMetrics, generate_cycle
from evcycle.uncertainty import run_monte_carlo


def model(params):
    departure = datetime(2026, 1, 5, 8, 0) + timedelta(
        minutes=params["departure_offset_min"]
    )
    frame = generate_cycle(
        lat_start=39.9042,
        lon_start=116.4074,
        lat_end=39.9592,
        lon_end=116.4584,
        departure_time=departure.strftime("%H:%M"),
        day_of_week="monday",
        month=1,
        router="mock",
        seed=42,
        traffic_multiplier=params["traffic_scale"],
        elevation_offset_m=params["elevation_offset_m"],
    )
    metrics = CycleMetrics.from_frame(frame)
    return {
        "mean_speed_kmh": metrics.avg_speed_kmh,
        "idle_fraction": metrics.idle_fraction,
        "energy_proxy": metrics.energy_proxy_kwh_per_100km,
    }


results = run_monte_carlo(model, n=20, seed=42)
output = Path(__file__).with_name("uncertainty_results.csv")
results.to_csv(output, index=False)
print(results.describe())
print(f"saved {output}")