# Installation

## Requirements

- Python 3.10 or later
- Linux, macOS, or Windows

## Editable installation

~~~bash
python -m pip install -e ".[dev]"
~~~

Verify the unpacked source tree:

~~~bash
pytest -q
python run_validation.py
~~~

MockRouter is the documented offline path and requires no credentials.

## Optional online routing

The OpenRouteService adapter requires ORS_API_KEY:

~~~bash
export ORS_API_KEY="replace-with-your-key"
evcycle generate ... --router ors
~~~

The OSRM public endpoint requires no key but is rate-limited. Online provider
responses can change and are not used for the fixed manuscript benchmark.
