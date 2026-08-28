"""Third-party action pins, across EVERY workflow rather than the one being edited.

`devops/ci-cd.md:81` pins `actions/checkout@v6`, and COMPLIANCE-SPEC-PASS's C-1 named
the drift. The fix commit `5519032` said `checkout is now @v6 in all five places` and
was right about its own count - `ci.yml` had grown a fifth checkout by then, so five
were changed. **`mirror.yml:28` was the sixth and was not among them**, and stayed
`@v4` while the project believed C-1 closed. A later reviewer found it.

**Why the miss was structural rather than careless.** The implementation plan's
shared-file table named `.github/workflows/ci.yml` and nothing else, so `mirror.yml`
and `pr-title.yml` were owned by nobody and read by nobody. A rule naming one file in
a directory selects for the files it does not name.

So this test's subject is **the directory**, not a file list. Adding a workflow puts
it under this guard automatically; that is the entire point, and it is why the walk is
a glob rather than the three names that happen to exist today.

Scope: pins for actions this project has taken a position on. It deliberately does not
assert a pin for every action - `astral-sh/setup-uv@v5` is a RECORDED DEVIATION from
the standard's `@v4` (ADR-0016, Accepted), and a test that mechanically enforced the
standard here would go red on a decision the project made on purpose.
"""

from __future__ import annotations

import re

from .conftest import REPO_ROOT

WORKFLOWS = REPO_ROOT / ".github" / "workflows"

# action -> the ref this project requires. Each needs a reason, not just a value.
REQUIRED_PINS = {
    # devops/ci-cd.md:81. C-1's population was six, and the fix reached five.
    "actions/checkout": "v6",
    # A moving ref is untrustworthy third-party code with commit access to our CI.
    # This was `@main` until a review caught it.
    "trufflesecurity/trufflehog": "v3.88.0",
}

_USES = re.compile(r"^\s*-?\s*uses:\s*([^@\s]+)@(\S+)", re.MULTILINE)


def _pins() -> list[tuple[str, str, str]]:
    """Every `uses: owner/action@ref` in the workflow directory, with its file."""
    found: list[tuple[str, str, str]] = []
    for path in sorted(WORKFLOWS.glob("*.yml")) + sorted(WORKFLOWS.glob("*.yaml")):
        for action, ref in _USES.findall(path.read_text()):
            found.append((path.name, action, ref))
    return found


def test_the_walk_found_workflows_and_pins() -> None:
    """Positive control on the instrument.

    Both assertions below filter a list this walk produced. A glob that matched no
    files, or a regex that matched no `uses:` line, would make them pass vacuously -
    which is the failure mode this whole module exists to catch one level up.
    """
    pins = _pins()
    assert pins, "no `uses:` pins found at all - the walk or the regex is broken"
    files = {name for name, _, _ in pins}
    assert "mirror.yml" in files, (
        "the walk missed mirror.yml, which is the exact file the last sweep missed - "
        f"saw: {sorted(files)}"
    )


def test_every_pinned_action_is_at_the_required_ref() -> None:
    """No workflow in the directory may drift from a pin the project has decided."""
    wrong = [
        f"{name}: {action}@{ref} (required @{REQUIRED_PINS[action]})"
        for name, action, ref in _pins()
        if action in REQUIRED_PINS and ref != REQUIRED_PINS[action]
    ]
    assert not wrong, "workflow action pins have drifted:\n  " + "\n  ".join(wrong)


def test_no_action_is_pinned_to_a_moving_ref() -> None:
    """`@main` or `@master` on a third-party action is arbitrary code at merge time.

    Broader than the table above, because the danger does not depend on the project
    having formed an opinion about the specific action first.
    """
    moving = [
        f"{name}: {action}@{ref}"
        for name, action, ref in _pins()
        if ref in {"main", "master", "latest", "HEAD"}
    ]
    assert not moving, "actions pinned to a moving ref:\n  " + "\n  ".join(moving)
