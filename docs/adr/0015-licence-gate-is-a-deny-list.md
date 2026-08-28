# ADR-0015: The licence gate is a deny-list, and four packages sit on neither list

**Status:** Accepted
**Type:** Deviation

> **Accepted, not Proposed**, unlike ADR-0012 to 0014. Those three change `DESIGN.md` and are held
> while the plan repoints against the frozen object. This one changes no design text: it records a
> deviation from a standard and documents the gate that shipped in U0. Nothing is waiting on it.

## Context

`devops/quality-gates.md:288-292` gives an allow-list of five SPDX identifiers — `MIT`,
`Apache-2.0`, `BSD-2-Clause`, `BSD-3-Clause`, `ISC` — and `:306` says anything on neither the
allow-list nor the flag-list is *"Custom / unknown — Always flag for review"*.

**The allow-list cannot be applied as written, and the reason is spelling rather than policy.**
Measured against the frozen resolve of this repository, `pip-licenses` reports **fifteen distinct
licence strings for six actual licences**:

```
30  MIT                              11  Apache-2.0            1  MIT-0
15  MIT License                       3  BSD License           1  The Unlicense (Unlicense)
11  BSD-3-Clause                      2  Apache Software License   1  PSF-2.0
 1  BSD-2-Clause                      1  ISC                   1  Mozilla Public License 2.0 (MPL 2.0)
 1  ISC License (ISCL)                1  Apache-2.0 OR BSD-3-Clause
 1  Apache-2.0 OR BSD-2-Clause
```

`MIT` and `MIT License` are the same licence. `ISC` and `ISC License (ISCL)` are the same licence.
Python package metadata has never had a single canonical spelling, and `--allow-only` matches
strings. **A gate configured with the standard's five identifiers is red on its first run against a
clean tree, for a tree containing no licence anyone objects to.**

## Decision

**The licence gate ships as a deny-list over the flag-list, not as an allow-list over the
allow-list.** It fails on the licences `quality-gates.md` says require legal review and an ADR —
strong copyleft and non-OSI terms — and passes otherwise.

The gate is green today and its negative arm was verified: `--fail-on=MIT` exits 1, so the pass is
not vacuous. There is **no strong copyleft anywhere in the tree.**

## Four packages sit on neither list, and `:306` says to flag them

| Package | Licence | Ships at runtime? | Assessment |
|---|---|---|---|
| `cffi` | `MIT-0` | **Yes** | MIT with the attribution requirement removed. Strictly more permissive than `MIT`, which is allow-listed. |
| `email-validator` | `Unlicense` | **Yes** | Public-domain dedication. More permissive than anything on the allow-list. |
| `typing_extensions` | `PSF-2.0` | **Yes** | The Python Software Foundation licence — the licence of CPython itself, which every Python program already depends on. |
| `pathspec` | `MPL-2.0` | **No** | Weak copyleft, file-level. **Dev and build only** — confirmed absent from `uv export --no-dev`, so it is not in anything we distribute. |

**None is a problem, and the point of this ADR is that saying so is a decision rather than an
observation.** `:306` requires them flagged; this is the flag, and the review is recorded rather
than skipped. The three runtime licences are each *more* permissive than the allow-list's own
entries. The one weak-copyleft package is not shipped, and MPL-2.0's obligations are file-level and
attach to distribution of the covered files.

## What this ADR does not do

**It does not extend the allow-list.** Adding `MIT-0`, `Unlicense` and `PSF-2.0` to
`quality-gates.md` is a change to the standards corpus and belongs there, raised as a defect against
that document — not decided unilaterally by one project. This ADR records why our gate deviates and
what the deviation admits.

**It does not solve the spelling problem generally.** A normalising layer between `pip-licenses`
output and SPDX identifiers would let the allow-list be used as written, and that is the better
long-term fix. It is not built here, because building a licence-string normaliser to satisfy a gate
is a larger and more error-prone artifact than the gate.

## Consequences

- **The gate is weaker than the standard intends.** A deny-list admits any licence nobody thought to
  deny; an allow-list admits only what was approved. That is the real cost and it is why this is an
  ADR rather than a configuration note. A new dependency arriving under an unusual permissive
  licence passes silently today.
- **The four-package table above is a dated claim** about a specific resolve. Re-derive it when the
  lock changes; it is not a standing property of the project.
- **`pip-licenses` is a dev dependency, so the gate is CI-only** and does not run for a consumer
  installing the package.

## How this was found

U0 was told to stand up the licence gate from `quality-gates.md`. It tried, measured the tree, and
reported that the standard's allow-list is red on a clean checkout — then landed the deny-list and
flagged the open half rather than either forcing a red gate or quietly widening the list until it
went green.

**The second of those is the failure this ADR exists to prevent.** Widening an allow-list until CI
passes is indistinguishable, in the final configuration, from having reviewed each licence — and
nothing in the repository would have recorded which of the two happened.
