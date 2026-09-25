"""Monte Carlo and Sobol--Jansen utilities matching the R2 configuration."""

from __future__ import annotations

from collections.abc import Callable, Mapping
import warnings

import numpy as np
import pandas as pd
from scipy.stats import qmc


def monte_carlo_inputs(n: int = 500, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    return pd.DataFrame(
        {
            "departure_offset_min": rng.uniform(-30.0, 30.0, n),
            "elevation_offset_m": rng.uniform(-5.0, 5.0, n),
            "traffic_scale": rng.uniform(0.8, 1.2, n),
        }
    )


def run_monte_carlo(
    model: Callable[[Mapping[str, float]], Mapping[str, float]],
    n: int = 500,
    seed: int = 42,
) -> pd.DataFrame:
    rows = []
    for params in monte_carlo_inputs(n=n, seed=seed).to_dict(orient="records"):
        rows.append({**params, **model(params)})
    return pd.DataFrame(rows)


def sobol_jansen(
    model: Callable[[Mapping[str, float]], float],
    n_base: int = 1000,
    seed: int = 42,
) -> pd.DataFrame:
    """Estimate first- and total-order indices for traffic and grade inputs."""
    # Generate A and B as one 2d-dimensional Sobol design. Splitting a
    # consecutive 2d sequence into two blocks can retain unwanted dependence.
    sampler = qmc.Sobol(d=4, scramble=True, seed=seed)
    # The manuscript reports N=1000. SciPy recommends powers of two for balance,
    # but the warning is suppressed here to preserve the declared experiment.
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message="The balance properties of Sobol",
            category=UserWarning,
        )
        unit = sampler.random(n_base)
    a = unit[:, :2]
    b = unit[:, 2:]

    def transform(row: np.ndarray) -> dict[str, float]:
        return {
            "traffic_scale": 0.5 + row[0],
            "grade_coefficient": 0.5 + row[1],
        }

    f_a = np.asarray([model(transform(row)) for row in a], dtype=float)
    f_b = np.asarray([model(transform(row)) for row in b], dtype=float)
    variance = float(np.var(np.concatenate([f_a, f_b]), ddof=1))
    if variance <= 0:
        raise ValueError("model output variance must be positive")

    records = []
    names = ["traffic_scale", "grade_coefficient"]
    for index, name in enumerate(names):
        ab = a.copy()
        ab[:, index] = b[:, index]
        f_ab = np.asarray([model(transform(row)) for row in ab], dtype=float)
        first = 1.0 - np.mean((f_b - f_ab) ** 2) / (2.0 * variance)
        total = np.mean((f_a - f_ab) ** 2) / (2.0 * variance)
        records.append({"parameter": name, "S1": float(first), "ST": float(total)})
    return pd.DataFrame(records)