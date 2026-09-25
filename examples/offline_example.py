"""Credential-free EVCycle example."""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from evcycle import CycleMetrics, generate_cycle


output = Path(__file__).with_name("offline_cycle.csv")
cycle = generate_cycle(
    lat_start=39.9042,
    lon_start=116.4074,
    lat_end=39.9592,
    lon_end=116.4584,
    departure_time="08:00",
    day_of_week="monday",
    month=1,
    router="mock",
    seed=42,
)
cycle.to_csv(output, index=False)
print(CycleMetrics.from_frame(cycle))
print(f"saved {output}")