# docs/archive - the retirement shelf

Records that nothing in the tracked tree names any more. Nothing here was
deleted and nothing here was edited: every file arrived by `git mv`, so
`git log --follow` reaches its whole history and its bytes are unchanged.

**Entry rule, and it is narrow.** A file moves here only when BOTH hold:

1. Its basename AND its full path appear in ZERO other tracked files -
   measured over the whole tracked corpus, not just `docs/`, and measured
   again without the `.md` suffix in case a reference drops it.
2. It is in no population a checker parses. That excludes `docs/briefs/`
   (parsed whole by `check-brief-report-references.py`), `docs/adr/`
   (parsed whole by `check-adr-numbers.py`), and any `docs/reviews/*.md`
   that `check-review-coverage.py` reads as a review round - declared or
   undeclared. Four review-round documents met rule 1 and were left in
   `docs/reviews/` for exactly this reason.

**Zero inbound links is not the same as retirable.** A record nothing
links to may still be the only account of something. Rule 2 is what keeps
that distinction from collapsing into "unlinked, therefore unwanted".

The retirement pass, its evidence, and every file it refused to move:
`docs/reviews/MEASURED-295-archive.md`.
