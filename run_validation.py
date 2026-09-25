#!/usr/bin/env python3
"""Run the fixed-seed offline R2 software benchmark.

The comparison signals are internal controls. They do not establish agreement
with measured driving or rank the scientific accuracy of cycle-development
methods.
"""

from __future__ import annotations

from datetime import time
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from evcycle.validation import CaseStudy, CaseStudyRunner


ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
RESULTS.mkdir(parents=True, exist_ok=True)

CASES = [
    CaseStudy(
        name="Urban short commute",
        origin=(39.9042, 116.4074),
        destination=(39.9592, 116.4584),
        departure_time=time(8, 0),
        day_of_week=1,
        month=1,
    ),
    CaseStudy(
        name="Suburban medium-distance trip",
        origin=(31.2304, 121.4737),
        destination=(31.2904, 121.5937),
        departure_time=time(10, 30),
        day_of_week=3,
        month=6,
    ),
    CaseStudy(
        name="Long highway trip",
        origin=(22.5431, 114.0579),
        destination=(23.1291, 113.2644),
        departure_time=time(14, 0),
        day_of_week=5,
        month=9,
    ),
    CaseStudy(
        name="Night-time urban delivery",
        origin=(30.5728, 104.0668),
        destination=(30.6328, 104.1668),
        departure_time=time(22, 0),
        day_of_week=4,
        month=11,
    ),
    CaseStudy(
        name="Weekend suburban trip",
        origin=(23.1291, 113.2644),
        destination=(23.0291, 113.4144),
        departure_time=time(9, 0),
        day_of_week=6,
        month=4,
    ),
]

DISPLAY = {
    "EVCycle": "EVCycle",
    "speed_state_control": "Speed-state",
    "stop_cruise_control": "Stop-cruise",
    "perturbed_profile_control": "Perturbed",
}

COLORS = {
    "EVCycle": "#3776a3",
    "speed_state_control": "#e67e22",
    "stop_cruise_control": "#4ca154",
    "perturbed_profile_control": "#c94c4c",
}


def write_summary(df: pd.DataFrame) -> None:
    aggregate = df.groupby("method")[
        [
            "avg_speed_kmh",
            "max_speed_kmh",
            "idle_fraction",
            "speed_std_kmh",
            "total_distance_km",
            "duration_s",
        ]
    ].agg(["mean", "std"])
    text = [
        "EVCycle R2 offline software benchmark",
        "=" * 44,
        "",
        "Internal controls are regression signals, not accuracy baselines.",
        "",
        aggregate.to_string(),
        "",
    ]
    (RESULTS / "case_study_summary.txt").write_text("\n".join(text), encoding="utf-8")


def plot_speed_profiles(results: list) -> None:
    fig, axes = plt.subplots(len(results), 1, figsize=(11, 13), dpi=300)
    for ax, result in zip(axes, results):
        for method, frame in result.cycles.items():
            ax.plot(
                frame["time_s"],
                frame["speed_kmh"],
                color=COLORS[method],
                label=DISPLAY[method],
                linewidth=0.55,
                alpha=0.85,
            )
        ax.set_title(result.case_name, fontsize=11, fontweight="bold")
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Speed (km/h)")
        ax.grid(alpha=0.25)
        ax.legend(loc="upper right", fontsize=7)
    fig.tight_layout()
    fig.savefig(RESULTS / "speed_profiles_comparison.png", dpi=300)
    plt.close(fig)


def plot_bar_comparison(df: pd.DataFrame) -> None:
    metrics = [
        ("avg_speed_kmh", "Mean speed (km/h)"),
        ("max_speed_kmh", "Maximum speed (km/h)"),
        ("idle_fraction", "Idle fraction"),
        ("speed_std_kmh", "Speed SD (km/h)"),
    ]
    methods = list(DISPLAY)
    fig, axes = plt.subplots(2, 2, figsize=(12.5, 8.3), dpi=300)
    fig.suptitle("EVCycle and internal-control metrics", fontsize=18, fontweight="bold")
    x = np.arange(len(methods))
    for ax, (metric, title) in zip(axes.flat, metrics):
        grouped = df.groupby("method")[metric]
        means = np.asarray([grouped.mean().get(method, 0.0) for method in methods])
        stds = np.asarray([grouped.std().get(method, 0.0) for method in methods])
        bars = ax.bar(
            x,
            means,
            yerr=stds,
            capsize=5,
            color=[COLORS[m] for m in methods],
            edgecolor="black",
            linewidth=0.5,
        )
        ax.set_title(title, fontsize=14, fontweight="bold")
        ax.set_xticks(x, [DISPLAY[m] for m in methods], rotation=12)
        ax.grid(axis="y", alpha=0.25)
        ax.set_axisbelow(True)
        for bar, mean in zip(bars, means):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height(),
                f"{mean:.2f}",
                ha="center",
                va="bottom",
                fontsize=9,
            )
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(RESULTS / "metrics_bar_comparison.png", dpi=300)
    plt.close(fig)


def main() -> None:
    runner = CaseStudyRunner(CASES, seed=42)
    results = runner.run_all()
    frame = runner.results_to_dataframe(results)
    frame.to_csv(RESULTS / "case_study_metrics.csv", index=False)
    write_summary(frame)
    plot_speed_profiles(results)
    plot_bar_comparison(frame)
    print(f"Completed {len(CASES)} offline cases.")
    print(f"Results: {RESULTS}")


if __name__ == "__main__":
    main()
