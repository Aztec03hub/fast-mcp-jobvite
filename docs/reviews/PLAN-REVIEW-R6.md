# PLAN-REVIEW-R6 — `docs/plans/IMPLEMENTATION-PLAN.md`, draft 7

Reviewer: `plan-review-r6`, fresh. I wrote none of this plan and ran none of rounds 1-5.
Subject: `docs/plans/IMPLEMENTATION-PLAN.md`, **1,847 lines, UNCOMMITTED in the working tree**, read
from the working tree as instructed.
Design read from the frozen git object `git show 135c3ac:docs/DESIGN.md` (1,994 lines), never from
the working tree.
Tree at review time: **HEAD `02245b1`** — four commits past draft 7's stated basis of `ff0bbdf`
(`5519032`, `80a7fd0`, `196512b`, `6072f5a` U2, `02245b1` ADR-0017).
Date: 2026-08-28. No file was edited, nothing was committed, no branch or stash operation was run.

---

## Verdict

**NOT at 0C/0H/0M.**

**Tally: 0 Critical / 1 High / 2 Medium / 5 Low.**

**Nothing here should stop U0, U15 or U2.** U2 has in fact landed clean while this review ran
(`6072f5a`); the full suite is **90 passed, 2 deselected, 0 skipped**, and both control harnesses
fire 11/11 and 15/15. The High binds **before U1 is dispatched**, not after — U1 is the next unit in
Wave A and is the first unit the defect bites.

Draft 7's two disposition claims are **both true and I verified them at source rather than accepting
them**: the collection guard is built, in the thorough variant, inside `tests/` (H1 closed by build),
and U15 landed three real `ci.yml` steps (M3 got stronger). **Both of draft 7's pytest measurements
reproduce under an independent hand on pytest 9.1.1**, including the positive control that the plugin
actually loaded. The decision at §4 rests on measurements that hold.

The tenth collision exists. It is the one I found, it is the High, and it is the same shape as
collisions 7, 8 and 9 — a surface nobody classified as code.

---

## What I ran, and what it said

All at HEAD `02245b1`, from the repo root:

```
python3 docs/reviews/check-coupling.py docs/DESIGN.md
  exit=0   60 STRIDE rows, 17 Critical/High, all 60 dispose of themselves, 23 naming a §8 case

python3 docs/reviews/check-coupling-controls.py
  exit=0   34/34 controls fired; post-run re-check of the real DESIGN.md: exit=0

python3 docs/reviews/check-coupling-sweep.py
  exit=0   0 escapes are holes

uv run --frozen pytest -q
  90 passed, 2 deselected in 1.58s      (0 skipped)

bash scripts/check-u0-test-controls.sh    11/11 controls fired
bash scripts/check-u15-gate-controls.sh   15/15 controls fired, clean post-run re-check
```

Every gate number the plan asserts at `:1718-1721` reproduces. The suite has grown from the plan's
recorded 56 to 90 because U2 landed 34 tests at `6072f5a`; the deselected count held at 2 and the
skip count held at 0.

### The two measurements draft 7 made, re-run independently

`uv run --frozen python -c "import pytest; print(pytest.__version__)"` → **9.1.1**, so the plan's
stated interpreter is the one this repository actually has.

**Probe 1 — per-directory conftest fixtures across sibling directories.** Built in a scratch tree
outside the repo, `tests/tools/conftest.py` defining `mock_transport`, one consumer in
`tests/tools/`, one in `tests/client/`:

```
tests/tools/test_t.py::test_here     PASSED
tests/client/test_c.py::test_there   ERROR  fixture 'mock_transport' not found
1 passed, 1 error
```

That is the plan's transcript at `:1306-1308` verbatim. **Confirmed.**

**Probe 2 — `pytest_plugins` in a non-rootdir conftest under `-W error`.** `tests/conftest.py`
carrying `pytest_plugins = ["tests.fixtures.transport"]`, rootdir at the scratch root (not `tests/`),
run with `-W error`:

```
1 passed in 0.00s     EXIT=0
```

No warning, no error. **Confirmed** — and the passing test *consumed the fixture*, which is the
positive control that the plugin was actually loaded rather than silently ignored.

**Probe 3 — mine, not the plan's.** The same registration works **without**
`tests/fixtures/__init__.py` (exit 0, fixture resolved). This matters because `tests/` is already a
package here — `tests/test_manifest.py:31` does `from .conftest import PYPROJECT, UV_LOCK` — and an
agent that creates `tests/fixtures/transport.py` and forgets the `__init__.py` is not blocked. The
mechanism §4 mandates is more robust than the plan claims, not less.

---

## HIGH

### H1 — The tenth collision: `[project] dependencies`, `uv.lock` and `tests/test_manifest.py` are one unowned shared surface, and the first unit that adds a runtime dependency turns U0's suite red

`tests/test_manifest.py:47-53` is an **exact set-equality over the whole runtime dependency list**:

```python
def test_fastmcp_and_fastmcp_slim_are_pinned_at_the_same_version() -> None:
    """The three-pin block of DESIGN.md:1406-1410, checked as a set not as prose."""
    assert set(_dependencies()) == {
        "fastmcp==4.0.0b4",
        "fastmcp-slim==4.0.0b4",
        "mcp==2.1.1",
    }
```

`pyproject.toml:15-19` holds exactly those three and nothing else.

**The plan schedules at least four runtime dependencies that are not in the tree at all.**
`grep -c '^name = "<pkg>"' uv.lock` returns **0** for each of `loguru`, `tenacity`, `defusedxml` and
`circuitbreaker` — they are not present even transitively, so each must be declared:

| Dependency | Scheduled at | Unit | In `uv.lock`? |
|---|---|---|---|
| `loguru` | `IMPLEMENTATION-PLAN.md:1619` (§7, *"Logging library: **`loguru`**"*) | U3 | **no** |
| `defusedxml` | `:1621`, and U4's Builds at `:624` | U4 | **no** |
| `tenacity` | `:1620`, and U7's Builds at `:762` | U7 | **no** |
| `circuitbreaker ^2` | `:807-818` (B47's blessed library, adopted if the rejection test passes) | U7 | **no** |
| `pydantic-settings` | U1's Builds at `:479` | U1 | yes, transitively only |

**Positive control, both arms, run rather than reasoned.** I copied `pyproject.toml` to a scratch
path, inserted `"loguru>=0.7"`, and evaluated the exact expression from `test_manifest.py:49`:

```
deps after adding loguru: ['fastmcp==4.0.0b4', 'fastmcp-slim==4.0.0b4', 'mcp==2.1.1', 'loguru>=0.7']
test_manifest.py:49 set-equality holds?  False        <- the addition goes red
control (unmutated) holds?               True        <- so the False is the mutation, not the harness
```

The mutation was asserted non-identical to source before the check ran, so neither arm is vacuous.

**Why this is a collision and not just a test that needs updating.** §4's `pyproject.toml` rule at
`:1277` enumerates a **closed** later-editor set: *"U11 edits rows inside the advisory-ignore table
U0 landed empty; **U1 adds `[project.scripts]`**, which U0 deliberately omitted...; U13 adds
`readme`. Same rule: touch your own key, nothing else."* `[project] dependencies` is not among the
named keys. And **`uv.lock` appears nowhere in §4 at all** — `grep -n 'uv\.lock'` over
`IMPLEMENTATION-PLAN.md:1255-1515` returns zero hits (positive control: the same grep over the whole
file returns nine, at `:182, 310, 378, 379, 457, 467, 1079, 1090, 1668`, so the pattern works and the
zero is a real absence).

Three properties compound:

1. **`uv.lock` is a whole-file regenerated artifact.** Every other shared surface in §4 is governed by
   *"the edits are non-overlapping line ranges by construction"* (`:1285-1286`). That mechanism does
   not exist for a lockfile. Two units regenerating it in overlapping time do not get a clean merge;
   they get a whole-file conflict, which is precisely the failure §4 opens by naming.
2. **The red arrives with a message that reads as a breach, not as an extension.** The failing test's
   siblings — `test_the_fastmcp_slim_justification_comment_survives:62`,
   `test_removing_fastmcp_slim_breaks_the_resolve:86` — exist specifically to stop the three pins
   being tidied away. An agent handed U4 alone sees a manifest-integrity test go red on a legitimate
   change, and **the cheapest green is to widen the set literal**. Nothing in the plan tells it not
   to, and U0's precedence rule (*"where the build and this section differ, the build wins"*,
   `:293-296`) arguably reads as licence.
3. **It bites the next unit dispatched.** U1 is Wave A. If U1 declares `pydantic-settings` directly —
   which is the correct thing to do for a package it imports — the suite goes red. U4 is Wave B and
   U7 is Wave C concurrent with four other lanes.

**This is not an ADR.** `DESIGN.md:1413-1418` gives the three-pin block as the packaging recipe and
nowhere says the dependency list is closed at three; the exact-set assertion is a property U0's
*build* added, not one the design mandates. Verified: `git show 135c3ac:docs/DESIGN.md` lines
1358-1384 contain no closure claim.

**Suggested fix (MY SUGGESTION — verify before adopting):** a fourth row in the Wave A shared-file
table at `:1274-1278`, in the same container-and-rows form the section already uses.

| Shared file | Rule |
|---|---|
| `pyproject.toml` `[project] dependencies` + `uv.lock` + `tests/test_manifest.py` | **U0 owns all three, and they move together or not at all.** A unit adding a runtime dependency (`loguru` U3, `defusedxml` U4, `tenacity` and the breaker U7, `pydantic-settings` U1) appends **one line** to `[project] dependencies`, runs `uv lock`, and adds the same string to the expected set in `tests/test_manifest.py:49`. **The three pins in that set are never removed, reordered or relaxed** — they are `DESIGN.md:1413-1418`, and `test_removing_fastmcp_slim_breaks_the_resolve` is the control that proves it. **`uv.lock` is regenerated whole, so two units may not add a dependency in overlapping time**: within a wave, dependency additions are serialised, and the unit that lands second re-runs `uv lock` on top rather than merging |

and add it to the numbered list as **collision 10**, restating the floor-not-ceiling sentence at
`:1376-1383` with the count corrected. Consider also loosening `test_manifest.py:49` from
set-equality to `expected <= set(deps)` **plus** a separate assertion that no line matching
`^(fastmcp|fastmcp-slim|mcp)\b` differs from its pin — that keeps the property the test exists for
while making an addition a non-event. I have not written that variant, so treat it as a sketch.

---

## MEDIUM

### M1 — U15's carried HIGH is closed by the tree, and the plan states the opposite in its most emphatic terms

`IMPLEMENTATION-PLAN.md:1076-1097` opens: *"**CARRIED, NOT CLOSED, and it is the most important
sentence in this unit: `pre-commit` is not a declared dependency, so on a fresh clone both gates
silently do not exist.**"* It goes on: *"this project's dev group does not [carry it], and
`pre-commit` appears nowhere in `uv.lock`"* (`:1079`); *"**Until a U0 follow-up adds
`pre-commit>=4.0.0`, runs `uv lock` and switches the CI step to `uv run --frozen pre-commit`,
C8-I1's Critical mitigation is not in force for the team**"* (`:1092-1094`); *"**No unit below may
read U15 as 'the commit-time gates are in place'**"* (`:1094-1095`).

**Two of those three conditions are satisfied, and the two factual claims are false.**

- `pyproject.toml:50` — `"pre-commit>=3.7"`, in the dev group, with a nine-line comment naming C8-I1.
- `uv.lock:523`, `:541`, `:1150-1151` — `pre-commit` is present and resolved at **4.6.2**.
- Landed at `80a7fd0`, *"Declare pre-commit, so a Critical row's mitigation exists on a fresh clone"*,
  which `git merge-base --is-ancestor 80a7fd0 HEAD` confirms is in history.

**This is the exact class of defect draft 7 exists to fix.** Draft 7 re-checked round 5's H1 and M3
against the moved tree and correctly changed their disposition. It did not re-check its own carried
HIGH against the same tree, and that HIGH had been closed one commit later.

**Two residues are still real and should survive the rewrite, not be dropped with it.**

1. **The CI step is still not on the frozen lock.** `ci.yml:283` reads
   `uv tool run pre-commit@4.6.2 run --all-files`, exactly as the plan describes at `:1085-1087`.
   The plan's third condition — *"switches the CI step to `uv run --frozen pre-commit`"* — is unmet.
   The plan's reasoning for why that matters is correct and should be kept.
2. **The declared floor is below the standard's, and unlike `setup-uv` nothing records the
   deviation.** `backend/tech-stack.md:157` and `:172` both read `"pre-commit>=4.0.0"` — I read both
   lines at source and they are identical. The tree declares `>=3.7`. The lock resolves 4.6.2 today,
   so `uv sync --frozen` installs a conformant version and the practical exposure is nil; but a
   `uv lock --upgrade` under a different resolver state could legally pick 3.x. `setup-uv@v5` got
   ADR-0016 for a smaller deviation; this got a comment.

**Suggested fix (MY SUGGESTION — verify before adopting):** rewrite `:1076-1097` in place rather
than appending — the plan's own rule at `:273-274` and `:1782`. Something in the shape of:

> **CLOSED IN PART, at `80a7fd0`.** `pre-commit>=3.7` is a declared dev dependency
> (`pyproject.toml:50`) and `uv.lock:1150` resolves it at 4.6.2, so `uv sync --frozen` on a fresh
> clone now produces an environment in which `pre-commit install` works and C8-I1's mitigation is
> installable for the team. **Two residues remain and are U0's:** `ci.yml:283` still runs
> `uv tool run pre-commit@4.6.2`, resolving outside the frozen lock and contradicting this project's
> `uv sync --frozen` discipline; and the declared floor is `>=3.7` where `backend/tech-stack.md:157`
> and `:172` both say `>=4.0.0`, a deviation nothing records — `setup-uv@v5` got ADR-0016 for less.
> The measured false negative stands as a warning: `uv run --frozen --offline pre-commit --version`
> exits 0 because `uv run` falls through to `PATH`, which reads as a green and is not one.

### M2 — The plan's ADR register is stale in three ways, and one of them is a licence to make a design change

`:1635` says the plan read *"all eleven ADRs"*. That was true at the freeze —
`git ls-tree --name-only 135c3ac docs/adr/ | grep -c '^docs/adr/0'` returns **11** — and it is a
statement about coverage in a section whose whole purpose is bounding coverage. There are now
**17** (`ff0bbdf` era: 15; HEAD: 17). Six are unread by the plan, and three of the six matter:

**(a) The `utils/constraints.py` gate is satisfied as written, and it should not be.** `:1444` reads
*"note that **no unit plans a shared `utils/constraints.py`** until ADR-0012 exists"*, and
`:1821-1822` *"**Until that ADR exists, no unit here plans a shared constraints module**"*.
**`docs/adr/0012-shared-inbound-constraints-module.md` exists**, filed at `fcc2341`, with
**`**Status:** Proposed`**. An agent handed U14 reads the gate, runs `ls docs/adr/`, finds 0012, and
is licensed to build the shared module — which is verbatim the outcome `:1822-1824` says the gate
exists to prevent (*"after the freeze doing it without the ADR is a design change made by whoever
happened to notice"*). The operative property is **Accepted**, not existence.

**(b) Q6 asks for an ADR that already exists.** `:1828` — *"Open, and it is a plan-level fix today
rather than a design change - **raised so it can become one**"* — and `:1839-1841` describes what
*"an ADR would settle"*. `docs/adr/0013-secret-absence-case-needs-a-pairing.md` (`c3d9530`,
**Proposed**) is that ADR, titled *"§8's secret-absence case needs a positive pairing, as the audit
cases have"*. The plan never names it. The same holds for `docs/adr/0014-c8-i1-empty-values-is-wrong.md`
(**Proposed**), which records exactly the `.env.example` argument the plan makes at length at
`:391-401` and never cites.

**(c) A Proposed design change contradicts a U2 verification bullet.**
`docs/adr/0017-the-unmapped-row...` (`02245b1`, **Proposed**, `Type: Design change`) decides *"The
unmapped row becomes `/problems/internal-error`, 500"*. `IMPLEMENTATION-PLAN.md:563` says
*"unmapped is `about:blank`"*. **The plan and the shipped build currently agree** — `errors.py:90`
is `UNMAPPED: Final = ProblemKind("about:blank", ...)` and `tests/test_error_contract.py:260`
asserts it — so this is not a defect today. It is an open item the plan does not know exists, on the
unit that just landed.

`ADR-0015` (Accepted) is described in substance at `:342-345` but never cited by number, and
`ADR-0016` (Accepted) is not mentioned at all.

**Suggested fix (MY SUGGESTION — verify before adopting):** three edits, all in place.

1. `:1444` and `:1821` — change *"until ADR-0012 exists"* to **"until ADR-0012 is Accepted"**, and
   note its current status so a reader does not have to look.
2. `:1826-1841` (Q6) — retitle as answered-in-part and name `ADR-0013` as the filed record, so the
   question reads as tracked rather than as an ask. Same for `ADR-0014` beside `:391-401`.
3. `:1635` — replace *"all eleven ADRs"* with **"the eleven ADRs that existed at the freeze
   (`135c3ac`); ADR-0012 to ADR-0017 postdate it and are read only where a unit cites them"**, then
   name ADR-0015 and ADR-0016 where the plan already describes their substance (`:342-345`,
   `:467`), and add ADR-0017 to §9 as an open design change against U2's `about:blank` bullet.

---

## LOW

### L1 — Four internal inconsistencies in §4 and the footer, three of which have survived two drafts and five review rounds

Each is small; the reason they are worth one finding is that **nothing has ever looked at them**, and
two are demonstrably inherited unchanged from draft 6 (`git show 299cf8b:docs/plans/IMPLEMENTATION-PLAN.md`).

**(a) The collision count is stale one paragraph after being corrected.** `:1376` reads *"**Nine
collisions to plan around, all real, and NINE IS A FLOOR**"* and the numbered list at `:1385-1452`
has nine items. `:1485` reads *"Two of the **eight** collisions above"*. Draft 6 had eight and said
eight (`draft6:1156`, `draft6:1247`) — consistently. Draft 7 updated the headline and not the recap.

**(b) A cross-reference points at the wrong collision, in the wrong direction.** `:1461` — *"which
holds only because **collision 6 below** puts registration in each unit's own `tools/*.py` rather
than in `server.py`"*. Tool registration is **collision 5** (`:1406`); collision 6 is `models/`
(`:1423`). The list runs `:1385-1452`; the sentence is at `:1454`, so it is **above**, not below.
Wrong in draft 6 too (`draft6:1223`), which means it survived rounds 1-5 untouched. The sentence
carries real weight — it is the load-bearing justification for the four-lane claim in Wave C.

**(c) The footer still identifies the document as draft 6.** `:1846-1847` reads *"Draft **6** by
`impl-plan-draft`, 2026-08-28, revised against `PLAN-REVIEW-**R4**.md`"*, byte-identical to
`draft6`'s last three lines, on a document whose `:3` reads *"Status: **DRAFT 7.** Revised against
`PLAN-REVIEW-R5.md`"*.

**(d) The COMPLIANCE-SPEC-PASS arithmetic at `:41-43` does not add up, and understates the tree.**
It reads *"**Six** of its nine defects have since been fixed in the tree (`2d2e1a3`, `ff0bbdf`); the
**two** that land on this plan — the README's Contributing section and the unowned changelog
obligation — are folded into U13 and §4."* Six plus two is eight, not nine. And I checked all nine
against the tree rather than against the claim: **all nine are closed**, by four commits, not two —
F-1/F-2/F-3/F-6/F-7 at `ff0bbdf`, F-4/C-2 at `2d2e1a3`, F-5 at `35de193`, C-1 at `5519032` (see L2
for a residue on C-1). Separately, the *"unowned changelog obligation"* is **A-5**, a MET-BY-ACCIDENT
item, not one of the nine defects — so the sentence mixes two populations.

**Suggested fix (MY SUGGESTION — verify before adopting):** `:1485` → "nine"; `:1461` → "collision 5
above"; `:1846-1847` → draft 7, `PLAN-REVIEW-R5.md`; `:41-43` → *"All nine of its defects are now
closed in the tree, across four commits — `ff0bbdf`, `2d2e1a3`, `35de193` and `5519032`. What lands
on this plan is the README's Contributing arm (F-6, folded into U13) and, from the MET-BY-ACCIDENT
set, the unowned changelog obligation (A-5, folded into U13 and §4)."*

### L2 — `mirror.yml` is in no ownership table, and it still carries the pin C-1 was closed on

`.github/workflows/mirror.yml:28` is `actions/checkout@v4`. `COMPLIANCE-SPEC-PASS.md` C-1 named the
population as *"`@v4` — `ci.yml:59,121,312,393`; **`mirror.yml:28`**"* — five places, four of them in
`ci.yml`. The fix commit `5519032` says *"checkout is now @v6 in **all five places**"*, and it is
right about its own count: `ci.yml` had grown a fifth checkout by then (the `links` job), so five
were changed. **`mirror.yml:28` was not among them.** Neither the commit message nor ADR-0016
mentions `mirror.yml` (`grep -in mirror` over both returns nothing). So a CONTRADICTED finding the
project believes closed is closed at 5 of 6.

That is a tree defect rather than a plan defect, and I report it because of *why* it survived: **the
plan's §4 shared-file table (`:1274-1278`) names `.github/workflows/ci.yml` and nothing else.**
`mirror.yml` and `.github/workflows/pr-title.yml` (added at `ff0bbdf`) appear in no ownership row
anywhere in the document. Nobody owns them, so nobody looks at them.

**Suggested fix (MY SUGGESTION — verify before adopting):** bump `mirror.yml:28` to
`actions/checkout@v6` in a one-line commit citing `ci-cd.md:81` and C-1 — verify the mirror workflow
still runs, I did not execute it. In the plan, extend §4's shared-file table's `ci.yml` row to read
**`.github/workflows/*.yml`**, so `mirror.yml` and `pr-title.yml` are U0's by the same rule rather
than unowned by omission.

### L3 — §8's declared-unread list is false in two places, which is the defect §8 says it fixed for `COMPLIANCE-SPEC.md`

Draft 7 correctly rewrote the `COMPLIANCE-SPEC.md` bullet, on the stated principle at `:43-45` that
*"a declared limitation that has since been discharged is a false statement about the plan's own
coverage."* It did not apply that principle to the two bullets on either side.

- `:1631-1633` — *"Every `standards/...:line` citation in this plan is quoted **from `DESIGN.md` or
  an ADR**."* U7 cites `STANDARDS.md:374-375` and `STANDARDS.md:316` at `:808` — a local research
  digest, which is neither — and `:820` says so explicitly in the same unit (*"I read it at
  `docs/research/STANDARDS.md:374-375`, **the local research digest, not the corpus**"*).
- `:1639` — *"I did **not** read `STANDARDS.md`, ... or any of the documents in `docs/reviews/`
  beyond the three gate scripts' docstrings and the plan's own review rounds."* Contradicted by
  `:808`/`:820` for `STANDARDS.md`, and by `:1156` and `:1650`, which cite
  `docs/reviews/COMPLIANCE-SPEC-PASS.md` — a document in `docs/reviews/` that is not a plan review
  round.

This understates coverage rather than overstating it, which is the safe direction, and that is why it
is Low. It is still a self-contradiction inside one document, and it is fix-one-miss-the-sibling —
which the plan names about itself three times.

**Suggested fix (MY SUGGESTION — verify before adopting):** rewrite `:1631-1633` as *"Every
`standards/...:line` citation in this plan is quoted from `DESIGN.md`, an ADR, or
`docs/research/STANDARDS.md` — the last is a local digest and not the corpus, and U7 says so at the
point it relies on one (`:819-822`). Round 6 verified ten such cites at source and all ten held; the
residue is real but unmeasured."* And amend `:1639` to except `STANDARDS.md` §B37/B47 and
`docs/reviews/COMPLIANCE-SPEC-PASS.md`.

### L4 — U0's "CI runs, at minimum" list omits three gates the tree now has, in the section that exists because such lists go stale

`:336-347` enumerates what CI runs. It does not name the **`links` job** (`ci.yml:454-470`,
`lycheeverse/lychee-action@v2`, `fail: true`), the **weekly `schedule`** (`ci.yml:47`), or the
**`.github/workflows/pr-title.yml`** workflow — all three landed at `ff0bbdf` and all three are
recorded four lines further down in the amendment table at `:468`.

*"At minimum"* is an honest floor, so this is not a false claim, and I nearly did not raise it. It is
Low because the list is what a later unit reads to know which gates its change must keep green, and
the link checker in particular constrains **every unit that writes a document** — a broken relative
link now blocks merge. Worth knowing that the job is `--offline` and carries no `--include-fragments`
(`ci.yml:463-468` explains why), so `#anchor` targets are **not** checked and the plan's own
intra-document links are out of scope.

**Suggested fix (MY SUGGESTION — verify before adopting):** append to the `:336-347` list: *"the
`links` job (`lychee`, relative links only, no fragments); the weekly `cron: '0 0 * * 0'` security
sweep; and, as a separate workflow, the semantic PR-title check."* Add one sentence to §4's rules
beside the `changelog.d` rule: *"Every unit that adds a document keeps its relative links resolving —
`ci.yml`'s `links` job is merge-blocking."*

### L5 — The U0 amendment table is already four commits behind, in the section whose stated reason for existing is that it goes stale

`:459-468` lists `db5c21e`, `35de193`, `2d2e1a3`, `ff0bbdf`, introduced at `:290-291` with *"a
section that describes only the unit's own commit is stale the moment anyone fixes a defect in it."*

Four later commits amend U0's files:

| Commit | What it changed in U0's files |
|---|---|
| `5519032` | `ci.yml` — `actions/checkout@v4`→`@v6` in five places; ADR-0016 filed for `setup-uv@v5` |
| `80a7fd0` | `pyproject.toml` dev group + `uv.lock` — `pre-commit>=3.7`. **This is what falsifies M1** |
| `196512b` | `.gitignore` — coverage artifacts |
| `6072f5a` | U2 landed: `src/fast_mcp_jobvite/errors.py`, `utils/correlation.py`, two test modules |

I rate this Low rather than Medium because the plan is uncommitted and its "as of" is genuinely
ambiguous — but at least `5519032` and `80a7fd0` predate this review, and a table that is behind at
the moment implementation agents read it does not do the job it was added for.

**Suggested fix (MY SUGGESTION — verify before adopting):** add the four rows, and add a line naming
the commit the table is current to — *"current as of `<sha>`"* — so the next reader can tell staleness
from completeness rather than assuming.

---

## What I checked and found clean, stated so the absence of a finding is bounded

**Draft 7's two disposition claims, verified at source rather than accepted.**
- *H1 closed by build.* `tests/test_collection_guard.py` exists (6,186 bytes, `35de193`), lives
  inside `tests/` — the single configured root, so its own removal fails collection — and its body
  walks `REPO_ROOT.rglob("test_*.py")` with an explicit skip-set (`:51-58`), cross-referencing
  against collection. That is the **thorough** variant of `backend/testing.md:162-165`, as the plan
  claims, not the minimal one; its docstring says so and cites `:138-141` and `quality-gates.md:76-81`.
- *M3 got stronger.* Three U15 steps are in `ci.yml`: `:238` *"Committed file types, whole tree"*,
  `:248` *"U15 gate controls, all fired"*, `:260` *"Secret scan hook runs clean"*. Three, as claimed.

**Ten standards citations subject-verified at source** in
`repos/evolv-coder-standards/standards/`, each read as a single numbered line and matched against
what the plan says it says: `backend/testing.md:138` (*"A collection-guard meta-test is required"*),
`:141`, `:162` (*"A more thorough variant..."*), `devops/quality-gates.md:76`, `:81` (*"test job MUST
fail"*), `documentation/readme-standard.md:56` (the Contributing link-or-inline clause U13 rests on),
`:83` (Quickstart may not require credentials), `documentation/changelog-standard.md:94`
(internal-only changes MUST NOT appear), `ai/tool-calling.md:173` and `:175` (the canonical
`X-Request-ID` / `request_id` / `request_id_var` triple). **10 of 10 hold.** §8 declares this class
unverified; **this is a sample of ten, not the population**, and the residue is real.

**Fifteen `DESIGN.md` citations subject-verified against the frozen `135c3ac` object**, by reading
each numbered line out of `git show 135c3ac:docs/DESIGN.md`: `:283` (`server.py`'s three
responsibilities, which is what makes collision 5's ruling legal), `:291` (`models/` one-per-tool),
`:428` (page caps 500/1000), `:449` (`start=0`), `:602` (breaker on the call path, the inline
fallback, and `circuitbreaker ^2` named), `:1222`, `:1289`, `:1319-1320` (the blanket positive-control
rule), `:1576`, `:1585`, `:1795` (the must-mitigate row reads `*(none)*` — the plan's headline claim,
and it holds), `:1830`, and C7-I2's three anchors `:1749`, `:1830`, `:1868`. **15 of 15 land on their
stated subject.** Round 5's M2 was applied correctly and the three C7-I2 anchors are right.

**COMPLIANCE-SPEC-PASS's nine defects, checked against the tree rather than against the plan's claim
about them.** F-1 weekly cron → `ci.yml:47`. F-2 PR title → `.github/workflows/pr-title.yml:56`,
`amannn/action-semantic-pull-request@v5`. F-3 links → `ci.yml:454-470`. F-4 ruff families →
`pyproject.toml:151` select block and `:170` `convention = "google"`. F-5 collection guard → above.
F-6 → `CONTRIBUTING.md` present. F-7 → `.github/pull_request_template.md` present. C-1 → `ci.yml`
five places at `@v6`, **`mirror.yml:28` still `@v4`** (L2). C-2 → `pyproject.toml:141`
`line-length = 88`. **Eight closed outright, one closed at 5 of 6.**

**The fixture tiers against the tree.** `docs/research/fixtures/` holds exactly **15** files. The
five the plan calls *recorded* (`:230-231`) are present and are the only `error_*` files; the eight
synthetic plus the two malformed (`:245-249`) account for the other ten. The plan's *"the recorded
tier is five files, and that is all of them"* at `:642-643` is exactly right, and the two malformed
bodies are correctly placed in the synthetic tier.

**`.env.example` against U0's §8 #3 text (`:386-401`).** Fifteen variables, parsed off the committed
file: six secret-class and empty (`JOBVITE_API_KEY`, `API_SECRET`, `FEED_KEY`, `FEED_SECRET`,
`COMPANY_ID`, `HTTP_TOKENS`), two empty non-secrets (`JOBVITE_TOOLS`, `PAGINATION_START_BASE`), seven
carrying values including `MAX_RESULTS=50` and `OUTBOUND_RATE_LIMIT=6`. The plan's counts are correct
and `JOBVITE_TLS_TERMINATED_BY_PROXY=false` is declared, so U1's TLS-refusal test at `:504-509` is
buildable. `tests/test_repo_hygiene.py:74`'s hard-coded `len(variables) == 15` is **not** an H1-shaped
hazard: I checked the plan for a sixteenth variable any unit must add and found none.

**`tests/conftest.py` against the rule §4 writes for it.** 35 lines: six module-level paths and two
session fixtures (`repo_root`, `fixtures_dir`). That is *"repo paths and the fixtures-directory
accessor, and nothing else"* (`:1278`) — accurate, and small enough for the rule to be enforceable.

**Not defects, checked and dismissed.** The `tools/jobs.py` split (U5 `search_jobs` / U12
`get_job_feed`) is not an unlisted collision — it is expressed in the Wave C table and U12's earliest
start is U5-and-U6 completion, so it is sequential like collision 3. `models/__init__.py` has three
potential creators but collision 6's *"one file per tool and never a shared module"* covers it.
`changelog.d/` fragments are one-per-unit and disjoint by construction. `tests/fixtures/` files are
one-per-unit and probe 3 shows the missing-`__init__.py` case is not a trap. The `links` job cannot
break on the plan's own `[§4](#4-...)` links because it runs without `--include-fragments`.

---

## What I could NOT settle

This list is for what I could not resolve, not for what I did not try.

1. **Whether the `links`, `codeql`, `secret scan` and SBOM jobs actually pass.** `ci.yml:16-19`
   states plainly that several have never run. I did not execute the workflow and did not run
   `lychee` locally. My claim about the links job is that it is **present and correctly scoped**,
   which is strictly weaker than "it is green".
2. **Branch protection settings** — required checks, `skipped == success`, approvals. These live in
   GitHub settings, not the tree, and the `github` MCP server failed to connect this session
   (*"Authorization header is badly formatted"*). Unasserted in both directions, same as the
   COMPLIANCE-SPEC pass.
3. **Whether `circuitbreaker ^2` evaluates half-open expiry on the call path or from a timer.** This
   is the plan's own named single experiment at `:815-818`, it gates H1's fourth dependency, and
   nobody has run it — including me.
4. **Whether ADR-0017 will be accepted**, and therefore whether U2's `about:blank` bullet at `:563`
   and the shipped `errors.py:90` are final. Plan and build agree today; the ADR is Proposed.
5. **Whether a `uv lock` regeneration under H1's fix reproduces the 72-package resolve** with four
   new direct dependencies added. The plan's executed 72-package figure (`:435-444`) is against the
   three-pin manifest only. I did not run a resolve with `loguru`/`tenacity`/`defusedxml` added,
   because doing so would write `uv.lock` in a checkout other agents are working.

---

*Round 6 by `plan-review-r6`, 2026-08-28. Gates, suite and both control harnesses re-run at
`02245b1`. `docs/DESIGN.md` read from the frozen `135c3ac` git object. Draft 7's two pytest
measurements re-run independently on pytest 9.1.1. No file was edited, nothing was committed, and no
branch, stash or checkout operation was performed.*
