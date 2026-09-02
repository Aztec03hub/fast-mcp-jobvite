# WORKLOG 208 - the orphan leads, read

`suborch-208`, 2026-09-02 01:02 AM CDT, on `fix/208-orphan-leads` cut from local
`main` at `43fca5f` (65 commits ahead of `origin/main` at `6e4fae3`; the push is
held).

**THE HEADLINE IS NOT A COUNT.** 55 file-level candidates narrow to 35 leads, and
**all 35 bare halves were CORRECT at the moment they were written.** Not one of
them is a citation that was ever wrong. The class is real, but its remedy is
almost never "move the orphan to match" - see §4.

## 1. What I measured, before and after

| | candidates |
|---|---|
| file-level, the pre-#208 figure | **55** (51 making a citation, 4 discussing) |
| TEST A drops - the bare line POSTDATES its own repoint | -19 |
| TEST B drops - every qualified half AGREES with it today | -1 |
| **leads to READ** | **35** |

The brief said 47 of 55 were unread and at least six were false. Both hold: 55
reproduced exactly, and TEST A drops **all six** known-false `src/`+`tests/`
continuation comments. It drops 13 more nobody had named.

**TEST A - COEXISTENCE.** Did the bare line itself, byte for byte, stand in the
file at the repoint commit's PARENT? If not, the two spellings were never in the
file together when the sweep ran, so the sweep cannot have walked past it. This
is the `git log -S` read the probe previously prescribed as manual work,
mechanised.

**TEST B - DISAGREES TODAY.** Does the file still cite that document in
QUALIFIED form at a value OTHER than the bare one? Only then does the document
contradict itself.

## 2. Three defects in the detector, two of which nobody had recorded

**D1 - THE PROBE'S HEADLINE ROW WAS ITS OWN CLOSED INSTANCE.** `ADR-0017` is the
one CONFIRMED instance and it was fixed at `be94bce`. The file today reads
`DESIGN.md:489-490` at `:16` and bare `:489-490` at `:67` - **the halves agree.**
The probe listed it FIRST anyway, because it reads history and never looked at
the present state of the other half. A detector whose top row is a closed
instance teaches its reader to discount the whole list. TEST B is that check;
`ADR-0017` is the single row it drops.

**D2 - THE PROBE WAS NONDETERMINISTIC.** Two runs over an IDENTICAL tree, same
code, differed on **99 lines** - every one a `-> :new` destination. `removed[f]
- added[f]` is a set of `str` tuples iterated in hash order, and Python
randomises string hashing per process. So no two readers saw the same output and
a diff between two runs meant nothing. The pairing is now sorted, and the
destination is **no longer printed at all**, because it was never evidence: when
one commit repoints several ranges in one file it pairs an arbitrary removal
with an arbitrary addition. After the fix, two runs differ on **0 lines**.

**D3 - the file-level pairing**, which the brief named and which TEST A closes.

## 3. The verdicts - all 35 read, as at the moment each was written

Read with `docs/adr/README.md:65-72`'s recipe (`git log -S` for the date, then
`git show <sha>^:docs/DESIGN.md`), never `git blame`, which that section records
as giving a confidently wrong answer. **All 35 resolved; none needed hand
work.**

**31 of 35: the bare half is CORRECT AS WRITTEN**, and the as-at text matches
what the citing line says about it, often verbatim:

- `U1-IMPL-REPORT.md:62` calls `:918-923` *"the requirements matrix"*; as at
  `c5de669^` line 918 is `| Tool | Requires |`.
- `U1-IMPL-REPORT.md:63` calls `:982-990` *"the two limits on the word
  'verified'"*; as at that parent, `:982` reads **"Two limits on the word
  'verified' here"**.
- `U0-REPORT.md:49` says a network call *"would quietly contradict `:1185`"*; as
  at `b53886e^`, `:1185` is *"The default suite runs with no network and no
  credentials"*.
- `DESIGN-R7-CONFIRM.md:399` quotes `:1650` as *"the total was stated in"*; as at
  `fe3e8b5^` that line begins *"That rule exists because the total was stated in
  prose three times"*.
- `DESIGN-DELTA-REVIEW.md:259` quotes `:832` as *"while §10.1, 582 lines away,
  deliberately withholds"*; the as-at line is exactly that sentence.

**2 of 35 land on a BLANK line** as at writing, which is the class #62 already
recorded, not this one: `PLAN-REVIEW-R2.md:142` (`:1654`) and
`CONFORMANCE-RESWEEP.md:173` (`:1274`). `PLAN-REVIEW-R2.md:142` is the sharper
of the two - its citing commit **is `135c3ac`, the freeze itself**.

**2 of 35 I could not settle by reading and they are in §6.**

## 4. THE ONE DOCUMENT-LEVEL CONTRADICTION, and it is not where the class predicted

`docs/plans/IMPLEMENTATION-PLAN.md` holds 8 of the 35, and it is the only
CONFIRMED self-contradiction in the set - but the contradiction is **between the
document's own declaration and its repointed halves**, not between two
citations.

The file declares, twice, that its citations are bound to one blob:

- `:20-28` - *"Every `DESIGN.md:NNN` citation below is a line number **in
  `c15b138`** ... **That is why this plan was deliberately NOT repointed at the
  re-freeze**"*
- `:160` - *"Every `DESIGN.md:<line>` citation resolves against the `c15b138` git
  object"*

**Both halves of that are falsified by the tree.** Measured:

    b0e86b8  2026-08-28  changed 182 lines of IMPLEMENTATION-PLAN.md (91 ins/91 del)
    c57f736  2026-08-29  wrote the "deliberately NOT repointed" paragraph

The sweep ran on the 28th; the paragraph claiming it did not was written on the
29th. It is true of the LATER re-freeze to `8a9d63c` and false of `b0e86b8`.

And the bare halves it left behind do not resolve against `c15b138` at all:

    :1220   135c3ac  "- the 200-with-401-body trap;"            <- the citing line's own words
            c15b138  <blank>
    :1222   135c3ac  "- **`.gitignore` covers the credential patterns ...**"
            c15b138  "says `showing 50 of 1,240`. That is more useful ..."
    :1250   135c3ac  "- **the manifest pins `mcp` and the frozen resolve has no lock drift**"
            c15b138  <blank>

**So the document says `c15b138` and its bare citations say `135c3ac`.** That is
one document disagreeing with itself, and it is a bigger instance than
`ADR-0017` because it is a declaration governing 111 citations rather than one
line.

## 5. What I did NOT do, and why

**I RULED NOTHING.** Three remedies are available and choosing between them is
Tier 0's:

1. **Repoint the bare halves to `c15b138`** - makes the document match its own
   declaration. This is "move the orphan to match", which the brief warns is
   usually wrong, and it is wrong here too for the ADR-0017 reason: the bare half
   is the untouched original and the repointed half was correct only until
   `DESIGN.md` moved again. It has moved four times since.
2. **Restore the qualified halves to `135c3ac`** - the `be94bce` remedy, applied
   to this file. Undoes `b0e86b8` here rather than extending it.
3. **Correct the declaration** to name `135c3ac`, and treat `b0e86b8`'s 91 lines
   as the defect.

I did not implement any of them, and I did not touch a single citation.

**A GAP I FOUND AND AM REPORTING RATHER THAN CLOSING.**
`docs/reviews/repoint-design-citations.py:135` skips exactly one directory:

    if m["file"].startswith("docs/adr/"):

`#111` ruled `docs/plans` a RECORD on the same reasoning, and `docs/reviews` and
`docs/worklogs` hold **26 of the 35 leads** while no ruling covers them at all.
The skip and the rulings are out of step. Widening that prefix is a one-line
change I deliberately did not make: which directories are records is a ruling.

## 6. What I could NOT settle

- **`IMPLEMENTATION-PLAN.md:978`, bare `:602`.** The citing line quotes *"`:602`
  now reads: 'If no library satisfies it, an inline breaker in ...'"*. As at
  `299cf8b^`, `:602` is the breaker's state-transition list - **not** the
  sentence quoted. Neither `135c3ac` nor `c15b138` carries the quoted text at
  `:602` either. Its repoint sha is `e87a859`, not `b0e86b8`, so it may be a
  different mechanism. I could not date the quoted sentence.
- **`PLAN-REVIEW-R1.md:488`, bare `:581`.** The as-at line is the breaker's
  transition list; the citing line calls `:581` *"a call-path constraint ... a
  one-library rejection test"*. Those are arguably the same subject read two
  ways, and I could not settle it by reading alone.
- **Whether `docs/reviews` and `docs/worklogs` are records.** That is a ruling,
  not a measurement, and §5 hands it over.

Attempted and settled, so NOT on this list: every other lead, the determinism
question, and the six known-false rows.

## 7. Gates

Exit codes read one per line, never `cmd && echo OK`. See the report to
`team-lead` for the pasted values.
