# Licensing survey: what the `evolvconsulting` GitHub org actually does

Date: 2026-08-27. Surveyed by the `licensing-survey` agent against the live GitHub API,
authenticated as `Aztec03hub`. Every claim below has its command in Appendix A.

## Summary

**There is no house licensing convention. 174 of 187 repos in the org have no LICENSE file at
all** (93%). Of the 13 that do, the licences are MIT (4), Apache-2.0 (3), GPL-3.0 (2),
AGPL-3.0 (1), and custom proprietary/all-rights-reserved text (3). Two of the three Apache-2.0
files are unedited boilerplate with `Copyright [yyyy] [name of copyright owner]` never filled
in, and the third carries a *third-party* author's name. So the real evidence base is far
smaller than 13.

**The copyright string is inconsistent across the four repos where evolv actually wrote one.**
It appears as `evolv Consulting` (2), `Evolv Consulting` (1), `Evolv` (1), `evolv Consulting,
Inc.` (1), and `Tristan` (1, a personal first name in an org repo). Lowercase-e `evolv
Consulting` is the most recent and most common form, and it matches the `package.json` author
string `evolv consulting <info@evolvconsulting.com>` in the org's most carefully licensed
public app. The `evolv-brand` skill also treats lowercase `evolv` as the brand form.

**Public repos give almost no precedent.** 19 repos are public; 14 of them have no LICENSE file
whatsoever, including all the hands-on-lab and demo repos. The three public repos with a real,
deliberate licence are `claude-conduit-app` (AGPL-3.0, and its README states the AGPL was
*forced* by bundling pm2, not chosen), `evolv-coder-lite` (MIT plus a NOTICE for vendored
upstream work), and `snowddl` (Apache-2.0 carrying `Copyright 2026 Vitaly Markov`, the upstream
SnowDDL author, so it is a third-party codebase, not evolv's own licensing decision).

**Recommendation: keep a permissive licence, but switch MIT to Apache-2.0, and normalise the
copyright line to `evolv Consulting`.** Reasoning in full below. If Phil prefers minimum
friction over the patent grant, MIT with the copyright line corrected to `evolv Consulting` is
defensible and is what the org's one comparable public library already does. What is *not*
defensible on this evidence is any claim that "MIT is what evolv does" - the org has no such
convention.

## Every repo in the org that carries a LICENSE file

174 of 187 repos returned HTTP 404 from `GET /repos/evolvconsulting/{name}/license`, which
means no licence file GitHub can see. Those are listed in Appendix B by count only. The 13 that
do carry one:

| Repo | Visibility | Archived | Language | SPDX (GitHub) | Verbatim copyright line |
|---|---|---|---|---|---|
| `fast-mcp-jobvite` | public | no | - | MIT | `Copyright (c) 2026 evolv Consulting` (this repo, provisional) |
| `snowddl` | public | no | Python | Apache-2.0 | `Copyright 2026 Vitaly Markov` |
| `claude-conduit-app` | public | no | JavaScript | AGPL-3.0 | none of evolv's own; GPL text only bears `Copyright (C) 2007 Free Software Foundation, Inc.`. `package.json` says `"author": "evolv consulting <info@evolvconsulting.com>"` |
| `evolv-coder-lite` | public | no | JavaScript | NOASSERTION (MIT + preamble) | `Copyright (c) 2026 evolv Consulting` |
| `dbt_sample_snowflake` | public | no | Python | Apache-2.0 | `Copyright [yyyy] [name of copyright owner]` (unedited boilerplate) |
| `evolv-ui` | private | no | TypeScript | NOASSERTION (proprietary) | `Copyright (c) 2026 evolv Consulting` |
| `evolv-coder-kit` | private | no | JavaScript | NOASSERTION (proprietary) | `Copyright (c) 2026 evolv Consulting, Inc. All rights reserved.` |
| `evolv-pptx` | private | no | Python | MIT | `Copyright (c) 2026 Tristan` |
| `cc-sf` | private | no | TypeScript | MIT | `Copyright (c) 2026 Evolv Consulting` |
| `ai-coding-rules` | private | no | Python | Apache-2.0 | `Copyright [yyyy] [name of copyright owner]` (unedited boilerplate) |
| `claude-code-kit` | private | **yes** | JavaScript | MIT | `Copyright (c) 2026 Evolv` |
| `azplot` | private | **yes** | Python | GPL-3.0 | none of evolv's own; `Copyright (C) 2007 Free Software Foundation, Inc.` |
| `sasr` | private | **yes** | Python | GPL-3.0 | none of evolv's own; `Copyright (C) 2007 Free Software Foundation, Inc.` |

All 19 public repos, with or without a licence:

| Repo | Archived | Language | Last updated | Licence |
|---|---|---|---|---|
| `fast-mcp-jobvite` | no | - | 2026-08-27 | MIT |
| `snowddl` | no | Python | 2026-08-21 | Apache-2.0 (upstream author) |
| `coco_semantic_modeling_hol` | no | HTML | 2026-08-20 | **none** |
| `claude-conduit-app` | no | JavaScript | 2026-08-18 | AGPL-3.0 |
| `evolvconsulting.github.io` | no | HTML | 2026-08-13 | **none** |
| `eck-e2e-weather-app` | no | - | 2026-08-05 | **none** |
| `eck-e2e-weather-platform` | no | - | 2026-08-05 | **none** |
| `evolv-hackathon-left-field-plugin` | no | Python | 2026-07-27 | **none** |
| `coco_sdlc_hol` | no | TypeScript | 2026-06-23 | **none** |
| `evolv-coder-lite` | no | JavaScript | 2026-06-18 | MIT (+ NOTICE) |
| `evolv-weather-demo` | no | JavaScript | 2026-06-09 | **none** |
| `americold` | no | - | 2026-06-08 | **none** |
| `cortex-pptx-tool` | no | JavaScript | 2026-05-23 | **none** |
| `e2e-snowflake-ai-hol` | no | Jupyter Notebook | 2026-04-05 | **none** |
| `snowflake-cards` | **yes** | Astro | 2026-04-03 | **none** |
| `coco-hol` | no | Python | 2026-03-06 | **none** |
| `dbt_sample_snowflake` | no | Python | 2025-02-21 | Apache-2.0 (boilerplate) |
| `race-to-the-finish-line` | no | Python | 2024-03-05 | **none** |
| `emojis-tell-your-story` | no | Python | 2024-02-22 | **none** |

## Answers to the five questions

**1. Is there a house convention?** No. 174/187 repos carry nothing. Among the 13 that do, five
distinct licence families appear. Even within MIT, the copyright holder is written four
different ways. The org's own standards corpus contains zero guidance on open-source licensing
(established by a prior sweep, not re-verified here). The honest reading is that licensing has
been decided ad hoc, per repo, by whoever created it.

**2. What do the public repos do?** 14 of 19 public repos have no licence at all, which under
default copyright law means all rights reserved and nobody may legally reuse them. That is
almost certainly unintentional for the hands-on-lab and demo repos, but it is the fact. Of the
five with a licence, one is upstream third-party code (`snowddl`), one is boilerplate nobody
filled in (`dbt_sample_snowflake`), one had its licence dictated by a dependency
(`claude-conduit-app`, AGPL because of bundled pm2), and one is `fast-mcp-jobvite` itself. That
leaves exactly **one** genuine precedent for an evolv-authored public library: `evolv-coder-lite`,
MIT, `Copyright (c) 2026 evolv Consulting`, with a NOTICE file for vendored upstream work.
One data point is a weak precedent, but it is the closest analogue we have and it points MIT.

**3. How is the copyright holder written?** Inconsistently. Verbatim strings found:
- `evolv Consulting` - `evolv-ui`, `evolv-coder-lite` (and the provisional `fast-mcp-jobvite`)
- `evolv Consulting, Inc.` - `evolv-coder-kit`, which also identifies evolv as "a Texas corporation"
- `Evolv Consulting` - `cc-sf`
- `Evolv` - `claude-code-kit` (archived)
- `Tristan` - `evolv-pptx` (a personal first name, no surname, in an org repo)
- `evolv consulting <info@evolvconsulting.com>` - `claude-conduit-app` `package.json` author field

Lowercase-e `evolv Consulting` is the majority form among the current, non-archived repos and
matches the brand's own lowercase treatment. If the goal is a defensible legal entity name, the
`evolv-coder-kit` form `evolv Consulting, Inc.` is the most precise, since it names the actual
corporation. My read: the provisional `Copyright (c) 2026 evolv Consulting` is fine and does not
need changing, unless Phil wants the `, Inc.` for legal precision.

**4. Any client work or client-derived repos?** Many, and none of them carry a licence, so none
of them are precedent. The org is full of client-named repos (Toyota, PayPal, SoFi, Velera,
LegalZoom, Ochsner, Aristocrat, Osaic, Vertiv, Sallie Mae, Cetera, VisiQuate, Nable, Autodesk,
Americold and others). Every one of these is private except `americold`, and every one returned
404 for a licence file. Two repos are third-party-derived and must be excluded from any
precedent reading: `snowddl` carries the upstream SnowDDL author's copyright
(`Copyright 2026 Vitaly Markov`), and `evolv-coder-lite`'s LICENSE explicitly states portions
derive from "GSD Redux" with upstream copyrights preserved in a NOTICE.

**5. Recommendation for `fast-mcp-jobvite`.**

Keep it permissive. The repo is a public integration connector for a third-party SaaS, meant to
be adopted and possibly published to PyPI, with no client data and no evolv proprietary logic.
Proprietary/all-rights-reserved would defeat its stated purpose, and copyleft is ruled out by
the repo's own CI licence gate, which allow-lists MIT, Apache-2.0, BSD-2-Clause, BSD-3-Clause
and ISC. Choosing GPL or AGPL for our own code while banning it in our dependencies would be
incoherent.

The real choice is MIT versus Apache-2.0. The substantive axis is the patent grant.

- **Apache-2.0** (my recommendation). Section 3 is an express patent licence from every
  contributor, with a retaliation clause that terminates the licence of anyone who sues over
  patents in the work. Section 4 requires preserving a NOTICE file if one exists, and requires
  stating changes in modified files. What this buys: enterprise adopters and their legal teams
  routinely prefer or require Apache-2.0 for exactly this reason, and an MCP connector aimed at
  corporate recruiting stacks will be read by exactly those people. It also gives evolv itself
  the retaliation protection if outside contributors arrive. What it costs: a longer file, a
  NOTICE convention to maintain, and slightly more ceremony on contributions. Note the org has
  three Apache-2.0 files already and two of them were never filled in, so if we go Apache we
  must actually complete the appendix line, `Copyright 2026 evolv Consulting`, rather than
  shipping the placeholder a third time.
- **MIT**. Roughly 170 words, universally understood, zero friction, and it matches the one
  genuine evolv public-library precedent (`evolv-coder-lite`). What it costs: no express patent
  grant. The prevailing view is that MIT conveys an implied patent licence through "use, copy,
  modify, merge, publish, distribute, sublicense, and sell", but it is implied, not written, and
  some corporate reviewers treat that gap as a real one. There is no patent retaliation clause.
- **BSD-3-Clause**. Functionally MIT plus a no-endorsement clause preventing anyone from using
  the evolv name to promote derived products. That clause has mild brand value. Otherwise it
  buys nothing MIT does not, has no patent grant either, and the org has never used it. I would
  not introduce a third convention for that.
- **Proprietary / all rights reserved**. What it buys: total control, and it is what evolv does
  for its genuinely proprietary tooling (`evolv-ui`, `evolv-coder-kit`). What it costs:
  everything this repo is for. It cannot be published to PyPI usefully, cannot be adopted, and
  cannot be contributed to. Only correct if Phil decides the connector is a competitive asset
  rather than a giveaway, which contradicts the stated intent.

**Concrete proposal.** Ship Apache-2.0 with the appendix line completed as
`Copyright 2026 evolv Consulting`, add a short NOTICE file naming evolv Consulting and the
project, and add `license = "Apache-2.0"` plus the matching classifier to `pyproject.toml` so
PyPI metadata agrees with the file. If Phil would rather not carry the NOTICE convention, keep
MIT as it stands, `Copyright (c) 2026 evolv Consulting`, which is already consistent with the
one real precedent. Either is defensible. The thing to avoid is leaving it undecided, which is
how 13 public repos ended up with no licence at all.

**Worth flagging separately:** 14 public evolv repos have no licence, which legally means no one
may reuse them. If any of those hands-on-lab or demo repos were published for customers or
prospects to use, that is a live gap independent of this decision.

## What I could NOT verify

- **Private repos invisible to this token.** I enumerated 187 repos as `Aztec03hub` with scopes
  `gist, read:org, repo, workflow`. If the org contains repos that account cannot see, they are
  absent from this survey and I have no way to count them. The 187 figure is what this token
  sees, not a proven org total.
- **404 means "no licence GitHub can detect", not proven absence.** A repo could carry licence
  text inside a README, a `docs/` file, or file headers and still 404 on the licence endpoint. I
  did not open README files for all 174 repos. I checked README licence sections only for
  `claude-conduit-app`.
- **Whether any repo has contractual licensing terms outside the repo.** Client work is very
  likely governed by MSAs and SOWs that never appear in git. Nothing here speaks to those.
- **Whether `snowddl` and `ai-coding-rules` were forked at the GitHub level.** The API reports
  `fork: false` for both, so they were copied rather than forked, and I inferred `snowddl`'s
  upstream provenance from the `Copyright 2026 Vitaly Markov` line and a `test_oie_fork_patches.py`
  file in its root, not from a fork relationship.
- **Legal advice.** This is a survey of practice plus a reading of licence terms. It is not
  legal review, and if the patent grant question actually matters for a Jobvite connector,
  someone with authority should say so.

## Appendix A: commands used

```
gh auth status
gh repo list evolvconsulting --limit 300 --json name,visibility,isArchived,primaryLanguage,updatedAt,description,licenseInfo
gh api repos/evolvconsulting/<name>/license            # run for all 187 names
gh api repos/evolvconsulting/<name>                    # fork/parent/archived/created, for the 13 licensed repos
gh api repos/evolvconsulting/<name>/contents           # root listing, for NOTICE checks
gh api repos/evolvconsulting/claude-conduit-app/readme
gh api repos/evolvconsulting/claude-conduit-app/contents/package.json
```

Licence bodies were base64-decoded from the `content` field of the `/license` response and
grepped for lines containing `opyright`. Copyright lines in the tables above are verbatim, with
capitalisation unchanged.

## Appendix B: the 404s

174 repos returned `gh: Not Found (HTTP 404)` from the licence endpoint, with no other error
shape observed. That count breaks down as 160 private and 14 public with no licence, plus the
5 licensed public repos and 8 licensed private repos making up the 187 total. Client-named
repos are all in the 404 set. I have not listed the private repo names here since several are
client names.
