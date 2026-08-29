"""Tool bodies and their INPUT models (DESIGN.md:289-290).

An input model lives beside its tool, never under `models/` - that
package holds the allow-listed **output** models only. The shared
inbound constraints every input model reuses come from
`utils/constraints.py` (ADR-0012).
"""

from __future__ import annotations
