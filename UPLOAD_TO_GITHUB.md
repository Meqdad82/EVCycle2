# Upload this unpacked R2 source to GitHub

## Recommended command-line workflow

Clone the existing repository, then copy the contents of this folder into the
clone. Do not copy this parent folder as an extra nested directory; pyproject.toml
must remain at the repository root.

~~~bash
git clone https://github.com/Meqdad82/EVCycle2.git
cd EVCycle2

# Copy all files from "EVCycle GitHub R2" into this directory.
# Then remove the obsolete binary archive:
git rm EVCycle_v2.0_code.zip

python -m pip install -e ".[dev]"
pytest -q
python run_validation.py

git add .
git commit -m "release: unpack and document EVCycle 1.0.0 R2 source"
git tag -a v1.0.0 -m "EVCycle 1.0.0"
git push origin main
git push origin v1.0.0
~~~

Create a GitHub release from tag v1.0.0 after the push.

## Required manuscript update

The upload creates a new commit. Replace the old hash
a8975bb1166eb441bb1679618f20a160e583a8b0 in:

- EVCycle R2/manuscript_R2_content.tex
- EVCycle R2/Response_Letter_R2.tex
- EVCycle R2/README_R2.md
- EVCycle R2/GITHUB_R2_ACTIONS.md

Recompile the clean manuscript, highlighted manuscript, and response letter
after inserting the new full commit hash.

## GitHub web-interface alternative

If Git is unavailable, use Add file > Upload files in the repository. Upload
the root files first, then create the evcycle, tests, configs, examples,
reference_results, and .github/workflows directories and upload their contents.
Delete EVCycle_v2.0_code.zip only after confirming that the unpacked package and
tests are visible.
