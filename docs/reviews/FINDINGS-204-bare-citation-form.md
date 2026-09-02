# FINDINGS 204 — the bare `:NNN` citation form

Agent `suborch-204`, task #204. Brief:
`docs/briefs/BRIEF-204-bare-citation-form.md`. Worktree
`fmj-worktrees/w204`, branch `fix/204-bare-citation-form`, cut from
**LOCAL `main` at `c552027`** — `origin/main` is **45 commits behind**
(`git rev-list --count origin/main..main`), derived, not taken from the
brief.

Design targets read from
`git show "$(cat docs/DESIGN-FREEZE.txt)":docs/DESIGN.md`, which resolves
to **`d1f1a52`**, 2134 lines. The SHA was derived, never retyped.

**This round declares no `REVIEW-COVERS` range, deliberately.** It is not
a code review of a commit span: it builds a selector and reads a corpus
at one SHA. Its two predecessors (`CITATION-READ-ADR-VERDICTS.md` and
`CITATION-READ-SRC-VERDICTS.md`) declare none either, and that is the
precedent.

---

## The headline, in one paragraph

**The discriminator exists, it is defensible, and it has 16/16 controls
firing in both directions.** The population is **2968 bare-form citation
sites in 164 files** — not 58 in 16 files, which was the register's
figure for `docs/adr/` alone. **No bare citation in this tree is
unresolvable**: UNANCHORED measures **0** once the anchor is a FILENAME
rather than another citation. And the round found **a third defect class**
— a citation whose two spellings were separated by a repoint, so one
document now contradicts itself — with **one instance confirmed by
reading a diff** and a candidate list whose weakness is stated below.

---

## 1. The discriminator — `docs/reviews/probe-204-bare-citations.py`

### The rule

A bare-form citation is `:N` or `:N-M` whose colon is **not preceded by a
filename character** `[A-Za-z0-9_./\-]`, minus six NAMED non-citation
shapes.

**The left boundary does almost all the work, and it is not a
blocklist.** `DESIGN.md:515` has `d` before the colon; `localhost:8080`
has `t`; `10:30` has `0`. **Ports and clock times are excluded BY
CONSTRUCTION**, which matters because a blocklist selects for the shape
nobody thought of — this project has measured that seven times.

### The three arms, measured

| Arm | Sites | Files | What it is |
|---|---|---|---|
| **A — CODE-SPAN** | **2835** | 140 | the whole content of a markdown code span, `` `:489-490` `` |
| **B — CONTINUATION** | **31** | 20 | a bare token after a qualified one on the same line, `DESIGN.md:354-370, :373-375` |
| **C — PROSE-BARE** | **102** | 35 | everything else |
| **total** | **2968** | **164** | |

**THAT FIGURE IS MEASURED AT `c552027`, BEFORE THIS ROUND'S OWN FILES
EXISTED, AND SAYING SO IS NOT PEDANTRY.** With the two probes and this
report in the tree the same command returns **2985 in 165 files** - my
own writing about the form added 17 sites to its population, in the same
way an exemption marker inflated 47 -> 61 from its own documentation.
**Any later round must re-derive rather than quote this number**, and
must not read the growth as the corpus growing.

**Arm A is a signal the language already carries.** The author typed
backticks to say "this is a token, not prose". It is the only arm with a
hard boundary on BOTH sides, and it is 95% of the corpus. That is the
answer to the brief's worry that the discriminator would have to be
invented: it did not have to be.

### Precision, measured by reading

**75 Arm-A sites read, 0 false positives.** 45 chosen at random (seed 7)
and — because a random sample is where a rare shape hides — **30 chosen
adversarially**, every site whose number is a port or an HTTP status
(`:80` ×17, `:200`, `:404`, `:443` ×2, `:401`, `:413`, `:422`, `:500`
×3, `:503`). Every one is a citation. `docs/adr/0019-...:64` writes
*"(`:443`, `:501`, `:631`), and those are **correct**"* — a citation, not
a port.

### The exclusions, each named and counted

| Shape | n | Example |
|---|---|---|
| JSON | 58 | `{"status":{"code":401}}` |
| SLICE | 55 | `reasons[:1]`, `untouched[:15]` |
| DOUBLE-COLON | 15 | `[::1]`, `::error::4/5` |
| FORMAT-SPEC | 10 | `f"{len(rows):4}"` |
| LOG-LINE | 4 | `\| INFO \| __main__:<module>:2` |
| GREP-PATTERN | 1 | `grep -rn ':1276-1278' docs/adr/` |
| **total** | **143** | |

`--excluded` prints all 143. **A shape excluded without being counted is
how a population shrinks with nobody noticing** — which is precisely what
`check-design-citations.py` learned at R13-H1, where a skip counter was
incremented and read nowhere.

### 16/16 controls, in BOTH directions

Five ADMIT cases (including the ADR-0017 instance, the continuation form,
an unticked prose form, and a brace-wrapped `` `{:86}` `` that must NOT
read as a format spec) and eleven REFUSE cases (slice ×2, JSON,
double-colon ×2, format spec, log line, grep pattern, a QUALIFIED
citation, a port, a clock time).

**`controls()` and `scan()` call one shared `excluded_shape()`.** An
earlier draft had the ladder written out twice, which is a control
testing a COPY of its subject — it would have gone on passing after the
scan's copy changed.

### TWO OF MY OWN RULES WERE MEASURED WRONG, and both are recorded in the file

**1. `GREP-PATTERN` was `"grep" in line[:start]` and excluded 21 sites,
20 of them real citations.** Lines like *"`grep -n` puts that word at the
end of `:172`"* name the tool and then make a citation. Tightened to
require the token be inside the quoted argument: **21 → 1**. This is the
loose-edge failure the brief warned about, committed by me, inside the
file built to avoid it.

**2. The ANCHOR was a CITATION when it should have been a FILENAME — the
same defect this whole task is about.** My first anchor asked "is there
another `file.ext:N` nearby", which is the identical filename-plus-colon
shape the three existing selectors are built on. It reported **19
UNANCHORED** sites. Reading two by hand killed the rule:

- `docs/briefs/BRIEF-187-floor-container.md:88` cites `:201-202` two
  lines under *"`check-row-floor-exactness.py` enumerates `scripts/*.sh`
  …"* — the file is named, with no line number.
- `docs/worklogs/PLAN-DRAFT7-SELF-AUDIT.md:20` cites `:5` in a table
  whose header at `:3` reads *"**Subject:**
  `docs/plans/IMPLEMENTATION-PLAN.md`"*.

A reader resolves from the last FILE NAMED, however it was named.
**UNANCHORED 19 → 0.**

---

## 2. The population by KIND, and the anchor ladder

The brief asked which sites have no nearby sentence naming a file. The
answer needed a ladder, because **choosing one window would have been the
ruling**, not the measurement. A first draft asked a single question
("named within 8 lines, stopping at a blank line?") and answered
UNANCHORED for 58% — an artefact of the window.

| Rung — the TIGHTEST scope naming a file | n |
|---|---|
| SAME-LINE | 744 |
| PARAGRAPH | 680 |
| PARAGRAPH-AMBIGUOUS | 435 |
| SECTION | 344 |
| SECTION-AMBIGUOUS | 484 |
| FILE | 2 |
| FILE-AMBIGUOUS | 279 |
| **UNANCHORED** | **0** |

**1770 of 2968 (59%) resolve to exactly ONE file** at their tightest
scope. The remaining 1198 resolve to a scope that names two or more
files, so a reader must pick. **281 (the FILE rungs) have no filename in
the enclosing section at all** and are the practically hard ones.

**The most-inherited documents:** `DESIGN.md` 95, `tool-calling.md` 32,
`ci.yml` 28, `STANDARDS.md` 25, `agent-guardrails.md` 24 — 214 distinct
files in all.

### THE ANCHOR IS RELIABLE AS A CENSUS AND UNRELIABLE PER SITE

I read the 66 `docs/adr/` sites against the anchor's verdict and it is
wrong on at least three:

- `0009-...:22` — `- **`:79`, record who approved…** ` — anchor says
  `DESIGN.md`; its two siblings at `:14` and `:18` make it
  `ai/agent-guardrails.md`.
- `0014-...:21-26` — `:48 JOBVITE_MCP_TRANSPORT=stdio` and five more —
  anchor says `DESIGN.md`; they are line numbers of a quoted
  `.env.example` listing.
- `0019-...:64` — `(`:443`, `:501`, `:631`)` — the ADR's own next clause
  says *"that document has its own"*, meaning `COMPLIANCE-SPEC.md`.

**So "the file a bare form inherits" cannot be derived mechanically with
per-site confidence.** It needs reading. Use the ladder for the shape of
the corpus; do not repoint anything off it.

---

## 3. `docs/adr/` re-measured — the brief's two numbers

| Claim (register / #196) | Re-measured at `c552027` |
|---|---|
| "58 bare `:NNN` citations in `docs/adr/`, across 16 files" | **66 sites in 17 files** |
| "7 ADRs carry a bare form and NO `DESIGN.md:N` form: 0002, 0008, 0009, 0011, 0015, 0023, 0030" | **HOLDS — exactly those seven** |

The 66-vs-58 gap is not a contradiction I can resolve: the 58 was
measured with a selector `CITATION-READ-ADR-VERDICTS.md` does not state,
so the two numbers are not joined to a shared definition. **Mine is
stated and runnable, which is the difference worth having.**

**A LARGE SHARE OF `docs/adr/`'s BARE FORMS DO NOT TARGET `DESIGN.md` AT
ALL**, and this is the corpus fact that matters most for what to do next.
They cite the external standards — `backend/rate-limiting.md`,
`ai/agent-guardrails.md`, `standards/devops/bash.md`,
`devops/quality-gates.md`, `architecture/gdpr-data-rights.md`. **Those
documents are not in this repository** (task #106: the standards corpus
is unwired until `STANDARDS_TOKEN` exists). **No round can verify them
here, by any selector.** Any plan to "read the bare forms" must say so up
front or it will produce an unsettleable list.

---

## 4. THE NEW CLASS: `ORPHANED-BY-REPOINT`

**One citation, two spellings, only one of them repointed.**

`docs/adr/0017-unmapped-errors-are-internal-error-not-about-blank.md`
names one range twice. At its introduction, `02245b1`:

    :15  **The contradiction (D1).** `DESIGN.md:489-490` states that every
         failure returns a complete RFC 9457 problem object …
    :66  - **`DESIGN.md:515` is amended**, and `:489-490`'s seven-member
         requirement then holds without exception …

Commit `b0e86b8` — *"Repoint 713 DESIGN.md citations, from the checker's
own parsed output"* — changed the first:

    -**The contradiction (D1).** `DESIGN.md:489-490` states that every failure returns a complete RFC
    +**The contradiction (D1).** `DESIGN.md:495-496` states that every failure returns a complete RFC

and left the second. **Today the file says `:495-496` at line 16 and
`:489-490` at line 67, about the same sentence.**

### Why it is a third class and not a subspecies

- **DRIFTED** — right when written, the target moved, never repointed.
  Remedy: a repoint.
- **WRONG** — never named its subject. Remedy: a repoint *and* an
  explanation of how the author read the wrong paragraph.
- **ORPHANED-BY-REPOINT** — right when written, the target moved, **the
  repoint RAN and fixed half the instance.** The document now contradicts
  itself, and the surviving half is invisible to the very tool that would
  fix it, because that tool is driven by the checker's parsed output and
  the checker requires the filename.

**The remedy is different from both**: repointing the orphan is not
enough, because the sweep will orphan the next one. The sweep has to see
the bare form.

### The candidate list, and its weakness — say this out loud

`docs/reviews/probe-204-orphaned-by-repoint.py` replays every commit that
changed a qualified citation and reports **55 candidates** (51 making a
citation, 4 discussing the change). **DO NOT PUBLISH THAT NUMBER AS A
FINDING.** The pairing is at FILE level, not LINE level: it asks whether
the range was repointed *anywhere* in the file and whether a bare form of
the old value stands *anywhere* in the file, and those two anywheres need
not be one citation.

Measured: it reported six sites in `src/` and `tests/`, e.g.

    src/fast_mcp_jobvite/services/jobvite_client.py:607
    # U7 - RESILIENCE (DESIGN.md:354-370, :373-375, :617).

`git log -S` on that exact comment returns **one** commit — its own
introduction at `8328d60`. **The line has never been repointed in either
half**, so its spellings do not disagree and it is not an orphan.
`src/fast_mcp_jobvite/config.py:389` falls the same way (`c5de669`,
one commit). **All six `src/`+`tests/` rows are false positives**, and the
`-> :NNN` destination the probe prints is not evidence either.

**The second `docs/adr/` candidate is also not an orphan, on reading.**
`0028-...:61` writes *"Amend `DESIGN.md:1276-1280`'s §8 arm … **`:1276-1278`
is what this ADR said**"* — a deliberate contrast between what it cited
and what the range is now.

**Confirmed: one, by reading a diff.** `docs/adr/0017-...:67`.

Two more things a reader should know before treating the rest as work:

- **`docs/plans/IMPLEMENTATION-PLAN.md` supplies 8 of the 55, and #111
  ruled it a RECORD that is not repointed.** Those are decisions, not
  defects. Another 30 are in `docs/reviews/`, which are records of rounds.
- **The class is not wholly new.** `542fbaf` is titled *"R14-M1: a bare
  continuation citation that was wrong at BOTH freezes"*, and
  `CITATION-READ-SRC-VERDICTS.md:593` names *"the bare `:N-N`
  continuation form"* explicitly. **One instance was fixed and no sweep
  followed.** My round is the first to give the shape a selector.

---

## 5. The brief's two questions, answered but not ruled

### "Is an UNANCHORED bare citation a defect in itself?"

**The question dissolves on measurement: there are none.** UNANCHORED is
**0 of 2968**. Every bare citation in this tree sits in a file that names
its document somewhere.

**The live question is AMBIGUITY, not absence.** 1198 sites (40%) resolve
only to a scope naming two or more files, and 281 have no filename in the
enclosing section at all. **My recommendation, and it is Tier 0's call:
do NOT make this a defect class.** A rule would fire on 40% of the corpus,
almost all of it prose a human reads without difficulty, and this project
has already measured what happens to a gate that is red by construction —
it gets switched off.

### "Should this form enter the wrong-subject register at all?"

**No, on the register's own rule, and it is not close.** The register
records *"a citation that RESOLVES and names the wrong subject"*. Being
bare is a matter of SPELLING, not of subject. A bare citation is wrong or
right for exactly the reasons a qualified one is.

**But `ORPHANED-BY-REPOINT` deserves its own record**, and not in the
register either — its rows are wrong-subject instances, and an orphan's
defect is that **one document contradicts itself**, which the `Cited` /
`Should be` columns cannot express. A register that folded it in would
lose the fact that the OTHER half of the same citation is already correct.

**What I would ask Tier 0 to rule** (and I have deliberately created no
task for it, per §D):

1. Repoint `docs/adr/0017-...:67` `:489-490` → `:495-496`? **#203 has
   since ruled that ADR citations are AS AT acceptance and are NOT
   repointed** — which, applied here, says leave it. **I think #203 does
   not reach this case and Tier 0 should say so either way**: #203
   protects a citation that was right at acceptance and drifted. Here the
   ADR's OTHER half was already moved off its acceptance value, so
   "as at acceptance" is no longer true of the document as a whole. The
   file is internally inconsistent whichever value you prefer.
2. Should the repoint TOOL learn the bare form? That is the only fix that
   stops the class recurring, and it is the one this round did not build.

---

## 6. Suggested fixes, one per finding

| # | Finding | Suggested fix |
|---|---|---|
| F1 | `docs/adr/0017-...:67`'s `:489-490` contradicts `:16`'s `:495-496` | Ruling first (above). If repointed: `:489-490` → `:495-496`, anchor phrase *"`type`, `title`, `status`, `detail`, `instance`, `request_id`, `timestamp`"*. |
| F2 | The repoint sweep cannot see the bare form, so it orphans one every time it runs | Feed `probe-204-bare-citations.py`'s Arm A + Arm B output into the repoint tool alongside the checker's parsed output, resolving each site's document by its anchor and **refusing** any site whose anchor is AMBIGUOUS rather than guessing. |
| F3 | `WRONG-SUBJECT-REGISTER.md`'s exclusion section says "58 bare citations across 16 files" | Replace the two digits with a pointer to `probe-204-bare-citations.py`, exactly as that file's own arithmetic section points at a `grep -c` instead of writing a number. The register's own rule — *"never restate the count in prose"* — already forbids what it does here. |
| F4 | The register's exclusion section implies the bare form is a wrong-subject candidate | Say instead that spelling is orthogonal to subject, and that `ORPHANED-BY-REPOINT` is a separate class needing its own record. |
| F5 | A large share of `docs/adr/`'s bare forms target the unwired standards corpus | Any future "read the bare forms" brief must scope itself to documents present in this tree, and say that the rest is blocked on #106 — otherwise it produces an unsettleable list and the round looks like it failed. |
| F6 | `probe-204-orphaned-by-repoint.py` pairs at FILE level | Tighten to line-level by replaying each file's blame-free history per line, or leave it as a lead generator with the caveat it now carries. I chose the caveat, because a half-tight pairing that LOOKS tight is worse than a loose one that says so. |

---

## 7. Gates — each exit code read on its own line

    uv run --frozen ruff format --check docs/reviews/probe-204-bare-citations.py      -> 0
    uv run --frozen ruff check        docs/reviews/probe-204-bare-citations.py        -> 0
    uv run --frozen mypy              docs/reviews/probe-204-bare-citations.py        -> 0
    python3 docs/reviews/probe-204-bare-citations.py --controls                       -> 0   (16/16 fired)
    python3 docs/reviews/probe-204-bare-citations.py                                  -> 0
    uv run --frozen ruff format --check docs/reviews/probe-204-orphaned-by-repoint.py -> 0
    uv run --frozen ruff check        docs/reviews/probe-204-orphaned-by-repoint.py   -> 0
    uv run --frozen mypy              docs/reviews/probe-204-orphaned-by-repoint.py   -> 0

The four checkers named in the brief's §E are recorded in the commit that
carries this report, each read on its own line.

**`actionlint` is NOT installed in this environment**, so no workflow
linting was run. I did not run the full `pytest` suite: nothing this
round adds is imported by it, and both new files are standalone probes.

---

## 8. What I did NOT verify

These are things I could not settle, not things I did not try.

- **I did not read all 2968 sites for CORRECT / WRONG / DRIFTED.** I read
  75 for the discriminator's precision and the 66 `docs/adr/` sites for
  their anchors, and I checked ~20 `DESIGN.md`-targeting ADR sites
  against the frozen object. **A full read is #196's job again at ~46x
  the volume, and it should not start until F5's scoping is settled.**
- **I could not verify any bare citation into the standards corpus** —
  those documents are not in this tree. That is a hard blocker, not a
  skipped step.
- **The 55-candidate orphan list is unread except for the 8 I name.** Six
  I refuted, one I confirmed, one (`0028`) I refuted by reading.
- **I did not tighten the orphan detector to line level.** It is a lead
  generator that says so.
- **I did not measure whether the repoint tool COULD consume the bare
  form** — F2 is a proposal I did not build or test.
- **I did not re-run `check-design-citations.py --since`**, only its
  default mode. The `--since` mode compares against the freeze and would
  report movement, which is a different question from the one this round
  asks.

## 9. Where my brief was wrong

- **"58 bare `:NNN` citations in `docs/adr/`, across 16 files"** — 66 in
  17 by a stated selector.
- **"THE BARE `:NNN` CITATION FORM IS UNREAD ACROSS EVERY CORPUS"** —
  R14-M1 (`542fbaf`) read and fixed one instance, and
  `CITATION-READ-SRC-VERDICTS.md:593` names the continuation shape. The
  form had never been SWEPT; it had been seen.
- **"which sites have NO nearby sentence naming a file, because those are
  unresolvable by any reader"** — there are none. The right question was
  ambiguity.
- **The brief framed this as a `docs/adr/` problem.** It is a repo-wide
  one: `docs/adr/` holds 66 of 2968 sites, 2%.

**The brief's seven-ADR list was exactly right**, and its instruction to
build the discriminator first was what made everything above possible.
