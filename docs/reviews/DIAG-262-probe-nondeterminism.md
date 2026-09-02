# DIAG-262: why `probe-252-selection-can-fail.sh` read 3/3, then 2/3, then 1/3

Written 2026-09-02 09:28 AM CDT. Worktree `/tmp/diag-262`, branch `diag/262`,
base `96072cd`.

---

## 0. THE ANSWER IN ONE PARAGRAPH

The probe is deterministic. Its **readback** is not. Every arm writes the
harness's stdout to the **fixed, machine-global path `/tmp/probe-252-arm.txt`**
and then greps it for the row's `SELECTOR` line. **Every** worktree of this
repo on this box carries that probe and `scripts/check-u3-audit-controls.sh`
- 82 of 82 when this was rewritten, and the number moves daily; the derivation
is in §3.1 and the literal is deliberately not repeated here - and several
other scripts run that harness. When a second run of any of them opens that same path
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

**CORRECTED.** This section first named six worktrees by hand and called that
an enumeration. It was not one: it was a sample. Enumerated -

```
git worktree list --porcelain | awk '/^worktree /{print $2}' \
  | while read -r w; do [ -f "$w/scripts/check-u3-audit-controls.sh" ] && echo "$w"; done | wc -l
```

**82 of 82** worktrees carried the harness when this paragraph was rewritten;
the reviewer got **75 of 77** an hour earlier. The number is not a constant -
agents add and remove worktrees all day - so what is recorded here is the
command, not its output, and a reader who needs the figure should re-run it.
The direction is what matters and it only ever gets worse: *every* worktree of
this repo on this box carries the harness, and `/tmp` is not per-worktree.
And the harness is invoked from at least four places -
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

**CORRECTED - a trap IS added, and the original reasoning here was a false
dichotomy.** The first version of this section said "no `trap` is added on
purpose", on the ground that `lib/harness-result.sh` arms an EXIT trap at
source time and bash has no trap stack, so a cleanup trap would **replace the
result emitter** and reintroduce the silence `7dab0dd` removed. That danger is
real, and it is real only for the *naive* form. The **chained** form does not
have it, and it is this repository's own established pattern - the `$COVDB`
trap in `scripts/check-u3-audit-controls.sh`, and
`docs/reviews/probe-252-rc4-verdict-trap.sh:82`. §5.2 below prescribes exactly
that chained form for the siblings; there was never a reason for the probe not
to have it too. Applied:

```bash
trap 'harness_result_emit; rm -f "$OUT"' EXIT
```

VERIFIED by amputation rather than by reading it: the probe aborted at its
dirty-tree guard (`rc=3`, the abnormal path a displaced emitter would render as
silence) still printed
`HARNESS-RESULT name=probe-252-selection-can-fail.sh rows=0 floor=0
status=refused`, and the count of `/tmp/probe-252-arm-*` files was unchanged
across the run.

The supporting sentence was also wrong and is withdrawn. It said "the probe
already leaves one file in `/tmp` per run today; it now leaves a uniquely named
one." Pre-fix the probe left **one file per MACHINE, reused forever**. The
`mktemp` alone would have swapped that for **one new file per RUN, unbounded**,
and four such files (~21KB apiece) had already accreted from the diagnosis runs
before anyone noticed. Trading a shared path for an unbounded one is a real
regression, and it was sold here as a non-change. The trap is what makes the
`mktemp` a fix rather than a swap.

`scripts/check-u3-audit-controls.sh`'s coverage database
(`COVDB="$(mktemp /tmp/u3-controls-covdb-XXXXXX)"`) was already doing exactly
this. **"The pattern was in the family and applied to one file out of five" was
wrong, and understated the job by a factor of four.** Measured, SHA-pinned at
this commit's parent `d314283`:

```
/usr/bin/grep -c 'OUT=/tmp/' scripts/*.sh | /usr/bin/grep -v ':0' | wc -l      -> 22

git grep -hn -E '/tmp/[A-Za-z0-9._-]+\.(txt|json|db)' d314283 \
      -- 'scripts/*.sh' 'docs/reviews/*.sh' \
  | /usr/bin/grep -vE '^[0-9]+:[[:space:]]*#' \
  | /usr/bin/grep -oE '/tmp/[A-Za-z0-9._-]+\.(txt|json|db)' | sort -u | wc -l -> 33
```

**22** `OUT=/tmp/` assignments in `scripts/*.sh`, and **33** distinct fixed
`/tmp` paths on executable (non-comment) lines across **28** tracked shell
harnesses. `/usr/bin/grep` is named explicitly because an interactive shell on
this box has `grep` shimmed to ugrep, which answers a different question; the
commands are printed so the next reader can re-run them instead of trusting
these numbers. This commit removes four of the 33 (`probe-252-arm`, `u3-base`,
`u3-mut`, `u3-sel`), leaving **29**. It is one job out of twenty-two, not one
out of five, and it needs its own sweep ticket.

### 5.2 The siblings - three APPLIED here, and the confirmed rest

The first version of this section deferred all of these. **That deferral was the
defect the review caught**: making `$OUT` private while leaving the harness's
three paths shared did not reduce the exposure, it removed the only signal the
exposure emitted. See §5.4. The three `check-u3-audit-controls.sh` paths are
therefore fixed in this commit.

| Site (pre-fix, `d314283`) | Path | Read window | State |
|---|---|---|---|
| `check-u3-audit-controls.sh:127,137,140` | `/tmp/u3-base.txt` | baseline write -> `tail` | **APPLIED** -> `$BASE_OUT` |
| `check-u3-audit-controls.sh:266,307,319,324` | `/tmp/u3-mut.txt` | **every verdict in the harness** | **APPLIED** -> `$MUT_OUT` |
| `check-u3-audit-controls.sh:468,474` | `/tmp/u3-sel.txt` | the intact-tree resolution check | **APPLIED** -> `$SEL_OUT` |
| `probe-252-rc4-verdict-trap.sh:55,137` | `/tmp/probe-252-rc4.txt`, `/tmp/probe-252-fake-fail.txt` | that probe's arms | still open - agents live in that file |
| `check-u9-http-amputation.sh:72` | `/tmp/u9-amp.txt` | that harness's arms | **CONFIRMED**, not fixed here |
| `check-u9-http-controls.sh:64` | `/tmp/u9-mut.txt` | that harness's verdicts | **CONFIRMED**, not fixed here |
| `check-u4-client-amputation.sh:62` | `/tmp/u4-amp.txt` | that harness's arms | **CONFIRMED**, not fixed here |
| `check-u4-client-controls.sh:75,124` | `/tmp/u4-base.txt`, `/tmp/u4-mut.txt` | baseline and every verdict | **CONFIRMED**, not fixed here |

The last four rows were parked in §7 as "did not check ... very likely the same
`/tmp` habit". They are no longer very likely, they are **confirmed**, at those
file:line cites, SHA-pinned:

```
git grep -n -E '=/tmp/[a-z0-9-]+\.txt|>/tmp/[a-z0-9-]+\.txt' d314283 \
  -- scripts/check-u9-http-amputation.sh scripts/check-u9-http-controls.sh \
     scripts/check-u4-client-amputation.sh scripts/check-u4-client-controls.sh
```

They are **deliberately not edited**: other agents are live in those files while
this lands. Recorded here rather than left in §7, because an item parked as
"very likely" is one nobody schedules.

The fix applied is `mktemp`, chained into the trap that already existed rather
than a second trap that would displace the emitter, and each path written ONCE
into a variable so the writer and the reader cannot drift:

```bash
BASE_OUT="$(mktemp /tmp/u3-base-XXXXXX)"
MUT_OUT="$(mktemp /tmp/u3-mut-XXXXXX)"
SEL_OUT="$(mktemp /tmp/u3-sel-XXXXXX)"
trap 'harness_result_emit; rm -f "$COVDB" "$BASE_OUT" "$MUT_OUT" "$SEL_OUT"' EXIT
```

The `rm -f` is not housekeeping: without it the `mktemp` would trade a shared
path for an unbounded per-run one, which is the mistake §5.1 made and withdrew.

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

**CORRECTED - the false kill has now been produced, and the reason this
section first gave for not producing it was wrong by three to four orders of
magnitude.**

The original text read: one probe run (279s) against a competitor replaying a
**real** `/tmp/u3-mut.txt` captured at row M6 of a normal run
(`/tmp/diag-262-mut-M6.txt`, 27 lines, `FAILED
tests/test_audit.py::test_arm1_before_the_side_effect_the_call_fails` at :25)
produced 3/3 and no false kill; and the stated reason was that "the harness's
read window on `/tmp/u3-mut.txt` is the few milliseconds between pytest exiting
and the grep, while `$OUT`'s is the full 90s". The negative result stands. The
**explanation does not.**

The corruptible window does not open when pytest exits. It opens at the `>` on
the pytest redirect at `:266` and closes at the verdict grep at `:319`, so the
**whole pytest row sits inside it** - which is the identical argument this
document makes correctly for `$OUT` at §3. Measured, by instrumenting a copy of
the harness with `date +%s.%N` at exactly those two points and running it once
(`/tmp/rev262-logs/instr.err`, recomputed independently from the raw
timestamps):

```
M1  15.77s  M2   0.59s  M3   0.62s  M4   0.60s  M5  17.61s
M6   0.58s  M7   0.59s  M8   0.58s  M9   0.62s  M10 18.95s
M11 15.46s  M12  0.63s  M13  0.62s  M14  0.63s  M15  0.65s
15 of 15 rows reach the :319 read;  total exposure 74.5s
```

**0.58s to 18.95s per row, 74.5s in total**, against a harness whose measured
solo wall time on this box is 87-95s: **roughly 80% of the run**, not
milliseconds. Comparable to `$OUT`'s 90s, not three orders of magnitude below
it.

And the false kill itself was produced. With M6's killer assertion neutered
exactly as the probe's arm 1 does it, the positive control solo (n=4,
`/tmp/rev262-logs/control-neutered-solo.log`) gives
`M6 ...: the selected tests went red, but NOT at test_arm1_... - a coincidence,
not a control` and `killed=14/15`. Under a concurrent writer putting the single
line a real rival harness's own M6 row writes to that path
(`/tmp/rev262-logs/sat-victim.log`):

```
M6  a pre-write audit failure no longer fails the call: killed by test_arm1_before_the_side_effect_the_call_fails
HARNESS-RESULT name=check-u3-audit-controls.sh rows=15 floor=15 killed=3/15 status=breach
*** FALSE KILL OBSERVED ***
```

A row whose killer *cannot fail* reported `killed by` that killer, manufactured
entirely from another process's bytes.

**The honest denominator, and it must not be rounded up.** That writer is
synthetic and saturating - `>` every 50ms - so it answers *"does a write landing
in the window produce a false kill"*, and **not** *"how often does one"*. With a
**genuine** rival (an unmodified second harness looping in another worktree) the
result was **0 false kills in 3 trials**, matching this document's own single
negative; and the observable there is narrow, because on a clean tree all 15
rows are legitimately killed, so only the neutered row can show a false kill and
3 trials is 3 row-windows, not 45.

So, precisely: the mechanism is **MEASURED**, the frequency is **UNMEASURED**,
and the structural reason once given for the low frequency is **REFUTED**. This
is why the path is fixed in §5.2 above rather than left as a written-down
proposal.

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

### 5.4 Applied here - the probe now asserts the tally it already printed

**This is the finding the review of this commit was built on, and it is the one
that mattered most.** Making `$OUT` private while leaving the harness's three
paths shared did not shrink the failure. It changed its *shape*, from a loud
refusal into a silent green - which is strictly worse, because a defect that
announces itself is one somebody fixes.

The arm passes when the row stops reporting `killed by`. A harness that lost
that row for **any other reason** renders identically, so the arm passes
vacuously - the precise failure this probe was written to rule out (its own
header: *"a selection that could never fail would produce exactly the same
fifteen greens"*). And `killed=N/15` was printed on screen the whole time with
nothing checking it. An arm that cannot fail is not a control.

MEASURED, before the §5.2 `mktemp` landed, running the probe as this commit
first shipped it against a rival truncating the then-shared `/tmp/u3-mut.txt`:

```
  harness : rc=1  HARNESS-RESULT ... killed=12/15 status=breach
  harness : rc=1  HARNESS-RESULT ... killed=13/15 status=breach
  harness : rc=1  HARNESS-RESULT ... killed=13/15 status=breach
########## ARMS: 3/3 passed
HARNESS-RESULT name=probe-252-selection-can-fail.sh rows=3 floor=3 fired=3/3 status=ok
```

`rc=0`. Three arms, none of which measured the harness it aimed at, and a clean
green over all three. Pre-fix, contention on `$OUT` gave `exit 2
status=refused`; this commit's first form gave that.

The discriminator is arithmetic and was available all along: each arm neuters
exactly ONE killer, so the harness must lose exactly ONE kill - `killed=14/15`.
Applied in `arm()`:

```bash
killed=$(printf '%s' "$result_line" | grep -oE 'killed=[0-9]+/[0-9]+')
if [ "$killed" != "$EXPECT_KILLED" ]; then   # EXPECT_KILLED=killed=14/15
  ...
  exit 2
fi
```

`exit 2` and `status=refused`, the same codes as the existing void branches, for
the same reason: a measurement that was not made must refuse, not pass.

PROVED BOTH WAYS, by running the real probe and reading its real exit code:

* **Positive control (the assertion fires).** The fixed probe, with this
  assertion, run against the **pre-fix** harness under the same rival:
  `ARM VOID: the harness reported killed=13/15, not killed=14/15`, `rc=2`,
  `HARNESS-RESULT ... rows=0 floor=0 status=refused`, at arm 1. The silent green
  above becomes a refusal on identical interference.
* **Negative control (it does not fire spuriously).** The fixed probe against
  the **fixed** harness under that same rival: `killed=14/15` on all three arms,
  `ARMS: 3/3 passed`, `status=ok`, `rc=0`.

**Both remedies are applied, not one.** §5.2's `mktemp` stops the contamination;
this stops a *future* contamination - from any of the 29 fixed `/tmp` paths still
in the tree, or from anything else that cuts the harness short - being reported
as a pass. The `mktemp` is the fix; the assertion is what makes the next one
visible instead of silent.

### 5.5 The gates that read these two files, RUN rather than reasoned about

§7 originally closed `check-row-floor-controls.sh` by inspection - "the edit is
a variable assignment plus comment in a file those gates read for its
`run_mutation`/anchor shape, but that is reasoning, not a run." The edits here
are much larger than that, so it was run, on both files, on the committed tree:

```
check-row-floor-controls.sh docs/reviews/probe-252-selection-can-fail.sh
  row invocations still matching: 2 (was 3, must be 2)
  HARNESS-RESULT name=probe-252-selection-can-fail.sh rows=2 floor=3 fired=2/2 status=breach
  CONTROL FIRED ... exiting 1                                              rc=0

check-row-floor-controls.sh check-u3-audit-controls.sh
  row invocations still matching: 14 (was 15, must be 14)
  HARNESS-RESULT name=check-u3-audit-controls.sh rows=14 floor=15 killed=14/14 status=breach
  CONTROL FIRED ... exiting 1                                              rc=0
```

The probe's `^arm "` anchor count is **3 before and 3 after** - `git show
bb57bf8:docs/reviews/probe-252-selection-can-fail.sh | /usr/bin/grep -c '^arm "'`
against the same count on the worktree - and that shape is what
`check-row-floor-controls.sh:198` selects on, so the selection is unchanged and
the control still finds its rows.

Worth naming, because it is a positive control on §5.4's new assertion in the
other direction: the floor control deletes one of the probe's three arms, and
the surviving two both ran to `fired=2/2`. The tally assertion did **not** fire
spuriously on a legitimately altered run.

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

This list is for what remains unsettled. Four items that were on it have since
been settled and are struck through with where they went, because an item left
here after it has been measured is one nobody re-reads.

* ~~**I never ran two probes in two real worktrees.**~~ **SETTLED, and the
  caveat was conservative.** Two genuine unmodified pre-fix probes started ~0s
  apart from two real worktrees voided on the **first** attempt, with the exact
  predicted signature (`/tmp/rev262-logs/genuineA.log`): 1 void in 1 genuine
  pair, against 2 in 3 for the replay. The replay under-stated the defect.
* ~~**I did not reproduce the `/tmp/u3-mut.txt` false kill.**~~ **SETTLED - see
  §5.2.** Produced under a saturating synthetic writer; 0/3 under a genuine
  rival. Mechanism MEASURED, frequency UNMEASURED, and the "narrow window"
  explanation REFUTED at 0.58-18.95s per row, 74.5s per run.
* ~~**I did not check the other selecting harnesses.**~~ **SETTLED, in the bad
  direction - see the §5.2 table.** `check-u9-http-amputation.sh:72`,
  `check-u9-http-controls.sh:64`, `check-u4-client-amputation.sh:62`,
  `check-u4-client-controls.sh:75,124` all carry it. Confirmed, not fixed here:
  other agents are live in those files.
* ~~**I did not re-run `check-row-floor-controls.sh` or the wiring gates.**~~
  **SETTLED - run, not reasoned.** See §5.5.

Still open:

* **Everything here is local.** Nothing ran on the runner, where worktree
  concurrency does not exist and this defect would therefore never appear. That
  cuts both ways: CI cannot catch a regression of this defect, so nothing but
  review protects these paths.
* **The frequency of the `/tmp/u3-mut.txt` false kill is not measured**, only
  its mechanism. See §5.2 for the denominator, which must not be rounded up into
  a rate.
* **29 fixed `/tmp` paths remain**, across 26 tracked shell harnesses, on this
  commit - re-run §5.1's derivation against `HEAD` rather than `d314283` to
  reproduce that pair. (A commit cannot cite its own SHA; an earlier draft of
  this line did, and the amend that followed made the cite dangle.) §5.1
  publishes the command for the PATHS but not for the FILES, and the two are
  not the same question: closure review read 27 harnesses here and called this
  bullet self-contradictory. It is not. That 27 comes from counting files
  WITHOUT §5.1's non-comment filter, which is the filter that produces the 29
  the same reader accepted - with it dropped the path count is 31, not 29, so
  the pair 27/29 mixes two populations. Both files leave the set on this
  commit, not one: `scripts/check-u3-audit-controls.sh` keeps no matching line
  at all, and `docs/reviews/probe-252-selection-can-fail.sh` keeps two, both of
  them COMMENTS about the path it stopped using. 28 - 2 = 26. The file half of
  the derivation, so the next reader need not re-invent it:

  ```
  git grep -n -E '/tmp/[A-Za-z0-9._-]+\.(txt|json|db)' HEAD \
        -- 'scripts/*.sh' 'docs/reviews/*.sh' \
    | sed 's|^HEAD:||' \
    | /usr/bin/grep -vE '^[^:]+:[0-9]+:[[:space:]]*#' \
    | cut -d: -f1 | sort -u | wc -l                                     -> 26
  ```

  This commit clears four of the 33. The rest need a sweep ticket, and until
  it lands the §5.4 assertion is the only thing standing between a contaminated
  harness and a green probe.
* **`probe-252-rc4-verdict-trap.sh:55,137` is not fixed.** Same defect, same
  remedy, deferred only because agents are live in that file.
