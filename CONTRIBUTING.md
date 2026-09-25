# Contributing

1. Create a focused branch.
2. Add or update tests for every behavior change.
3. Run pytest -q and python run_validation.py.
4. Do not describe synthetic output as measured validation.
5. Keep configuration, random seeds, and provider provenance visible.
6. Submit a pull request explaining scientific and software consequences.

Code should target Python 3.10+, follow the configured Ruff rules, and avoid
committing credentials, API responses containing personal data, or generated
results.
