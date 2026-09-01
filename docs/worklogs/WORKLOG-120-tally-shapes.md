# WORKLOG #120 - the tally half of the shape-list defect

Branch `fix/tally-shapes`, off `main` at 251e306. Not merged, not pushed.

## The short version

**Q1 (the filed defect): the brief's hypothesis was RIGHT, and I applied it.**
`scripts/ci-harness-gate.sh` no longer parses prose. Each harness publishes
`fired=N/M`, `killed=N/M` or `applied=N/M` on the canonical `HARNESS-RESULT`
line through `scripts/lib/harness-result.sh`, and the gate reads the field its
own flag names. The three prose literals are deleted from the gate.

**Q2 (what the census exposes): the brief's numbers are WRONG, and the real
answer is FOUR harnesses, not thirteen.** Details and the corrected census
below. Of those four, none has a decorative tally: every one is already read by
the harness's own internal gate. What was missing is the SECOND, INDEPENDENT
layer that the sibling steps have.

**One defect found that #120 did not ask about**, pre-existing and recorded
below: `scripts/ci-harness-gate-controls.sh` has been exercising a copy of the
gate with the shared library MISSING since #107, so all 24 of its rows were
certifying a gate whose canonical-line machinery was absent.

**One thing I checked and did NOT file.** `check-u1-pid1-shutdown.sh` is the
only script under `scripts/` that `ci.yml` never invokes. That is deliberate and
argued in the script itself at `scripts/check-u1-pid1-shutdown.sh:35-38` ("CI
has no Docker daemon"), accepted in `docs/reviews/REVIEW-R3.md:519-520`, and
recorded in `CONTRIBUTING.md:151`. It prints no tally and is outside #120.

## CORRECTION: the brief's census undercounts two of its three flags

`docs/briefs/EVIDENCE-120-tally-shapes.md:52-61` reports the flags `ci.yml`
passes as 9 `--controls-fired`, 2 `--result-killed`, 2 `--anchors-applied`.

Two of those three are wrong. The census counted flags that sit on the SAME
LINE as `ci-harness-gate.sh`, and thirteen of the thirty-one gate invocations
in `ci.yml` are multi-line `run: |` blocks whose flags are on a continuation
line. Joining continuations first:

```
                     census   measured
--controls-fired          9         13
--result-killed           2          2
--anchors-applied         2          7
```

This is the census's own subject arriving one level up: a count whose selector
cannot see the form the writer did not picture. The regeneration snippet at
`docs/briefs/EVIDENCE-120-tally-shapes.md:63-67` only covers the SCRIPT side,
so the flag side was never regenerable and could not have been re-derived.

**So "roughly thirteen harnesses print a tally nothing reads" is not right.**
The true gap is four:

| harness | prints | gate flag | verdict |
|---|---|---|---|
| `check-u7-resilience-amputation.sh` | `applied` | none | **missing second layer -> flag ADDED** |
| `check-u9-http-amputation.sh` | `applied` | none | **missing second layer -> flag ADDED** |
| `check-u10-write-amputation.sh` | `applied` | none | **missing second layer -> flag ADDED** |
| `check-harness-anchors-controls.sh` | `fired` | n/a - not run through the gate | **correctly outside the gate; see below** |

Every other tally-printing harness already had its flag.

## Q1 - what I built, and the one route I deliberately did NOT take

### The change

`scripts/lib/harness-result.sh` gains `harness_result_tally <kind> <n> <m>` and
one optional field on the canonical line:

```
HARNESS-RESULT name=<basename> rows=<n> floor=<n> [<tally>] status=<ok|breach|refused>
```

`<tally>` is `fired=N/M`, `killed=N/M` or `applied=N/M` - **one name per
meaning, never one field over four.** The function REFUSES any other kind, so a
fifth meaning cannot be smuggled in under a fourth name. The field is OMITTED
entirely when a script publishes none; a fabricated `fired=0/0` would be read by
the gate as "this harness holds zero controls" and would be a false finding on
every script that simply has no tally.

`scripts/ci-harness-gate.sh` loses its three prose regexes and reads the field
its own flag names, selecting the line by `name=`. The three diagnoses stay
written apart, byte-for-byte as they were, because they describe three different
things. The AMPUTATION inversion gets no field at all: it is a reading of the
exit code, not a tally, and `--amputation` is where it lives.

`docs/reviews/check-harness-result.sh` gains the same set equality one level
down: `{ scripts that print a tally } == { scripts that publish that same
tally }`, per kind.

### The tempting wrong answer, and why I rejected it

There is a cheaper route that touches no harness: every one of the 26
tally-printing harnesses **already gates on its own tally internally** and exits
non-zero when it is short. I verified this for all 26 by reading each one's
closing comparison. So `status=ok` combined with the existing `rows=` field
ALREADY implies a complete tally, and the gate's three branches could have been
replaced by `status=ok && rows > 0` with no harness edits at all.

**That would have been wrong, and it is worth writing down why.** It makes the
gate's tally check a restatement of the exit code it has already checked at
`scripts/ci-harness-gate.sh:220`. The whole value of the gate's tally branch is
that it is an INDEPENDENT second reading: delete a harness's own `[ "$FIRED"
-ne "$TOTAL" ]` line and the harness exits 0, but the published field is still
short and the gate still fails. Derive it from `status` and that property is
gone. This is the same claim `docs/reviews/check-harness-result-controls.sh`
makes with its C8 amputation row about `status` itself.

The independence survives the change because the field is passed the SAME two
variables the harness's own comparison uses and its own sentence prints - it is
a second reading of the counters, not a second counting.

### The call sites are DERIVED, not hand-written

All 26 `harness_result_tally` calls were inserted by a transformer that parses
the arguments out of the echo statement already in the file, so the field cannot
disagree with the prose beside it. It asserted its population (26 changed, 0
already-done, 0 refused) and refuses a partial pass. A hand-written table of 26
harness/variable pairs would have been the shape list this change exists to
delete, one level up.

It handled three irregular forms correctly without special-casing:
`check-u0-test-controls.sh`'s `$((TOTAL - BAD))/$TOTAL`,
`check-u11-advisory-controls.sh`'s `$FIRED/$HELD`, and
`check-u15-gate-controls.sh`'s `${FIRED}/${TOTAL}`.

## Q2 - per harness, is the tally asserted or decorative?

**Neither answer is "decorative" anywhere.** I expected to find some and did not.
Every one of the 26 tally-printing harnesses gates on its own tally and exits
non-zero when it is short - `[ "$FIRED" -ne "$TOTAL" ]`, `[ "$FAIL" -eq 0 ] ||
exit 1`, `[ "$ROWS" -ne "$APPLIED" ]`, `[ "$BAD" -eq 0 ]` as a final statement,
and three more spellings. A number printed here is always read by SOMETHING.

So the real question is not "read or not read" but **"read twice or read once"**,
and the four harnesses in the corrected census are the ones read only once.

### The three that gained a flag

`check-u7-resilience-amputation.sh:389`, `check-u9-http-amputation.sh:311` and
`check-u10-write-amputation.sh:328` each compare `APPLIED` to `ROWS` and exit 3
or 1. Each also prints a phrase from the gate's anchor vocabulary on the path
that produces a short tally - `COULD NOT APPLY` at `:122`/`:126`/`:113` and
`AMPUTATION DID NOT LAND` at `:129`/`:133`/`:120` - so the gate's vocabulary
grep is a further layer again.

**Verdict: missing assertion, and I added it.** These three differ from their
five `--anchors-applied` siblings for no reason anyone decided: the steps were
written at different times. The second layer is what catches a harness whose own
comparison is DELETED, which is the failure the other five are protected from
and these three were not. It costs one flag.

### The one that is correctly outside the gate

`check-harness-anchors-controls.sh` is run by `ci.yml:909-922` INLINE, not
through `ci-harness-gate.sh`, and that step reads only its exit code. Its tally
is read by its own `[ "$FIRED" -ne "$TOTAL" ]` at `:322`.

**Verdict: leave the step as it is - and the reason is not "it was fine".** It
and `ci-harness-gate-controls.sh` are the two harnesses that deliberately PRINT
anchor-failure vocabulary as part of passing: they exercise a checker by
breaking anchors on purpose. `ci-harness-gate.sh` fails any harness whose output
contains a vocabulary phrase, so wrapping either of them in the gate would fail
it for doing its job. Both now publish their tally field regardless, so the
second layer is one line away for whoever wants it; I did not add an inline
grep to `ci.yml` because inline gate logic in a `run:` block is the two-lists
defect #27 removed.

I have NOT measured that these two print a vocabulary phrase on a passing run -
I read it out of their sources. See the unsettled list.

## The positive controls, and what each PROVED

The brief asked for a positive control per flag, not per file, and for proof
that a new gate FAILS when its field is absent or wrong. All rows live in
`scripts/ci-harness-gate-controls.sh`, run the REAL gate against stub harnesses,
and were watched failing before being trusted.

**28/28 controls fired** (was 24/24). Five rows are new and I read the actual
`::error::` text of each rather than scoring it on exit code alone - a row can
fire for the wrong reason and this family has shipped one that did.

| row | stub publishes | flag | what the gate said | proves |
|---|---|---|---|---|
| C12 | no field, prose `13/14 controls fired.` still printed | `--controls-fired` | `carries no readable 'fired=N/M' field` | the fired gate fails CLOSED on an absent field, and is no longer reading the prose |
| C25 | no field, prose `RESULT: 11 killed, 1 not killed` printed | `--result-killed` | `carries no readable 'killed=N/M' field` | same, for killed |
| C26 | no field, prose `ROWS: 11   ANCHORS APPLIED: 9` printed | `--anchors-applied` | `carries no readable 'applied=N/M' field` | same, for applied |
| C27 | no canonical line at all | `--controls-fired` | `printed no HARNESS-RESULT line naming itself` | the OTHER structural message is reachable; without this row it is dead code |
| C28 | a perfect `applied=11/11` | `--controls-fired` | `carries no readable 'fired=N/M' field` | **the three names did not get collapsed into one reader.** A gate matching "any tally field" passes this row and would then read an anchor count under a control flag |

C28 is the row the brief's warning asks for. C12/C25/C26 are the "gate that
greps a phrase its harness never prints" arm, one per flag, each with the prose
still present so the row also proves the prose is no longer what is read.

The pre-existing counting rows C9/C10/C11/C13/C14/C15/C16/C24 were carried over
onto the fields and still fire, so the numeric arms (short tally, zero tally)
are unchanged in behaviour.

## FINDING F1 (pre-existing, not part of #120's brief): the gate's own controls
## harness has been testing a gate with the shared library missing since #107

`scripts/ci-harness-gate-controls.sh:32-33` copied only `ci-harness-gate.sh`
into its work directory. The gate sources `$(dirname
"${BASH_SOURCE[0]}")/lib/harness-result.sh`, which in that directory does not
exist. Measured verbatim, on `main` at 251e306, by replaying the harness's own
setup:

```
/tmp/tmp.liOvw0H64C/scripts/ci-harness-gate.sh: line 57: /tmp/tmp.liOvw0H64C/scripts/lib/harness-result.sh: No such file or directory
/tmp/tmp.liOvw0H64C/scripts/ci-harness-gate.sh: line 150: harness_result_ran: command not found
```

All 24 rows still passed, because `row()` compares only the exit code and a
`command not found` under `set -uo pipefail` with no `-e` changes none. So since
#107 this harness has been certifying a gate whose canonical-line machinery was
entirely absent - and no `HARNESS-RESULT name=ci-harness-gate.sh` line appears
anywhere in its 24 rows of output, which is the visible symptom nobody looked at.

**This is the switched-off-versus-broken shape, inside the controls written to
prevent it.**

**Fix, shipped here:** `cp -R "$REPO/scripts/lib" "$WORK/scripts/"`, with the
measurement above recorded at the site. The gate's own line now appears in the
control output (`HARNESS-RESULT name=ci-harness-gate.sh rows=1 floor=0
status=breach` on a failing row), which is how I know the fix landed.

It is also load-bearing for #120: the stubs now source that same file to publish
their tally through the REAL emitter rather than echoing a hand-typed
`HARNESS-RESULT` line, which would have put a second copy of the format beside
the one file that is supposed to own it.

## The container gate found two more, and one of them was my own instrument

Extending `docs/reviews/check-harness-result.sh` with the per-kind equality
produced this on its first run:

```
::error::these harnesses print a tally that nothing publishes, so their
         ci.yml gate step cannot read it:
           ci-harness-gate-controls.sh (prints a 'fired' tally, publishes none)
           ci-harness-gate.sh (prints a 'fired' tally, publishes none)
```

- **`ci-harness-gate-controls.sh` was a TRUE positive.** It prints its own
  `N/M controls fired.` at `:201` and is a tally-printing script like any other.
  It now publishes `fired`.
- **`ci-harness-gate.sh` was a FALSE positive of my own selector.** Its only
  match is the DIAGNOSIS it prints when a tally is short - `only N of M controls
  fired` - and a message about a failed tally is not a tally. The gate counts
  nothing and has nothing to publish.

The fix is a filter on the LINE (`::error::` lines are not tally lines), not an
exemption for the file. An exemption list would be the hand-kept list this whole
family of changes exists to delete, and it would have hidden the true positive
sitting next to it. Final state:

```
print a tally line                   : 27
publish the MATCHING tally field     : 27
EQUAL: all 27 tally-printing scripts publish the matching field.
```

27 = the 26 harnesses plus `ci-harness-gate-controls.sh`.

The equality is stated per kind, so a harness that publishes `applied` while
printing `fired` fails it - the machine-checked form of the property C28 proves
at the gate.

## Static gates, each exit code read on its own line

Run in the sandbox worktree with every change applied:

```
python3 scripts/check-harness-anchors.py --self-check --floor 458   exit=0
    (floor derived from ci.yml, not retyped; 34 harnesses, 458 anchors,
     UNMOVED - the inserted calls are not anchors)
python3 docs/reviews/check-row-floor-exactness.py                   exit=0
    (24 harnesses, 16 --min-rows compared to live counts, all equal)
python3 docs/reviews/check-no-errexit.py                            exit=0
    (50 tracked shell scripts, none enables errexit)
python3 docs/reviews/check-no-sigpipe-pipelines.py                  exit=0
    (40 files, 0 in executable code; the new reader uses a here-string)
bash docs/reviews/check-harness-result.sh                           exit=0
bash -n on every edited shell file                                  SYNTAX OK
```

## What I did NOT verify

1. **That `check-harness-anchors-controls.sh` and `ci-harness-gate-controls.sh`
   print an anchor-failure vocabulary phrase on a PASSING run.** This is the
   reason I gave for leaving them outside `ci-harness-gate.sh`, and I read it out
   of their sources rather than measuring it. Both contain the phrases (`DID NOT
   LAND` and `ANCHOR NOT UNIQUE` in the first; those plus `COULD NOT APPLY` in
   the second), and both exist to exercise a checker by breaking anchors on
   purpose, so I believe it - but a phrase present in source is not a phrase
   printed at runtime, which is the exact distinction `ci-harness-gate.sh:112-116`
   was built around. **To settle it:** run each and
   `grep -F 'COULD NOT APPLY' -e 'DID NOT LAND' -e 'ANCHOR NOT UNIQUE'` its
   output. I did not, because both mutate tracked files and every window I had
   was occupied by the exit-code probe, which fails on a tree that moves under
   it.

2. **The `ci.yml` job as a whole has not been run.** I ran the individual gate
   commands from the changed steps, which is what the preamble asks for, but the
   job takes hours and #105 records that no CI run has ever gone green here.

3. **Whether any harness should publish a tally it does not currently print.**
   I only asked whether printed tallies are published and read. A harness that
   counts something internally and prints nothing would be invisible to both the
   census and my checker, because both start from the print statement. That is a
   real blind spot in the same shape as the census's own, one level further in.

## The BEFORE ledger, complete: 37 of 37 rows

Committed at `docs/reviews/ledgers/LEDGER-120-before.txt`. Measured on
`fix/tally-shapes` at 251e306, i.e. the tree WITHOUT this change.

35 rows `rc=0 status=ok`. The only two non-zero rows are both deliberate
refusals by design, not findings:

```
check-suite-floor.sh                       rc=2    status=refused 
ci-harness-gate.sh                         rc=2    status=refused 
```

- `check-suite-floor.sh` reaches its usage branch with no argument (this is
  exactly what row C1 of check-harness-result-controls.sh asserts).
- `ci-harness-gate.sh` run bare names no harness and refuses (row C2).

### One row in this ledger was CONTAMINATED and I re-measured it

The first completed pass recorded `check-u9-http-controls.sh rc=3
status=refused`. That refusal was NOT the harness reporting on itself: the
preceding `check-u9-http-amputation.sh` had been killed by the 900s budget
and stranded a mutation, and u9-http-controls refused because the TREE was
dirty. Left in the ledger it would have shown as `rc=3 -> rc=0` in the
comparison, and I would have been explaining a move that was an artefact of
my own broken pass rather than anything my change did.

I dropped the row, restored the stranded mutation, and re-measured on a
clean tree: **rc=0 status=ok, 42s**. The pre-drop file is kept at
`/tmp/tally-ledgers/before-with-poisoned-row.txt` for anyone who wants it.
The probe defect that produced this is filed as task #146.
