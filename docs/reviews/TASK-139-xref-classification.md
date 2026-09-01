# Task #139 - all 46 unresolved `§n.m` references, read and classified

Branch `fix/139-refs`, cut from `fix/139-xref-population` at `f05ba94`.
Not a code review: no `REVIEW-COVERS` declaration, because this document reviews
citations in prose, not a commit range.

## What I measured, before any fix

Population re-derived, not taken from the brief: tracked `*.md`, minus
`docs/worklogs/`, `docs/plans/`, `docs/reviews/`, `docs/briefs/` and
`CHANGELOG.md` - **54 files**. Referent `docs/DESIGN.md` for `docs/adr/*`, `None`
otherwise. Script committed at `scratch139/measure.py`.

**46 unresolved across 8 files. The brief's per-file figures were all correct**,
which is the first time today a re-measurement has agreed:

| File | Brief | Measured |
|---|---|---|
| `docs/data-inventory.md` | 15 | 15 |
| `docs/research/FASTMCP.md` | 15 | 15 |
| `docs/adr/0022-...` | 4 | 4 |
| `docs/research/STANDARDS.md` | 4 | 4 |
| `docs/research/JOBVITE-CONTRACT.md` | 3 | 3 |
| `docs/adr/0017-...` | 2 | 2 |
| `docs/adr/0019-...` | 2 | 2 |
| `docs/adr/0030-...` | 1 | 1 |

**But 46 is not the cost of widening, and this is the brief's one wrong number.**
`unresolved()` raises `ValueError("no numbered headings found at all")` for
**12 of the 54 files**, and `check()` turns each into a `failures.append` - a red
line, not a skip. Widening `DEFAULT_TARGETS` to this population therefore costs
**58 failure lines: 46 unresolved references plus 12 heading-set refusals.**
Two of those 12 carry section references that no instrument would ever read -
`docs/README.md` (4: `§13`, `§11`, `§11`, `§11`) and
`docs/CREDENTIAL-CHECKLIST.md:45` (1: `§7.2`, `§7.2`, `§1.1`) - so widening as
stated would report 12 files as broken while leaving 5 real references
unchecked. The referent is what makes an ADR checkable (#139's own fix); the
same is true of these.

## The verdict table - all 46

Four verdicts were offered. **Two of them were never used, and two categories
the brief did not name account for 21 of the 46.** Nothing here is STALE
(no reference points at a renumbered section) and nothing is GENUINELY BROKEN
(no reference names a section existing nowhere).

### WRONG REFERENT - 19

Both files cite `docs/DESIGN.md` throughout and were given referent `None`.
**Measured: with referent `docs/DESIGN.md`, both go to zero unresolved.**
Every target read and confirmed on subject.

| Site | Ref | Target in `DESIGN.md` | Subject checked |
|---|---|---|---|
| `docs/data-inventory.md:30` | §2.1 | `2.1 Tool schemas` | allow-listed output models |
| `docs/data-inventory.md:43` | §6.1 | `6.1 Candidate free text is attacker-authored` | fencing before a model |
| `docs/data-inventory.md:67` | §7.7 | `7.7 Middleware` | `ResponseCachingMiddleware` rejected |
| `docs/data-inventory.md:69` | §5.3 | `5.3 Audit logging and request_id` | the audit event |
| `docs/data-inventory.md:80` | §7.2 | `7.2 Authentication and scopes` | bearer token, three scopes |
| `docs/data-inventory.md:81` | §4.1 | `4.1 Authentication, and three credential classes` | single-point redaction |
| `docs/data-inventory.md:82` | §4.1 | same | header credentials, never in a URL |
| `docs/data-inventory.md:91` | §7.1 | `7.1 Transport` | transport |
| `docs/data-inventory.md:91` | §7.2 | `7.2 Authentication and scopes` | authentication and scoping |
| `docs/data-inventory.md:91` | §2.1 | `2.1 Tool schemas` | allow-listed output models |
| `docs/data-inventory.md:92` | §6.1 | `6.1 ...attacker-authored` | fencing |
| `docs/data-inventory.md:92` | §4.1 | `4.1 Authentication...` | single-point redaction |
| `docs/data-inventory.md:92` | §5.3 | `5.3 Audit logging...` | audit logging |
| `docs/data-inventory.md:93` | §11 | `11. Threat model` | rates the disclosure paths |
| `docs/data-inventory.md:102` | §1.1 | `1.1 The constraint that shapes everything` | "**One** genuine Jobvite 200 exists" |
| `docs/research/STANDARDS.md:159` | §2.1 | `2.1 Tool schemas` | "regex on every identifier", control-character rejection - both present at `DESIGN.md:153` and `:172` |
| `docs/research/STANDARDS.md:624` | §7.2 | `7.2 Authentication and scopes` | the unverifiable read-only key |
| `docs/research/STANDARDS.md:645` | §11 | `11. Threat model` | the S/T/R/I/D/E grid |
| `docs/research/STANDARDS.md:1077` | §11 | `11. Threat model` | same grid |

**Suggested fix, and it is Tier 0's because it changes the gate:** add
`"docs/data-inventory.md": "docs/DESIGN.md"` and
`"docs/research/STANDARDS.md": "docs/DESIGN.md"` to `DEFAULT_TARGETS`. I did not
edit either document: naming `DESIGN.md` on 19 prose lines is noise where the
referent is the whole point, and `data-inventory.md`'s own §7 is literally
titled "Security measures, by reference".

### CROSS-DOCUMENT - 22, all FIXED in the document

**`docs/research/FASTMCP.md`, 15 sites.** Every one is a `[SPIKE §n]` tag, a
shorthand declared at `:7-8` and pointing at `FASTMCP-SPIKE-4.md`. All fifteen
targets read and confirmed on subject: §1.1 install/resolve, §1.2 httpx→httpx2,
§1.3 packaging recipe, §3.1 sessionless default (x2), §3.3 dual-era, §9.1
lifespan composition, §10.1 Python matrix, §13.1 RateLimiting default,
§13.3 Retry refuted, §14.1 D4 verdict, §14.2 ErrorHandling × RFC 9457,
§14.4 Ping inert, §19.5 SIGTERM replacement, §13 (middleware round 1).
Sites: `:22 :23 :24 :29 :36 :41 :72 :79 :81 :415 :489 :494 :495 :498 :503`.

**`docs/adr/0022-...`, 4 sites** (`:31 :80 :91 :94`), all `§2.3` of
`JOBVITE-CONTRACT.md` - "2.3 Response headers" at `:81`, established by the
ADR's own `:9`. Read: it carries the `Set-Cookie: AWSALBAPP-*` `_remove_`
observation, the other four headers, and the "no rate-limit header of any kind"
finding - all three things the four citing lines claim of it.

**`docs/adr/0019-...:59`**, `§5.4` - the pre-ADR `DESIGN.md`. Fixed by naming
the file: `` `:603` `` → `` `DESIGN.md:603` ``.

**Fix applied**, per the `_EXEMPT` comment's own precedent: the citation now
names the file, so no exemption is needed and a reader following the pointer
arrives somewhere. 46 → 23.

### QUOTATION OF A REPAIRED DEFECT - 1, deliberately NOT fixed

`docs/adr/0019-...:15` quotes the broken `DESIGN.md` line verbatim inside a
blockquote. **The reference is supposed to be unresolvable - it is the defect
the ADR exists to record**, and the ADR's fix (`§5.4` → `§4.1`) has landed:
`grep -n '§5\.4' docs/DESIGN.md` returns nothing, and `:678` now reads `(§4.1)`.
Naming the file inside the quotation would falsify the quotation.
**Suggested fix: an `_EXEMPT` entry** keyed on the content `"jobFeed` URL is
itself a secret"`, if and when this file becomes a target. I did not add one:
`_EXEMPT` is consulted per `name`, so an entry for a file not in
`DEFAULT_TARGETS` is inoperative code.

### EXTERNAL STANDARD, NOT A DOCUMENT SECTION - 3, correct as written

`_REFERENCE` matches `§` anywhere; `_NAMES_A_DOCUMENT` only matches `*.md`. So
an RFC section citation is reported as a broken internal one:

- `docs/adr/0017-...:31` and `:60` - **RFC 9457 §4.2.1** (`about:blank` for
  unmapped HTTP errors). Correct: that is the section of RFC 9457 defining it.
- `docs/adr/0030-...:58` - **RFC 9457 §3.2** (extension members). Correct.

**Suggested fix, Tier 0's:** in `unresolved()`, `continue` on a line matching
`RFC\s*\d+`, alongside the existing `_NAMES_A_DOCUMENT` skip - an RFC is another
document this checker does not read. **`:60` is already covered by that rule;
`:31` was not**, because the blockquote wrapped between "RFC" and "9457 §4.2.1",
leaving the reference on a line naming nothing. **I rewrapped that quote** so the
citation and its RFC stay on one line. The words of the quotation are unchanged.

### STALE - 0.   GENUINELY BROKEN - 0.

## The finding the checker cannot see: 8 references that RESOLVE and are WRONG

`FASTMCP.md` and `FASTMCP-SPIKE-4.md` both number their sections from 1. Eight
`[SPIKE §n]` tags named a single-digit section that **exists in FASTMCP.md too**,
so the checker accepted them - pointing the reader at the wrong text:

| Site | Tag | Intended (`FASTMCP-SPIKE-4.md`) | Resolved to (`FASTMCP.md`) |
|---|---|---|---|
| `:25` | §7 | `7. Transport, path, client styles` | `7. Lifespan` |
| `:26` | §4 | `4. Auth refusals` | `4. Resources, templates, prompts` |
| `:27` | §5 | `5. ToolError vs plain exception × masking` | `5. Authentication` |
| `:28` | §10 | `10. fastmcp.json and required env vars` | `10. Deployment, packaging, CLI` |
| `:47` | §2 | `2. Does fastmcp.server.lifespan survive 4.0?` | `2. Server construction` |
| `:80` | §3 | `3. Sessionless 2026-07-28 protocol` | `3. Tools` |
| `:489` | §6 | `6. Middleware` | `6. Transports` |
| `:846` | §3 | `3. Sessionless 2026-07-28 protocol` | `3. Tools` |

Each intended target was read and matches the citing sentence; each resolved
target does not. **This is exactly what the brief warned of - a citation that
resolves is not a citation that is correct** - and it was invisible from the
unresolved list, which is why the 15 flagged sites and these 8 silent ones were
both fixed by the same edit. The legend at `:7-8` now says why a bare number is
unsafe here.

`:848`'s `§11` is a genuine SELF reference (`11. Deprecations and breaking
changes`) and was left alone; its `[SPIKE]` tag carries no section number.

## The other correction: `ADR-0019` had the wrong line number in three places

The ADR's title, `:13` and `:40` all said `DESIGN.md:605`. Its filename and its
own `:59` said 603. Settled against the blob the ADR itself names:

    git show 135c3ac:docs/DESIGN.md | grep -n '§5\.4'
    603:line carries the URL, because the v1 `jobFeed` URL is itself a secret (§5.4)...

**603 is right, 605 was wrong, three sites corrected in place.** No gate could
have caught this: `check-design-citation-shape.py` reads `DESIGN.md:N` against
the CURRENT design, and this citation is deliberately against a historical blob.

## What I changed

- `docs/research/FASTMCP.md` - 23 `[SPIKE §n]` tags → `[FASTMCP-SPIKE-4.md §n]`,
  legend at `:7-8` rewritten in place.
- `docs/adr/0022-...` - 4 lines now name `JOBVITE-CONTRACT.md`.
- `docs/research/JOBVITE-CONTRACT.md` - `§13.1/§13.2/§13.4` → `§13 row 1/2/4`.
  §13 is a table of ten numbered ROWS, not subsections, so these could never
  resolve. All three verified against the row they mean: row 1 settles whether a
  success body carries a `status` block (`:143`), row 4 the record-level
  not-found shape (`:161`), row 2 the `start` base (`:189`).
- `docs/adr/0019-...` - 605 → 603 at three sites; `:59` now names `DESIGN.md`.
- `docs/adr/0017-...` - one blockquote line rewrapped.
- `scratch139/` - the measurement and edit scripts, so both replay.

**Result: 46 → 23 unresolved.** The 23 are the 19 wrong-referent, the 3 RFC
references and the 1 deliberate quotation - **none of which is fixable in the
document.** All three remaining classes need a decision on the checker.

## What I deliberately did NOT do

- **Did not widen `DEFAULT_TARGETS` and wired nothing.**
- **Did not add an `_EXEMPT` entry.** For a file outside `DEFAULT_TARGETS` it is
  inoperative code; `_EXEMPT` is keyed on `name`.
- **Did not edit `data-inventory.md` or `STANDARDS.md`.** Their defect is the
  referent, not the prose.
- **Did not touch `docs/DESIGN.md`**; verified unmodified against the freeze
  (`git hash-object` = `639f4b7...` = `git rev-parse 5d17cd7:docs/DESIGN.md`).
- Did not go near `fmj-worktrees/tally-shapes` or `tally-rebuild`.
- Spawned **zero Tier-2 workers**: 46 citations in 8 files is one measurement
  script and eight reads, and a pane costs more than that.

## Gates, exit codes one per line

    0    python3 docs/reviews/check-cross-references.py
    0    python3 docs/reviews/check-cross-references.py --controls   (3/3 fired)
    0    python3 docs/reviews/check-design-citation-shape.py
    0    python3 docs/reviews/check-clause-citations.py
    0    python3 docs/reviews/check-standards-citations.py
    0    python3 docs/reviews/check-design-freeze.py
    0    python3 docs/reviews/check-coupling.py docs/DESIGN.md
    0    python3 docs/reviews/check-checkers-are-wired.py
    0    python3 docs/reviews/check-adr-numbers.py
    0    python3 docs/reviews/check-design-citations.py
    0    python3 docs/reviews/check-obligations.py
    0    python3 docs/reviews/check-resweep-verdicts.py
    0    python3 docs/reviews/check-coupling-sweep.py
    0    python3 docs/reviews/check-coupling-controls.py
    0    python3 docs/reviews/check-env-vars-are-declared.py
    0    python3 docs/reviews/check-no-errexit.py
    0    python3 docs/reviews/check-no-sigpipe-pipelines.py
    1    python3 docs/reviews/check-plan-measurements.py      <- INTERPRETER, not me
    0    uv run --frozen python docs/reviews/check-plan-measurements.py

The default `check-cross-references.py` run is non-vacuous: 34/15/24 numbered
headings and 337/164/20 references across its three targets.

**The exit-1 is the bare interpreter, not this branch.** Under `python3` it
reports M3 and M4 STALE; under `uv run --frozen python` all four PASS and it
exits 0. `ci.yml:572` invokes it as `python3`, which is the same
inherited-not-chosen interpreter defect task #46 fixed in four other places.
It touches no file I edited.

## What I could NOT settle

- **Whether `docs/research/STANDARDS.md`'s referent should be `DESIGN.md`.** All
  four of its references resolve there and are on subject, so mechanically yes -
  but STANDARDS.md is a survey of an external corpus, and declaring the design
  its referent is a statement about what that document IS. That is a ruling.
- **Whether the 12 heading-set refusals should be admitted or excluded.** Ten
  carry no `§` at all and cost nothing to exclude; two carry five real
  references and would then go unchecked. Excluding by "has no numbered
  headings" is a hand-kept property that silently drops the two that matter.

## What I did not attempt

- Running the full `pytest` suite or the harness floors. Nothing here touches
  Python, `ci.yml` or any harness, and no gate above reads a `*.md` I changed
  except `check-cross-references.py` itself.
