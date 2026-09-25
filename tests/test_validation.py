from datetime import time

from evcycle.validation import CaseStudy, CaseStudyRunner


def test_case_study_runner_exposes_r2_control_names():
    case = CaseStudy(
        name="test",
        origin=(39.9042, 116.4074),
        destination=(39.9592, 116.4584),
        departure_time=time(8, 0),
        day_of_week=1,
        month=1,
    )
    result = CaseStudyRunner([case], seed=42).run_all()[0]
    assert set(result.cycles) == {
        "EVCycle",
        "speed_state_control",
        "stop_cruise_control",
        "perturbed_profile_control",
    }
    assert all(len(frame) == len(result.cycles["EVCycle"]) for frame in result.cycles.values())
