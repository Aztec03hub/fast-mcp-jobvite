# The credentialed suite

Tests here need a real Jobvite credential. **CI never runs them and never skips them.**
They are excluded by *selection* - the `credentialed` marker, deselected by the
`-m` in `[tool.pytest.ini_options].addopts` - because a skip counts as a failure
(`DESIGN.md:1185-1188`).

**CI does `--collect-only` against them** (`DESIGN.md:1200-1205`). A suite that is
excluded and never collected rots silently: an import error or a renamed fixture in
it is invisible until the day someone finally has a credential.

## The contract for a unit adding an arm here

- Mark it `@pytest.mark.credentialed`. `--strict-markers` is on, so a typo in that
  name is a collection error rather than a test that quietly selects nothing.
- It must still **import and collect** with no credential present. Read credentials
  inside the test body, never at module scope.
- Read fixtures from `docs/research/fixtures/` via `tests/conftest.py`'s
  `FIXTURES_DIR`. Do not copy them here.

## This directory is empty today, and that is a real gap

U0 writes no credentialed arm, so the collect step currently has nothing to collect
and passes on pytest's exit code 5 ("no tests collected") as well as 0. **That means
it cannot presently distinguish "the suite is empty" from "the suite is healthy."**
The first unit to add an arm here should tighten `.github/workflows/ci.yml`'s
`collect-credentialed` step to require exit 0 and a non-zero collected count.
