# EVCycle

EVCycle is an MIT-licensed Python package for producing one-second electric-
vehicle speed and grade profiles from a route description. The package is
intended for simulation-input preparation, teaching, software regression
tests, and sensitivity studies.

This R2 source tree makes the manuscript scope explicit:

- the navigation-data conversion procedure is an implementation of a
  published approach, not a new driving-cycle theory;
- traffic and grade transformations are visible engineering assumptions;
- MockRouter provides deterministic offline examples;
- the included comparison signals are internal controls, not measured
  validation or canonical implementations of Markov, micro-trip, or
  stochastic cycle-development methods.

No measured GPS or telematics dataset is included. Generated cycles must not be
described as validated real-world driving without an external comparison.

## Quick offline workflow

From the repository root:

~~~bash
python -m pip install -e ".[dev]"
pytest -q
python run_validation.py
~~~

The validation script uses MockRouter and does not require credentials. It
creates:

- results/case_study_metrics.csv
- results/case_study_summary.txt
- results/speed_profiles_comparison.png
- results/metrics_bar_comparison.png

Versioned copies from the verified run supplied with this folder are in
reference_results/.

For this reconstructed source tree, the fixed-seed aggregate means are
approximately:

| Signal | Mean speed (km/h) | Maximum speed (km/h) | Idle fraction | Speed SD (km/h) |
| --- | ---: | ---: | ---: | ---: |
| EVCycle | 39.73 | 67.06 | 0.305 | 27.55 |
| Speed-state control | 54.11 | 119.88 | 0.359 | 48.81 |
| Stop--cruise control | 56.18 | 108.31 | 0.215 | 39.46 |
| Perturbed-profile control | 56.27 | 113.59 | 0.291 | 42.05 |

The original ZIP implementation was unavailable when this unpacked source was
prepared. After uploading and tagging this tree, use its generated CSV as the
source of truth and update any manuscript value that differs.

## Python API

~~~python
from evcycle import generate_cycle

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

cycle.to_csv("beijing_mock_cycle.csv", index=False)
~~~

The output columns are:

| Column | Unit | Meaning |
| --- | --- | --- |
| time_s | s | Elapsed time at 1 Hz |
| speed_ms | m/s | Non-negative vehicle speed |
| speed_kmh | km/h | Vehicle speed |
| elevation_m | m | Interpolated route elevation |
| acceleration_ms2 | m/s2 | First difference of speed |
| road_grade_pct | % | Elevation change divided by distance change |
| distance_m | m | Cumulative distance |

## Command line

~~~bash
evcycle generate \
  --lat-start 39.9042 --lon-start 116.4074 \
  --lat-end 39.9592 --lon-end 116.4584 \
  --departure-time 08:00 --day-of-week monday --month 1 \
  --router mock --seed 42 --output cycle.csv
~~~

## Traffic and grade assumptions

MockRouter returns route distance, duration, road class, speed cap, and a
deterministic elevation profile. EVCycle applies:

- a documented time/day traffic scalar;
- a configurable grade-response coefficient;
- explicit stop and transition bounds;
- iterative distance reconciliation and speed-cap enforcement.

These are transparent synthesis rules, not observations of a driver or local
traffic state.

## Uncertainty configuration

The manuscript configuration is stored in configs/uq_r2.yaml:

- Monte Carlo: 500 independent realizations, seed 42; the sampled elevation
  value is used as the amplitude of a spatially correlated error profile;
- Sobol--Jansen: 1000 base samples, two independent inputs, second-order
  indices disabled, 4000 model evaluations, seed 42.

## Repository release steps

This folder replaces the inaccessible binary ZIP with editable source.
Before journal resubmission:

1. copy these files to the repository root;
2. remove EVCycle_v2.0_code.zip;
3. run the offline workflow on a clean checkout;
4. commit the results;
5. create the v1.0.0 tag and release;
6. replace the old commit hash in the R2 manuscript and response letter with
   the new release commit.

See RELEASE_CHECKLIST.md and SOURCE_PROVENANCE.md.
For copy and push commands, see UPLOAD_TO_GITHUB.md.


## License

MIT. See LICENSE.