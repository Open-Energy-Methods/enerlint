# Contributing (draft)

Contributions should first identify a physical equation, sign conventions,
required output fields, numerical tolerances and a reference case independent
of the implementation. Each added check must include a correct baseline,
a deliberately incorrect case, and an explicitly documented undetectable case
or limitation. Prefer public benchmark material with documented licenses.

Run `python -m pip install -e ".[dev]"` then `python -m pytest -q`.

Before opening a pull request, describe:

1. What physics and boundary assumptions are checked?
2. Which errors are detected, and which remain untested?
3. Which input/provenance rights permit reproduction?
4. What independent numerical reference supports expected outputs?
5. Is your example synthetic, externally sourced, or measured?

Do not claim certifications, safety guarantees or validation beyond the tests.
