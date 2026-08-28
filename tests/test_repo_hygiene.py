"""DESIGN.md §8 case #3 - `.gitignore` covers the credential patterns, and
`.env.example` carries no real value.

Asserted against the COMMITTED files, because the row this covers (C8-I1) is about
what reaches the repository rather than what reaches a log.

**What this test must NOT assert, and why the negative statement is the important
half.** Draft 2 of the plan said "every value in `.env.example` is empty". That is
false against the committed tree and it is dangerous. Seven of the fifteen variables
carry a value; eight are empty, and only SIX of those eight are secret-class -
`JOBVITE_TOOLS` and `JOBVITE_PAGINATION_START_BASE` are empty non-secrets. The
cheapest way to make "every value is empty" pass is to empty
`JOBVITE_MAX_RESULTS=50` and `JOBVITE_OUTBOUND_RATE_LIMIT=6`, which un-answers the
design's Q1 and re-blocks U1, U6 and U7 (PLAN-REVIEW-R2.md:255-270).

So the assertion is keyed on SECRET-CLASS, not on emptiness, and the deliberate
non-secret defaults are pinned positively so that an agent "fixing" the tree by
emptying them turns this red instead of green.
"""

from __future__ import annotations

import re

from .conftest import ENV_EXAMPLE, GITIGNORE

# DESIGN.md:1504-1509 counts five credential variables; §7.2 adds JOBVITE_HTTP_TOKENS,
# the bearer-token map, as the sixth secret-class name. Six, enumerated here and
# cross-checked against the file below so the list cannot silently go stale.
SECRET_CLASS = [
    "JOBVITE_API_KEY",
    "JOBVITE_API_SECRET",
    "JOBVITE_FEED_KEY",
    "JOBVITE_FEED_SECRET",
    "JOBVITE_COMPANY_ID",
    "JOBVITE_HTTP_TOKENS",
]

# Deliberate values. Emptying either is a regression, not a cleanup.
NON_SECRET_DEFAULTS = {
    "JOBVITE_MAX_RESULTS": "50",
    "JOBVITE_OUTBOUND_RATE_LIMIT": "6",
    "JOBVITE_MCP_TRANSPORT": "stdio",
    "JOBVITE_MCP_HOST": "127.0.0.1",
    "JOBVITE_MCP_PORT": "8000",
    "JOBVITE_ENABLE_WRITES": "false",
    "JOBVITE_TLS_TERMINATED_BY_PROXY": "false",
}

CREDENTIAL_PATTERNS = [".env", ".env.*", "*.key", "*.pem", "secrets/"]


def _declared_variables() -> dict[str, str]:
    """Parse `.env.example` into name -> value. Derived from the file, never remembered."""
    out: dict[str, str] = {}
    for line in ENV_EXAMPLE.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        match = re.match(r"^([A-Z0-9_]+)=(.*)$", stripped)
        assert match, f"unparseable line in .env.example: {line!r}"
        out[match.group(1)] = match.group(2).strip()
    return out


def test_the_parser_actually_found_variables() -> None:
    """Positive control on the instrument.

    Every assertion below iterates a dict this parser produced. A parser that
    matched nothing would make all of them pass vacuously.
    """
    variables = _declared_variables()
    assert len(variables) == 15, (
        f"expected the design's fifteen variables, parsed {len(variables)}: {sorted(variables)}"
    )


def test_every_secret_class_variable_is_empty() -> None:
    variables = _declared_variables()
    missing = [name for name in SECRET_CLASS if name not in variables]
    assert not missing, f".env.example does not declare {missing}"
    carrying = {name: variables[name] for name in SECRET_CLASS if variables[name] != ""}
    assert not carrying, f"secret-class variables carrying a value: {carrying}"


def test_the_deliberate_non_secret_defaults_are_intact() -> None:
    """The guard against 'fixing' the tree by emptying values that answer Q1."""
    variables = _declared_variables()
    wrong = {
        name: (variables.get(name), expected)
        for name, expected in NON_SECRET_DEFAULTS.items()
        if variables.get(name) != expected
    }
    assert not wrong, f"non-secret defaults changed (got, expected): {wrong}"


def test_no_value_in_env_example_looks_like_a_real_credential() -> None:
    """DESIGN.md:1222 - no REAL value.

    A placeholder that looks like a credential is the thing a reader copies by
    accident and a scanner mistakes for a finding.
    """
    variables = _declared_variables()
    suspicious = {
        name: value for name, value in variables.items() if name in SECRET_CLASS or len(value) >= 20
    }
    offenders = {name: value for name, value in suspicious.items() if value != ""}
    assert not offenders, f"values that could be mistaken for credentials: {offenders}"


def test_gitignore_covers_every_credential_pattern() -> None:
    entries = {
        line.strip()
        for line in GITIGNORE.read_text().splitlines()
        if line.strip() and not line.strip().startswith("#")
    }
    missing = [pattern for pattern in CREDENTIAL_PATTERNS if pattern not in entries]
    assert not missing, f".gitignore does not cover {missing}"


def test_gitignore_does_not_negate_the_credential_patterns() -> None:
    """`!.env.example` is the one legal negation; any other un-ignores a credential.

    Ignoring `.env.*` and then re-including something under it would restore
    exactly the hole the pattern list exists to close, and a membership check over
    the entries above cannot see a `!` line.
    """
    negations = {
        line.strip() for line in GITIGNORE.read_text().splitlines() if line.strip().startswith("!")
    }
    assert negations == {"!.env.example"}, f"unexpected gitignore negations: {negations}"
