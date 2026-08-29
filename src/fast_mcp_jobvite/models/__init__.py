"""Allow-listed OUTPUT models, one file per tool (DESIGN.md:291).

No input model lives here. Input models sit beside their tool in
`tools/`, and their shared constraints come from `utils/constraints.py`
(ADR-0012).

**One file per tool, never a shared module.** Two tools sharing an
output module is the collision the plan's SS4 ownership table exists to
prevent, and an output model is the surface most likely to be widened
by a unit that does not own it.
"""

from __future__ import annotations
