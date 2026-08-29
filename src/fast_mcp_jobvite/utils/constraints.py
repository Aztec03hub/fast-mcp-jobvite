"""Shared inbound constraint types for input models (ADR-0012).

**Every input model imports its constraints from here. No input model
defines its own** - DESIGN.md:302-306 and ADR-0012, which is
**Accepted** and applied into SS3's module block at the freeze.

**Why the rule exists.** ADR-0012 records that housing the input
models without housing their validators re-runs the ownership
ambiguity one layer down: three units write input models, and a
control-character rule copied into each of them is three rules that
must agree. The duplication is "the first thing an implementer would
factor out on sight", so the module is specified rather than left to
whoever noticed.

**What a violation looks like to a caller: nothing shaped like a
problem object.** DESIGN.md:548-568 is explicit that every check here
lives in the input models, therefore runs **before the tool body**,
and is raised by the framework - so by SS5.1's own reasoning (a
problem object is safe precisely because it is *returned* rather than
*raised*) none of these rejections can return one. That is SS5.1's
third exception, not an exception to it. The rule still **fails
closed**, which is the whole of what B25 and B30 require.

**Why the character rule is not covered by `max_length` or by the
output allow-list** (DESIGN.md:176-183). A name carrying a NUL or a
bidi override is a well-formed short string, so every length and
regex check passes it. The allow-list is an **output** filter and
SS6.1's fencing applies on the way back out, so neither reaches an
inbound argument on its way to Jobvite.

**Scope actually built here, stated rather than implied.** This module
holds the **character rule** of DESIGN.md:172-175. The three
structural limits of DESIGN.md:162-164 - nesting depth 5, 1,000 list
items, 100 dict keys - are **not here**, because no input model in the
tree today is deeper than one flat object, so the code would have no
caller and no reachable test. Writing an unreachable limit and a test
that cannot exercise it is worse than recording the gap: it would read
as discharged. The gap is filed as its own task.
"""

from __future__ import annotations

import re
from typing import Annotated, Final

from pydantic import Field, StringConstraints

#: C0 and C1 control characters, **except** tab, newline and carriage
#: return, which DESIGN.md:181-183 names as the three permitted ones.
#: `\x7f` (DEL) sits between the two ranges and is included.
_CONTROL_CHARACTERS: Final = r"\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f"

#: Unicode bidirectional overrides and isolates. A bidi override in a
#: string argument re-orders how a reviewer or a model reads the rest
#: of the line while leaving the bytes intact, which is why
#: DESIGN.md:181-183 names it beside the control characters rather
#: than leaving it to `max_length`.
#:
#: LRE/RLE/PDF/LRO/RLO, then LRI/RLI/FSI/PDI.
_BIDI_OVERRIDES: Final = "‪-‮⁦-⁩"

#: The one rule every inbound string is tested against. Matching means
#: **rejection**, so it is used as a negative lookahead below rather
#: than as a validator that has to be remembered at each call site.
FORBIDDEN_CHARACTERS: Final = re.compile(f"[{_CONTROL_CHARACTERS}{_BIDI_OVERRIDES}]")

#: A pattern admitting only strings that contain no forbidden
#: character. `\A` and `\z` rather than `^`/`$`: in Python `$` also
#: matches before a trailing newline, so `^...$` would admit a string
#: ending in one - and a trailing newline in a field that reaches a
#: log line is the log-forging shape C7-T1 records.
#:
#: **`\z`, not `\Z`, and this was MEASURED rather than transcribed.**
#: pydantic-core compiles patterns with the Rust `regex` crate, which
#: has no `\Z` and refuses the pattern at class-construction time:
#: `SchemaError: regex parse error ... unrecognized escape sequence`.
#: Python's own `re` spells the same anchor `\Z`, so a pattern copied
#: from Python docs fails here and a pattern copied from here would be
#: wrong in a `re.compile`. `FORBIDDEN_CHARACTERS` below is the Python
#: engine's copy and is a character class, which both engines spell
#: identically.
_NO_FORBIDDEN = f"\\A(?:(?![{_CONTROL_CHARACTERS}{_BIDI_OVERRIDES}]).)*\\z"

#: Default ceiling for a free-form string argument. DESIGN.md:156
#: requires an explicit `max_length` on **every** string; this is the
#: value a field takes when it has no tighter reason of its own.
MAX_TEXT_LENGTH: Final = 256

#: Ceiling for a Jobvite identifier. `eId` is an opaque 8-character
#: identifier (DESIGN.md:471-473), and the ceiling is deliberately
#: looser than 8 because the width is `[INFERRED]` in the research and
#: a tighter bound would refuse a valid id on our own guess.
MAX_IDENTIFIER_LENGTH: Final = 64

#: A string argument: length-bounded, and free of control characters
#: and bidi overrides. **`strip_whitespace` is deliberately NOT set** -
#: silently rewriting an argument before validating it means the value
#: Jobvite receives is not the value the caller sent, and the audit
#: event would record the rewritten one.
SafeText = Annotated[
    str,
    StringConstraints(
        max_length=MAX_TEXT_LENGTH,
        pattern=_NO_FORBIDDEN,
    ),
]

#: A Jobvite identifier: alphanumerics, hyphen and underscore only.
#: DESIGN.md:156 requires a regex on **every** identifier, and this
#: one admits no character the forbidden set covers, so it discharges
#: the character rule by construction rather than by composition.
JobviteIdentifier = Annotated[
    str,
    StringConstraints(
        min_length=1,
        max_length=MAX_IDENTIFIER_LENGTH,
        pattern=r"\A[A-Za-z0-9_-]+\z",
    ),
]

#: A bounded positive count, for any argument that names a quantity.
PositiveCount = Annotated[int, Field(ge=1)]
