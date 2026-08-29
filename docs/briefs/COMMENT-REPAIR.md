# COMMENT-REPAIR - a colon flowed into the prose of ~44 comments

**Read `docs/briefs/PREAMBLE.md` first.** Task tools, isolation, evidence standards, gates and
delivery rules are there and are not repeated here.

Your agent name is `comment-repair`. Your branch is `fix/comment-repair`. Your report goes to
`docs/worklogs/COMMENT-REPAIR-REPORT.md`, committed on your branch.

## What is wrong

`#:` is the Sphinx attribute-documentation prefix, used here for module-level constants. A reflow
stripped only the `#`, so the `:` fell into the body text. **It is not just a wrong prefix - the
colon has been flowed into the prose at whatever position the rewrap put it:**

```
# a proxy URL - which has neither - passed through whole : and reached
# the caller's problem `detail`. Measured before the fix: :
# `https://user:hunter2@proxy.internal:8080/path` came back unchanged. :
# : `://` before the `@` is what separates this from an email address,
# which must : not be touched: ...
```

**The tool is already fixed** (`59f0a8b`) and will not create more. This is repairing what exists.

## Measure first, and report the number before you change anything

```bash
grep -rn "^\s*# : " --include="*.py" src/ tests/ scripts/ docs/ | wc -l   # first lines only
grep -rnE "^\s*#.*( : | :$)" --include="*.py" src/ tests/ scripts/ docs/ | wc -l   # whole runs
```

**Run BOTH, and understand why they differ by about 4x.** The first sees only the FIRST line of a
damaged run: the continuation lines lost their marker too and read as ordinary comments with a colon
in the middle. Measured once: 55 by the first, 195 by the second.

**Do not carry a number out of this brief.** It said "44", which was measured at a different commit
than the one the agent started from - eleven more had landed in between. Get your own and put it in
the report.

## THE CONSTRAINT THAT MAKES THIS A CAREFUL TASK

**Some colons in those lines are real punctuation. Some are the escaped marker. No regex can tell
them apart.** `"Measured before the fix: :"` contains one of each.

So: **work file by file, reading each comment against what it said before it was reflowed.**
`git log -p --follow -- <path>` and `git show f0c3764~1:<path>` reach the earlier text. The damage
PREDATES the B49b sweep - 38 sites already existed at `f0c3764~1` - so do not assume one commit
introduced it, and do not assume the pre-sweep version is clean either.

**Where the original cannot be recovered, REWRITE the sentence so it reads correctly** rather than
leaving a mangled one. Say in the report which sites were reconstructed from history and which were
rewritten. Those are different claims and a reader needs to know which they are getting.

**Getting this wrong silently rewrites the explanations that carry the reason a thing exists**, which
is most of the value in this codebase's comments. A mangled comment is better than a confidently
wrong one.

## DO NOT run any reflow tool over these files

`docs/reviews/b49b/reflow-doc-lines.py` no longer CREATES this, but re-wrapping an already-corrupted
comment moves the stray colons to new positions and destroys the evidence of where they came from.
Repair first. If a repaired comment then breaks `W505`, hand-wrap it.

## Two more things while you are in there

- **Restore `#:` where it was the marker.** A run that begins `#:` continues `#:` on every line -
  that is the Sphinx convention, and it is what the fixed tool now emits.
- **`scripts/*.sh` and `ci.yml` are OFF LIMITS** - `harness-gates` is live in both. If you find
  damage there, report it and leave it.

## Gates

The full list is in `CONTRIBUTING.md`. This is a comment-only change, so **`git diff` must add and
remove zero non-comment lines**:

```bash
# added side
git diff <base>..HEAD -- src/ tests/ | grep '^+' | grep -v '^+++' \
  | sed 's/^+//;s/^[[:space:]]*//' | grep -vc '^#'
# removed side - the half the first version of this brief never checked
git diff <base>..HEAD -- src/ tests/ | grep '^-' | grep -v '^---' \
  | sed 's/^-//;s/^[[:space:]]*//' | grep -vc '^#'
```

**The first version of this brief got this wrong in two ways, and the agent quoted it back rather
than quietly passing.** It said `grep -c "^+[^#+]"`, which (1) demands the `#` in column 1, so every
INDENTED comment counts as code - it returned 22 on a diff whose 22 lines were all comments - and (2)
checked only the ADDED side, so it would pass a diff that DELETED a line of code while rewriting the
comment above it. Strip leading whitespace, and check both directions.

`docs/` is `extend-exclude`d from ruff, so W505 does not apply there; `src/` and `tests/` are linted.

## In the report

Your measured count before and after. Per file: how many sites, how many reconstructed from history,
how many rewritten. The zero-non-comment-lines check. **End with what you could not settle** - and
any comment whose original meaning you could not recover belongs there by name, not silently rewritten
and forgotten.
