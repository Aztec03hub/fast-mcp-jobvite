# CODE-REVIEW-R8 - U14, the argument layer, merged and never reviewed

**Subject SHA: `20e71eda89dd21dd5eb8a5880f105b8c8885db0f`**, which is `main`'s tip. Read in a
worktree pinned there (`/tmp/r8-work`, branch `review/r8`). U14 merged at `f2447ed`; its own commits
are `01669e3`, `cb9b042`, `2c6ff19`.

**Design read as `git show c15b138:docs/DESIGN.md`,** never from a working tree.

**Read-only on `src/`, `tests/`, `scripts/`.** One mutation was applied inside my own worktree, proved
LANDED with `cmp` against a backup taken first, and proved RESTORED with `cmp` after. `git status
--porcelain` is empty and `cmp` is identical for both backed-up files. Nothing is in any tree now.

---

## Baseline, read from the terminal, each on its own line

Floors DERIVED from `ci.yml` at `20e71ed`, never retyped:

```
$ grep -oE 'check-suite-floor\.sh [0-9]+' .github/workflows/ci.yml | head -1
check-suite-floor.sh 768
$ grep -oE 'check-harness-anchors\.py --self-check --floor [0-9]+' .github/workflows/ci.yml
check-harness-anchors.py --self-check --floor 401
```

| Gate | Result | Exit |
|---|---|---|
| `uv run --frozen pytest -q` | **768 passed, 6 deselected, 0 skipped**, 46.89s | **0** |
| `bash scripts/check-u14-arguments-amputation.sh` | **10 rows, 10 anchors applied, 0 vacuous**, 791 total surviving assertions | **0** |

768 passed == the 768 floor. 0 skipped.

**All ten amputation rows reproduce U14's reported survivor counts EXACTLY** - 16, 18, 50, 104, 98,
97, 101, 103, 104, 100 - with 0 vacuous rows. The report's harness table is accurate as re-measured,
including the two rows it says it repaired. **A4 is genuinely closed**: it now reports 1 failed / 104
passed rather than going vacuous, so the `OrphanInput` arm does what the report claims.

---

# FINDINGS

## R8-H1 - HIGH. There is an inbound model outside `tools/`, and its extra-key refusal can be deleted with the whole 768-test suite green. MEASURED - SURVIVING MUTATION.

`src/fast_mcp_jobvite/approval.py:95` defines `class ApprovalAnswer(BaseModel)`. It is populated
from data that arrives from outside this server - `src/fast_mcp_jobvite/approval.py:419`,
`result = await ctx.elicit(message, response_type=ApprovalAnswer)` - so it is an **inbound model**.
It lives outside `src/fast_mcp_jobvite/tools/` and is not any registered tool's `params` annotation,
so it is invisible to **both** of U14's enumeration routes
(`tests/test_arguments_sweep.py:61`, `TOOLS_DIR: Final = SRC / "fast_mcp_jobvite" / "tools"`).

The brief said: *"If there is an inbound model outside `tools/`, that is a High."* There is.

**Measured, not argued.** Mutation **R8-M1** changed `src/fast_mcp_jobvite/approval.py:108` from
`model_config = ConfigDict(extra="forbid")` to `ConfigDict(extra="allow")`:

```
====================== 768 passed, 6 deselected in 46.65s ======================
R8M1_EXIT=0
```

**SURVIVED.** Identical to baseline. Every one of U14's per-model assertions -
`extra="forbid"`, `strict=True`, the structural limits, the string ceilings - is scoped to a
container this model is not in, so deleting its only declared protection costs nothing.

This is the R7-H1 shape again (*a hand-kept list beside its container*), one level up: U14 correctly
replaced the hand-kept **list** with a container, and then chose a container narrower than the
property it is asserting. The sweep's own name says `INPUT_MODELS`; what it enumerates is
`TOOL_INPUT_MODELS`.

**Suggested fix (HYPOTHESIS - I did not run it).** Do not widen route B to all of `src/`; U14 is
right that this sweeps `models/` and needs a rule that is not a name. Instead make the *narrowness
visible and checked*: add a third route that enumerates **every `BaseModel` subclass in `src/` that
is named as a `response_type=` or `requested_schema=` argument anywhere in the tree**, and assert
that set is a subset of the swept models. That is the same "exclude by USE, not by name" rule route
B already uses, applied to the second way a model receives outside data. On today's tree it would
find exactly `ApprovalAnswer` and fail, which is the point.

---

## R8-H2 - HIGH. The two approval legs disagree about what counts as approval, and the comment asserting they agree is at the divergence. MEASURED.

`src/fast_mcp_jobvite/approval.py:420-425` says:

> `# THE SAME CONJUNCTION AS THE MRTR LEG, in the shape this`
> `# mechanism returns it`

and `src/fast_mcp_jobvite/approval.py:426-430` uses `result.data.approve is True`, with
`_approved_by_conjunction`'s docstring (`src/fast_mcp_jobvite/approval.py:275`) explaining:

> *"`is True` rather than a truth test: a JSON `"true"`, a `1` or a non-empty dict are all truthy and
> none of them is the boolean the schema asked for."*

**That guard works on the MRTR leg and is defeated before it runs on the elicitation leg.** The MRTR
leg reads a raw dict (`src/fast_mcp_jobvite/approval.py:409-410`), so `content.get("approve") is
True` sees the wire value. The elicitation leg validates through `ApprovalAnswer` first, and
`src/fast_mcp_jobvite/approval.py:110` declares `approve: bool` with **no `strict=True`** - all six
tool input models set it (`tools/candidates.py:175,190,229,289`, `tools/jobs.py:119,456`); this one
does not. Pydantic's lax mode therefore **coerces the value to `True` before `is True` ever sees
it.**

Measured with both real functions:

```
value        MRTR leg (_approved_by_conjunction)   ELICITATION leg (ApprovalAnswer)
True               True                                 True
'true'            False                                 True   <== LEGS DISAGREE
1                 False                                 True   <== LEGS DISAGREE
'yes'             False                                 True   <== LEGS DISAGREE
'on'              False                                 True   <== LEGS DISAGREE
False             False                                False
'false'           False                                False
0                 False                                False
```

**Consequence.** On the handshake era, a host answering `{"approve": "yes"}` authorises a
`create_candidate` write - the tool that emails a candidate. On the modern era the identical answer
refuses. `ApprovalAnswer`'s own docstring (`src/fast_mcp_jobvite/approval.py:98`) states the whole
purpose of the class is that **"BOTH ERAS ASK FOR EXACTLY THIS SHAPE"** so the payload is
era-independent. The shape is shared; the *acceptance rule* is not, and the divergence is in the
direction that can email someone.

**Suggested fix (HYPOTHESIS - I did not run it).** Add `strict=True` to
`src/fast_mcp_jobvite/approval.py:108`: `model_config = ConfigDict(extra="forbid", strict=True)`.
Under strict mode pydantic refuses `"true"`, `1`, `"yes"` and `"on"` for a `bool` field, which makes
`result.data.approve is True` mean on this leg what `content.get("approve") is True` already means on
the other. **Verify with a positive control that the four coercing values now refuse**, because a
green suite will not notice - see R8-H1, this model is swept by nothing.

Note both Highs have **one root cause**: `ApprovalAnswer` is an inbound model that no sweep reaches.
Fix R8-H1's enumeration and R8-H2 becomes a test failure rather than a review finding.

---

## R8-M1 - MEDIUM. ADR-0029's central claim is false: the middleware seat exists in the pinned framework. (Brief question 4.)

`docs/adr/0029-the-body-size-limit-has-no-middleware-to-live-in.md:1` is titled *"§2.1's 1 MiB body
limit is placed at a middleware this design does not have"*, and line 8 states: **"There is no
middleware here that sees a request body."**

The first half is true of the tree. The second is stated as an impossibility, and it is wrong.
Measured against the installed, locked framework:

```
fastmcp 4.0.0b4
run_http_async: ['self', 'show_banner', 'transport', 'host', 'port', 'log_level', 'path',
                 'uvicorn_config', 'middleware', 'json_response', 'stateless_http', 'stateless',
                 'host_origin_protection', 'allowed_hosts', 'allowed_origins', 'sockets']
http_app: ['self', 'path', 'middleware', 'json_response', ...]
create_streamable_http_app [... 'routes', 'middleware', 'host_origin_protection', ...]
```

**`middleware` is a first-class parameter of `run_http_async`**, which is the very call
`src/fast_mcp_jobvite/__main__.py:441` already reaches through `**http_run_kwargs(settings)`. A
Starlette ASGI middleware that sees the raw body is placeable today without touching the framework.
The ADR conflates *"we have not built one"* with *"there is nowhere to put one"*, and the second
form is what closes an obligation.

This independently reproduces the ruling recorded on task #77 (*"the seat exists, so it is a gap not
an impossibility"*), which landed after my base SHA - I did not read it before measuring.

**Suggested fix (HYPOTHESIS).** Rewrite ADR-0029's title and its line 8 **in place** to say the
limit is unbuilt rather than unplaceable, and name `run_http_async(middleware=...)` as the seat, so
the next reader does not re-derive the framework signature. Task #81 already exists for building it.

---

## R8-M2 - MEDIUM. `MAX_PAYLOAD_BYTES` under-measures the arrived payload by up to 5.95x. (Brief question 2.)

`src/fast_mcp_jobvite/utils/constraints.py:281`:

```python
encoded = json.dumps(payload, default=str, ensure_ascii=False).encode("utf-8")
```

U14 parked this as unsettled item 3 (*"key order, whitespace and escaping all differ ... bounded and
conservative"*). **It is not conservative in the direction that matters, and here is the number.**
A caller sends a value as `\uXXXX` escapes; each is 6 bytes on the wire and re-serialises to 1 byte
with `ensure_ascii=False`:

```
Q2 escaped wire bytes:      6008
Q2 re-serialised bytes:     1009
Q2 under-measurement ratio: 5.95x
Q2 wire bytes that still pass the 1048576 cap: ~6243651
```

So **a ~6.2 MB argument payload passes a 1 MiB cap.** `ensure_ascii=False` widens this: with
`ensure_ascii=True` a non-ASCII character re-escapes, but a plain-ASCII escape such as `A`
still collapses to one byte either way, so the gap does not close by flipping that flag alone.

This is a MEDIUM rather than a HIGH because the layer's own comment
(`src/fast_mcp_jobvite/utils/constraints.py:196-204`) already refuses to call this the body cap, and
ADR-0029 plus task #81 own the real bound. **A byte-exact bound belongs at R8-M1's middleware seat**,
where the arrived bytes are still the arrived bytes.

**Suggested fix (HYPOTHESIS).** Leave `check_structural_limits` as the approximate argument-payload
bound it says it is, and add the measured ratio to the caveat comment so the next reader has the
number rather than the word "approximation". The exact bound is task #81's.

---

## R8-L1 - LOW. `check-adr-numbers.py` reports ADR-0030 free at this SHA, and ADR-0030 is already taken.

At `20e71ed`:

```
$ python3 docs/reviews/check-adr-numbers.py
ADRs: 29, numbered 0001-0029
Every ADR number is unique, contiguous, and matches its own heading.
ADRCHECK_EXIT=0
```

The brief names ADR-0030 as the next free number and tells me to run the checker first *"because two
units have collided on a number here before, both correct when they looked."* The checker agrees
0030 is free. **Task #67 records `RULED as ADR-0030 (Accepted) at f6e98f9`.** So the collision the
brief warns about is live right now, and the checker cannot see it - it reads `docs/adr/` in the
working tree, and `f6e98f9` is not an ancestor of `20e71ed`.

I have **not** claimed a number. Nothing in this report needs one: R8-M1 corrects ADR-0029 rather
than raising a new ADR, and both Highs are code defects.

**Suggested fix (HYPOTHESIS).** Have `check-adr-numbers.py` also scan `docs/adr/` across every local
branch (`git for-each-ref --format='%(refname)' refs/heads` then `git ls-tree <ref> docs/adr/`) and
report the highest number seen anywhere, not just in the checked-out tree. The failure mode is a
checker whose container is one worktree while the numbers are minted across many.

---

## R8-N1 - NIT. `_measure`'s docstring claims a recursion-safety property the size check ahead of it does not have. Measured NOT reachable.

`src/fast_mcp_jobvite/utils/constraints.py:227-230` says the before-descent check means *"a payload
that would blow the interpreter's own recursion limit is refused before it can."* True of `_measure`
- but `check_structural_limits` runs `json.dumps` at `src/fast_mcp_jobvite/utils/constraints.py:281`
**first**, and that recurses over the whole structure before any depth check happens.

**I chased it and it does not bite** (brief question 3):

```
recursionlimit 1000
depth 5000:  ValueError 'argument payload nests deeper than 5 levels'
depth 20000: *** RecursionError ***
max wire-parseable depth: 9997
verdict at that depth: ValueError(depth)
json.loads depth 20000: RecursionError
cyclic: ValueError 'Circular reference detected'
```

`json.dumps` tolerates deeper than `json.loads` accepts, so **every depth reachable from the wire
(up to 9997) yields a clean `ValueError`**, and a cyclic structure also yields `ValueError`
("Circular reference detected") - both fail closed and both convert to a `ValidationError` through
the before-validator. **The code is correct; only the docstring's reasoning is.** The property is
real but it is delivered by `json.loads`'s limit being tighter, not by the check ordering.

**Suggested fix (HYPOTHESIS).** Amend the docstring to say the descent is bounded by the depth check
*and* that the size check ahead of it recurses, with the measured 9997-vs-20000 margin as the reason
that is safe - so a future change to `ensure_ascii`, `default=`, or the encoder does not silently
remove a margin nobody recorded.

---

## R8-N2 - NIT. `_measure` branches on `set`/`frozenset`, which a JSON-parsed payload cannot contain.

`src/fast_mcp_jobvite/utils/constraints.py:249`:
`if isinstance(payload, (list, tuple, set, frozenset)):`

The comment above it (`:245-248`) is right that naming the types beats excluding `str` from
`Sequence`. But `set` and `frozenset` cannot arrive from `json.loads`, so on the real inbound path
those two are unreachable. Harmless, and arguably good defence for a non-JSON caller.

**Suggested fix (HYPOTHESIS).** Leave the code; add half a sentence to the existing comment saying
`set`/`frozenset` are defence for a non-JSON producer rather than a shape the wire can deliver, so
nobody later "simplifies" them out believing they were reachable, or writes a coverage arm for a
branch no payload can enter.

---

# The brief's four questions, answered

**1. Is five the whole inbound surface?** **No.** Five is the whole *tool* inbound surface, and U14
is right about that half. Enumerated from a different direction - `grep -rn '^class .*BaseModel'`
over all of `src/`, plus every `@server.tool` decorator - I find 5 tool registrations
(`tools/jobs.py:342,654`, `tools/candidates.py:606,656,702`) matching the 5 input models exactly, so
the equality claim holds inside `tools/`. Outside it, **`ApprovalAnswer` at `approval.py:95` is a
sixth inbound model** (R8-H1), and the MRTR leg at `approval.py:409-410` is a **seventh inbound
path with no model at all** - `_approved_by_conjunction` reads `content.get("approve")` straight off
a raw dict, so no structural limit, no `extra="forbid"` and no `strict=True` applies to it.

**2. Can `check_structural_limits` be reached with a payload it does not measure?** **Yes** - R8-M2,
5.95x under-measurement, a ~6.2 MB wire payload passing a 1 MiB cap. Heavy escaping is exactly the
case the brief guessed at, and the ratio is 6:1 per escaped character.

**3. Does the depth check terminate?** **Yes, at every depth reachable from the wire** - R8-N1. Max
`json.loads`-parseable depth is 9997 and that yields `ValueError`, not `RecursionError`. Cycles give
`ValueError("Circular reference detected")` from `json.dumps`. Both fail closed. The caller gets a
`ValidationError` from the framework, per `DESIGN.md:181-190`.

**4. Is ADR-0029 right that the body cap has no middleware to live in?** **No** - R8-M1. The seat is
`run_http_async(middleware=...)` in the locked `fastmcp 4.0.0b4`, reachable from the call
`__main__.py:441` already makes.

---

# Mutations applied, and proof of restore

| ID | Subject | File:line | Verdict |
|---|---|---|---|
| **R8-M1** | `ApprovalAnswer` stops forbidding extra keys | `src/fast_mcp_jobvite/approval.py:108` | **SURVIVED** - 768 passed, 6 deselected, 0 skipped, exit 0 |

Applied with a Python `str.replace` whose anchor was **asserted unique and present before mutating**
(`assert s.count(anchor) == 1`). Proved LANDED by `cmp` against a backup taken first:

```
src/fast_mcp_jobvite/approval.py /tmp/r8-approval.bak differ: byte 5165, line 108
```

Proved RESTORED after, by `cmp` **and** `git status`:

```
$ cmp src/fast_mcp_jobvite/approval.py /tmp/r8-approval.bak && echo "RESTORE PROVED BY cmp: identical"
RESTORE PROVED BY cmp: identical
$ git status --porcelain
$ git rev-parse HEAD
20e71eda89dd21dd5eb8a5880f105b8c8885db0f
```

`PYTHONDONTWRITEBYTECODE=1` throughout. No `git stash`, no `git checkout <path>`. `tests/` and
`scripts/` were backed up but never modified; `cmp` confirms `tests/test_arguments_sweep.py` is
identical to its pre-review backup. **`ci.yml` was not touched.**

U14's own amputation harness was re-run unmodified (10/10 rows, 0 vacuous, exit 0); its mutations are
applied and restored by the harness itself, and the tree was clean afterwards as shown above.

---

# Claims in `U14-IMPL-REPORT.md` that I re-measured, and how they held

| Claim | Verdict |
|---|---|
| Five input models, not four | **HOLDS** - confirmed from a second direction (5 `@server.tool` sites) |
| Both routes asserted EQUAL, guarded against `set() == set()` | **HOLDS** - three guards at `tests/test_arguments_sweep.py:207-269`; the `OrphanInput` arm at `:269` operates on a synthetic tree so it cannot be satisfied by the real tree's shape |
| A4 was vacuous and is now closed | **HOLDS** - re-run gives 1 failed / 104 passed, not vacuous |
| A6, the limits are load-bearing, 97 survivors | **HOLDS EXACTLY** - re-run gives 8 failed / 97 passed |
| All 10 amputation rows, 0 vacuous | **HOLDS EXACTLY** - all ten survivor counts reproduce |
| No arm reads its expectation out of the code under test | **HOLDS** - `tests/test_arguments_sweep.py:589-592` joins the four constants to the design's literals 5 / 1_000 / 100 / 1024*1024, and the arms use literals |
| Every derived parametrisation has a population assertion | **HOLDS** - `tests/test_arguments_sweep.py:346-358` asserts `len(STRING_FIELDS) >= 9` **and** that exactly `["SearchCandidatesInput"]` has no string field; the second half is what makes the first non-vacuous |
| Suite 768 passed, 0 skipped | **HOLDS** - re-measured 768 / 0 skipped / exit 0 |
| Unsettled item 1, the inbound surface boundary | **CORRECT TO HAVE PARKED IT, AND THE ANSWER IS BAD** - R8-H1 |
| Unsettled item 3, `MAX_PAYLOAD_BYTES` re-serialises | **CORRECT, AND THE MAGNITUDE IS 5.95x** - R8-M2 |

The report is accurate everywhere I checked it. Its two self-flagged unsettled items are both real
defects, which is the argument for reading an honest "could not settle" list as a work queue rather
than as closure.

---

# What I could NOT settle

1. **Whether `ApprovalAnswer` and the MRTR raw-dict path are reachable by an *untrusted* party.**
   Both receive data from the **host**, not from the tool caller, and how much the host is trusted is
   a threat-model question I did not find settled in the frozen design. R8-H1 stands regardless -
   an inbound model outside every sweep is a gap whoever fills it - but whether R8-H2 is a privilege
   boundary crossing or an internal inconsistency depends on that ruling, and it is yours.

2. **Whether a `strict=True` on `ApprovalAnswer` breaks a real host.** I did not run the fix. If some
   host in the field answers `{"approve": 1}`, adding `strict=True` turns today's silent approval
   into a refusal - which is the right direction, but it is a behaviour change on the write path and
   it needs the fix's own positive control before it lands.

3. **The exact reachable ceiling on R8-M2.** I measured 5.95x for `A`-style escapes. I did not
   search for a worse constructor (surrogate pairs, or a key-order/whitespace interaction), so 5.95x
   is a lower bound on the gap, not the maximum.

4. **Whether `check-standards-citations.py` passes.** U14 records it exits 2 in any `/tmp` worktree
   for want of a sibling corpus. I did not symlink around it, so I have not run it, and I cannot say
   whether U14's citations resolve. U14's suggested fix (an env var falling back to the sibling)
   still looks right to me and is still unbuilt.

5. **The coverage floors U14 did not read off a run.** Its unsettled item 6 says the tool-module 85%
   floor and the critical-path 95%/90% floor were not re-measured. I did not measure them either -
   `ci.yml` holds them and the suite passes, but neither of us has read those numbers.

**The worktree `/tmp/r8-work` is left in place** and clean at `20e71ed` with only this report added,
so the mutation evidence above can be re-run. Remove it after reading.
