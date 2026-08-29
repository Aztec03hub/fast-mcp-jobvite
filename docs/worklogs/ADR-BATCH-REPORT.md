# ADR-BATCH - eight Accepted ADRs applied, and `docs/DESIGN.md` re-frozen

**Branch:** `adr/batch`, rebased onto `main` at `b077202`. It was rebased TWICE: `main` moved by two
commits (round 2's review of U1, U3 and U4) while this batch was running, which invalidated the
first rebase's fast-forward and, with it, the freeze SHA the first pass had stamped. The SHA was
re-derived and re-stamped rather than carried.
**Base pinned:** `70cd2ca`, in a worktree at `/tmp/adr-batch-work`. The shared checkout was never
written to and never had anything checked out in it.

## THE NEW FROZEN SHA IS `c15b138`

`docs/DESIGN.md` was frozen at `135c3ac` for the whole project. It is now frozen at

```
c15b138  Wire check-cross-references.py into ci.yml and CONTRIBUTING, now that it is green
```

Every future brief cites `c15b138`. The re-freeze is verified rather than asserted:

```
$ python3 docs/reviews/check-design-citations.py --since c15b138
DESIGN.md is byte-identical to c15b138. No citation can have moved.
```

The value was **derived**, in the same command that wrote it, by
`git log -1 --format=%h -- docs/DESIGN.md` - never typed from a scrollback. Two commits land after
it and neither touches `docs/DESIGN.md`, which is why the freeze SHA is not the branch head.

Re-stamped where `135c3ac` named the LIVE frozen design: `docs/reviews/check-design-citations.py`'s
`--since` usage block, and `IMPLEMENTATION-PLAN.md:20`, `:144` and `:2308`. **Left alone everywhere
it records what a reviewer read at the time** - eleven files under `docs/reviews/` and
`docs/worklogs/`, plus `IMPLEMENTATION-PLAN.md:2076` and `:2318`, which describe method and history.
Rewriting those would falsify a record.

`docs/DESIGN.md` went from **1,994 to 2,045 lines**.

---

## What each ADR changed, before and after

### ADR-0012 - `utils/constraints.py`

**Before:** §3's module layout ended at `utils/normalise.py`, and the four inbound structural limits
of §2.1 were placed nowhere.
**After:** the layout carries a fifth `utils/` member with the three-line description the ADR
specifies, and the paragraph below the block states that every input model imports its constraints
from it and none defines its own. §11 untouched, exactly as the ADR requires.

### ADR-0013 - §8 gains a positive pairing for the log stream

**Before:** case #2 read, in full, *"a secret never reaching a log record, including the `jobFeed`
URL;"* - an absence a server emitting no log records passes perfectly.
**After:** a new case immediately above it asserts that **the log stream carries records for an
invocation that produced them**, and #2 is rewritten to say it is asserted against that stream
rather than against silence. Both cite ADR-0013 and the construction at the audit pair.

**One thing the ADR wanted and the design's format cannot carry.** ADR-0013 says the pairing gets
"the stronger property" by being named by `C5-I1`, a §11 row. I tried it: `check-coupling.py` parses
a Test cell as **one** case name, so `C5-I1` naming two made the row cite a case that does not exist,
and the gate went red. The pairing instead carries an explicit owner in its own text - **required by
C5-I1 (§4.1, §5.3)** - which is what GATE-2 asks for and what turned the gate green. The weaker
property is recorded here rather than papered over.

### ADR-0014 - C8-I1's evidence clause

**Before:** *"`.env.example` is committed with **empty values**"*, which is false against the tree:
seven of fifteen variables carry a deliberate value, two of them the B15 answer.
**After:** *"`.env.example` is committed with **every secret-class variable empty**"*, naming all six.
**No rating changed and no disposition changed** - C8-I1 is still Critical, still mitigated. Only the
sentence describing the evidence moved, which is precisely the limit the ADR set.

`.env.example:4`'s own *"Every value here is EMPTY on purpose"* is the sibling ADR-0014 names and
explicitly does not govern. **It is still there.** Left to U1, as the ADR says.

### ADR-0017 - the unmapped row

**Before:** `| Anything unmapped | about:blank per :212 | - |`, a status column of `-` against
`:489-490`'s requirement that every problem object carry a `status`.
**After:** `| Anything unmapped, including an unhandled exception in a tool body |
/problems/internal-error, "Internal Server Error" | 500 |`, followed by a paragraph keeping
`about:blank` for its **actual** scope - an unmapped HTTP status received from Jobvite - and saying
so. **The ADR does not close the `about:blank` question and neither does this**: the constant
survives, unreachable today, with the reason written at the constant.

### ADR-0018 - the exit status

**Before:** `finally: sys.stdout.flush(); sys.stderr.flush(); os._exit(0)`.
**After:** the ADR's block verbatim - `status = 0`, `except KeyboardInterrupt`, `except BaseException`
logging and setting `EXIT_SOFTWARE` and re-raising, `finally` flushing and calling
`os._exit(status)`. Plus a paragraph explaining why the constant was the defect and that this must
be discharged **by side effect**, not by asserting `70` against a synthetic exception.

`os._exit` still runs **unconditionally**. The stdio hang stays closed, the SIGTERM mitigation is
unchanged, and `DESIGN.md:959-961`'s measurement stands. Only the constant moves.

### ADR-0019 - `§5.4` becomes `§4.1`

One character range, in one line. The near-miss ADR-0019 warns about -
`COMPLIANCE-SPEC.md`'s three correct `§5.4` references to its own numbering - was **not** touched;
`grep -rn '§5\.4'` over the tree now returns those three and nothing in `DESIGN.md`.

### ADR-0021 - `approval_mechanism`

**Before:** two rows - §8's audit case and `C4-R1`, a **High** row - required "the mechanism that
produced it (§5.3)", and §5.3 said nothing about a mechanism.
**After:** §5.3's approval paragraph defines `approval_mechanism` with the closed set
`elicitation`, `sampling`, `no_handler`, says why the set is closed, says the value names a protocol
path and carries no PII, and says explicitly that this is *how* the answer arrived and not *who*
gave it, so ADR-0009's boundary is untouched. §8's audit case gains the arm. Both rows cite §5.3 and
§5.3 now carries the subject, which is the whole point.

### ADR-0022 - the cookie jar

**Its subject is not `DESIGN.md`.** `grep -in cookie docs/DESIGN.md` returns nothing. The clause is
`docs/research/JOBVITE-CONTRACT.md` §2.3, which **is** in this repository.

**Before:** *"**Do not implement a cookie jar.**"* - a prohibition an implementer discharges by
doing nothing, which ships the session Jobvite told us not to carry.
**After:** *"**Clear the cookie jar after every request**"*, with the measured `httpx2` 2.12.0
default beside it. The `[RECORDED]` observations - four `AWSALBAPP-*` cookies, all `_remove_` - are
untouched; only the instruction derived from them changes.
`IMPLEMENTATION-PLAN.md`'s U4 bullet is rewritten to match.

**No code change was needed.** U4 already clears the jar in a `finally` in `JobviteClient.request`,
with `test_no_cookie_jar_is_carried_between_requests` and the positive control
`test_positive_control_httpx2_DOES_carry_cookies_by_default` behind it.

---

## The citations

**841 at the pinned base, 847 now, across 82 files.** Three separate repoint passes were needed,
because the batch edited `DESIGN.md` three times: the ADRs themselves, then the cross-reference
gate's finding, then §8's new case gaining an owner.

| Pass | Against | MOVED | BROKEN |
|---|---|---|---|
| 1 | `135c3ac`, the original freeze | **693** | **40** |
| 2 | the ADR-batch commit, before the cross-reference fix | **569** | 0 |
| 3 | the cross-reference-fix commit, before §8's case gained an owner | **266** | 0 |
| post-base (task #11) | `135c3ac` | **1** | 3 |

Passes 2 and 3 were run against commits on this branch **before** it was rebased onto
`origin/main`; those SHAs no longer exist and are described rather than quoted, because a dead SHA
in a report reads exactly like a live one.

Every MOVED line was applied by **`docs/reviews/repoint-design-citations.py`**, written for this and
committed rather than left in `/tmp`. It parses `check-design-citations.py`'s own output with a
regex, asserts it parsed a non-zero number of MOVED lines, keys on **(file, line-it-sits-on,
old-range)** so a line carrying several citations is safe and `DESIGN.md:151` cannot match inside
`DESIGN.md:1512`, and fails loudly naming any citation the report claimed and the tree does not
carry. **Nothing was retyped.**

### How the repoints were verified, since a repoint that resolves is not a repoint that is right

Not by arithmetic. By **content identity**: for all 693 of pass 1, the new range's text was compared
byte for byte with the old range's text out of `git show 135c3ac:docs/DESIGN.md`.

```
677 repoints verified by CONTENT IDENTITY, 16 mismatched
CONTROL a deliberately wrong target is rejected: True
```

All 16 were inspected individually. Every one is a **range** whose first and last lines are still
byte-identical and which grew to contain new prose - `970-981 -> 990-1023` around the shutdown block,
`567-713 -> 580-733` around the whole of §5.3, `496-519 -> 502-532` around the error registry. One,
`F10-RULING.md:144`, was the same length and still differed: the diff showed a single interior line,
and it was my own ADR-0018 wording change. **None was a repoint landing on the wrong subject.**

### The 40 BROKEN, and what happened to each

`BROKEN` means the cited line itself changed, so the tool refuses to guess. So did I.

**20 repointed BY SUBJECT** - the subject survived at a new address, each read out of the new text
and matched against the old:

| Old | Subject | New |
|---|---|---|
| `1760` | the `C8-I1` row | `1808` |
| `507-515` | the error registry table, header through the unmapped row | `513-521` |
| `515` | the unmapped row | `521` |
| `974-978` | the §7.4 shutdown code block | `994-1008` |
| `1289-1295` | §8 #18, lifespan teardown on SIGTERM | `1337-1343` |
| `1294-1295` | its last two lines | `1342-1343` |
| `1229-1231` | "This case is positive on purpose", through the pairing sentence | `1277-1279` |
| `1229-1232` | the same plus the PII case below it | `1277-1280` |

in `.pre-commit-config.yaml`, `IMPLEMENTATION-PLAN.md` (x6), `PLAN-REVIEW-R3.md`,
`PLAN-REVIEW-R4.md` (x2), `U1-IMPL-REPORT.md`, `U3-IMPL-REPORT.md`, `server.py`, `test_audit.py`
(x2), `test_error_contract.py`, `test_shutdown.py` (x3). The final line numbers above shifted once
more in passes 2 and 3 and were carried by the tool, not by hand.

**18 left alone deliberately.** These do not cite a live subject; they **record where a defect was**,
and the defect is what these ADRs fix. Repointing them would falsify the record:

- `ADR-0019` x3 - its title, its Context quote, its Decision. The whole ADR is *about*
  `DESIGN.md:603`, verified against the frozen object it names.
- `ADR-0013:13`, `ADR-0014:13`, `ADR-0017:17` and `:66` - each quotes the OLD text verbatim as its
  evidence.
- `check-cross-references.py:4` and `check-design-citations.py:8` - "why this exists" prose about
  the defect.
- `check-design-citations.py:63` and `:212` - **not citations at all**: a docstring example and a
  regex test string.
- `PLAN-DRAFT9-REPORT.md:290` and `:300` - pasted tool output.
- `U0-REPORT.md:233`, `U2-REPORT.md:210` and `:225`, `U3-IMPL-REPORT.md:236`,
  `U4-IMPL-REPORT.md:254` - findings quoting the text they found wrong.

**2 rewritten with the code**, not repointed: `errors.py:85` and `:247` asserted *"the design's table
gives this row no status"*, which ADR-0017 makes false. They are replaced.

### A defect the first pass introduced, and the fix

Pass 1 silently shifted **three of `check-design-citations.py`'s own example citations** - the
docstring illustrating the two forms, and the regex string inside `controls()`. A script that WRITES
an example citation is not CITING anything. The repointer now skips any line carrying
**`REPOINT-EXEMPT`**, five such lines are marked, the examples are restored to the addresses they
illustrate, and a positive control asserts no unmarked citation is left in that file. Its 3/3
controls still fire.

### The citations from commits that landed on `main` while this ran

`docs/reviews/REVIEW-CODE-R2.md` arrived at `b077202`, written against `DESIGN.md` as frozen at
`135c3ac`. **Nine** of its citations were repointed, each verified by the same content-identity
check as pass 1. Its tenth, `:47`, cites `DESIGN.md:603` as the address the cross-reference gate was
red on, which is the defect ADR-0019 fixes, and is left alone with the rest of that population.

### The four citations that postdate the pinned base

Task #11's finding, handled on this branch after the rebase rather than left for merge.
`scripts/check-u1-pid1-shutdown.sh:5` cited `DESIGN.md:982-990`; verified byte-identical at
`1026-1034` and repointed from the checker's parsed output. The other three -
`docs/briefs/ADR-BATCH.md:26` and `:84`, `docs/briefs/CODE-REVIEW-R2.md:83` - all cite
`DESIGN.md:603` **as the address of the defect ADR-0019 fixes**, and are left alone for the same
reason ADR-0019's own three are.

### `OBLIGATIONS.md`

Five anchors moved and all five were repointed from `check-obligations.py`'s own parsed output:
`B59`, `B75` and `B82` into `ci.yml` when the new gate step landed, and `B78` and `B81` into
`IMPLEMENTATION-PLAN.md` when the freeze re-stamp reflowed a line. 28 mappings, 21 verified against
their subject, 7 recorded as absent. Exit 0, and `--controls` exit 0 with a green post-run re-check.

---

## The mutation rows that changed meaning

### ADR-0017 inverts U2's **M10**, exactly as it predicted

U2's row read `KILLED M10 unmapped becomes /problems/internal-error   3 failed, 31 passed`. **That
mutant is now the shipped behaviour.** The row is replaced by the mutation in its new direction and
**re-run rather than predicted**:

```
KILLED  M10 unmapped becomes about:blank (INVERTED, ADR-0017)  2 failed, 32 passed
```

killed by `test_every_registry_row_maps_to_its_registry_type_and_status[anything unmapped]` and
`test_a_problem_object_is_returned_never_raised`. **The numbers changed with the direction** - 3
failures became 2 - which is why they were measured and not carried forward.

U2-REPORT's **D1** and **D2** are rewritten in place, not appended to: D1 is now
"DECIDED, ADR-0017" and D2 records that `INTERNAL_ERROR` stopping being dead code was the answer and
the dead constant was the symptom.

### ADR-0018 adds U1's **M14** and repoints **M12**

- **M12** (`os._exit` removed from the `finally`) kept its meaning, but its anchor string moved from
  `os._exit(0)` to `os._exit(status)`. The harness used `str.replace`, which **silently no-ops on a
  moved anchor**; it now asserts the anchor is unique first. Still killed by
  `test_only_stdio_exercises_the_forced_exit`.
- **M14 is new**: `os._exit(status)` becomes a constant `os._exit(0)` again, the call still
  unconditional. That is precisely ADR-0018's defect and nothing else. Killed by
  `test_the_shipped_entry_point_is_what_the_case_exercises`, which now asserts `os._exit(status)`,
  `EXIT_SOFTWARE = 70`, and the **absence** of `os._exit(0)` anywhere in the module - the absence is
  what stops this reverting silently, and it forced the module docstring's own prose to be corrected
  too.
- **Amputation row H** removed the whole `finally` by regex against `os._exit\(0\)`, which after
  this change would have matched nothing and amputated nothing, reporting a survivor that was never
  cut. It is repointed and now **asserts `n == 1`**.

`check-u1-boot-controls.sh`: **14/14 controls fired**.
`check-u1-boot-amputation.sh`: exit 0, survivors reported as its output.

U1-IMPL-REPORT's **F1** is rewritten from "ADR filed, not applied" to "Accepted and APPLIED", with
its five `os._exit(0)` prose mentions corrected and the **still-open** part stated plainly: nothing
discharges the status by side effect yet, because nothing that can crash `mcp.run` exists.

---

## The cross-reference gate: green, and wired

`check-cross-references.py` exited 1 on exactly one finding, `DESIGN.md:603`'s `§5.4`. ADR-0019
fixed it and the gate now exits **0**: 34 numbered headings and 325 references in `DESIGN.md`, 164
in `IMPLEMENTATION-PLAN.md`, 20 in `COMPLIANCE-SPEC.md`, **0 unresolved**.

It is wired into `ci.yml`'s `design-gates` job in the same commit, with a selector control asserting
the reference count is not zero, and added to `CONTRIBUTING.md`'s gate list.

**It earned its place before it was wired.** My own ADR-0017 paragraph wrote *"RFC 9457 §4.2.1"*
with the filename on the previous line, and the checker - correctly - read it as an internal
reference and went red. **A new instance of exactly the defect class ADR-0019 is about, introduced
in the commit that fixes ADR-0019.** Nothing else would have caught it.

`CONTRIBUTING.md` also gains a section stating plainly that **`check-design-citations.py` is not a
gate and why**: it verifies that a cited line EXISTS, never that the line still carries its subject,
and a contracted range still resolves and still reads plausibly. Three such defects were found by
hand and none by any instrument. Wiring it would publish a green that means less than a reader would
assume. The repointer is documented beside it.

---

## Gates

Every one judged by **exit code on its own line**, never by grepping output.

| Gate | Result |
|---|---|
| `uv lock --check` | exit 0 |
| `ruff check .` | exit 0 |
| `ruff format --check .` | exit 0, 42 files |
| `mypy` | exit 0, 31 source files |
| `pytest` | **294 passed, 2 deselected, 0 skipped** |
| `check-committed-file-types.py --all` | exit 0 |
| `check-coupling.py` | exit 0 |
| `check-coupling-controls.py` | exit 0, **34/34 fired**, post-run re-check green |
| `check-coupling-sweep.py` | exit 0, **0 escapes are holes**, 23 rows |
| `check-obligations.py` | exit 0, 28 mappings |
| `check-obligations.py --controls` | exit 0, post-run re-check green |
| `check-plan-measurements.py` | exit 0 |
| `check-cross-references.py` | exit 0, **newly wired** |
| `check-design-citations.py` | exit 0, 847 citations, 82 files |
| `check-design-citations.py --controls` | exit 0, 3/3 fired |
| `check-u1-boot-controls.sh` | exit 0, **14/14 fired** |
| `check-u1-boot-amputation.sh` | exit 0 |

The baseline was **294 passed, 2 deselected, 0 skipped**, and it is unchanged. The two code changes
altered what existing tests assert, not how many there are.

The remaining harnesses, all exit 0:

| Harness | Result |
|---|---|
| `check-u0-test-controls.sh` | **11/11 fired** |
| `check-u15-gate-controls.sh` | **15/15 fired** |
| `check-u11-advisory-controls.sh` | **15/15 fired** |
| `check-u3-audit-controls.sh` | **15 killed, 0 not killed** |
| `check-u4-client-controls.sh` | **17 killed, 0 not killed** |
| `check-u15-gate-amputation.sh` | exit 0 |
| `check-u3-audit-amputation.sh` | exit 0 |
| `check-u4-client-amputation.sh` | exit 0 |

`pip-audit` and `check_advisories.py` were NOT run: they reach the network, and this worktree has no
credential path to it.

---

## Commits, and the merge

```
d1e15c7  Re-stamp the freeze at c15b138, and repoint the obligation anchors it moved
c4b5c04  Repoint the one post-base citation the batch could not have seen (task #11)
c15b138  Wire check-cross-references.py into ci.yml and CONTRIBUTING  <- THE FROZEN SHA
d08a96c  Fix the cross-reference gate's one finding, and exempt the checkers' own examples
31db393  ADR-0018, ADR-0022, and all eight statuses to Accepted
2efc093  ADR-0017: the unmapped condition is /problems/internal-error, not about:blank
f6bfc5b  Repoint 713 DESIGN.md citations, from the checker's own parsed output
e6ec5cb  Apply the six design-text ADRs to the frozen DESIGN.md
```

```bash
git checkout main && git merge --ff-only adr/batch && git push origin main
```

`--ff-only` matters: it keeps `c15b138` as the SHA every re-stamped document names. If `main` has
moved and a fast-forward is refused, rebase `adr/batch` again and **re-derive the freeze SHA** with
`git log -1 --format=%h -- docs/DESIGN.md` before pushing, because a merge commit or a second rebase
changes it and every re-stamp goes stale silently.

The worktree at `/tmp/adr-batch-work` is removed.

---

## What I did NOT verify

1. **That any repoint lands on the right SUBJECT rather than the right TEXT.** Content identity
   proves the new range holds the same bytes as the old one. It cannot prove the old range was
   pointing at the right thing to begin with. Every contracted range in this tree that was wrong
   before is still wrong, and this pass would not have noticed.
2. **The 16 range-spanning repoints beyond their endpoints.** I read each one's first and last line
   and diffed one of them. I did not read the interior of the other 15; a range that now *contains*
   text it did not contain before may be a worse citation than it was, and only reading each would
   settle that.
3. **ADR-0018 by its side effect.** No case forces `mcp.run` to fail for a real reason and reads the
   process's exit status. The ADR names that as what would discharge it, and it is not built. The
   structural test asserts the SOURCE says `os._exit(status)`; it never observes a non-zero exit.
4. **That `EXIT_SOFTWARE = 70` is the right value.** ADR-0018 says explicitly it does not choose it
   and a reviewer may prefer `1`. I took the ADR's number without an argument of my own.
5. **`about:blank`'s reachability.** ADR-0017 leaves it open and so do I. `UNMAPPED` is now reached
   by no code path at all, which is an unreferenced constant a future reader may delete as dead. The
   comment says why it stays; nothing enforces that.
6. **That the eight external `§n.m` references resolve in their own documents.**
   `check-cross-references.py` skips them and I did not follow them. ADR-0019 records this and it is
   still true.
7. **The advisory gates.** `check_advisories.py` and `pip-audit` were not run - both reach the
   network. Nothing in this batch touches `pyproject.toml` or `uv.lock`, and `uv lock --check`
   exits 0, so no dependency moved; but the advisory expiry half is time-dependent and could be red
   for a reason this branch did not cause.
8. **CI itself.** Nothing here has been through GitHub Actions. The `design-gates` job's new step
   was run locally and `ci.yml` was checked with a YAML parser; the workflow has not executed.
9. **The `.env.example:4` sibling ADR-0014 names.** Still says *"Every value here is EMPTY on
   purpose"* thirty-seven lines above a populated variable. Out of this ADR's scope by its own text,
   and it is U1's, but it is still false in the tree today.
10. **Whether `C5-I1` naming the pairing matters.** ADR-0013 wanted the row-naming property; the
    table's format cannot carry two case names in one cell. I gave the case an explicit owner in its
    own text instead, which satisfies GATE-2. Whether that is enough for what ADR-0013 was worried
    about is a judgement I made and did not test.
