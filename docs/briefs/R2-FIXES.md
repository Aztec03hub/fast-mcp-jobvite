# R2-FIXES - ten verified-open findings, and one that is U7's not yours

**Read `docs/briefs/PREAMBLE.md` first.** Tools, isolation, evidence standards, gates and delivery
rules are there and are not repeated here.

Your agent name is `r2-fixes`. Your branch is `fix/r2-leftovers`. Your report goes to
`docs/worklogs/R2-FIXES-REPORT.md`, committed on your branch.

## Read this before the findings

`docs/reviews/R2-LEFTOVER-VERDICTS.md` is merged on `main`. **It is the authority, not this brief.**
Every finding there carries a reproduction and a suggested fix as text, because its author was
read-only on `src/` and `tests/`. Read the verdict, reproduce it yourself, then fix it.

**`docs/reviews/REVIEW-CODE-R2.md` is the ORIGINAL report and it has been wrong twice** - H-4 and
M-6 both rested on a `grep` at one path reported as an absence everywhere. Prefer the verdicts
document, and where the two disagree, measure.

## The ten

- **M-1** `audit.py:348` raises `AuditWriteError` with no `from None`, from inside `emit()`'s
  `except` at `:336`. Reproduced: `args` False, `__context__` True, traceback True. One `from None`.
- **M-2** `config.py:453` calls `Settings()` outside any `try`; `__main__.py:421` catches only
  `ConfigurationError`. Reproduced in real processes - `PORT=99999`, `TRANSPORT=htp`,
  `MAX_RESULTS=0` all exit 1 with a traceback echoing `input_value=`.
- **M-3** `EXIT_CONFIGURATION_REFUSED = 78 -> 1` leaves the full suite green.
- **M-8** the *figure* is stale and the *mechanism* is not: `pyproject.toml:167-173` still sets no
  `parallel`/`sigterm`/`COVERAGE_PROCESS_START`, so the subprocess arms are unmeasured. **Take the
  comment, not the machinery, and NOT an `omit`.**
- **L-6** `test_shutdown.py:161-174` uses substring assertions where `:195` uses `ast.parse`.
- **nit-1** `config.py:261-262` still says "registers nothing".
- **nit-2** `config.py:236` is str-only, so `SecretStr("")` is a present empty credential.
- **nit-3** `redact_text` swallows the closing quote and comma. Two shapes reproduced.
- **nit-4** deleting `.lower()` from `audit.py:235` leaves the full suite green.

**M-4 is FIXED but carries a residual you should close**: R2's fix had two halves and only the test
landed - the `check-u1-boot-controls.sh` row was never added, so the behaviour is held by the suite
and not by the gate.

## The three traps, and two are the same trap

**1. M-3 and nit-4 are SURVIVING MUTATIONS at the full suite** - demonstrated, not inferred. Your fix
is not done when a test exists; it is done when **that mutation dies**. Re-run each one after fixing.

**nit-4's mechanism is the interesting part and it will bite a careless fix.** `test_audit.py:597`'s
literal is all digits and hyphens, so it is *invisible* to `.lower()`. **Any replacement test that
keeps an all-numeric literal reproduces the nit exactly.** Use a literal with a letter in it.

**M-3 has a sharp contrast in this same repo:** `test_shutdown.py:174` pins `EXIT_SOFTWARE = 70` with
a source substring. One of the two `sysexits.h` numbers this server shows a supervisor is anchored
and the other is not. **And L-6 is about rewriting that very assertion** - so when you rewrite it,
keep what it holds. Deleting it un-pins the one number that *is* pinned. Fix M-3 and L-6 together.

**2. M-1'S REPRODUCTION HAS A TRAP THAT ALREADY FOOLED ONE AGENT.** `loguru`'s handler defaults to
`catch=True` and swallows the sink exception before `emit()`'s `except` can see it. **A probe with a
default sink shows nothing, and you conclude the leak cannot happen.** The verdicts author's first
probe did exactly that and says so. Build the probe against a sink that does not swallow.

**3. M-6 IS WRONG AND YOU MUST NOT "FIX" IT.** It claimed `grep -rn "deadline" src/ docs/DESIGN.md`
finds nothing; at R2's own pinned SHA that grep returns five hits, one a bolded paragraph citing
`backend/resilience.md:74-76` by name and answering it. R2 asked for a deviation record that was
already in the frozen design, one section above the code it was reviewing.

**What genuinely remains from M-6 belongs to U7, not to you and not to U4.** `DESIGN.md:373-374`
promises a *total outbound budget* and nothing in `src/` implements one - `config.py`'s
`outbound_rate_limit` is a RATE limit, not a time budget. It is on the board for U7's brief. **Do not
implement it, do not re-file it against U4, and do not touch
`src/fast_mcp_jobvite/services/jobvite_client.py`** - see Isolation.

## Isolation - one file is off limits and it is not negotiable

**`src/fast_mcp_jobvite/services/jobvite_client.py` belongs to `u6-pagination`, which is live in it
right now.** That is why **L-4 is NOT in your list**: it is a real open finding in that file
(`:539-544` still raises `JobviteUpstreamError` producing `"Jobvite returned status none: ..."`,
reproduced end to end) and it waits for U6 to land. Leave it alone.

Everything else in `src/` and `tests/` is yours. `ci.yml` is mine - **report the numbers, do not edit
it.** If a fix needs a `ci.yml` change, say so and I will make it.

## Standing requirements

- **Every fix ships with the mutation or amputation that proves the test can fail.** Write the
  control, run it against the UNFIXED code, watch it survive, then fix, then watch it die. A control
  that has only ever passed cannot be told from one that cannot fail.
- **Restore with `cp` from a backup and verify with `cmp`.** `git diff --quiet` is blind to an
  untracked file and has lied here. **Never `git stash` and never `git checkout <path>`** - one agent
  chained those inside a command it read as read-only and staged a base revision over three committed
  files this morning. It recovered only because the stash existed.
- **`docs/DESIGN.md` is FROZEN at `c15b138`.** A defect there is a **Proposed** ADR, never an edit.
  Cite by subject from `git show c15b138:docs/DESIGN.md`.
- Run `python3 docs/reviews/check-design-citation-shape.py` before delivering. It exits **0** today.
  Do not be the one who takes it back to 1.
- **Run `ruff format` BEFORE your final harness run, not after.** It re-wrapped a signature and broke
  an amputation anchor *after* a green harness run this morning; only the static anchor checker saw it.
- The suite floor in `ci.yml` is `421` and the anchor floor is `171`. Your work should raise both -
  **measure them, report them, and leave the edit to me.**
- **No `Co-Authored-By:` or "Generated with" trailer. Ever.**

## How to deliver

Commit and push your branch. **Do NOT merge to main and do NOT push main.** `SendMessage` to
`"team-lead"` as your final action with: per finding what you measured before, what you changed, and
the mutation proving it; gate exit codes read from the terminal; the new floors; and **what you could
not settle**. If you judge a finding wrong, say so with evidence rather than fixing it to be safe -
one of these thirteen was already wrong and saying so was the right answer.
