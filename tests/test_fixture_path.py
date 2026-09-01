"""The fixture path resolves, and U4 asserts byte-exact on it.

This is a positive control on the SEARCH ITSELF, not decoration. A test
that globs a path that does not exist returns a clean empty list and
passes every "nothing unexpected here" assertion written over it. Every
later unit's fixture reads go through `conftest.FIXTURES_DIR`, so if
that path is ever wrong, this is the test that says so instead of
fifteen downstream suites quietly asserting against nothing.
"""

from __future__ import annotations

from .conftest import FIXTURES_DIR

# Enumerated from the committed tree, not remembered.
# DESIGN.md:1332-1337 puts these in three tiers: recorded (byte-exact
# captures of real Jobvite error transport), structural (the one genuine
# 200), and synthetic.
EXPECTED_FIXTURES = {
    "candidate_create_success.json",
    "candidate_list_empty.json",
    "candidate_list_injection.json",
    "candidate_list_success.json",
    "error_auth_200_body401.json",
    "error_auth_401.json",
    "error_route_404.json",
    "error_task_400.html",
    "error_v1_auth_401.txt",
    "job_list_empty.json",
    "job_list_success.json",
    "jobfeed_empty.json",
    "jobfeed_success.json",
    "malformed_not_json.txt",
    "malformed_truncated.json",
}


def test_fixtures_directory_resolves() -> None:
    assert FIXTURES_DIR.is_dir(), (
        f"{FIXTURES_DIR} does not exist. Every fixture read in this suite would "
        f"return a clean empty rather than an error."
    )


def test_every_expected_fixture_is_present() -> None:
    on_disk = {p.name for p in FIXTURES_DIR.iterdir() if p.is_file()}
    assert EXPECTED_FIXTURES <= on_disk, (
        f"missing: {sorted(EXPECTED_FIXTURES - on_disk)}"
    )


def test_fixtures_are_readable_and_non_empty() -> None:
    """A zero-byte fixture satisfies a presence check, nothing more."""
    empty = [
        name
        for name in sorted(EXPECTED_FIXTURES)
        if (FIXTURES_DIR / name).stat().st_size == 0
    ]
    assert not empty, f"zero-byte fixtures: {empty}"
