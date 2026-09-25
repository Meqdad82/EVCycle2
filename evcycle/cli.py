"""Command-line interface."""

from __future__ import annotations

from pathlib import Path

import click

from evcycle.api import generate_cycle


@click.group()
def main() -> None:
    """Generate route-based EV driving-cycle inputs."""


@main.command()
@click.option("--lat-start", type=float, required=True)
@click.option("--lon-start", type=float, required=True)
@click.option("--lat-end", type=float, required=True)
@click.option("--lon-end", type=float, required=True)
@click.option("--departure-time", default="08:00", show_default=True)
@click.option("--day-of-week", default="monday", show_default=True)
@click.option("--month", type=int, default=1, show_default=True)
@click.option("--router", default="mock", show_default=True)
@click.option("--seed", type=int, default=42, show_default=True)
@click.option("--output", type=click.Path(path_type=Path), default=Path("cycle.csv"))
def generate(
    lat_start: float,
    lon_start: float,
    lat_end: float,
    lon_end: float,
    departure_time: str,
    day_of_week: str,
    month: int,
    router: str,
    seed: int,
    output: Path,
) -> None:
    """Generate one cycle and save a CSV file."""
    frame = generate_cycle(
        lat_start=lat_start,
        lon_start=lon_start,
        lat_end=lat_end,
        lon_end=lon_end,
        departure_time=departure_time,
        day_of_week=day_of_week,
        month=month,
        router=router,
        seed=seed,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output, index=False)
    click.echo(f"saved {len(frame)} samples to {output}")


if __name__ == "__main__":
    main()
