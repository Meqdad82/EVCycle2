# R2 release checklist

- [ ] Copy this folder's contents to the GitHub repository root.
- [ ] Remove EVCycle_v2.0_code.zip after confirming the unpacked files exist.
- [ ] Confirm pyproject.toml and CITATION.cff both report version 1.0.0.
- [ ] Run python -m pip install -e ".[dev]".
- [ ] Run pytest -q.
- [ ] Run python run_validation.py.
- [ ] Inspect all generated CSV and PNG files.
- [ ] Confirm README claims match implemented provider behavior.
- [ ] Commit the unpacked source.
- [ ] Record the new full commit hash.
- [ ] Create annotated tag v1.0.0 and a GitHub release.
- [ ] Replace the old manuscript hash with the new release commit.
- [ ] Optionally archive the release with Zenodo or Software Heritage.
