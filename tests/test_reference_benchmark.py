from run_validation import CASES

from evcycle.validation import CaseStudyRunner


def test_fixed_seed_aggregate_regression_values():
    runner = CaseStudyRunner(CASES, seed=42)
    frame = runner.results_to_dataframe(runner.run_all())
    aggregate = frame.groupby("method")[
        ["avg_speed_kmh", "max_speed_kmh", "idle_fraction", "speed_std_kmh"]
    ].mean()
    expected = {
        "EVCycle": (39.73, 67.06, 0.305, 27.55),
        "speed_state_control": (54.11, 119.88, 0.359, 48.81),
        "stop_cruise_control": (56.18, 108.31, 0.215, 39.46),
        "perturbed_profile_control": (56.27, 113.59, 0.291, 42.05),
    }
    for method, values in expected.items():
        actual = aggregate.loc[method].to_numpy()
        for observed, target in zip(actual, values):
            assert abs(observed - target) < 0.03
