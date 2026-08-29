"""The README is checked by the suite, where prose drift hides.

`documentation/readme-standard.md` is `priority: required` and asks for
three things a human reviewer reliably fails to notice: the required
sections present in the prescribed order with exact heading text (:44),
a configuration table listing EVERY environment variable the component
reads (:65), and a link checker (:68).

The configuration-table check is the one that will actually earn its
place. The standard says at :65 that "New variables added in a PR
require the table to be updated in the same PR" - which is a rule with
no enforcement, and therefore a rule that decays on the first busy
afternoon. Here it fails the build instead.

These live in the suite rather than as a CI step so that `pytest` alone
catches them, and because the suite is where this project already floors
and audits its own checks.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "README.md"
CONFIG = ROOT / "src" / "fast_mcp_jobvite" / "config.py"

# : `readme-standard.md:44-58`, in the prescribed order. Title and the
# one-line : description are not `##` headings, and status badges are
# images directly under : the description, so the check starts at
# Quickstart.
REQUIRED_SECTIONS = [
    "Quickstart",
    "Installation",
    "Configuration",
    "Usage examples",
    "API / CLI reference link",
    "Development setup",
    "Testing",
    "Deployment",
    "Contributing",
    "License",
    "Maintainers",
]

LENGTH_CAP = 500  # readme-standard.md:63


def headings() -> list[str]:
    return re.findall(r"^## (.+)$", README.read_text(), re.M)


def test_the_readme_exists_and_the_rest_of_this_module_is_not_vacuous() -> None:
    """Without this, every check below passes on an empty file.

    A search at a path that does not exist returns a clean empty, which
    is indistinguishable from a real absence.
    """
    assert README.is_file(), "README.md is missing; every other test here is vacuous"
    assert README.read_text().strip(), "README.md is empty"
    assert CONFIG.is_file(), f"{CONFIG} is missing; the config-table check is vacuous"


def test_the_required_sections_are_present_in_the_prescribed_order() -> None:
    """readme-standard.md:44 - exact headings, prescribed order."""
    found = [h for h in headings() if h in REQUIRED_SECTIONS]
    missing = [s for s in REQUIRED_SECTIONS if s not in found]
    assert not missing, f"missing required sections: {missing}"
    assert found == REQUIRED_SECTIONS, (
        "sections are out of order.\n"
        f"  expected: {REQUIRED_SECTIONS}\n  found:    {found}"
    )


def test_every_env_var_the_server_reads_is_in_the_configuration_table() -> None:
    """readme-standard.md:65, the check most likely to fire.

    The variables are derived from `config.py` - the thing that actually
    reads them - not from `server.json`, which is a declaration that can
    itself drift. `pydantic-settings` maps a field `api_key` to
    `JOBVITE_API_KEY` via `env_prefix`, so the field names are
    reconstructed into their env spellings.
    """
    source = CONFIG.read_text()

    prefix = re.search(r'env_prefix\s*=\s*"([^"]+)"', source)
    assert prefix, "no env_prefix found in config.py; this check cannot be trusted"

    # Parse with `ast`, not a regex. The first version of this test used
    # `^ ([a-z_]+)\s*:` over everything after `class Settings`, which
    # ran past the end of the class and collected `try:`, `else:` and a
    # local annotation - inventing JOBVITE_TRY, JOBVITE_ELSE and
    # JOBVITE_REASONS. It failed loudly, which was luck: an
    # over-collecting parser produces false ALARMS, while an
    # under-collecting one produces a silent green. The guard below was
    # written against the second case and could not see the first.
    tree = ast.parse(source)
    settings = next(
        (
            n
            for n in ast.walk(tree)
            if isinstance(n, ast.ClassDef) and n.name == "Settings"
        ),
        None,
    )
    assert settings is not None, "no Settings class in config.py"

    fields = [
        node.target.id
        for node in settings.body
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)
    ]
    expected = {
        f"{prefix.group(1)}{f.upper()}" for f in fields if not f.startswith("_")
    }

    # Bounded on BOTH sides. A parser that collects too few yields a
    # vacuous green; one that collects too many yields a false alarm
    # that trains people to edit the test. `server.json` is an
    # independent declaration of the same surface, so disagreement
    # between the two is itself worth failing on.
    server_json = (ROOT / "server.json").read_text()
    declared = set(re.findall(r'"(JOBVITE_[A-Z0-9_]+)"', server_json))
    assert expected == declared, (
        "config.py and server.json disagree about the variable surface.\n"
        f"  read but undeclared: {sorted(expected - declared)}\n"
        f"  declared but unread: {sorted(declared - expected)}"
    )

    documented = set(re.findall(r"`(JOBVITE_[A-Z0-9_]+)`", README.read_text()))
    undocumented = sorted(expected - documented)

    assert not undocumented, (
        "these variables are read by config.py but absent from the README's "
        f"Configuration table: {undocumented}"
    )


def test_every_relative_link_resolves() -> None:
    """`readme-standard.md:68` - a broken link blocks merge.

    Only repo-relative links are checked. Network links are deliberately
    NOT fetched: a test that reaches the network is a test that fails on
    a train.
    """
    links = re.findall(r"\]\((\./[^)]+)\)", README.read_text())
    assert links, "no relative links found; this check would pass vacuously"

    dead = [link for link in links if not (ROOT / link[2:]).exists()]
    assert not dead, f"dead relative links: {sorted(set(dead))}"


def test_the_readme_is_within_the_length_cap() -> None:
    """readme-standard.md:63 - the 500-line cap."""
    lines = len(README.read_text().splitlines())
    assert lines <= LENGTH_CAP, f"README is {lines} lines, cap is {LENGTH_CAP}"


@pytest.mark.parametrize(
    "phrase",
    ["coming soon", "TBD", "lorem ipsum", "TODO:"],
)
def test_the_readme_contains_no_placeholder_prose(phrase: str) -> None:
    """`readme-standard.md:75-77` forbids these outright.

    Note what is NOT forbidden: saying plainly that something does not
    exist yet. "The server exposes no tool yet" is a statement of
    current behaviour and is the honest alternative to a "coming soon"
    heading over an empty section.
    """
    assert phrase.lower() not in README.read_text().lower(), (
        f"README contains placeholder prose: {phrase!r}"
    )


async def test_the_readme_tool_count_matches_the_server() -> None:
    """The README quotes `Tools: N`. N must be true.

    It said `Tools: 0` and stayed correct only because nothing had
    landed. When `search_jobs` landed the line became false, and every
    other check in this module still passed: the sections were present,
    the links resolved, nothing read as a placeholder. A number copied
    out of a command's output is a second enumeration of something the
    code already knows, and the copy is the half that rots.

    Counted through a real MCP client, the same way `test_server.py`
    counts, so it cannot drift with the CLI's output format.
    """
    import os
    from unittest import mock

    from fastmcp import Client

    from fast_mcp_jobvite.server import create_server

    stated = re.search(r"^\s*Tools:\s*(\d+)\s*$", README.read_text(), re.M)
    assert stated, "the README no longer quotes a `Tools: N` line"

    placeholders = {
        "JOBVITE_API_KEY": "placeholder",
        "JOBVITE_API_SECRET": "placeholder",
        "JOBVITE_FEED_KEY": "placeholder",
        "JOBVITE_FEED_SECRET": "placeholder",
        "JOBVITE_COMPANY_ID": "placeholder",
        "JOBVITE_TOOLS": "search_jobs",
    }
    with mock.patch.dict(os.environ, placeholders, clear=False):
        server = create_server()
        async with Client(server) as client:
            actual = len(await client.list_tools())

    assert int(stated.group(1)) == actual, (
        f"README says Tools: {stated.group(1)}, the server exposes {actual}. "
        "Re-run the inspect command in the README and paste its real output."
    )
