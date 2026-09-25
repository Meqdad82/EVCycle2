# Usage

## Offline Python example

Run:

~~~bash
python examples/offline_example.py
~~~

The example writes examples/offline_cycle.csv and prints descriptive metrics.

## Validation benchmark

~~~bash
python run_validation.py
~~~

The three controls are:

- speed-state control: a seeded first-order discrete-state generator;
- stop--cruise control: stops, constant cruise plateaus, and linear ramps;
- perturbed-profile control: a seeded perturbation of the stop--cruise signal.

They exercise code paths and plotting. They are not accuracy baselines.

## Uncertainty example

~~~bash
python examples/uncertainty_example.py
~~~

This runs a small demonstration. The manuscript sample counts are declared in
configs/uq_r2.yaml and should be used for archived release results.
