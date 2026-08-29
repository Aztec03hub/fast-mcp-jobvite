# PLAN-REVIEW-R7 — `docs/plans/IMPLEMENTATION-PLAN.md`, draft 8

Reviewer: `plan-review-r7`, fresh. I wrote none of this plan and ran none of rounds 1-6.
Subject: `docs/plans/IMPLEMENTATION-PLAN.md`, **2,000 lines**, read from the working tree. It was
uncommitted when I was briefed and **was committed mid-review at `4e5a1b2`, byte-identical to what I
read, under a message saying it is draft 7** — see L5. Draft 7 read from the committed object at
`80a7fd0` for before/after checks.
Design read from the frozen git object `git show 135c3ac:docs/DESIGN.md`, never from the working tree.
Tree at review time: **HEAD `b7fd35d`** — three commits past round 6's `02245b1` (`b993ada`,
`328dfcb`, `b7fd35d`).
Date: 2026-08-28. No file in the repository was edited, nothing was committed, and no branch, stash
or checkout operation was run. Every probe ran in a scratch tree outside the repository.

---

## Verdict

**NOT at 0C/0H/0M.**

**Tally: 0 Critical / 1 High / 1 Medium / 5 Low.**

**Nothing here should stop U1 being dispatched next.** I looked for that specifically. U1's write set
is `config.py`, `__main__.py`, `server.py`, `server.json`, `.env.example`, its `ci.yml` block, its
`[project.scripts]` key, and one runtime dependency. Collision 10's new row governs the dependency;
no other closed set in the tree fires on anything U1 does. **The High binds U5** — the first unit
scheduled to add a credentialed arm — and it should be fixed before U5, not before U1.

Draft 8's applied work holds up. **I verified all eight of round 6's findings at source rather than
accepting them**, plus the self-audit's five numeric corrections, and re-ran every gate and the suite
at the SHA draft 8 pins to. All of it reproduces. The ADR register's six statuses are correct against
the seventeen files, one by one.

**The eleventh collision exists.** It is the same species as the tenth — a test whose name describes
one thing while its body closes a set the plan schedules units to grow — and it is again not a source
module. Both arms measured.

---

## What I ran, and what it said

All at HEAD `b7fd35d`, from the repo root:

```
python3 docs/reviews/check-coupling.py docs/DESIGN.md
  exit=0   60 STRIDE rows, 17 Critical/High, all 60 dispose of themselves, 23 naming a §8 case

python3 docs/reviews/check-coupling-controls.py
  exit=0   34/34 controls fired; post-run re-check of the real DESIGN.md: exit=0

python3 docs/reviews/check-coupling-sweep.py
  exit=0   0 escapes are holes

.venv/bin/python -m pytest -q
  90 passed, 2 deselected in 1.46s      (0 skipped)

bash scripts/check-u0-test-controls.sh    11/11 controls fired
bash scripts/check-u15-gate-controls.sh   15/15 controls fired, clean post-run re-check

python3 docs/reviews/check-obligations.py
  exit=0   28 mappings, 21 anchors verified, 7 recorded absent      <- see M1
```

**Every number in draft 8's re-pinned measurement block at `:1844-1849` reproduces at the SHA it
names.** `git status --short` after the run showed no change to any file I touched.

---

## HIGH

### H1 — The eleventh collision: the collection guard turns red on the first test FILE whose tests are all marker-excluded, and U5 is scheduled to create exactly that file

`tests/test_collection_guard.py:139-155` compares two sets and asserts the difference is empty:

```python
def test_every_test_file_is_reachable_from_testpaths() -> None:
    discovered = _discovered_test_files()      # rglob("test_*.py") over the tree
    collected  = _collected_test_files()       # parsed from --collect-only
    orphans = sorted(p.relative_to(REPO_ROOT).as_posix() for p in discovered - collected)
    assert not orphans, (...)
```

**`_collected_test_files()` runs collection through the marker selector** —
`tests/test_collection_guard.py:81-82` passes `-m` / `not credentialed and not network` to the
subprocess. A file every one of whose tests carries `credentialed` or `network` is therefore
**discovered and not collected**, and lands in `orphans`.

The module's own comment says the opposite. `tests/test_collection_guard.py:147-148`:

> `# The credentialed subtree is collected but deselected by marker, so it appears in`
> `# --collect-only output. Anything discovered and NOT collected is the defect.`

**That claim is false, and it has never been tested, because `tests/credentialed/` holds one file and
it is `README.md`** (`ls tests/credentialed/` → `README.md` only). The guard passes today only
because the two `network`-marked tests that exist (`tests/test_manifest.py:85`, `:115`) sit in a file
whose *other* tests are unmarked, so that file is still collected. **No test file in this repository
is presently wholly marker-excluded, so the branch the comment describes has never run.** A green
licenses only what it checked.

**Measured, both arms, in a scratch tree outside the repository**, on this project's own interpreter
(`.venv/bin/python`, pytest 9.1.1), with the real `pyproject.toml` copied in and the real guard module
copied in unmodified:

```
TREATMENT  tests/credentialed/test_live.py  (one @pytest.mark.credentialed test)
           tests/test_net.py                (one @pytest.mark.network test)

  test_every_test_file_is_reachable_from_testpaths  FAILED
  AssertionError: test files exist but are not reachable from `testpaths`...
      tests/credentialed/test_live.py
      tests/test_net.py
  1 failed, 2 passed

CONTROL    the same tree, those two files deleted, nothing else changed
  3 passed
```

The instrument behind it, run directly so the mechanism is visible rather than inferred:

```
$ pytest --collect-only -q --tb=no -o addopts= -p no:cacheprovider \
         -m "not credentialed and not network"
tests/test_plain.py::test_plain
1/3 tests collected (2 deselected)        <- the two deselected files are ABSENT from the output
```

**The plan schedules the file that fires this.**

| Where | What it schedules |
|---|---|
| `IMPLEMENTATION-PLAN.md:740` | *"**U5 adds the FIRST credentialed arm**, and tightens CI's credentialed-collect step"* |
| `:1640-1641` | *"The credentialed suite is written as the units land... **Each tool unit adds its credentialed arm** behind the declared marker"* |
| `:296-300` | a `network` marker beside it, with *"a unit that adds a network-touching arm"* addressed directly |
| `tests/credentialed/README.md:12-19` | *"The contract for a unit adding an arm here"* — three bullets, **none of which is the guard** |

**Nothing warns the unit.** §4's only statement about the guard, at `:1406-1407`, is:

> *"the collection guard is live: a `test_*.py` created anywhere **outside `testpaths`** now turns the
> suite red rather than being silently uncollected."*

`tests/credentialed/` is **inside** `testpaths` (`pyproject.toml:69`, `testpaths = ["tests"]`). A U5
agent reads that sentence, puts its arm exactly where `tests/credentialed/README.md` tells it to, and
is red anyway — for a reason the sentence says cannot happen and the guard's own comment says is
handled. **The shape of the red is the trap, again**: the failure message reads *"test files exist but
are not reachable from `testpaths`, so they never run and the suite is green without them"*, which is
a false diagnosis of a correctly-placed file, and the cheapest green is to add the new directory to
`_SKIP_DIRS` at `:40-48` — which deletes the guard's coverage of the whole credentialed subtree, the
one subtree `DESIGN.md:1244-1249` exists to keep from rotting.

**Why this is the same species as collision 10 and not a repeat of it.** Collision 10 is a unit
against an assertion over `[project] dependencies`. This is a unit against an assertion over *the set
of collectable files*. Both are tests closing a set the plan schedules units to grow; both were
invisible from the plan because the ownership model is drawn on source modules; and both have a name
that describes something narrower than the body —
`test_every_test_file_is_reachable_from_testpaths` is a claim about `testpaths`, and the body is a
claim about the marker selector.

**This is not an ADR.** `git show 135c3ac:docs/DESIGN.md` is silent on the guard — the plan says so
itself at `:451-452` (*"It is not a design finding and does not need an ADR. `DESIGN.md` is silent on
the guard"*), and `:1200-1205` mandates collecting the credentialed suite, which the fix below
strengthens rather than weakens.

**Suggested fix (MY SUGGESTION — verify before adopting), two parts.**

1. **The build.** Drop the `-m` selector from `_collected_test_files()`
   (`tests/test_collection_guard.py:81-82`). `--collect-only` does not execute anything, so collecting
   the excluded arms costs nothing and is what the guard actually means to measure. Verified in the
   same scratch tree: with the selector removed, all six node ids including
   `tests/credentialed/test_live.py::test_needs_a_credential` and `tests/test_net.py::test_needs_network`
   appear, exit 0, and the guard's set difference is empty. Add a control that *plants* a wholly
   credentialed file and asserts the guard still passes, so the branch stops being untested — and
   correct the comment at `:147-148`, which is the load-bearing false claim.
2. **The plan.** Add it as **collision 11** and restate `:1450`'s floor-not-ceiling sentence with the
   count corrected to eleven; extend §4's `tests/conftest.py` neighbourhood with a shared-surface row
   in the same container-and-rows form:

   | Shared file | Rule |
   |---|---|
   | `tests/test_collection_guard.py` + the marker set | **U0 owns it.** Its `discovered - collected` assertion runs collection **through the `-m` selector**, so a test file whose tests are *all* `credentialed` or *all* `network` reads as an orphan. **U5 lands the first such file.** The unit that adds the first wholly-excluded test file also drops the `-m` from `_collected_test_files()` and adds the planted-file control, **in the same commit as its arm** — it does not add a directory to `_SKIP_DIRS` |

   And repoint `:1406-1407` — *"outside `testpaths`"* is not the trigger — and add the guard as a
   fourth bullet to `tests/credentialed/README.md`'s *"contract for a unit adding an arm here"*.

---

## MEDIUM

### M1 — A fourth reviewer gate landed in `docs/reviews/` with no CI step, no ownership row and no mention in the plan, and it is the gate whose subject is every artifact the remaining fifteen units will move

`docs/OBLIGATIONS.md` and `docs/reviews/check-obligations.py` landed at `b993ada` / `328dfcb`, two
commits before the SHA draft 8 pins its own measurements to. It runs clean today (28 mappings, 21
anchors verified, 7 recorded absent, exit 0). **Nothing runs it.**

Positive-controlled: `grep -n "obligations\|check-obligations\|OBLIGATIONS\|check-resweep"` over
`.github/workflows/ci.yml` and `.pre-commit-config.yaml` returns **zero hits in both**, against a
control of the same grep over the repo, which returns eight hits — all in `docs/`. So the zero is a
real absence and not a bad search. A repo-wide `grep -rn "check-obligations"` finds it referenced only
by `docs/OBLIGATIONS.md`, `docs/reviews/CONF-6-PROPAGATION-AUDIT.md` and its own docstring.

**Why this is a plan finding and not only a tree finding.** Three things sit on the plan:

1. **The plan's CI list is the register for exactly this.** `:363-371` enumerates what CI runs and
   names the *three* `check-coupling*.py` scripts individually. A fourth checker of the same class,
   living in the same directory, absent from that list and from every workflow, is a visible
   asymmetry the plan is the only document positioned to record.
2. **`OBLIGATIONS.md` decays under the plan's own schedule, not under U0's.** Its map is
   B-number → the artifact that discharges it, anchored to text in `pyproject.toml`, `ci.yml`,
   `.env.example` and `CONTRIBUTING.md`. **U1, U5, U11, U13 and U15 all edit those files.** The file's
   stated purpose (`docs/OBLIGATIONS.md:14-19`) is to stop an obligation reverting silently when
   somebody deletes the line that met it — and with no gate, that is precisely what a unit editing its
   own block will do, unnoticed. This is the `pre-commit`-undeclared shape one level up: **a control
   that is not wired is not a control**, which this project has now paid for twice.
3. **`b7fd35d` edited three U0-owned files from outside §4's closed editor lists.** That commit
   appends B-number comments to `pyproject.toml`, `.env.example` and `.github/workflows/ci.yml`
   (`git show --name-only b7fd35d`). §4's `ci.yml` row at `:1324` gives the file to U0 with a closed
   later-editor list — *"U1, U11, U13 and U15 each own exactly the block naming their unit and touch
   nothing else"*, plus U5 — and `:1325` does the same for `pyproject.toml`. **The obligation-annotation
   pass is a cross-cutting editor of both, and it is in no row.** It is the same failure mode as
   collision 7 and collision 10: a class of write nobody classified.

I rate this Medium rather than Low because, unlike `mirror.yml:28` (round 6's L2, a one-line residue),
this is an entire control class with no trigger, whose subject is the file set every remaining unit
writes into, and it is unmentioned in a plan that pins its own measurement block to a commit *from
that same pass*.

**Suggested fix (MY SUGGESTION — verify before adopting), three parts, all small.**

1. Add a CI step beside the three coupling gates:
   `python3 docs/reviews/check-obligations.py` — it is a plain `python3` script with no project
   imports, exactly like `check-coupling.py`, so it needs no `uv run`. Add
   `--controls` as its own step if the controls arm is intended to be enforced; I ran only the default
   arm.
2. Extend `:363-371`'s CI list with it, and add one rule beside §4's `changelog.d` rule:
   *"A unit that edits a line `docs/OBLIGATIONS.md` anchors to updates the mapping in the same commit;
   `check-obligations.py` is the check."*
3. Add a §4 shared-file row (or extend the `pyproject.toml` and `ci.yml` rows) admitting the
   obligation-annotation class of edit, so the closed editor lists stop being false at HEAD. Name
   `docs/OBLIGATIONS.md` as U0's, since it anchors into U0's files.

---

## LOW

### L1 — Draft 8 fixed round 6's stale collision count and immediately recreated the identical defect one section away, in the table that carries collision 10

Round 6's L1(a) was *"nine collisions"* in the headline above a nine-item list, recapped as *"eight"*
at `:1485`. Draft 8 fixed it: `:1450` reads **ten**, `:1579` reads *"the ten collisions above"*. Both
verified.

**The shared-file table went from three rows to five in the same draft, and both prose counts of it
still say three.** The table is `:1322-1328` — header, separator, then five rows: `ci.yml`;
`pyproject.toml`; `mirror.yml` and `pr-title.yml`; the `[project] dependencies` + `uv.lock` +
`test_manifest.py` surface; `tests/conftest.py`. Draft 8 added rows three and four itself, from round
6's L2 and H1.

- `:1410` — *"In Wave A itself the only files two units touch are **the three** in the shared-file
  table"*
- `:1412` — *"Draft 6 said 'the one shared file is `pyproject.toml`' in the same section whose table
  already listed two, and **now lists three**"* — a sentence whose entire subject is a count going
  stale under a growing table

`:1412` is the harder one: it is offered as the corrected version of a sentence that survived the
finding that falsified it, and it is wrong in the same way, in the same draft that corrected it.

**Suggested fix (MY SUGGESTION — verify before adopting):** `:1410` → *"the five in the shared-file
table"*; `:1412` → *"...whose table already listed two, and now lists **five**"*. Consider deriving
both from the table the way §4 already derives the lane count from the earliest-start column —
*"every row in the shared-file table above"* — since this is now the second draft in a row to leave a
count behind its own table.

### L2 — The header says three places gate on "until ADR-0012 exists"; there were two, and only two were corrected

`:29-31` — *"**three places** gate on **'until ADR-0012 exists'** ... Every ADR gate now reads
**Accepted**."* `:1522` repeats it: *"this is the same error in **all three places** the plan gates on
an ADR."*

**Draft 7 had two.** `git show 80a7fd0:docs/plans/IMPLEMENTATION-PLAN.md | grep -n "ADR-0012\|constraints module\|constraints\.py"` returns `:1444` and `:1818-1822` — two gate sites, no third.
Draft 8 corrected both: `:1519` (*"until **ADR-0012 is ACCEPTED**"*) and `:1959` (*"Until that ADR is
ACCEPTED"*). `:1968` says so itself — *"corrected here and in collision 8"*, which is two — and the ADR
register row at `:1750` says *"Gated on in collision 8 and Q5"*, which is also two. **The plan
contains three internal statements of this count and two of them say two.**

This is the self-audit's failure #1 species — a number narrating history rather than counted —
recurring in the paragraph that reports the fixes for it. It understates nothing and misleads no
agent, which is why it is Low.

**Suggested fix (MY SUGGESTION — verify before adopting):** `:29` → *"two places"*; `:1522` → *"in
both places the plan gates on an ADR"*. If a third site was intended (Q6/ADR-0013 reads as a
disposition rather than a gate, and collision 5's *"that is an ADR"* is a rule rather than an
existence gate), name it instead — an unnamed third is the ambiguity.

### L3 — The amendment table gained round 6's four rows and is still two commits short, and one of the two is the SHA draft 8 pins its own measurements to

`:494-503` now carries eight rows and, better than round 6 asked for, a self-upkeep rule at `:505-510`
ending with a verification command:

> `git log --oneline b53886e..HEAD -- pyproject.toml .github/workflows/ci.yml tests/ scripts/`

**Run as written, that command returns ten commits; the table has eight.** The two it does not have:

| Commit | What it changed in U0's files |
|---|---|
| `2228f19` | `ci.yml` — TruffleHog `@main` → a release tag, *"in the step whose entire job is finding secrets"*. It **predates every row in the table** and was missed by drafts 7 and 8 and by round 6 |
| `b7fd35d` | `.env.example`, `.github/workflows/ci.yml`, `pyproject.toml` — the B-number obligation comments (M1 above). **This is the SHA `:1844` pins the gate measurements to**, so the draft demonstrably knew it existed |

The plan's own certainty check falsifies the table it is printed beside. That is a smaller defect than
the four-commit gap round 6 found — the rule now exists and the command is right — which is why it
stays Low.

**Suggested fix (MY SUGGESTION — verify before adopting):** add both rows, and widen the embedded
command to the file set the table actually covers: `... -- pyproject.toml uv.lock .github/workflows/ tests/ scripts/ .gitignore .env.example`. Verified: the plan's command as printed returns **ten**
commits against an eight-row table, and the widened form returns **eleven** — the extra one being
`9ca76fe`, which the plan's own file list cannot see because it names `ci.yml` and not the workflows
directory. That is L3 and round 6's L2 landing in the same place: **a file list that names one file in
a directory selects for the files it does not name**, and the plan's verification command has the
identical defect its `mirror.yml` ownership row was added to fix.

### L4 — Round 6's L1(d) was applied for the arithmetic and not for the population, so one sentence still mixes the nine defects with a MET-BY-ACCIDENT item

`:66-71` correctly replaces draft 7's *"six of its nine (six plus two is eight)"* with *"**All nine of
its defects are now disposed of**, across four commits and not two"*, names all four commits, and
records the `mirror.yml:28` residue. All verified.

The half not applied: `:70-71` still reads *"**The two** that land on this plan — the README's
Contributing section and the unowned changelog obligation — are folded into U13 and §4."* Following
*"all nine of its defects"*, *"the two"* reads as two of the nine. It is not. **The changelog item is
A-5, a MET-BY-ACCIDENT row** — `COMPLIANCE-SPEC-PASS.md:135` (*"3.0.2 `CHANGELOG.md` — MET BY ACCIDENT
— A-5 below"*) and `:515` (*"A-5 — `CHANGELOG.md` conformance is unrecorded and ungated"*) — and the
nine are the 7 MISSING plus 2 CONTRADICTED. Round 6's suggested wording named F-6 and A-5 separately
for exactly this reason. The word "A-5" appears nowhere in the plan (`grep -n "A-5"` → zero hits;
positive control: the same grep over `COMPLIANCE-SPEC-PASS.md` returns three).

**Suggested fix (MY SUGGESTION — verify before adopting):** `:70-71` → *"What lands on this plan is
the README's Contributing arm (**F-6**, folded into U13) and, from the MET-BY-ACCIDENT set, the
unowned changelog obligation (**A-5**, folded into U13 and §4)."*

### L5 — Draft 8 was committed under a message that says it is draft 7 with six defects still open

`4e5a1b2` is titled ***"Land plan draft 7, with its six known defects held open for draft 8."*** Its
body says ***"DRAFT 7 IS KNOWN WRONG IN SIX PLACES"*** and closes with ***"Draft 8 applies round 6's 1
High, 2 Mediums and 5 Lows together with these six"*** — stated as future work.

**The content of that commit is draft 8, with all of it already applied.**
`git show 4e5a1b2:docs/plans/IMPLEMENTATION-PLAN.md | head -3` reads *"Status: **DRAFT 8.** Revised
against `PLAN-REVIEW-R6.md`"*, and `git show 4e5a1b2:docs/plans/IMPLEMENTATION-PLAN.md | diff - docs/plans/IMPLEMENTATION-PLAN.md`
is **byte-identical** to the working tree I reviewed. The commit landed during this round.

This is not a plan defect — the file is right — but it corrupts the one instrument this plan tells its
readers to trust. `:505-510` says a reader who needs certainty about U0's amendments runs
`git log --oneline`; §8 and the amendment table are both built on git as ground truth; and this
project's standing rule is *verify code content, not commit messages*, which exists for exactly this.
Against this history, `git log` reports that draft 7 landed with six defects open, when draft 8 landed
with them closed. **Round 8, briefed as I was that "draft 8 is uncommitted in the working tree", will
find it committed under a draft-7 label** and has to reconcile that before it can start.

**Suggested fix (MY SUGGESTION — verify before adopting):** it is HEAD's parent, so an amend rewrites
`main` — which this project does not do lightly and which other agents' checkouts are sitting on. The
safer form is a one-line follow-up commit recording the mislabel, in the same shape as `328dfcb`
(*"Correct `b993ada`: ..."*), which is the precedent this repository already set two commits earlier.
Whichever is chosen, draft 9's header should note that draft 8 is committed at `4e5a1b2` under a
draft-7 message, so the next round is not briefed against a working tree that no longer differs.

---

## What I checked and found clean, stated so the absence of a finding is bounded

**Round 6's High, re-derived rather than accepted — and its rule tested for sufficiency, which is what
I was asked.** `tests/test_manifest.py:49` is the exact-set assertion; `pyproject.toml` holds three
runtime pins. The new row at `:1327` is correct in substance. **Two questions about it, both settled
in its favour:**

- *Does the rule work for two units that must both add a dependency?* The row's answer is
  sequencing — *"Units adding a runtime dependency are therefore SEQUENCED on this surface, never
  concurrent."* **I checked whether that is schedulable against §4's own wave tables and it is, with
  room to spare: no two dependency-adding units are ever concurrent under the current schedule.** U1
  (`pydantic-settings`) is Wave A, concurrent only with U2 and U11, neither of which adds a
  dependency. U3 (`loguru`) and U4 (`defusedxml`) are Wave B and `:1417-1420` already forbids running
  them concurrently for an unrelated reason. U7 (`tenacity`, `circuitbreaker`) is Wave C, concurrent
  with U8, U12 and U9, none of which adds a dependency. **So the rule contradicts nothing and costs no
  lane.** It is worth saying that in the row — as written it reads like a constraint an orchestrator
  must enforce, when it is in fact already satisfied by the dependency order, and an orchestrator that
  believes it needs a lock will serialise lanes it does not have to.
- *Is the tenth collision the one that breaks U1?* Yes, and it is the only one. I checked the whole of
  U1's write set against every closed-set assertion in the tree; see the next two entries.

**Round 6's M1, every factual claim read at source.** `pyproject.toml:50` → `"pre-commit>=3.7"`;
`uv.lock:523`, `:541`, `:1150` → present and resolved at 4.6.2; `git merge-base --is-ancestor 80a7fd0
HEAD` → in history. Both residues confirmed: `ci.yml:283` is
`uv tool run pre-commit@4.6.2 run --all-files --show-diff-on-failure`, and
`backend/tech-stack.md:157` and `:172` both read `"pre-commit>=4.0.0"` — I read both numbered lines
and they are identical. Draft 8's rewrite at `:1119-1145` is accurate in every particular, is a
rewrite in place rather than an append, and keeps the `uv run` false-negative measurement.

**Round 6's M2 — every Status in the ADR register table checked against its own file, not sampled.**
`for f in docs/adr/0*.md; do grep -m1 '^\*\*Status:\*\*' "$f"; done`:

| ADR | File says | Table says |
|---|---|---|
| 0012 | Proposed | **Proposed** ✔ |
| 0013 | Proposed | **Proposed** ✔ |
| 0014 | Proposed | **Proposed** ✔ |
| 0015 | Accepted | **Accepted** ✔ |
| 0016 | Accepted | **Accepted** ✔ |
| 0017 | Proposed, `Type: Design change` | **Proposed, `Type: Design change`** ✔ |

**6 of 6.** 0001-0011 are all Accepted, so *"the eleven ADRs that existed at the freeze"* carries no
hidden Proposed. Counts: `git ls-tree --name-only 135c3ac docs/adr/ | grep -c '^docs/adr/0'` → **11**;
`ls docs/adr/0*.md | wc -l` → **17**. Both of `:1744`'s numbers are right. **This is the whole
population, not a sample** — the one place in this review where that is true of a citation class.

**Round 6's five Lows.** L1(a) fixed at `:1450`/`:1579` (see L1 above for what it recreated).
L1(b) fixed — `:1550` reads *"collision 5 above"*, and `:1554` records the old error. L1(c) fixed —
the footer reads draft 8. L1(d) fixed for arithmetic, not for population (L4 above). L2 — the plan
now carries the `mirror.yml` + `pr-title.yml` ownership row at `:1326` and the residue at `:500`;
**at `b7fd35d`, where I measured, `.github/workflows/mirror.yml:28` was still `actions/checkout@v4`**
and `ci.yml` was `@v6` at `:77`, `:139`, `:330`, `:411`, `:458` (five places). **See the tree-moved
note below: `9ca76fe` has since closed it, so the plan's `:500` and `:1326` residue claims are now
stale in the tree's favour and want rewriting rather than deleting** — the ownership row is the
finding's real content and should survive. L3 — `:1740-1743` now excepts `STANDARDS.md` and
`COMPLIANCE-SPEC-PASS.md` from the declared-unread list. L4 — `:363-371` now names the `links` job,
the weekly cron and the PR-title workflow. L5 — see L3 above.

**The self-audit's five corrections.** #1 *"five commits"* at `:40`. #2 *"All nine ... disposed of ...
four commits"* at `:66-68`. #3 *"6 insertions, 1 deletion"* at `:496` — confirmed against
`git show --numstat db5c21e -- scripts/check-u0-test-controls.sh`. #4 the measurement block re-pinned
to `b7fd35d` at `:1844` and re-run — every number reproduces. #5 the eleven-vs-seventeen bound at
`:1744` with the register table. **All five applied, all five verified.**

**Every closed-set assertion in `tests/` and `scripts/`, enumerated rather than sampled, and checked
against what the plan schedules.** Found by `grep -n "== {\|== \[\|len(.*) ==\|frozenset(\|set("` over
`tests/*.py` and `scripts/*.py` — eleven sites:

| Site | Closes | Does the plan schedule growth? |
|---|---|---|
| `test_manifest.py:49` | the runtime dependency set | **yes — collision 10, now governed** |
| `test_collection_guard.py:152` | the collectable-file set | **yes — H1 above, not governed** |
| `test_repo_hygiene.py:74` | `len(.env.example vars) == 15` | **no.** Diffed both ways: `JOBVITE_*` tokens in `git show 135c3ac:docs/DESIGN.md` vs `.env.example` → **empty in both directions**; the same diff against the plan → empty. No sixteenth variable is named in the frozen design or in the plan. Round 6's dismissal holds, independently |
| `test_repo_hygiene.py:136` | `.gitignore` negations `== {"!.env.example"}` | no — no unit adds a negation |
| `test_error_contract.py:107` | `REQUIRED_MEMBERS` 7-tuple | no — it is `error-contract.md:66` verbatim |
| `test_error_contract.py:246`, `:257` | the seven registry `ProblemKind`s | no — `DESIGN.md:510-511` forbids minting locally, and no unit plans an eighth. ADR-0017 would swap `UNMAPPED`'s type, not add a kind, and the dict comprehension at `:237-241` dedupes by `.type`, so the count holds either way |
| `test_error_contract.py:313` | no `success:` envelope under `src/` and `tests/` | yes, and **correctly so** — it is a ban, and `:305-312` already says it is near-vacuous today and must be re-asserted by U14 (`:1253-1259`) |
| `test_fixture_path.py:46` | `EXPECTED_FIXTURES` | **no — it is `<=`, a subset**, so adding a fixture is a non-event. Correctly built |
| `check-committed-file-types.py:56`, `:81` | allowed extensions / basenames | no. Every extension in a backticked path anywhere in the plan (`.py .md .toml .json .yml .lock .txt .sh .yaml .html`, plus `.example`) is allowlisted. `.xml` is **not** allowlisted, but nothing schedules an XML file — `grep -in xml` over the plan returns prose only, and `defusedxml` is a parser for a route the design says we do not call (`DESIGN.md:337-339`) |
| `test_file_type_gate.py:256`, `:263` | allowlist-parser fixtures, in `tmp_path` | no — self-contained |

**The `Network-dependent arms` CI step** (`ci.yml:192-193`, `uv run --frozen pytest -m network`) is
not a latent exit-5 failure: two network-marked tests exist at `tests/test_manifest.py:85` and `:115`,
and running the selector gives `2 passed, 90 deselected`, exit 0.

**Not defects, checked and dismissed.** U1's `[project.scripts]` addition trips nothing — no assertion
in `tests/` closes over `pyproject.toml`'s key set. The `[tool.uv] prerelease` and `line-length`
assertions are single-value, not set-closing. `tests/credentialed/` lacking an `__init__.py` where
`tests/` has one is not the cause of H1 — the failure is the marker selector, not packaging, and the
scratch reproduction had no `__init__.py` either. `changelog.d/` fragments remain one-per-unit.

---

## What I could NOT settle

For what I could not resolve, not for what I did not try.

1. **Whether removing `-m` from `_collected_test_files()` has a cost I have not seen.** I measured that
   it collects the excluded arms and that the guard then passes with wholly-excluded files present.
   What I did not test is a credentialed arm that does real work at *import* time — module-scope
   credential reads are forbidden by `tests/credentialed/README.md:16-17`, but that is a convention,
   not a gate, and collection imports the module. The fix is right; whether it needs a companion rule
   is open.
2. **Whether the `links`, `codeql`, `secret scan`, `pr-title` and SBOM jobs actually pass.**
   `ci.yml:16-19` says several have never run. I ran none of the workflow. Same limit round 6 declared.
3. **Branch protection** — required checks, `skipped == success`, approvals. Out of tree, and the
   `github` MCP server failed to connect this session (*"Authorization header is badly formatted"*).
   Unasserted in both directions.
4. **Whether `check-obligations.py --controls` passes.** I ran only the default arm (exit 0). If the
   controls arm is red, M1's suggested CI step needs the default arm only, and that changes the fix.
5. **Whether a `uv lock` regeneration with the four new direct dependencies still resolves 72
   packages.** Same reason as round 6: it would write `uv.lock` in a checkout other agents are working,
   and I was told not to.
6. **Whether ADR-0012, 0013, 0014 or 0017 will be accepted.** All four are Proposed; the plan gates
   correctly on Accepted in both ADR-0012 sites and records ADR-0017 as open at `:1763-1768`.
7. **How many `standards/...` citations in the plan hold at source.** Round 6 verified ten of an
   unmeasured population. I verified two more (`backend/tech-stack.md:157`, `:172`) for M1's sake and
   did not sweep the rest. §8 declares this class unverified and the residue is still real.

---

## The tree moved while this round ran, and here is exactly what it changes

I measured everything at **`b7fd35d`** and pinned every number to it. Three commits landed during the
write-up: **`1b7975b`** (B101, the reviewer checklist), **`9ca76fe`** *"Close C-1 at 6 of 6, and guard
the directory instead of the file"* — which sets `.github/workflows/mirror.yml:28` to
`actions/checkout@v6`, re-verified at source — and **`4e5a1b2`**, now HEAD, which is L5. I re-read
`mirror.yml:28` after the move and diffed the plan against `4e5a1b2` (identical). Nothing else in this
review's evidence base is touched: H1's failing assertion, the seventeen ADR statuses and the
`.env.example` variable set are unaffected by all three.

**What it changes for draft 9:** the `mirror.yml` residue is closed, so `:500` (*"It did not reach
`mirror.yml:28`, which is still `@v4`"*) and `:1326` (*"**still `@v4` today**"*) become false
statements about the tree the moment draft 9 is read. **Rewrite them in place — do not delete the
row.** The ownership rule is what the finding was actually for, and `9ca76fe`'s own message says so:
*"the plan's shared-file table named `.github/workflows/ci.yml` and nothing else, so `mirror.yml` and
`pr-title.yml` were owned by nobody and therefore read by nobody."* L3's widened verification command
is the same lesson a third time.

**This is L3's and round 6's L5's mechanism arriving during a single review**, which is the argument
for the SHA-pinning discipline draft 8 adopted at `:1844` and against any count of commits.

---

*Round 7 by `plan-review-r7`, 2026-08-28. All three coupling gates, both control harnesses and the
full suite re-run at `b7fd35d`. `docs/DESIGN.md` read from the frozen `135c3ac` git object; draft 7
read from `80a7fd0`. H1 reproduced in a scratch tree outside the repository with a matched control.
No file in the repository was edited, nothing was committed, and no branch, stash or checkout
operation was performed.*
