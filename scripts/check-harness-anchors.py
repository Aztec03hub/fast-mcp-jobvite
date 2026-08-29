#!/usr/bin/env python3
"""Static anchor checker for the mutation and amputation harnesses.

WHY THIS EXISTS. Every harness in `scripts/` anchors on SOURCE TEXT: it finds a
literal string in a file under `src/` and replaces it. Any reformatting can
invalidate an anchor, and *a mutation that applies to nothing tests nothing*.
B49b reflowed 1608 lines, broke U3's M8, and CI noticed only because that one
step happened to grep for `COULD NOT APPLY` - the run that found it took
minutes. Reading the anchors and grepping the target file takes milliseconds,
which is what you want on the sweep commit itself.

WHAT IT CHECKS. For every anchor: the target file exists, and the anchor occurs
in it EXACTLY ONCE. Zero hits is a stale anchor; two or more is the
`ANCHOR NOT UNIQUE` failure the harnesses themselves raise, and both mean the
row silently tests nothing.

HOW IT FINDS ANCHORS, and why nothing here is a hand-kept list. A hand-kept list
beside its container is blind to the member nobody added, so the anchor
positions are DERIVED, never tabulated:

  Shape A, the shell helpers. `run_mutation() { local id="$1" file="$2"
  old="$3" ... }` - the helper's own `local` line names its parameters, so the
  file argument is whichever position is called `file` and the anchor is
  whichever is called `old`. U5's helper takes an extra `selector` and needs no
  special case, because its `local` line says so.

  Shape B, the inline Python heredocs. `python3 - "$CONFIG" <<'PY' ...
  s.replace("anchor", "mutant") ... PY` - the heredoc body is parsed with `ast`
  and every `.replace()` with two string-literal arguments yields an anchor. The
  file is the `$VAR` passed to `python3`, resolved from the script's own
  top-level assignments.

COMPLETENESS, checked rather than assumed. A parser that silently skips a call
site is exactly the defect this checker exists to catch, one level up. So it
counts the call sites it *could* see independently of the ones it parsed and
fails if they disagree - `--self-check` reports the tally. An unparseable
heredoc is an error, not a skip.

Exit codes:
  0  every anchor resolves uniquely
  1  at least one anchor is stale, ambiguous, or its target file is missing
  2  the checker could not parse a harness (a parser gap, not a repo defect)
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = REPO_ROOT / "scripts"

# A heredoc opened with a QUOTED delimiter, which is the only form used here and
# the only form in which the body is literal rather than shell-expanded.
HEREDOC_RE = re.compile(r"<<'(?P<tag>[A-Za-z_][A-Za-z0-9_]*)'\n(?P<body>.*?)\n(?P=tag)\n", re.S)
# `python3 - "<path expression>"` - the file the heredoc, or the helper, edits.
PY_INVOKE_RE = re.compile(r'python3\s+-\s+"(?P<path>[^"]+)"')
ASSIGN_RE = re.compile(r'^(?P<var>[A-Za-z_][A-Za-z0-9_]*)=(?P<val>.+)$', re.M)
VAR_REF_RE = re.compile(r'\$\{(?P<a>[A-Za-z_][A-Za-z0-9_]*)\}|\$(?P<b>[A-Za-z_][A-Za-z0-9_]*)')
# `name() {` AND `name () {` - the space is legal, two harnesses use it, and
# a regex without it returned a silent zero for both.
FUNCDEF_RE = re.compile(r"^(?P<name>[a-z_][a-z0-9_]*)\s*\(\)\s*\{", re.M)
LOCAL_RE = re.compile(r'^\s*local\s+(?P<decls>.+)$', re.M)
LOCAL_ARG_RE = re.compile(r'(?P<name>[a-z_][a-z0-9_]*)="\$(?P<pos>\d+)"')


@dataclass
class Anchor:
    harness: str
    line: int
    shape: str
    target: str
    text: str


class ParseError(Exception):
    pass


def _resolve_vars(src: str) -> dict[str, str]:
    """Script-level `VAR=value` assignments, expanded against one another.

    A value produced by a command substitution - `$(mktemp -d)`, `$(cd .. && pwd)`
    - is a path that only exists at runtime, so it resolves to the empty string.
    Every target path in these harnesses is written relative to one of those
    (`"$REPO/scripts/..."`, `"$TREE/$GATE_REL"`), so emptying them leaves exactly
    the repo-relative path this checker needs, after a leading-slash strip.
    """
    raw: dict[str, str] = {}
    runtime: set[str] = set()
    for m in ASSIGN_RE.finditer(src):
        var, val = m.group("var"), m.group("val").strip()
        if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
            val = val[1:-1]
        if "$(" in val or "`" in val:
            runtime.add(var)
            val = ""
        raw.setdefault(var, val)

    # Only the command substitution itself is emptied, never the variables built
    # on it. Emptying those TRANSITIVELY was tried and is wrong in one direction
    # while right in the other: `SCRIPT="$REPO/scripts/check-suite-floor.sh"`
    # over a `REPO=$(cd .. && pwd)` needs its literal tail KEPT, while
    # `TREE="$WORK/tree"` over an `mktemp -d` needs its literal tail DROPPED. The
    # difference is not visible in the assignment, so it is not decided here -
    # `_expand_path` decides it against the filesystem, which can tell them apart.
    del runtime
    resolved: dict[str, str] = {}

    def expand(name: str, seen: frozenset[str]) -> str:
        if name in resolved:
            return resolved[name]
        if name in seen or name not in raw:
            return ""
        out = VAR_REF_RE.sub(
            lambda mm: expand(mm.group("a") or mm.group("b"), seen | {name}), raw[name])
        resolved[name] = out
        return out

    for key in raw:
        expand(key, frozenset())
    return resolved


def _expand_path(expr: str, variables: dict[str, str]) -> str:
    """Expand a quoted shell path expression to a repo-relative path.

    A harness that mutates a COPY of the tree writes the copy's own layout into
    the path - `"$WORK/C/$GATE_REL"` - so an emptied runtime prefix can still
    leave a scratch segment in front. Leading segments are dropped one at a time
    until the path names a file that exists, and the FIRST such path wins; if
    none does, the expanded path is returned unchanged and reported as
    unresolved, which is a finding rather than a silent pass.
    """
    out = VAR_REF_RE.sub(
        lambda mm: variables.get(mm.group("a") or mm.group("b"), ""), expr)
    out = re.sub(r"/{2,}", "/", out).lstrip("/")
    parts = out.split("/")
    for i in range(len(parts)):
        candidate = "/".join(parts[i:])
        if (REPO_ROOT / candidate).is_file():
            return candidate
    return out


def _helper_signatures(src: str) -> dict[str, tuple[dict[str, int], str]]:
    """name -> ({param name: 1-based positional index}, body), read off `local`.

    Only helpers taking a parameter called `old` can carry an anchor; the rest
    are returned too, and the caller ignores them. The body comes back because a
    helper that does NOT take the target as a parameter names it in its own
    `python3 - "..."` invocation instead, and that is where the target is read
    from - derived from the helper, never from a table kept beside it.
    """
    sigs: dict[str, tuple[dict[str, int], str]] = {}
    for fm in FUNCDEF_RE.finditer(src):
        body = src[fm.end():]
        end = body.find("\n}")
        body = body[: end if end != -1 else len(body)]
        params: dict[str, int] = {}
        for lm in LOCAL_RE.finditer(body):
            for am in LOCAL_ARG_RE.finditer(lm.group("decls")):
                params[am.group("name")] = int(am.group("pos"))
        if params:
            sigs[fm.group("name")] = (params, body)
    return sigs


def _split_call(src: str, start: int) -> tuple[list[str], int]:
    """Tokenize one shell call beginning at `start`, honouring '' "" and \\-newline.

    Returns (argv, index just past the call). Written by hand rather than with
    `shlex` because shlex's POSIX mode discards the distinction between a
    literal single-quoted anchor and a double-quoted one that shell would
    expand, and an anchor is exactly the thing that must not be re-quoted.
    """
    argv: list[str] = []
    cur = ""
    started = False
    i = start
    n = len(src)
    while i < n:
        c = src[i]
        if c == "\\" and i + 1 < n and src[i + 1] == "\n":
            i += 2
            continue
        if c == "\n":
            i += 1
            break
        if c in " \t":
            if started:
                argv.append(cur)
                cur = ""
                started = False
            i += 1
            continue
        if c == "'":
            j = src.find("'", i + 1)
            if j == -1:
                raise ParseError("unterminated single quote")
            cur += src[i + 1 : j]
            started = True
            i = j + 1
            continue
        if c == '"':
            j = i + 1
            buf = ""
            while j < n and src[j] != '"':
                if src[j] == "\\" and j + 1 < n:
                    buf += src[j : j + 2]
                    j += 2
                    continue
                buf += src[j]
                j += 1
            if j >= n:
                raise ParseError("unterminated double quote")
            cur += buf
            started = True
            i = j + 1
            continue
        cur += c
        started = True
        i += 1
    if started:
        argv.append(cur)
    return argv, i


def _shape_a(name: str, src: str, sigs: dict[str, tuple[dict[str, int], str]],
             variables: dict[str, str]) -> tuple[list[Anchor], int]:
    """Anchors passed as arguments to a shell helper. Returns (anchors, call sites seen)."""
    carriers = {h: pb for h, pb in sigs.items() if "old" in pb[0]}
    if not carriers:
        return [], 0
    # `(?!\s*\(\))` excludes the helper's own DEFINITION line: `amputate () {`
    # also begins with the name and a space, and counting it as a call site
    # produced a phantom row whose "anchor" was `{`.
    call_re = re.compile(
        r"^(?P<name>" + "|".join(map(re.escape, carriers)) + r")[ \t]+(?!\(\))", re.M)
    anchors: list[Anchor] = []
    seen = 0
    for m in call_re.finditer(src):
        seen += 1
        lineno = src.count("\n", 0, m.start()) + 1
        argv, _ = _split_call(src, m.start())
        params, body = carriers[m.group("name")]
        if "file" in params:
            need = max(params["file"], params["old"])
            if len(argv) <= need:
                raise ParseError(f"{name}: call to {m.group('name')} at line {lineno} "
                                 f"has {len(argv) - 1} args, needs {need}")
            target = _expand_path(argv[params["file"]], variables)
        else:
            # No `file` parameter, so the helper edits a path it names itself.
            inv = PY_INVOKE_RE.search(body)
            if inv is None:
                raise ParseError(
                    f"{name}: helper {m.group('name')} takes an `old` anchor but names no "
                    "target - neither a `file` parameter nor a `python3 - \"...\"` invocation")
            target = _expand_path(inv.group("path"), variables)
            if len(argv) <= params["old"]:
                raise ParseError(f"{name}: call to {m.group('name')} at line {lineno} "
                                 f"has {len(argv) - 1} args, needs {params['old']}")
        anchors.append(Anchor(name, lineno, "shell-arg", target, argv[params["old"]]))
    return anchors, seen


def _shape_b(name: str, src: str, variables: dict[str, str]) -> tuple[list[Anchor], int]:
    """Anchors that are string literals inside an inline `python3 -` heredoc."""
    anchors: list[Anchor] = []
    seen = 0
    for m in HEREDOC_RE.finditer(src):
        body = m.group("body")
        if ".replace(" not in body and "re.sub(" not in body:
            continue
        line = src.count("\n", 0, m.start()) + 1
        # The heredoc's target file: the $VAR on the `python3 -` line that opened it.
        head = src[: m.start()].rsplit("\n", 1)[-1]
        inv = PY_INVOKE_RE.search(head)
        try:
            tree = ast.parse(body)
        except SyntaxError as exc:  # a parser gap, never a silent skip
            raise ParseError(f"{name}: heredoc at line {line} does not parse: {exc}") from exc
        # Anchors are not always written inline. Half of U1's rows bind one to a
        # local first - `anchor = "..."` then `s.replace(anchor, ...)` - so an
        # inline-literals-only parser skips them WITHOUT ERRORING, which is the
        # very defect this checker exists to catch, one level up. Measured: it
        # saw 2 of U1's 7 and 14 of the controls' 20 before this resolution
        # existed. Only single-assignment string constants are resolved; a name
        # bound twice is left unresolved rather than guessed at.
        assigned: dict[str, str | None] = {}
        for node in ast.walk(tree):
            if (isinstance(node, ast.Assign) and len(node.targets) == 1
                    and isinstance(node.targets[0], ast.Name)):
                name = node.targets[0].id
                value = (node.value.value
                         if isinstance(node.value, ast.Constant)
                         and isinstance(node.value.value, str) else None)
                assigned[name] = None if name in assigned else value

        def literal(node: ast.expr) -> str | None:
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                return node.value
            if isinstance(node, ast.Name):
                return assigned.get(node.id)
            return None

        for node in ast.walk(tree):
            if not (isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "replace"
                    and len(node.args) == 2):
                continue
            seen += 1
            anchor_text = literal(node.args[0])
            if anchor_text is None:
                continue  # the generic helper: `s.replace(old, new)` over parameters
            if inv is None:
                raise ParseError(
                    f"{name}: literal .replace() at line {line} but no `python3 - \"...\"` "
                    "on the opening line; the target file cannot be resolved")
            anchors.append(Anchor(name, line + node.lineno, "py-heredoc",
                                  _expand_path(inv.group("path"), variables), anchor_text))

        # `re.sub(pattern, repl, s, flags=re.S)`. U15's amputation harness
        # anchors ENTIRELY this way and, uniquely among the harnesses, has no
        # vocabulary for reporting that a row did not apply - `re.sub` that
        # matches nothing returns the string unchanged and raises nothing, so
        # the row runs, prints a result, and tested an INTACT tree. A regex
        # anchor is still an anchor; it is checked with `re.search` instead of
        # `str.count`, with the call's own flags.
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "sub"
                    and isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "re"
                    and node.args):
                continue
            seen += 1
            pattern = literal(node.args[0])
            if pattern is None:
                continue
            if inv is None:
                raise ParseError(f"{name}: literal re.sub() at line {line} but no "
                                 "`python3 - \"...\"` on the opening line")
            anchors.append(Anchor(name, line + node.lineno, "py-regex",
                                  _expand_path(inv.group("path"), variables), pattern))
    return anchors, seen


def _shape_c(name: str, src: str, variables: dict[str, str]) -> tuple[list[Anchor], int]:
    """Anchors held in a `@@`-delimited spec here-document.

    U15's control harness declares its rows as `label@@OLD@@NEW@@test` lines and
    splits them with parameter expansion. WHICH field is the anchor is not
    guessed: the loop's own `NAME="${...@@...}"` assignments are read in source
    order, and the field whose variable is called `OLD` is the anchor - the same
    derive-don't-tabulate rule the shell helpers use.
    """
    field_re = re.compile(r'^\s*(?P<name>[A-Za-z_][A-Za-z0-9_]*)="\$\{[a-z_]+(?:%%|#\*)[^}]*@@[^}]*\}"',
                          re.M)
    order = [m.group("name") for m in field_re.finditer(src)]
    if "OLD" not in order:
        return [], 0
    idx = order.index("OLD")
    anchors: list[Anchor] = []
    seen = 0
    for m in HEREDOC_RE.finditer(src):
        body = m.group("body")
        if "@@" not in body:
            continue
        head = src[: m.start()].rsplit("\n", 1)[-1]
        # The loop that consumes the spec is what edits the file, so the target
        # comes from the `python3 - "..."` inside that loop, not from the spec.
        inv = PY_INVOKE_RE.search(src[m.end():])
        if inv is None:
            raise ParseError(f"{name}: an @@ spec here-document has no "
                             "`python3 - \"...\"` consumer after it")
        target = _expand_path(inv.group("path"), variables)
        base = src.count("\n", 0, m.start()) + 1
        for offset, row in enumerate(body.splitlines(), start=1):
            if not row.strip() or "@@" not in row:
                continue
            seen += 1
            fields = row.split("@@")
            if len(fields) <= idx:
                raise ParseError(f"{name}: spec row at line {base + offset} has "
                                 f"{len(fields)} fields, needs at least {idx + 1}")
            try:
                text = ast.literal_eval(fields[idx])
            except (ValueError, SyntaxError) as exc:
                raise ParseError(f"{name}: spec row at line {base + offset} carries an "
                                 f"anchor that is not a Python literal: {exc}") from exc
            if not isinstance(text, str) or not text:
                continue
            anchors.append(Anchor(name, base + offset, "spec-row", target, text))
        del head
    return anchors, seen


def collect(path: Path) -> tuple[list[Anchor], dict[str, int]]:
    src = path.read_text()
    variables = _resolve_vars(src)
    sigs = _helper_signatures(src)
    a_anchors, a_seen = _shape_a(path.name, src, sigs, variables)
    b_anchors, b_seen = _shape_b(path.name, src, variables)
    c_anchors, c_seen = _shape_c(path.name, src, variables)
    return (a_anchors + b_anchors + c_anchors,
            {"shell call sites": a_seen, "python edits": b_seen, "spec rows": c_seen})


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--self-check", action="store_true",
                    help="print the per-harness tally of call sites seen vs anchors parsed")
    ap.add_argument("--quiet", action="store_true", help="print only failures and the verdict")
    ap.add_argument("--floor", type=int, default=0, metavar="N",
                    help="fail if fewer than N anchors were resolved. Every anchor this "
                         "checker reads is one it can no longer read silently: if a parser "
                         "shape stops matching, the count drops and every row it covered "
                         "goes unchecked WITH THE RUN STILL GREEN. The floor lives in "
                         "ci.yml, the same one place the suite floor lives, and lowering "
                         "it is a visible diff that has to be defended.")
    args = ap.parse_args()

    # THIS CHECKER'S OWN CONTROL HARNESS IS NOT A HARNESS OF THE PRODUCT. It
    # anchors into a throwaway copy of the tree, so its targets are runtime
    # paths that resolve to nothing and its rows arrive as findings about files
    # that do not exist. Found by that control harness on its first run, as a
    # positive control that was passing for the wrong reason.
    #
    # Matched on the FILENAME, derived from this file's own stem. The first
    # attempt excluded any script whose TEXT mentioned this checker, and a
    # comment added to check-u15-gate-amputation.sh - a real harness with four
    # live anchors - then excluded it silently, dropping the count from 154 to
    # 150. A predicate over prose is a predicate any prose can trip.
    stem = Path(__file__).stem
    harnesses = [h for h in sorted(SCRIPTS.glob("check-*.sh"))
                 if not h.name.startswith(stem)]
    if not harnesses:
        print(f"ERROR: no harnesses found under {SCRIPTS} - is the path right?")
        return 2

    total = 0
    stale: list[tuple[Anchor, str]] = []
    unread: list[tuple[str, str]] = []

    # A harness that edits a file by a mechanism this parser cannot read yields a
    # clean zero, which is indistinguishable from a harness that anchors on
    # nothing - and a clean zero that explains itself is the dangerous kind. So
    # the mechanisms are detected independently of the parse, and any harness
    # that performs edits while contributing no anchors is NAMED on every run.
    MECHANISMS = {
        "sed -i": "in-place `sed -i` expressions",
        ".replace(": "Python `str.replace`",
        "re.sub(": "Python `re.sub`",
        "@@": "an `@@`-delimited spec table",
    }

    for h in harnesses:
        try:
            anchors, tally = collect(h)
        except ParseError as exc:
            print(f"PARSER GAP: {exc}")
            return 2
        if not anchors:
            src = h.read_text()
            found = sorted({d for k, d in MECHANISMS.items() if k in src})
            if found:
                unread.append((h.name, ", ".join(found)))
        if args.self_check:
            counts = ", ".join(f"{k}={v}" for k, v in tally.items())
            print(f"  {h.name:36s} anchors={len(anchors):3d}  ({counts})")
        for a in anchors:
            total += 1
            target = REPO_ROOT / a.target
            if not target.is_file():
                stale.append((a, f"target file does not exist: {a.target}"))
                continue
            text = target.read_text()
            if a.shape == "py-regex":
                # DOTALL, because every re.sub anchor here passes flags=re.S and
                # the patterns span lines. Checking one without it would report a
                # live anchor as stale, which is the loudest possible way to be
                # wrong and the reason it is stated here rather than defaulted.
                hits = len(re.findall(a.text, text, re.S))
            else:
                hits = text.count(a.text)
            if hits != 1:
                stale.append((a, f"{hits} hits in {a.target} (need exactly 1)"))

    if not args.quiet:
        print(f"harnesses scanned: {len(harnesses)}")
        print(f"anchors resolved: {total}")

    if unread:
        print(f"UNREAD MUTATION MECHANISMS ({len(unread)}) - these harnesses edit files by a")
        print("means this checker cannot read, so their rows are NOT covered below:")
        for scriptname, mechanism in unread:
            print(f"  {scriptname}: {mechanism}")

    for a, why in stale:
        print(f"STALE ANCHOR  {a.harness}:{a.line} [{a.shape}]  {why}")
        print(f"    anchor: {a.text.splitlines()[0][:100]!r}"
              + (" ..." if len(a.text.splitlines()) > 1 else ""))

    if stale:
        print(f"FAIL: {len(stale)} of {total} anchors do not resolve uniquely.")
        return 1
    if total < args.floor:
        print(f"FAIL: only {total} anchors were resolved, below the floor of {args.floor}. "
              "A parser shape has stopped matching, so the rows it covered are now "
              "unchecked - and every one of them would still report OK.")
        return 1
    print(f"OK: all {total} anchors resolve to exactly one hit in their target file"
          + (f" (floor {args.floor})." if args.floor else "."))
    return 0


if __name__ == "__main__":
    sys.exit(main())
