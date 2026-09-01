# BRIEF #134 — estimate the wrong-paragraph citation RATE

## §A — Read the canon FIRST

**Read `docs/briefs/PREAMBLE.md` in full first, and follow it.** Read the
design at the freeze, never from the working tree:

    git show "$(cat docs/DESIGN-FREEZE.txt)":docs/DESIGN.md

Then read `docs/reviews/WORKLOG-126-blank-end-sweep.md` — especially its
findings F1 and F2, and its closing "what I did not settle".

## §B — The argument, which is a selection-bias argument

Two checkers gate design citations today:

- `check-design-citations.py` — the cited line **exists**.
- `check-design-citation-shape.py` — the range cannot be its subject
  (starts/ends blank, inverted, absurd).

**Neither can see a citation that lands on real prose in the WRONG
PARAGRAPH.** Those resolve, pass both gates, and stay wrong forever. Five
were found by reading (#114). Two more (#132, #133, now fixed) fell out of
#126's sweep.

**The two from #126 are the reason this task exists.** #126's population
was the 47 citations whose range ends on a blank line. Ending blank and
citing the wrong paragraph are **independent properties**. F2 was visible
only because its range happened to have both. So #126 was, accidentally, a
47-item random-ish sample of the full population — and it turned up two.

Two in 47 is ~4%. Over ~880 citations that would be ~35 wrong ones. It
might also be luck. **Nobody knows, and the whole point of this task is to
replace "some are wrong" with a NUMBER**, because a rate is a decision
input and an anecdote is not.

## §C — What to do

1. **Enumerate the container.** Every `DESIGN.md:<range>` citation in
   tracked files, from git — not a path glob. `check-design-citations.py`
   already does this enumeration; reuse its selector rather than writing a
   second one that disagrees with it.

2. **Draw a RANDOM sample of 40.** Seed the RNG from a constant you
   record in the report, so the exact sample can be redrawn and checked.

   **The sample must NOT be drawn on any property an existing checker
   tests** — not blank-ended, not near a section boundary, not "looks
   suspicious". That reintroduces exactly the bias that hid this class.
   Random over the whole container.

3. **For each of the 40, read the claim and read the range.** Verdict:
   - `CORRECT` — the range contains the claim.
   - `WRONG-PARAGRAPH` — resolves, but the claim is elsewhere. Record
     where the claim actually is.
   - `UNJUDGEABLE` — you cannot tell what the site is claiming. Say so;
     do not guess, and do not silently score it correct.

   **`UNJUDGEABLE` is a real verdict and its count matters.** A citation
   whose claim nobody can reconstruct is its own finding.

4. **Report the rate** with its numerator and denominator, and the
   `UNJUDGEABLE` count separately. Do not extrapolate to a total with more
   precision than 40 samples support — give a range, and say plainly that
   40 is a small sample.

## §D — What NOT to do

- **Do not fix anything.** This task measures. A repoint made mid-sample
  changes the population under you, and #126 already showed that a
  mechanical repoint can manufacture a wrong citation (a clean `end - 1`
  would have produced `DESIGN.md:906`, an unrelated sentence, permanently
  green). File what you find; the sweep is a separate decision that
  depends on your number.
- **Do not widen the sample to chase findings.** If you find three wrong
  in the first ten, that is the result — finish the 40 and report the
  rate. Stopping early on a hot streak, or continuing until you find
  something, both destroy the estimate.

## §E — Constraints

- Branch `review/citation-rate` off current `main`.
- **Do not merge and do not push.** I merge and push, always.
- No `Co-Authored-By` or "Generated with" trailer.
- Do not `git stash` — other agents are live on this tree.
- `git commit -F` with a **quoted** heredoc (`<<'MSG'`).
- Cite `file:line` only from `grep -n` or a numbered Read. Never count
  offsets inside a `sed -n X,Yp` window — that has produced wrong
  citations here, which would be a bleak way to fail this particular task.
- Report to `docs/reviews/REPORT-134-citation-rate.md`.

## §F — Report back

`SendMessage` to `team-lead`: the seed, the rate with numerator and
denominator, the `UNJUDGEABLE` count, every WRONG-PARAGRAPH site with
where its claim actually lives, and your own assessment of whether the
number justifies a full sweep. If you think the sampling design is wrong,
say so before spending 40 reads on it — I would rather rebuild the design
than get a confidently wrong number.
