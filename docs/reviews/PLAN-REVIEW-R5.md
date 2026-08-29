# PLAN-REVIEW-R5 - `docs/plans/IMPLEMENTATION-PLAN.md`, draft 6

Reviewer: `plan-review-r5b`, fresh. I wrote none of this plan and ran none of rounds 1-4.
Subject: `docs/plans/IMPLEMENTATION-PLAN.md` at `299cf8b`, 1543 lines.
Design read from the frozen git object: `git show 135c3ac:docs/DESIGN.md` (1994 lines), never from
the working tree.
Date: 2026-08-28.

---

## Verdict

**NOT READY** - but narrowly, and not in a way that should stop the units now in flight.

**Tally: 0 Critical / 2 High / 3 Medium / 1 Low.**

Both Highs are additions, not rewrites: one is a required gate that exists in the standards corpus
and in this repository's own compliance spec and appears in neither the design, the plan, nor the
built tree; the other is a shared-file rule the plan itself says is missing and then does not write.
Neither touches U0, U11 or U15, and neither is a design finding, so **U15's build should continue
and U0 stands.** The blocked thing is Wave C - U5, U6, U8, U9, U12 running concurrently - and both
fixes are table rows plus one test file.

I did not manufacture these. I also did not find a defect in the citation machinery, the §8 case
list, the unit decomposition, the dependency graph, or the U0 section's agreement with the build,
and I say so plainly below.

---

## What I ran, and what it said

All three gates and the suite, from the repo root, 2026-08-28:

```
python3 docs/reviews/check-coupling.py docs/DESIGN.md
  exit=0   60 STRIDE rows, 17 Critical/High, all 60 dispose of themselves, 23 naming a §8 case

python3 docs/reviews/check-coupling-controls.py
  exit=0   34/34 controls fired; post-run re-check of the real DESIGN.md: exit=0 (still green)

python3 docs/reviews/check-coupling-sweep.py
  exit=0   0 escapes are holes

uv run --frozen pytest -q
  17 passed, 2 deselected in 0.63s      (0 skipped)

bash scripts/check-u0-test-controls.sh
  11/11 controls fired.
```

Every number the plan asserts about the gates is reproduced. The controls harness reports 34 here,
which is the fourth reading of a number the plan correctly refuses to hard-code.

---

## HIGH

### H1 - The collection-guard meta-test is a corpus-level MUST, and it is in no unit, no design section, and not in the built tree

**The standard, read at source rather than through `DESIGN.md`:**

- `standards/backend/testing.md:138-141`: *"**A collection-guard meta-test is required.** Add a
  meta-test that walks the repository for `test_*.py` files and asserts every discovered file is
  reachable from the configured `testpaths`. The guard must itself live inside a configured root so
  that its own absence fails collection"*, with a worked `tests/test_collection_guard.py` at
  `:145-160`.
- `standards/devops/quality-gates.md:76-81` (API-03): *"A collection-guard meta-test ... MUST be
  present in a configured root and MUST pass in CI. **If the guard is absent** or if any test file
  lives outside the configured roots, **the CI backend test job MUST fail.**"*
- And this repository already knew: `docs/research/COMPLIANCE-SPEC.md:297-307`, §2.4
  *"Test-discovery guard (required, easy to forget) ... Create `tests/test_collection_guard.py`
  asserting no `test_*.py` exists outside `testpaths`."*

**It is absent everywhere.** `grep -n 'collection_guard|collection-guard|testpaths'` over `tests/`,
`docs/plans/IMPLEMENTATION-PLAN.md` and `docs/DESIGN.md` returns nothing. (Positive control on the
search: the same pattern hits `pyproject.toml`, where `testpaths = ["tests"]` is configured - so the
pattern works and the zero is a real absence, not a bad path.) `ls tests/` shows
`test_fixture_path.py`, `test_manifest.py`, `test_markers.py`, `test_repo_hygiene.py` and no guard.
The plan's *"CI runs, at minimum"* list at `IMPLEMENTATION-PLAN.md:271-279` does not name it.

**Why it matters here specifically, rather than as a checkbox.** This plan's entire test strategy is
selection-based - `-m "not credentialed and not network"` in `addopts`, a `tests/credentialed/`
subtree that is collected but never run, and a stated zero-skip rule. That is precisely the
configuration in which a test file landing outside `testpaths`, or a marker typo moving a file out of
the selected set, produces a green run over fewer tests than anyone believes. The plan already
understands this failure - it is why `--strict-markers` is called *"not housekeeping"* - and API-03
is the sibling defence it does not have. Fifteen units will each add test files; the guard is what
makes "the suite grew" checkable.

**A positive control on my reading of the corpus, because a reviewer quoting a standard at a project
usually finds it already met.** The adjacent requirement, API-04 skip-as-green
(`quality-gates.md:84-93`, *"assert `pytest` exit code 0 AND that the reported `SKIPPED` count is
0"*), **is** implemented, in `.github/workflows/ci.yml`'s *"Default suite, zero skips"* step with its
`grep -qE '[0-9]+ skipped'` enforcement. So the corpus is not uniformly unimplemented here and this
is a specific gap, not a sweep.

**This is not an ADR.** `DESIGN.md` is silent on the guard rather than contradicting it, and the plan
is not the design. If the team judges that a frozen design which enumerates every CI gate should have
named this one, that is a separate ADR about the design's completeness.

**Suggested fix (MY SUGGESTION - verify before adopting):** two edits and one file.

1. Add to `IMPLEMENTATION-PLAN.md:271`'s *"CI runs, at minimum"* list: `the collection-guard
   meta-test (backend/testing.md:138-141, quality-gates.md:76-81 API-03)`.
2. Add to U0's **Builds** and **Verified by**: `tests/test_collection_guard.py` - glob
   `**/test_*.py` from the repo root, cross-reference against the paths reported by
   `pytest --collect-only -q`, fail on any file not collected. Take the thorough variant
   (`backend/testing.md:162-165`), not the minimal one: the minimal form only asserts collection
   exits 0, which passes over a file that is silently uncollected - the exact defect API-03 names.
   Give it a mutation control in `scripts/check-u0-test-controls.sh`: drop a `test_orphan.py` outside
   `testpaths` in the copied tree and require the guard to go red.
3. Because U0 is built, land this as a **U0 follow-up commit**, not by reopening the unit. The plan's
   U0 precedence rule says the build wins where the two differ - it does not say the build is
   complete, and this is a gap in both.

---

### H2 - `tests/conftest.py` is a concurrent-write surface in the widest wave, and §4 names the hazard without writing the rule

`IMPLEMENTATION-PLAN.md:1252-1254`: *"**`tests/conftest.py` is the same shape waiting**: U0 owns it,
every later unit adds fixtures to it, and no row here says so yet."*

That sentence is correct and it is the whole finding. §4 opens by stating its own contract - file
ownership, *"One owner per file, for the life of the unit"* - and then leaves the one file every
test-bearing unit must write with no owner and no mechanism. For `ci.yml` and `pyproject.toml` the
plan invented a container-and-rows mechanism (`:1106-1107`); for `conftest.py` it stops at the
diagnosis.

**This is the ninth collision, and it is worse-placed than collisions 7 and 8.** By §4's Wave C table
(`:1130-1136`), U5 and U6→U7 start at U4-landing, U9 starts at U5, and U8 and U12 start together
when U5 and U6 have both completed - **four to five units overlapping in time, every one of which
adds fixtures.** U0's built `tests/conftest.py` is already module-level shared state, not just
fixtures: `REPO_ROOT`, `FIXTURES_DIR`, `PYPROJECT`, `UV_LOCK`, `ENV_EXAMPLE`, `GITIGNORE` and two
session fixtures. U4 needs a fixture returning each recorded fixture body; U5 and U8 need a
`MockTransport` factory; U9 needs a client-with-token factory. Those land in one file, concurrently,
with no rule.

An orchestrator reading `:1252` will act on it. **An agent handed U8 alone will not** - it reads §4,
finds no `conftest.py` row, and writes. That asymmetry is the same one the plan names for the U0
precedence sentence at `:249-251`.

**Suggested fix (MY SUGGESTION - verify before adopting):** apply the container-and-rows mechanism
the plan already invented, rather than a coordination rule.

Add a third row to the Wave A shared-file table at `:1105-1107`:

| Shared file | Rule |
|---|---|
| `tests/conftest.py` | **U0 owns the file and it stays small.** It holds repo paths and the fixtures-directory accessor only. **A unit that needs fixtures creates `tests/fixtures/<unit-subject>.py` as a pytest plugin and registers it in one `pytest_plugins` line** - `tests/fixtures/transport.py` (U4), `tests/fixtures/tools.py` (U5), `tests/fixtures/http.py` (U9). One file per unit, write sets disjoint by construction, same rule as `models/`. **No unit adds a fixture body to `conftest.py`** |

and add it to the numbered list as collision 9, restating the floor-not-ceiling sentence at `:1156`
with the count corrected. If the `pytest_plugins` line is judged too fine a shared edit, the
alternative is conftest-per-directory (`tests/client/conftest.py`, `tests/tools/conftest.py`), which
needs no shared line at all - I have not tested which the team prefers, and either closes it.

---

## MEDIUM

### M1 - The per-module coverage floors have no owning unit, no stated mechanism, and the answer already exists in a document the plan never read

`IMPLEMENTATION-PLAN.md:266-269` assigns them by description and not to anyone: *"**ADR-0010's
per-module floors (85% tools, 90% client, 95% `utils/`, 95 line / 90 branch on critical paths) land
with the units that create those modules**"*. The built `pyproject.toml` repeats it: *"the per-module
floors are enforced by the units that create those modules."*

No unit's section says so. `grep -n 'coverage|85%|90%|95%'` over the plan hits lines 265-268, 821,
1106, 1177, 1374 and 1399-1409 only - **nothing inside U3, U4, U5, U6, U7, U8, U10 or U12**, which
are the units that create those modules. An agent handed U5 alone builds no floor, because U5's own
1543-line-document section never mentions one. And if an agent *does* act on `:267`, the only home
configured today is `pyproject.toml` - a file §4 at `:1107` closes over `{U0, U11, U1, U13}`, with
U5 ∥ U6 and U8 ∥ U12 concurrent. Either outcome is a defect: the obligation is dropped, or it lands
in an unowned shared file.

**The repository already answered this, in a file the plan's §8 lists as unread.**
`docs/research/COMPLIANCE-SPEC.md:274-296`, §2.3 *"Coverage targets per module category (gap G6
resolved)"* carries the same table with the same numbers and then rules on the mechanism:
*"`fail_under = 80` is the only threshold that is mechanically enforceable in one number; **[REC]**
enforce the per-module targets **in review** (§5 checklist) rather than inventing a bespoke coverage
plugin. Adding per-module gates is possible via `coverage`'s `[tool.coverage.paths]` only awkwardly -
not worth the machinery."* That downgrades this from a collision to an ambiguity, which is why it is
Medium and not High.

**Suggested fix (MY SUGGESTION - verify before adopting):** rewrite `:266-269` in place to say what
enforcement is, rather than who owns a file:

> the 80% overall floor is the only mechanically enforced number. **ADR-0010's per-module floors
> (85% `tools/`, 90% the client, 95% `utils/`, 95 line / 90 branch on critical paths) are enforced in
> review, not in configuration** - `COMPLIANCE-SPEC.md:293-296` rules that a bespoke per-module
> coverage gate is not worth the machinery. **No unit writes a coverage key into `pyproject.toml`**;
> each unit's reviewer checks its module against ADR-0010's row, and each unit reports its measured
> coverage in its worklog.

Then delete the *"land with the units that create those modules"* phrasing from `pyproject.toml`'s
comment, which currently reads as a build obligation.

### M2 - C7-I2 appears nowhere in the plan, and §8's list of unowned threat rows is wrong by one

`IMPLEMENTATION-PLAN.md:1399-1401` makes an explicit enumeration: *"The rows named by no unit are
**C1-R1, C2-R1, C4-E1, C7-I1 and C8-I1** - stated as a list, with no total"*.

`grep -oE 'C[0-9]+-[A-Z][0-9]+'` over the plan returns 25 distinct ids. `C7-I2` is not among them -
it appears nowhere in the document at all. In the frozen design it is a live row:

- `DESIGN.md:1799` - *"Full tracebacks reach the server log ... asserts a boundary without naming a
  control: no retention, access-control or destination is specified"*, disposition `residual`.
- `DESIGN.md:1880-1881` - *"**Mitigate before production release** (inherent Medium, unmitigated):
  C3-I1 and C6-D1 ... **C7-I2 log-stream handling**, and C8-R1 configuration-change logging."*
- `DESIGN.md:1918` - a Residual Risk row: *"Accepted only until C7-I2's action is taken. If the log
  destination is a developer's local disk this is minor; if it is shipped anywhere it is not, and
  nothing currently says which."*

The plan carries the other three members of that list by name and with care - C3-I1 and C6-D1 in U1,
U6 and Q1; C8-R1 in Q3, which explicitly declines to specify a mitigation and says so. C7-I2 is the
one that was dropped rather than declined, so a reader gets three tracked rows and no signal that a
fourth exists. It does not block implementation - the design's *"must mitigate before implementation
proceeds"* table at `DESIGN.md:1845` is genuinely empty, which I verified - but the enumeration at
`:1399` claims completeness it does not have.

**Suggested fix (MY SUGGESTION - verify before adopting):** add `C7-I2` to the list at `:1399` and
give it the same one-sentence treatment Q3 gives C8-R1 - it is a deployment decision (where the log
goes, who reads it, how long it is kept), it belongs in U13's deployment section beside the
read-only-key requirement, and the plan does not specify it because specifying an unspecified
mitigation is not a plan's job. Rewrite the sentence in place; do not append.

### M3 - U15's "touches no file any other unit writes" is already false against the unit being built right now

`IMPLEMENTATION-PLAN.md:927-928`: *"**Depends on.** U0 only. **Parallel with U11 throughout**, and it
touches no file any other unit writes."*

The in-flight `scripts/check-committed-file-types.py` (untracked at review time) documents its own
CI mode in its usage block:

```
  scripts/check-committed-file-types.py          # the staged set (pre-commit)
  scripts/check-committed-file-types.py --all    # every tracked file (CI)
```

A `--all` mode with no CI step is inoperative code; a CI step makes U15 a writer of
`.github/workflows/ci.yml`, the file §4 at `:1106` gives to U0 with a closed later-editor list of
`{U1, U11, U13, U5}`. U15 is *"parallel with U11 throughout"*, and U11's own edit is to that same
file. This is collision 7's shape one unit later - which is the fix-one-miss-the-sibling failure the
plan names three times about itself.

It is Medium rather than High because the design mandates only commit-time
(`DESIGN.md:1626-1636`), so the CI step is a choice, not an obligation - but it is a choice the build
has already made.

**Suggested fix (MY SUGGESTION - verify before adopting):** replace the sentence at `:927-928` with:

> **Depends on.** U0 only. **Parallel with U11 throughout.** It owns `.pre-commit-config.yaml`,
> `scripts/check-committed-file-types.py` and `.file-type-allowlist` outright. **If the file-type
> gate is also run in CI (`--all`), that step is U15's own block in `ci.yml` under the shared-file
> rule in §4** - a pre-commit hook is bypassable with `--no-verify`, so the server-side arm is worth
> having, and it must be scheduled rather than added by whichever agent notices.

and add U15 to the ci.yml editor list at `:1106`.

---

## LOW

### L1 - No unit is told to write a changelog fragment

`changelog.d/README.md` is a committed repository convention: *"Agents working in worktrees drop a
fragment here instead of editing `CHANGELOG.md` directly, so parallel work never conflicts on one
file. **One fragment per unit of work.** Filename: `<task-id>-<slug>.md`"*, with an explicit ruling on
what does and does not earn one and a record of two entries already removed for breaching it.
`COMPLIANCE-SPEC.md:352-360` carries the standard behind it.

The word "changelog" does not appear in the plan. Fifteen units will ship user-visible behaviour and
none is told to leave a fragment; the convention exists precisely because the alternative is fifteen
agents editing one file. The mechanism already prevents the collision, so this is Low - the risk is
a missing record, not lost work.

**Suggested fix (MY SUGGESTION - verify before adopting):** one sentence in §4, beside the
no-`git stash` rule at `:1258-1261`: *"Every unit that changes user-visible behaviour leaves a
`changelog.d/<unit>-<slug>.md` fragment and never edits `CHANGELOG.md`; per that file's own rule, CI
changes, test-only changes, refactors and review documents get no fragment."*

---

## What I checked and found clean, stated so the absence of a finding is bounded

**The citation machinery. Sample: 25 of 25 §8 anchors, and 7 of 7 threat-row cites - the whole
population, not a sample, because it was cheap.** Every anchor read with `sed -n '<n>p'` out of
`/tmp/DESIGN-frozen.md`, which is `git show 135c3ac:docs/DESIGN.md`, and matched **by subject**
against the plan's §1 table:

- `:1220` → *"the 200-with-401-body trap"* (#1). `:1221` → *"a secret never reaching a log record,
  including the `jobFeed` URL"* (#2). `:1222` → `.gitignore`/`.env.example` (#3). `:1226` → audit
  event mandated fields (#4). `:1232` → candidate PII (#5). `:1236` → EEO fields (#6). `:1238` →
  argument-schema violation (#7). `:1240` → control character / bidi (#8). `:1244` → structural
  limit (#9). `:1246` → off-loopback bind (#10). `:1250` → manifest pins `mcp` (#11). `:1255` →
  undeclared marker (#12). `:1260` → retry/breaker `request_id` (#13). `:1266` → read-only key
  (#14). `:1273` → expired advisory-ignore (#15). `:1277` → `request_id` on every result (#16).
  `:1284` → trace context (#17). `:1289` → SIGTERM teardown (#18). `:1296` → fencing (#19). `:1297`
  → unknown non-string field (#20). `:1298` → `create_candidate` no retry (#21). `:1299` → approval
  four arms (#22). `:1301` → 4xx not tripping the breaker (#23). `:1302` → `eId`/`EId` (#24).
  `:1303` → approval on both eras (#25). **25/25 land on their own case.**
- Threat rows, matched by **row id at line start** rather than by text: C2-I1 `:1681`, C3-I1 `:1695`,
  C5-R1 `:1724`, C6-D1 `:1738`, C7-T1 `:1746`, C8-R1 `:1759`, C8-I1 `:1760`, C9-T1 `:1770`.
  **8/8 correct.** The revision-history cite `:1816` and the production-release list `:1830` also
  resolve to their stated subjects.
- The header's *"empty must-mitigate table (`DESIGN.md:1845`)"* is **correct and I tried to break
  it**: `:1791-1795` is the *"Must mitigate before implementation proceeds"* table and its single row
  reads `*(none)*`. The *production-release* list at `:1830` is non-empty, which is a different list,
  and the plan does not conflate them.

**The standards citations, which §8 declares unverified.** The plan says *"I did not read the
standards corpus"* and that every `standards/...:line` cite is quoted through `DESIGN.md`. I read
five at source in `evolv-coder-standards/standards/`, and **all five hold at the exact cited lines**:
`ai/tool-calling.md:173-175` (*"the canonical triple verbatim: HTTP header `X-Request-ID`, log field
`request_id`, ContextVar `request_id_var`"* - the plan's *"mandated verbatim"* is exactly right),
`backend/testing.md:82` (`branch = true`), `backend/testing.md:583-589` (the category table
ADR-0010 remaps), `backend/resilience.md:166-168` (4xx MUST NOT trip the breaker),
`backend/resilience.md:224-226` (retry and transition logging carrying `request_id`).
`devops/quality-gates.md:286-307` also confirms ADR-0015's premise: five allow-listed SPDX ids, and
*"Custom / unknown - Always flag for review"* at `:307`. **The residue §8 declares is real but the
sample came back clean**, which is worth recording as evidence rather than leaving as an open risk.

**U0's section against the build.** `pyproject.toml`, `.github/workflows/ci.yml`, `tests/` and
`docs/worklogs/U0-REPORT.md` all agree with `IMPLEMENTATION-PLAN.md:242-372`. The three deferrals are
commented steps naming their owner (pip-audit→U11, coverage→U1, capability-drift→U1), the licence
gate landed as a deny-list with ADR-0015 behind it and the plan describes it as one, the
credentialed-collect step accepts `0` or `5` with the tightening owed to U5, and `tests/conftest.py`
carries the fixtures-by-path rule the plan states at `:301-304`. The one wording drift I found is
harmless: `U0-REPORT.md:309` says the coverage *"floors are configured in `pyproject.toml` today"*
where only `fail_under = 80` is - that is M1's subject, not a separate finding.

**U15's section is buildable from its own words.** The in-flight
`scripts/check-committed-file-types.py` implements exactly the five rules the plan's `:919-960`
specifies, in the plan's own order - allowlist-from-the-index at rule 0, extension denylist,
allowlist-first, magic number, NUL backstop, fail-closed with `exit 2` for the gate's own errors -
without having read the design section. **The ceiling is carried, not dropped**: the script's
docstring states *"WHAT IT DOES NOT DO, from the design's own admission at DESIGN.md:1634-1636: it
stops a FILE of the wrong type ... It does nothing about confidential prose pasted into Markdown"*,
which matches `DESIGN.md:1634-1636` verbatim in substance. That is the strongest available evidence
that U15's section is buildable in isolation: it already was.

**Not defects, checked and dismissed.** `.gitignore` has one writer (U0) and no later unit needs it.
`.env.example` is correctly rowed to U1 with U0 as a reader. `models/` per-file, tool registration in
`tools/*.py`, the U6/U7 sequencing, the U5-reads-while-U6-writes rule, U12's dependency on U6 and
U14's last position are all internally consistent and consistent with `DESIGN.md:283-291`. The eight
named collisions are all real and correctly described.

---

## The judgement

> *The plan says a unit reporting no defect has more probably not looked than found none. Is that
> true of the plan itself - where is it most likely that five rounds of reviewers have all not
> looked?*

**Yes, and it has a name and a line number: `docs/research/COMPLIANCE-SPEC.md`, declared unread at
`IMPLEMENTATION-PLAN.md:1379-1385` and unread by every review round including, until this afternoon,
this one.**

The plan's §8 lists six documents it did not read and treats them as one undifferentiated residue:
`COMPLIANCE-SPEC.md`, `STANDARDS.md`, `LICENSING-SURVEY.md`, `DECISIONS.md`, `data-inventory.md`, and
the seventeen documents in `docs/reviews/`. That framing is what hid this, because the six are not
alike. Five are background. **`COMPLIANCE-SPEC.md` is a 661-line specification of this exact
repository's obligations** - §1.2 a CI job table, §1.5 pinned action versions *"(copy exactly)"*,
§1.6 the licence allow-list string *"(verbatim)"*, §2.2 `pyproject.toml` blocks *"ready to paste"*,
§2.3 the per-module coverage ruling, §2.4 the test-discovery guard, §3.1 the README's required
sections in exact order, §5 the RFC 9457 × `ToolError` analysis, §6 a do-not-copy list, §7 a
reviewer pass/fail checklist. It is the same subject matter as U0, U11, U13 and half of §4, written
before them and never consulted by any of them.

**The evidence that this is where the unlooked-at defects live is that I found this round's two
best findings there, in about ten minutes, with no cleverness.** H1 is `COMPLIANCE-SPEC.md` §2.4 read
literally and then confirmed at source in the corpus. M1's resolution is §2.3 read literally. I did
not read §1.2, §1.5, §1.6, §3.1, §5, §6 or §7 - and §3.1 alone specifies the README's required
sections in exact order, which is U13's entire deliverable and which the plan currently specifies
from `DESIGN.md:1533-1540` and `readme-standard.md` cites it has not verified.

**Why five rounds missed it, which is the part worth carrying.** Every round has reviewed the plan
against `DESIGN.md`, because `DESIGN.md` is authority and the plan says so in its second paragraph.
But `DESIGN.md` is *itself* a downstream document. When a plan and a design agree, a reviewer
comparing them finds nothing - and both were written by readers who had not opened
`COMPLIANCE-SPEC.md` either. **A review that only ever compares two documents to each other can
confirm consistency and can never find a shared omission**, which is exactly the plan's own
"a unit reporting no defect has more probably not looked" applied one level up. It is also the same
structural lesson round 4 recorded from the opposite direction: R4's best findings came from the
built unit, mine came from the unread upstream document, and **both are places outside the
plan-versus-design axis that four rounds of reading never left.**

**Concretely, and this is my recommendation whatever is done with H1 and H2:** before U13, and
before U11 enables the advisory step, someone reads `COMPLIANCE-SPEC.md` §§1.2, 1.5, 1.6, 3.1, 5, 6
and 7 against the plan and the built `ci.yml`. Not as a review round - as one pass by one agent with
a diff. If it produces nothing, that is a real green, because it will be the first time anything in
this project has looked there.

---

*Round 5 by `plan-review-r5b`, 2026-08-28. Gates and suite re-run at `299cf8b`. `docs/DESIGN.md` read
from the frozen `135c3ac` git object. No file was edited and nothing was committed.*
