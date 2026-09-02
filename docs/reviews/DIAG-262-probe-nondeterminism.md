# DIAG-262: why `probe-252-selection-can-fail.sh` read 3/3, then 2/3, then 1/3

Written 2026-09-02 09:28 AM CDT. Worktree `/tmp/diag-262`, branch `diag/262`,
base `96072cd`.

---

## 0. THE ANSWER IN ONE PARAGRAPH

The probe is deterministic. Its **readback** is not. Every arm writes the
harness's stdout to the **fixed, machine-global path `/tmp/probe-252-arm.txt`**
and then greps it for the row's `SELECTOR` line. Seven worktrees on this box
carry this probe and `scripts/check-u3-audit-controls.sh`, and several other
scripts run that harness. When a second run of any of them opens that same path
with `>`, the two writers hold independent offsets on one inode; the file fills
with NUL bytes; `grep` classifies it as binary, prints **nothing**, and exits.
`$sel_line` comes back **empty**, and the probe's first void branch - which
tests only for the *presence* of `SELECTOR N node(s)* - fires and says
*"$row took the WIDE fallback"*. That sentence is a claim about a selector line
the probe never read. Which arm is hit is pure timing, which is exactly the
reported signature: **a different arm voiding each time.**

Neither refuted cause was wrong. They were both about the **map**. The defect is
downstream of the map, in how the probe reads what the harness printed.

---

## 1. THE TWO CAUSES ALREADY REFUTED (not re-tested here)

Recorded at `docs/reviews/probe-252-selection-can-fail.sh:126-131` and in
`c03a3a3`'s message:

1. **"Neutering the killer changes what it covers, so the map stops naming
   it."** Refuted: M6's selector was 7 nodes with the killer named, identical on
   the intact and the neutered tree.
2. **"The coverage map is unstable build to build."** Refuted: stable across
   three builds on a clean tree.

Both interrogate the coverage map. This diagnosis leaves the map alone: the map
is fine, and so is the harness line it prints. The corruption happens between
the harness writing that line and the probe reading it.

---

## 2. REPRODUCTION, WITH A REAL DENOMINATOR

Every run is the whole probe (3 arms x one full 15-row harness, ~270-285s).

| Condition | Runs | Voids | Result |
|---|---|---|---|
| **Solo**, probe as committed at `96072cd` | **6** | **0** | 6/6 `rc=0`, `ARMS: 3/3 passed` |
| **Contended**, one replayed second probe | **3** | **2** | 2 x `rc=2` `status=refused`, 1 x 3/3 |
| **Contended**, `$OUT` made per-process | **3** | **0** | 3/3 `rc=0`, `ARMS: 3/3 passed` |

**Solo it is deterministic - 0 voids in 6.** So the cause is not in the probe's
own sequence, not in the map, not in ordering between arms, and not in anything
left behind between rows: six consecutive runs on one tree, one after another,
all identical.

Wall times, for the record: solo 272, 271, 272, 273, 284, 269s. The voided
contended runs took **92s and 89s** - they exited at arm 1, one harness in.

### 2.1 What "contended" means, precisely

`/tmp/diag-262-competitor.sh` replays what a second run of this probe does to the
one file the two runs share, and nothing else:

```
bash scripts/check-u3-audit-controls.sh >/tmp/probe-252-arm.txt
```

i.e. truncate at harness start, then append that harness's stdout over the ~90s
it takes. The replayed bytes are a **real** `$OUT` captured from a completed arm
of a real run (`/tmp/diag-262-harness-snapshot.txt`, 42 lines), spread over a
90s cycle - the harness's own measured wall time. Nothing is fabricated and no
other file is touched.

This is a **replay of a second probe, not a live second worktree.** I was scoped
to one worktree, and two probes in the *same* worktree cannot coexist - the
second one's `git status --porcelain` pre-flight aborts on the first one's
mutated test file. In different worktrees, which is the real configuration on
this box, no guard sees the other run at all. The shared object (the file) and
the write pattern are the real ones.

---

## 3. THE ROOT CAUSE, WITH THE EVIDENCE

**`docs/reviews/probe-252-selection-can-fail.sh:52`** (as committed at `96072cd`):

```
52:OUT=/tmp/probe-252-arm.txt
```

Used at `:103` (write) and read at `:113-117`:

```
103:  bash "$HARNESS" >"$OUT" 2>&1
113:  sel_line=$(grep -E "^$row .*: SELECTOR " "$OUT" | tail -1)
114:  verdict_line=$(grep -E "^$row " "$OUT" | grep -v ': SELECTOR ' | tail -1)
117:  echo "  harness : rc=$harness_rc  $(grep -E '^HARNESS-RESULT' "$OUT" | tail -1)"
```

The read window is the **whole 90s** the harness runs plus the grep, because the
file is opened `>` at `:103` and not read until `:113`. Anything that opens the
same path in that window corrupts it.

The observed failure, verbatim from `/tmp/diag-262-contend-3.log`:

```
########## ARM M6 - neuter the assertion in test_arm1_before_the_side_effect_the_call_fails
grep: /tmp/probe-252-arm.txt: binary file matches
grep: /tmp/probe-252-arm.txt: binary file matches
  selector: 
  verdict : 
grep: /tmp/probe-252-arm.txt: binary file matches
  harness : rc=1  
  ARM VOID: M6 took the WIDE fallback, so this arm did not test
  the selected path. THIS PROBE CANNOT AIM - refusing rather than
  reporting a breach it did not measure. See task #262.
HARNESS-RESULT name=probe-252-selection-can-fail.sh rows=0 floor=0 status=refused
```

Three things in that block are worth naming separately:

* **`grep` printed nothing and exited.** Over a NUL-bearing file GNU `grep`
  writes `binary file matches` **to stderr** and suppresses the matching line, so
  `$(...)` captures the empty string at exit 0. A silent false zero, in the exact
  shape this project has recorded before.
* **`sel_line`, `verdict_line` and the `HARNESS-RESULT` line are ALL empty.** The
  harness ran fine - `harness_rc=1`, which is the correct code for a
  neutered-killer arm - and every fact about it was lost on the way back.
* **The void message is a misdiagnosis.** `case "$sel_line" in *"SELECTOR "[0-9]*"
  node(s)"*)` at `:141-149` cannot tell *"the selector line says WIDE"* from
  *"there is no selector line"*, and it reports the first. #262 was therefore
  handed a sentence about the coverage map every single time, which is why both
  investigated causes were map causes.

### 3.1 Who the other writer is, in the real configuration

Six sibling worktrees on this box carry `scripts/check-u3-audit-controls.sh`
(checked, all six exist): `/tmp/review-270`, `/tmp/review-270-base`,
`/tmp/review-7a2`, `/tmp/review-254`, `/tmp/w254`,
`/home/plafayette/claude_projects/evolv/fmj-worktrees/w194`. `/tmp` is not
per-worktree. And the harness is invoked from at least four places -
`docs/reviews/probe-252-selection-can-fail.sh:40`,
`docs/reviews/probe-252-rc4-verdict-trap.sh:45`,
`docs/reviews/check-row-floor-controls.sh:172`, and
`scripts/ci-harness-gate.sh` (`docs/reviews/REVAMP-238-ci.md:201`) - so
concurrent runs are the normal state of this repository, not an exotic one.

This also dates the symptom without needing a log: the probe read **3/3 when it
was written** and stopped reproducing later, which is what a defect that needs a
second concurrent runner looks like as the number of live worktrees grows.

---

## 4. PROVED BOTH WAYS

**The failure occurs under the explanation.** Shared `$OUT`, one replayed second
probe: **2 voids in 3 runs**, both at the first arm, both with the
`binary file matches` line and an empty `sel_line` above them. The run that
survived (contend#2) is timing, not a counter-example - the third cycle simply
had the competitor past line 17 of 42 at each of the three grep instants.

**The failure does not occur when the cause is removed.** One line changed -
`OUT="$(mktemp /tmp/probe-252-arm-XXXXXX)"` - **with the identical competitor
still running**, same command, same tree, same cycle: **0 voids in 3 runs**,
`rc=0`, `ARMS: 3/3 passed` each time (273s, 279s, 274s). Nothing else was
touched.

And the negative control on the other side: **0 voids in 6 solo runs** of the
unmodified probe, which is what says the interference is doing the work rather
than the mktemp.

---

## 5. THE FIX

### 5.1 Applied here (proved both ways)

`docs/reviews/probe-252-selection-can-fail.sh:52` -
`OUT=/tmp/probe-252-arm.txt` becomes `OUT="$(mktemp /tmp/probe-252-arm-XXXXXX)"`,
with the measurement written at the line so it cannot be "tidied" back.

No `trap` is added on purpose. `lib/harness-result.sh` arms an EXIT trap at
source time and bash has no trap stack, so a cleanup trap here would **replace
the result emitter** and reintroduce the silence `7dab0dd` removed. The probe
already leaves one file in `/tmp` per run today; it now leaves a uniquely named
one.

`scripts/check-u3-audit-controls.sh:84` already does exactly this for its
coverage database (`COVDB="$(mktemp /tmp/u3-controls-covdb-XXXXXX)"`). The
pattern was in the family and applied to one file out of five.

### 5.2 Proposed, NOT applied - the four siblings

Same defect, same fix, in a file several agents are live in right now, so it is
written down rather than edited:

| Site | Path | Read window |
|---|---|---|
| `scripts/check-u3-audit-controls.sh:127,137,140` | `/tmp/u3-base.txt` | baseline write -> `tail` |
| `scripts/check-u3-audit-controls.sh:266,307,319,324` | `/tmp/u3-mut.txt` | **every verdict in the harness** |
| `scripts/check-u3-audit-controls.sh:468,474` | `/tmp/u3-sel.txt` | the intact-tree resolution check |
| `docs/reviews/probe-252-rc4-verdict-trap.sh:55,137` | `/tmp/probe-252-rc4.txt`, `/tmp/probe-252-fake-fail.txt` | that probe's arms |

Fix: `mktemp`, with the paths added to the existing
`trap 'harness_result_emit; rm -f "$COVDB"' EXIT` at `:88` rather than a second
trap.

`/tmp/u3-mut.txt` is the one that matters, because `:319` reads a **verdict** out
of it:

```
319:  elif grep -qE "^(FAILED|ERROR) [^ ]*$want" /tmp/u3-mut.txt; then
320:    echo "$id: killed by $want"
```

A concurrent harness in another worktree runs the **same rows against the same
test names**, so the lines it writes to that path are precisely the lines that
satisfy this grep. That is a false KILL - a lying green in the harness whose
stated purpose is to prevent one - and it is the same family as #263's rc=4
verdict trap and #254's collection-error-scored-as-a-kill.

**I did not reproduce it.** One probe run (279s) against a competitor replaying a
**real** `/tmp/u3-mut.txt` captured at row M6 of a normal run
(`/tmp/diag-262-mut-M6.txt`, 27 lines, `FAILED
tests/test_audit.py::test_arm1_before_the_side_effect_the_call_fails` at :25)
produced 3/3 and no false kill. The reason is structural and it is the same
reason `$OUT` *is* reproducible: the harness's read window on `/tmp/u3-mut.txt`
is the few milliseconds between pytest exiting and the grep, while `$OUT`'s is
the full 90s. So: **mechanism present by construction, not observed in 1 attempt,
narrow window.** It should still be fixed; it should not be reported as measured.

### 5.3 Proposed, NOT applied - stop the misdiagnosis

`docs/reviews/probe-252-selection-can-fail.sh:141`, before the two `case`
statements:

```bash
if [ -z "$sel_line" ]; then
  echo "  ARM VOID: no SELECTOR line for $row in the harness output at all."
  echo "  This is NOT the wide fallback - it is a readback that returned"
  echo "  nothing. Check \$OUT for NUL bytes and for a second run of this"
  echo "  probe or of \$HARNESS elsewhere on this machine."
  exit 2
fi
```

Not applied because it fixes legibility, not the defect, and I have not measured
it both ways. It is worth having: for the whole of #262 the probe answered "the
map went wide" to a question the map had never been asked, and two days of
map-shaped hypotheses followed from that one sentence.

---

## 6. WHAT I RULED OUT, AND HOW

All of these are answered by the **6 solo runs, 0 voids** table in section 2 -
each is a mechanism that would have to show up in a solo sequence.

* **Ordering dependence between arms / alone-vs-in-sequence.** Every solo run
  executed all three arms in the same order and all three passed, six times. A
  row that passes alone and fails in sequence would not survive that.
* **State left between rows** - a coverage database, `.pytest_cache`,
  `__pycache__`, a partly restored source file. `COVDB` is already `mktemp` per
  run (`:84`) and removed by the EXIT trap (`:88`); `-p no:cacheprovider` is on
  every pytest call; `PYTHONDONTWRITEBYTECODE=1` is exported at `:63`; both the
  probe (`:106-110`) and the harness (`:273-277`) fail the run *loudly* on a
  restore that leaves a diff. Six consecutive runs on one tree, no drift.
* **A timeout firing near the row's real cost.** `BASELINE_TIMEOUT=900`,
  `ROW_TIMEOUT=900`, `SELECTOR_TIMEOUT=120` (`:51-53`) against a measured harness
  wall of ~90s. Not close, and a `timeout` firing would print the explicit
  `TIMED OUT after 900s` branch at `:269`, which appears in none of the 12 logs.
* **Test-order randomisation.** Not installed. The only pytest plugins in this
  environment are `pytest`, `pytest-asyncio`, `pytest-cov` - no `pytest-randomly`,
  no `pytest-xdist`. `addopts` (pyproject `:157-163`) sets no ordering flag.
* **Coverage writing several data files.** `[tool.coverage.run]` sets no
  `parallel`, no `concurrency`, no `COVERAGE_PROCESS_START` - the config comment
  says so itself and treats it as a known gap.
* **A test reading the clock or the filesystem.** Would not produce a *selector*
  void; the selector is computed before the mutation is even written (`:163-164`)
  and is a pure function of the anchor text and the coverage db.
* **The two already-refuted map hypotheses.** Not re-run, per the brief. Both are
  consistent with this diagnosis: the map is fine, and the harness printed the
  right line - the probe never got to read it.

## 7. WHAT I DID NOT VERIFY

* **I never ran two probes in two real worktrees.** Scoped to one worktree; the
  competitor is a byte-faithful replay of what a second one writes to the shared
  path. The corruption, the `binary file matches`, and the empty `sel_line` are
  all real.
* **I did not reproduce the `/tmp/u3-mut.txt` false kill** (section 5.2). One
  attempt, structural reason for the narrow window given.
* **I did not check the other selecting harnesses** -
  `check-u9-http-amputation.sh`, `check-u4-client-amputation.sh` - for the same
  fixed-path pattern. They use the same deriver and very likely the same `/tmp`
  habit. Unmeasured.
* **Everything here is local.** Nothing ran on the runner, where worktree
  concurrency does not exist and this defect would therefore never appear.
* **I did not re-run `check-row-floor-controls.sh` or the wiring gates** against
  the one-line change. The edit is a variable assignment plus comment in a file
  those gates read for its `run_mutation`/anchor shape, but that is reasoning,
  not a run.
