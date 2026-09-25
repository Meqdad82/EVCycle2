import numpy as np

from evcycle.uncertainty import monte_carlo_inputs, sobol_jansen


def test_monte_carlo_ranges_and_seed():
    first = monte_carlo_inputs(n=25, seed=42)
    second = monte_carlo_inputs(n=25, seed=42)
    assert first.equals(second)
    assert first["departure_offset_min"].between(-30, 30).all()
    assert first["elevation_offset_m"].between(-5, 5).all()
    assert first["traffic_scale"].between(0.8, 1.2).all()


def test_sobol_jansen_returns_two_parameters():
    def model(params):
        return 2.0 * params["traffic_scale"] + 0.5 * params["grade_coefficient"]

    result = sobol_jansen(model, n_base=32, seed=42)
    assert list(result["parameter"]) == ["traffic_scale", "grade_coefficient"]
    assert np.isfinite(result[["S1", "ST"]].to_numpy()).all()
    assert result.loc[0, "ST"] > result.loc[1, "ST"]
