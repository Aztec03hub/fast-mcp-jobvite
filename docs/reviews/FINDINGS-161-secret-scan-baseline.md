# FINDINGS — #161: the secret-scan step, and seven corrections to its brief

**Agent:** `suborch-161` (Tier 1) · **Branch:** `fix/161-secret-baseline`
· **Cut from:** `ccbdaae` · **Worktree:**
`/home/plafayette/claude_projects/evolv/fmj-worktrees/w161`

This is not a code-review round, so it carries no `REVIEW-COVERS`
declaration: it reviewed nothing on the trunk, and a declaration here
would manufacture coverage for commits nobody read.

---

## 1. The defect, reproduced rather than re-derived

`ci.yml`'s `Secret scan hook runs clean` step, run with CI's exact
invocation from a worktree at `ccbdaae`:

```
$ uv tool run pre-commit@4.6.2 run --all-files --show-diff-on-failure
committed-file-type gate (...)...........................Passed
secret scan (detect-secrets, staged content)..............Failed
- hook id: detect-secrets
- exit code: 3
- files were modified by this hook

The baseline file was updated.
Probably to keep line numbers of secrets up-to-date.
Please `git add .secrets.baseline`, thank you.
...
-        "line_number": 1344,
+        "line_number": 1617,
-  "generated_at": "2026-09-01T20:33:41Z"
+  "generated_at": "2026-09-02T01:22:26Z"
EXIT=1
```

Three hooks, two Passed, one Failed, and the printed diff is the hook's
own rewrite. Everything the brief and task #161 say about the mechanism
holds. **The entry is `.github/workflows/ci.yml`, `is_secret: false`, the
literal `inspect-only-not-a-credential` — not a secret, and never was.**

**The baseline holds 22 entries across 13 files in `.secrets.baseline` at
`ccbdaae`. Verified, and the brief's figure was right.**

---

## 2. Seven corrections to the brief

### C1 — the brief's `ci.yml` line numbers are stale, in the brief that says not to recall them

§D cites `ci.yml:1330-1332` for the intent comment and §C cites
`ci.yml:1333-1336` for the `pre-commit` invocation. At `ccbdaae`, from
`grep -n`:

| What | Brief | Measured |
|---|---|---|
| `- name: Secret scan hook runs clean` | — | `1498` |
| the "what this step genuinely covers" comment | `1330-1332` | `1516-1518` |
| the `run:` block | `1333-1336` | `1519-1522` |

§F of the same brief says *"`ci.yml` is freshly rewritten, so read it
rather than recalling it"*, one paragraph after quoting recalled line
numbers. **Suggested fix, and it is the fix this repository already made
for `OBLIGATIONS.md` anchors and for its 20 `ci.yml` citations: cite the
step by its `name:`, which is unique and does not drift.** Both citations
in this report do that.

### C2 — the drift is 273 lines, not 87

Task #161 states *"`ci.yml` grew by 87 lines since the baseline was
written"*. Measured: the baseline records `1344`; `detect-secrets`
rewrote it to `1617`. That is **273**. The 87 was presumably a diff
against a different pair of commits. It changes nothing about the
diagnosis and everything about how fast the ratchet bites — the figure
understates it by a factor of three. **Suggested fix: none needed beyond
this record; the number is not load-bearing anywhere.**

### C3 — §B's path would have swapped one red step for another

§B assigns `docs/reviews/check-secrets-baseline.py`. That directory is
the container `docs/reviews/check-checkers-are-wired.py` enumerates, and
that checker **is** a CI gate. A `check-*.py` placed there and invoked
only through `.pre-commit-config.yaml` is not named in any `run:` body,
so the wiring gate would have gone red — replacing the failing step with
a different failing step.

**It is in `scripts/` instead**, beside `check-committed-file-types.py`,
which is its actual sibling: the other commit-time gate, also driven from
`.pre-commit-config.yaml`, also under `scripts/`. `docs/reviews/` holds
review checkers; `scripts/` holds the gates the tooling runs.

**This is exactly the hole task #153 already records** — the wiring
checker selects BY PATH, so a checker under `scripts/` can be unwired
forever at exit 0. I did not rely on that hole: the checker's `--controls`
mode is invoked by name from the `Secret scan hook runs clean` step, so
the name does appear in a `run:` body and the gate is genuinely wired.
Reading it as an accidental exemption would be wrong; reading it as a
reason to close #153 would also be wrong.

### C4 — §E is right that `probe-*` is invisible, and understates it

§E says `check-checkers-are-wired.py` enumerates by the `check-` prefix
so a `probe-*` file is invisible (#155). Confirmed:
`docs/reviews/probe-secrets-baseline.py` is invisible to it. **So is
`scripts/check-secrets-baseline.py`, for the different reason in C3.**
Two independent blind spots, and neither was relied on. The wiring gate
was run and exits 0 — but a green from it says nothing about either of
these two files, which is the point of writing this down.

### C5 — §D's suggested shape works, and has an unstated side effect that changes the answer

§D suggests copying the baseline to a temp file and scanning with
`--baseline <the copy>`. That is what the checker does, and the tree is
never written. **But `detect-secrets` takes its `is_baseline_file` filter's
`filename` from whatever `--baseline` it was given**, so pointing it at a
copy un-excludes the real `.secrets.baseline` — a file consisting largely
of hex digests. Measured:

```
committed 22   scan 46   (24 extras, ALL in .secrets.baseline,
                          each once as Hex High Entropy String and
                          once as Secret Keyword)
```

Taken at face value the suggested shape reports 24 unaudited findings on
a clean tree. `_drop_baseline_self_findings` reproduces the filter,
keyed on the baseline's own path so it can discard nothing else, and
control `C5` proves a finding in any other file survives it.

### C6 — the gate's own implementation file was two unaudited findings

The checker's control fixtures originally spelled the digest field name
beside a quoted value, which is precisely what `KeywordDetector` matches.
**The file implementing the gate was therefore two findings the gate would
have refused, and the gate would have gone red on the commit that
introduced it.** It passed the first run only because the file was still
untracked and `detect-secrets scan` picks its population with
`git ls-files` — a clean pass that meant nothing.

**Then the comment written to explain that added a THIRD**, by quoting the
pair it was warning about. Same class as the exemption marker this
project measured inflating from its own documentation, where the most
careful writers expanded the hole fastest.

Both are now assembled from fragments at runtime, so no line spells the
pair in code or in prose and the recursion cannot occur rather than being
excused. **Suggested fix for the class, offered not applied: nothing in
CI tells you a NEW tracked file would be a finding until it is tracked.
A `git add -N` before the scan would close that, and it is a decision
about the hook's contract, not an edit.** Recorded rather than done.

### C7 — the brief asked for a positive control and the fixture needed one first

§E asks for both arms. Building them found that `detect-secrets scan`
returns an **empty result at exit 0** in a directory that is not a git
repository. The probe's first run therefore measured nothing and said so,
because it checks its own fixture holds exactly one entry before running
an arm. A probe without that check would have printed four passes.

---

## 3. What was built

| File | What it is |
|---|---|
| `scripts/check-secrets-baseline.py` | the gate; `--controls` is its comparison controls |
| `docs/reviews/probe-secrets-baseline.py` | the end-to-end arms, incl. an amputation |
| `.pre-commit-config.yaml` | the `detect-secrets` remote hook replaced by a local one |
| `.github/workflows/ci.yml` | the step's comment rewritten; `--controls` wired into it |
| `CONTRIBUTING.md` | both new commands listed, in the same commit as the step |

The gate compares the SET of `(filename, type, hashed_secret)`.
`line_number` and `generated_at` are excluded by construction. `type` is
IN the key, so the same string newly flagged by a second plugin is a new
finding. Nothing is `git add`ed, nothing is `|| true`, the hook is not
dropped — all three shortcuts §D names are refused, and the `ci.yml`
comment says so where the next person will look.

### The stale direction: it WARNS, and here is the reason

An entry in the baseline whose finding is gone from the tree is a stale
allowance. It is printed by name with a count on every run, and it does
not fail.

**A stale allowance grants nothing** — the string it excused is no longer
in the tree — so its risk today is zero. Failing on it would make the
gate go red for a DELETION, and leave exactly one way to clear it:
hand-editing `.secrets.baseline`. That is the trap this whole task exists
to remove, one column over, and a gate red for improving the tree is the
D3 shape (`U0-REPORT`) this repository has already accepted twice, for
the shellcheck hook and for `pip-audit`.

**Today the count is 0**, so failing would cost nothing *now* — which is
exactly the argument that would have justified the old hook too. The
residual risk is that a stale pair silently re-excuses the identical
string if it returns to the identical file; that string was audited, so
the risk is real but small, and it is stated rather than hidden. **If
Tier 0 wants it to bite, the shape is a ratchet on the count, not a
demand for zero.**

---

## 4. Measurements, each exit code on its own line

Run in the worktree at `c276a45` plus the `CONTRIBUTING.md` edit.

```
EXIT=0  uv tool run pre-commit@4.6.2 run --all-files --show-diff-on-failure
        committed-file-type gate .......... Passed
        secret scan (set-compared) ........ Passed
        ShellCheck v0.10.0 ................ Passed
        (git status --porcelain: empty afterwards)

EXIT=0  uv run --frozen ruff check .
EXIT=0  uv run --frozen ruff format --check .
EXIT=0  uv run --frozen mypy
EXIT=0  uv run --frozen pytest --cov --cov-report=term-missing --cov-report=json
        887 passed, 0 skipped, 6 deselected, 62.57s
EXIT=0  bash scripts/check-suite-floor.sh 887   (rows=887 floor=887 status=ok)
EXIT=0  python3 docs/reviews/check-coverage-floors.py
        Overall: 97.20% line against an 80% floor
EXIT=0  SHELLCHECK_OPTS=--severity=warning actionlint
EXIT=0  python3 scripts/check-harness-anchors.py --self-check --floor <from ci.yml>
EXIT=0  python3 scripts/check-committed-file-types.py --all
EXIT=0  python3 docs/reviews/check-coupling.py docs/DESIGN.md
EXIT=0  python3 docs/reviews/check-cross-references.py
EXIT=0  python3 docs/reviews/check-coupling-controls.py
EXIT=0  python3 docs/reviews/check-coupling-sweep.py
EXIT=0  python3 docs/reviews/check-obligations.py
EXIT=0  python3 docs/reviews/check-obligations.py --controls
EXIT=0  python3 docs/reviews/check-plan-measurements.py
EXIT=0  python3 docs/reviews/check-resweep-verdicts.py
EXIT=0  python3 docs/reviews/check-checkers-are-wired.py
EXIT=0  python3 docs/reviews/check-design-freeze.py
EXIT=0  python3 docs/reviews/check-no-errexit.py
EXIT=0  python3 docs/reviews/check-no-sigpipe-pipelines.py
EXIT=0  python3 docs/reviews/check-adr-numbers.py
EXIT=0  python3 docs/reviews/check-env-vars-are-declared.py
EXIT=0  python3 docs/reviews/check-settings-are-read.py
EXIT=0  python3 docs/reviews/check-landing-published.py
EXIT=0  python3 docs/reviews/check-row-floors.py
EXIT=0  python3 docs/reviews/check-row-floor-exactness.py
EXIT=0  python3 docs/reviews/check-design-citation-shape.py
EXIT=0  python3 docs/reviews/check-standards-citations.py
EXIT=0  python3 docs/reviews/probe-ci-checker-steps.py
EXIT=0  python3 scripts/check-secrets-baseline.py --controls
        arms=6 failed=0
EXIT=0  uv run --no-project --with detect-secrets==1.5.0 python \
          docs/reviews/probe-secrets-baseline.py
        arms=5 failed=0
EXIT=0  the gate on the real tree
        audited=22 found=22 new=0 stale=0 files=13 baseline-self-dropped=24
```

The positive controls, both arms, are `A1` and `A2` of the probe, and
`A4` is what makes `A2` mean anything:

```
PASS  A0 the fixture starts clean
PASS  A1 a line number moving stays GREEN
PASS  A2 a new secret turns it RED
PASS  A3 a removed finding WARNS and stays green
PASS  A4 amputating the digest makes A2 GREEN
```

`A4` deletes the digest from the comparison key in a COPY of the checker
and re-runs `A2`'s planted secret: it passes. So `A2` is measuring the
comparison and not a checker that fails on anything.

**No planted secret is a literal anywhere.** Every value the probe plants
is concatenated at runtime, no value is ever printed, and the checker
prints digests only. Nothing synthetic reached a commit.

---

## 5. What I could NOT settle

- **Whether CI is green end to end.** I fixed the one failing step and
  ran every gate I could run locally, but I do not push, and the last
  observed run is `46dafe0`. `pip-audit`, TruffleHog over full history,
  CodeQL and the SBOM steps need the network and the Actions runner.
- **Whether the stale direction should ratchet.** It is 0 today, so
  there is no measurement to choose between "warn forever" and "ratchet
  the count". I ruled WARN with the reason in §3; the ruling on whether
  to tighten it later is Tier 0's, and it needs an occurrence first.
- **`check-u1-pid1-shutdown.sh` and `check-clause-citations.py`** — not
  attempted, and they are not in scope for this change: neither reads
  anything I touched, and both are documented as human-run.

## 6. What I did NOT do

- No push, no merge, no rebase, no `git stash`, no branch of another
  agent touched.
- I did not regenerate `.secrets.baseline`. It is byte-identical to
  `ccbdaae`, deliberately: a regeneration would have made the step green
  for days and hidden whether the real fix works.
- I did not widen `check-checkers-are-wired.py`'s container (#153). That
  is a decision about another checker's scope and it belongs to whoever
  takes #153.
- I did not touch `docs/DESIGN.md`, any ADR, or `docs/OBLIGATIONS.md`.
  Nothing here moves an obligation anchor; `check-obligations.py` exits 0
  and its `--controls` exit 0.
