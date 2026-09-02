# BRIEF #210 #215 #216 #217: the ADR-citation ruling's EVIDENCE, four findings, one document

Read `docs/briefs/PREAMBLE.md` IN FULL first. It is the canon; this file is only the work.

**Worktree:** your own, off `d2159e7` (main). Branch `fix/210-adr-ruling-evidence`.
**Read the findings first:** `git show 1045edb:docs/reviews/REVIEW-R21.md` (branch `review/r21`).

You have FOUR tasks because they all land in `docs/adr/README.md` and its evidence document, and
two agents editing one file is how a merge puts damage back.

**THE RULING ITSELF IS NOT IN SCOPE.** ADR citations are AS AT acceptance and are NOT repointed
(`ec57a65`). That stands. Every finding below is about the EVIDENCE the ruling cites, and
`review-r21` was explicit that in neither case is the defect the ruling. Do not relitigate it.

## #210 (H2) - the "five ADRs carry the NEAR form" class does not hold

`docs/adr/README.md:54-64` counts five ADRs as carrying the near form "and it does not work". The
COUNT of five verifies. The CLASS does not:

- **ADR-0030 has ZERO `DESIGN.md:N` citations in the whole file**, so it cannot show anything
  drifting. It is counted as evidence of a failure it structurally cannot exhibit.
- **ADR-0025's only blob line is `:117`** - the exact line the SAME document holds up twelve lines
  later, at `:71-73`, as THE FORM THAT BINDS. It is its own counter-example.
- ADR-0024 and ADR-0031 also anchor inside the named blob.
- **Genuinely near-form: one.** ADR-0019 - which the README already calls "the proof".

The discriminator the section boasts about at `:62` ("naming a BLOB, not naming a commit") does
NOT separate NEAR from BINDING, which is the only distinction the section draws.

**The conclusion survives; the evidence is one case, not five.** Rewrite the prose IN PLACE so it
says that. Do not append a correction - this project rules that a reviewed document is REWRITTEN,
never annotated with a rider. And note where the error sat: in the paragraph bragging two
sentences earlier about catching a loose selector.

## #215 (L2) - "all 64 citations in this directory" was falsified by its own commit

It is 68 now, because the ruling's own commit added four. `64/19` is exact once README is
excluded. **Prefer deleting the number to correcting it** - ADR-0034 ruled that a stale count is
DELETED, not corrected, and this is the same claim shape. If you keep a figure, it carries the
command that produces it.

## #216 (L3) - the evidence document still prescribes what the ruling refuses

`docs/reviews/CITATION-READ-ADR-VERDICTS.md:56` still says a DRIFTED citation's "remedy is a
repoint", which `ec57a65` refuses. A ruling that leaves its own source document prescribing the
refused remedy is how the refused remedy comes back.

## #217 (N1) - the ADR index table stops at 0023

Twelve ADRs are missing, INCLUDING the two the new ruling cites by number. Rebuild the table by
DERIVING it from the files, and say in your report whether anything now regenerates it or whether
this will simply go stale again in twelve more ADRs - if nothing does, that is worth a task.

## Deliverable

One commit (or a small series), all gates green, exit codes read on their OWN LINE - no
`&& echo OK` anywhere. Then the `git merge --ff-only` command for me.

Run at minimum: `check-design-citations.py`, `check-brief-report-references.py`,
`check-review-coverage.py`, and the two shell control suites. `actionlint` is NOT installed here -
say so rather than claiming it.

## Where I think I am wrong

- I have NOT re-read ADR-0024 and ADR-0031 to decide whether they are "binding" in the strong
  sense. `review-r21` says 0030 settles #210 on its own regardless. Check that claim.
- I do not know whether `64/19` is still exact today; the set has grown. Derive it.
