#!/usr/bin/env python3
"""Task #143: consolidate `design-gates`, `supply-chain` and `links` into ONE job.

WHY A SCRIPT AND NOT A HAND EDIT: the sub-orchestrator protocol requires edits be
replayable - the one task that survived its sandbox being destroyed survived
because every edit was applied by a script. This one is idempotent-by-refusal: it
asserts the exact anchors it expects and exits non-zero rather than splicing into
a tree that has moved.

WHAT IT DOES, and the measured reason:
  GitHub bills each JOB rounded UP to a whole minute. Measured over
  2026-08-28..2026-09-02 with `filter=all` (578 runs, 1326 jobs), the three
  jobs merged here billed 634 minutes across 210 run-attempts while their
  MEASURED work - reconstructed from per-step timings - totals a median of 28s.
  One job billing one minute costs 214. Saving: 420 minutes, 66%.

Run from the repo root. Verify with `git diff` and actionlint.
"""
import sys
from pathlib import Path

F = Path(".github/workflows/ci.yml")


def die(msg: str) -> None:
    print(f"REFUSED: {msg}", file=sys.stderr)
    raise SystemExit(2)


def main() -> int:
    if not F.exists():
        die(f"{F} does not exist - run me from the repo root")
    lines = F.read_text().split("\n")
    if len(lines) != 1637:
        die(f"expected 1637 lines, found {len(lines)} - the file has moved; re-derive the ranges")

    def at(n: int) -> str:
        return lines[n - 1]

    # ANCHORS. Each is asserted because a sed matching nothing succeeds silently.
    anchors = {
        103: "  design-gates:",
        104: "    name: Design coupling gates",
        108: "    steps:",
        631: "          exit 0",
        1472: "  supply-chain:",
        1500: "      # LICENCE GATE - a DENY-list on the standard's flag-list, not an allow-list,",
        1557: "          extra_args: --only-verified",
        1582: "  # ---------------------------------------------------------------------------",
        1617: '  # are. Do not read a green here as "the citations are sound".',
        1618: "  links:",
        1626: "      - name: Relative links resolve",
        1636: "          fail: true",
    }
    for n, want in anchors.items():
        if at(n) != want:
            die(f"anchor line {n} is {at(n)!r}, expected {want!r}")

    def rng(a: int, b: int) -> list[str]:
        return lines[a - 1 : b]

    def reindent(block: list[str], frm: str = "  ", to: str = "      ") -> list[str]:
        out = []
        for ln in block:
            out.append(to + ln[len(frm) :] if ln.startswith(frm) else ln)
        return out

    header = [
        "  # ---------------------------------------------------------------------------",
        "  # THE STATIC GATES, THE SUPPLY CHAIN AND THE LINK CHECK, IN ONE JOB.",
        "  #",
        "  # These were three jobs until task #143. GitHub bills each JOB rounded UP to a",
        "  # whole minute, so three jobs whose work totals well under a minute billed",
        "  # THREE minutes on every run. MEASURED over 2026-08-28..2026-09-02 with",
        "  # `filter=all` (578 runs, 1326 jobs; `filter=latest` hides re-run attempts",
        "  # GitHub bills anyway, and it is the API default):",
        "  #",
        "  #     job                     n    billed   median   p90     max",
        "  #     Design coupling gates  220   220 min    11s     28s      34s",
        "  #     Supply chain           220   220 min    26s     31s      39s",
        "  #     Link check             210   214 min     6s      8s     126s",
        "  #     -----------------------------------------------------------",
        "  #     BEFORE, 210 run-attempts carrying all three:      634 min",
        "  #     AFTER,  one job (modelled from per-STEP timings): 214 min",
        "  #     SAVING:                                           420 min (66%)",
        "  #",
        "  # The merged job's duration is not a guess: it is the sum of the three jobs'",
        "  # WORK steps plus ONE prologue, taken from the per-step timestamps the jobs",
        "  # API returns. Median 28s, p90 42s, max 148s; 2 of 210 run-attempts would",
        "  # cross 60s and bill 2 minutes. That case is priced into the 214 above.",
        "  #",
        "  # WHY THESE THREE AND NOT THE OTHER TWO:",
        "  #   `test` is the long pole (median 87s, max 7522s) - merging anything into",
        "  #     it buys nothing and couples a 5-second gate to a 2-hour matrix.",
        "  #   `codeql` stays out. It bills 354 min, the SECOND largest line, but its",
        "  #     median is 64s - it is over the minute boundary on its own merits, not",
        "  #     from rounding a trivial job. Merging it would ADD its 64s to this job",
        "  #     and still bill 2 minutes, saving ~1 min/run at the cost of running the",
        "  #     design gates under CodeQL's instrumented environment. Not worth it.",
        "  #",
        "  # THE PROLOGUE IS SHARED, and that is the second saving. `design-gates` and",
        "  # `supply-chain` ran BYTE-IDENTICAL prologues - checkout at fetch-depth 0,",
        "  # setup-uv with the cache, setup-python, `uv sync --frozen`. One job runs it",
        "  # once. fetch-depth 0 is required by BOTH (the freeze gate resolves a SHA a",
        "  # shallow clone does not contain; TruffleHog needs full history to see a",
        "  # secret removed in a later commit), and the link check does not care, so the",
        "  # merged checkout is the strictest of the three rather than a compromise.",
        "  #",
        "  # PERMISSIONS ARE THE UNION, which is a WIDENING and is stated rather than",
        "  # buried: `security-events: write` came from `supply-chain` and now covers",
        "  # the design gates too. Whether TruffleHog and the SBOM steps actually need",
        "  # it here has NOT been measured - they upload no SARIF - so it is preserved",
        "  # unchanged rather than narrowed on a guess. Narrowing it is its own task.",
        "  # ---------------------------------------------------------------------------",
        "  static-gates:",
        "    name: Static gates, supply chain and links",
        "    runs-on: ubuntu-latest",
        "    # UNCAPPED WOULD MEAN SIX HOURS - observed max 148s for the merged work",
        "    # (modelled from per-step timings; the three jobs' own maxima were 34s, 39s",
        "    # and 126s). 6x headroom.",
        "    timeout-minutes: 15",
        "    permissions:",
        "      contents: read",
        "      security-events: write",
        "    steps:",
    ]

    supply = [
        "      # ---------------------------------------------------------------------",
        "      # SUPPLY CHAIN - was its own job until #143. NONE of the actions below",
        "      # have ever been executed; the pip-licenses step HAS been run locally.",
        "      # ---------------------------------------------------------------------",
        "",
    ] + rng(1500, 1557)

    links = (
        [
            "      # ---------------------------------------------------------------------",
            "      # LINK CHECK - was its own job until #143. It needs no uv and no deep",
            "      # history; it rides the checkout this job already has.",
            "      # ---------------------------------------------------------------------",
        ]
        + reindent(rng(1582, 1617))
        + ["", *rng(1626, 1636)]
    )

    out = (
        rng(1, 97)  # everything through `jobs:`; the old banner at 98-102 is replaced
        + header
        + rng(109, 631)  # the design gates, verbatim
        + [""]
        + supply
        + [""]
        + links
        + rng(632, 1467)  # blank, banner, the whole `test` job
        + rng(1559, 1581)  # the codeql banner and job, untouched
        + [""]
    )

    F.write_text("\n".join(out))
    print(f"rewrote {F}: 1637 -> {len(out)} lines")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
