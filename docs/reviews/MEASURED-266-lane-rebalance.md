# MEASURED-266: repacking the 12 harness lanes

Branch `ci/266-lane-rebalance`, based at `a849f7f`, one commit `6466bd2`.
`.github/workflows/ci.yml` is the only file changed.

## 0. Canon read

- `MUST-READ-DOCS.md` - read. TIER-1 row 11 is `standards/devops/ci-cd.md`.
- `standards/devops/ci-cd.md` (`priority: required`, v1.3.5) - read in full.
  Nothing in this change contradicts it. Its Required-Gate Integrity section
  is the clause closest to this work ("Skipped is not green"): this repack
  adds no `if:`, no conditional job and no skip, so no step can become a
  skipped-but-required check. Its "Run jobs in parallel when possible"
  best-practice is what the repack acts on.
- `standards/devops/bash.md` (`priority: required`, and NOT in the TIER-1
  table as the brief warned) - read. It governs script bodies; this change
  moves step blocks between jobs and edits one comment, and alters **zero**
  bytes of any `run:` body, proved by the step-body hash diff in section 3.
- `docs/DESIGN.md` is FROZEN; not touched. `docs/adr/0*.md` - 36 ADRs listed;
  none governs job packing.
- `docs/reviews/REVAMP-238-ci.md` sections 5, 6, 7, 7a, 7a.1 - read, and
  section 7a's mistakes list read FIRST as instructed.

**I could not find any doc I was told to read and failed to locate.**

## 1. What the run actually says

Every figure below is derived from run `33629034552`'s own payload
(`gh api repos/:owner/:repo/actions/runs/33629034552/jobs?per_page=100`),
recomputed, not read back from prose:

    16 jobs, conclusion=success
    sum of job durations                3824s   (/16 = 239s)
    largest single step                  304s   check-u3-audit-amputation
    LPT floor = max(304, 239)            304s
    ACTUAL WALL                          463s   (ONE DRAW)

The 12 harness jobs contribute 35 work steps totalling **3316s**, plus 6-15s
of setup each (checkout, uv, setup-python, `uv sync --frozen`); 13s is the
per-lane overhead used in every prediction below.

## 2. The packing result

LPT over the 35 measured step durations, with `check-u3-audit-amputation`
pinned to its own lane and the U14 sweep isolated (see section 5):

| lanes | predicted harness pole |
|---|---|
| 11 | 325s |
| **12** | **317s** |
| 13 | 317s |
| 14 | 317s |

**Twelve is optimal, and twelve is the count that already exists.** This
repack therefore needs no new job and no deleted job: 16 jobs before, 16
after. Thirteen and fourteen lanes buy nothing at all, which settles the
"keep 16 or fewer" constraint without spending any of its headroom.

    harness pole   458s  ->  317s   predicted, from step durations
    lane work span 53-446s -> 213-304s

| lane (job id) | predicted s | steps | contents |
|---|---|---|---|
| `harness-u3-amputation` | 317 | 1 | U3 audit amputation harness ran every row |
| `harness-u4-amputation` | 312 | 2 | U4 client amputation harness ran every row; U12 job feed amputation, every row applied |
| `harness-critcov-u9c` | 299 | 3 | Critical-path coverage amputation, every row applied; U9 HTTP hardening controls, all fired; Body cap amputation, every row applied |
| `harness-u7a-u5c-u6c` | 298 | 3 | U7 resilience amputation, every row applied; U5 jobs controls, all fired; U6 paging controls, all fired |
| `harness-u8c-u7c` | 291 | 2 | U8 candidate controls, all fired; U7 resilience controls, all fired |
| `harness-u12c-u4c` | 291 | 3 | U12 job feed controls, all fired; U4 client mutation controls, all killed; U6 paging amputation, every anchor applied |
| `harness-u9-amputation` | 289 | 4 | U9 HTTP hardening amputation, every row applied; U10 write amputation, every row applied; Stranded-mutation control; Suite-floor guard amputation, every row killed |
| `harness-u1-controls` | 288 | 3 | U1 boot mutation controls, all fired; U5 jobs amputation, every anchor applied; Harness anchor checker controls, all fired |
| `harness-u1-amputation` | 287 | 5 | U1 boot amputation harness ran every row; U8 candidate amputation, every row applied; U11 advisory controls, all fired; Mirror liveness controls, all fired; Harness gate controls, all fired |
| `harness-u10-controls` | 287 | 3 | U10 write controls, all fired; U0 test controls, all fired; U15 gate amputation, every row applied |
| `harness-u3-controls` | 287 | 3 | U3 audit mutation controls, all killed; Body cap controls, all fired; U15 gate controls, all fired |
| `harness-u14-sweep` | 226 | 3 | U14 argument sweep controls, all fired; U14 argument sweep amputation, every row applied; Log redaction amputation, every row applied |

**317s is the FLOOR, not a target missed.** That lane holds one step, the
304s `check-u3-audit-amputation`, plus setup. Packing is exhausted. The
only remaining lever is sharding that step's ROWS, which the brief
deliberately sequences after this task.

## 3. The set is IDENTICAL - derived, not asserted

Both step sets were derived from the YAML by the same script, keyed on
`(step name, sha256 of the step body with its name removed)`, and diffed
with the job column dropped:

    python3 derive_steps.py > before.tsv   # at a849f7f
    python3 derive_steps.py > after.tsv    # at 6466bd2
    diff <(cut -f2,3 before.tsv | sort) <(cut -f2,3 after.tsv | sort)

    156 steps before, 156 after, EMPTY DIFF

Same steps, same bodies, same multiplicities. No check was added, removed,
weakened or made conditional. Every check still runs on every trigger.

Comment lines were counted independently and are conserved exactly:
**1298 before, 1298 after, 0 lost, 0 duplicated.**

## 4. A defect IN MY OWN TOOL, caught by a check the brief did not ask for

My first transformer ended each step's block at the next step's `- name:`
line. A comment banner sitting between two steps was therefore captured by
BOTH neighbours - as the first one's trailing text and the second one's
leading banner - so when they landed in different lanes the banner was
**duplicated**. Measured: the U9 `THE AMPUTATION STEP TAKES` banner went
from 1 occurrence to 2.

**The step-set diff in section 3 was blind to this**, because it hashes step
bodies and comments are not part of a step body. A green diff over the
thing I chose to measure said nothing about the thing I broke. The
comment-line conservation count is the instrument that caught it, and it
exists only because I went looking for a second one.

Fixed by computing every block boundary FIRST and running block *k* to
where block *k+1* begins, so a banner is claimed by exactly the step it
introduces. Re-derived after the fix: 1298 -> 1298, 0 lost, 0 gained.

## 5. Constraints, each checked rather than assumed

- **No step split.** Steps move whole; the transformer relocates text blocks
  and never edits inside one.
- **`check-u3-audit-amputation` untouched.** It is pinned alone in
  `harness-u3-amputation`, byte-identical to `a849f7f`.
- **No pair separated that depended on its partner.** Derived three ways:
  all 12 harness preambles are byte-identical (one distinct preamble across
  12 jobs); there are **no `needs:` edges anywhere in ci.yml**, so all 16
  jobs are already independent; and every harness work step is a
  self-contained `bash scripts/ci-harness-gate.sh <script>` invocation
  sharing only the checkout. The only harness steps that are not are two in
  `harness-misc`, and both stay put. Nothing passes an artifact to anything.
- **U14 deliberately ISOLATED.** `tests/test_arguments_sweep.py:1167` rglobs
  `tests/`, so a file stranded in the checkout by a co-tenant harness is
  visible to U14's sweep (#261, #256). Its lane holds only its own unit
  (U14 controls, U14 amputation, log redaction) at 226s - the one lane left
  deliberately under the pole. Body-cap, which shared its job before, was
  moved OUT; that is strictly safer than the shipped arrangement.
- **Nothing outside ci.yml references the renamed jobs.** Every old job id
  and job name was grepped repo-wide: zero live references. The only hits
  are in `docs/reviews/REVAMP-238-ci.md`, which are dated records of runs
  `33610211810`/`33614887374` and are correctly NOT repointed (ec57a65).
  `main` also has no branch protection and zero rulesets (#158), so no
  required-status-check name is broken by the renames - that is a real
  reason this is safe today and a reason it would need re-checking the day
  protection is added.

## 6. Findings, each with a fix

**F1 (Medium, FIXED here).** The U9 banner in ci.yml made three claims and
all three were false BEFORE this change: the amputation "takes ~13
MINUTES" (measured 201s), "is the slowest step in this file" (the slowest
is U3 audit amputation at 304s), and is "left in the same job deliberately"
(the two U9 steps were already in separate jobs). *Fix:* rewritten in place
in `6466bd2`, stating what was wrong and keeping the reasoning that is still
load-bearing, rather than appending a correction or deleting the paragraph.

**F2 (Medium, FIXED here, in my own tool).** Section 4's banner duplication.
*Fix:* boundary-first block computation, plus a comment-line conservation
count that would have caught it. Anyone repeating this kind of surgery
should conserve comments as a separate assertion from step bodies.

**F3 (Low, NOT fixed - reported).** My first attempt to run the ci.yml
checkers guessed `scripts/` and got `ABSENT` for eight of ten - a clean,
self-explaining zero from a path that does not exist. The real checkers live
in `docs/reviews/`. *Fix:* the commands are now derived from ci.yml's own
`run:` bodies rather than guessed; that is the method any future runner
should use, and it is what section 7 records.

**F4 (Nit, NOT fixed - reported).** Six lane job ids now carry compound
names (`harness-u7a-u5c-u6c`). #245 recorded that a step named for its
battery goes stale when the battery changes. These names will go stale the
moment the pack is recomputed. *Fix, deliberately not applied:* number the
lanes (`harness-lane-01`..`harness-lane-12`) so the name carries no claim.
I did not apply it because a numbered lane tells a reader nothing about
what failed, and this repack is meant to be legible in the Actions UI.
Worth a ruling if the lanes are ever repacked again.

## 7. Gates, each read by exit code

    actionlint 1.7.7, SHELLCHECK_OPTS=--severity=warning   rc=0
    check-checkers-are-wired.py                            rc=0
    check-checkers-are-wired.py --self-test                rc=0
    check-env-vars-are-declared.py                         rc=0
    check-no-errexit.py                                    rc=0
    check-cross-references.py                              rc=0
    check-design-citation-shape.py                         rc=0
    check-timeout-literals.py                              rc=0
    check-timeout-literals.py --self-test                  rc=0
    check-harness-result.sh                                rc=0
    check-pytest-bounded.sh                                rc=0

**actionlint WAS run**, not skipped: the pinned 1.7.7 tarball was fetched and
its sha256 verified against ci.yml's own pin. Its rc=0 is proved
non-vacuous - the same binary, on a copy of the same file with one runner
label corrupted inside a repacked lane, reports `ci.yml:1670: label
"ubuntu-latest-TYPO" is unknown` and exits 1.

## 8. Merge

    git -C /home/plafayette/claude_projects/evolv/repos/fast-mcp-jobvite \
        merge --ff-only ci/266-lane-rebalance

## 9. What I did NOT verify

- **The wall.** No CI run was dispatched. 463s is ONE DRAW of a quantity this
  project has been wrong about five times, with job durations varying
  0.62x-1.65x between runs of this same workflow and the pole changing
  identity between them. **The 317s figure is a PREDICTION from step
  durations, which are stable; it is not a measured wall.** Whether the wall
  follows depends on queueing, which is external and was 4-5s in this run and
  305s in an earlier one.
- **That the repacked jobs actually run green.** Every gate that PARSES
  ci.yml passes, but no harness was executed in this worktree, and the
  workflow has not run once in this shape.
- **The 13s per-lane setup overhead** is the mean of 12 observations spanning
  6-15s. A lane that draws 15s rather than 13s exceeds my predicted figure by
  2s; this does not move which lane is the pole.
- **Whether GitHub admits 16 jobs promptly today.** Unchanged by this work
  and unchanged in kind: the job count is identical before and after, so this
  repack neither improves nor worsens the queueing exposure.
- **The two `harness-misc` steps that are not bare gate calls** (`Harness gate
  controls` and `Stranded-mutation control`) were left in place and their
  interaction with new co-tenants was reasoned about, not measured.
- **pytest, ruff, mypy** were not run. This change touches no Python and no
  shell body, so they are not in the blast radius - but I did not run them.
