#!/usr/bin/env python3
"""#116: bind each harness timeout bound to ONE name, used by both the
`timeout` call and the abort message that explains it.

The defect: `timeout 900 ...` and `echo "...900s with no result..."` are two
copies of one decision. Change the call and the message lies, at exit 0, in
the exact output a reader turns to when something has gone wrong.

Three names, not one: the arms are different decisions (baseline / row /
selector) that must stay separately adjustable even where they share a value.
Enumerates the container; never a hand-written file list."""
import re
import subprocess
import sys

INV = re.compile(r'\btimeout\b((?:\s+(?:-k\s+\d+\w?|-s\s+\S+|--\S+))*)\s+(\d+)\b')
FIG = re.compile(r'\b(\d+)s\b')
SET = re.compile(r'^set -[a-z]*uo pipefail\s*$')
VAR = {'BASELINE': 'BASELINE_TIMEOUT', 'ROW': 'ROW_TIMEOUT', 'SELECTOR': 'SELECTOR_TIMEOUT'}


def arm_of(line):
    if 'BASELINE HUNG' in line or 're-check HUNG' in line:
        return 'BASELINE'
    if 'SELECTOR PROBE' in line:
        return 'SELECTOR'
    return 'ROW'


def classify(lines):
    """-> (inv index -> arm), (echo index -> arm), (arm -> value)"""
    inv_arm, echo_arm, vals = {}, {}, {}
    pend = None
    for i, line in enumerate(lines):
        m = None
        for m2 in INV.finditer(line):
            m = m2
        if m:
            pend = (i, m.group(2))
        if 'echo' in line and FIG.search(line) and pend is not None:
            a = arm_of(line)
            inv_arm[pend[0]] = a
            echo_arm[i] = a
            if a in vals and vals[a] != pend[1]:
                sys.exit("REFUSED: %s arm has two values in one file: %s and %s"
                         % (a, vals[a], pend[1]))
            vals[a] = pend[1]
            pend = None
    return inv_arm, echo_arm, vals


def main():
    changed = inv_n = echo_n = 0
    files = subprocess.check_output(['git', 'ls-files', 'scripts/*.sh'], text=True).split()
    for f in files:
        with open(f) as fh:
            lines = fh.read().splitlines(keepends=True)
        inv_arm, echo_arm, vals = classify([x.rstrip('\n') for x in lines])
        if not vals:
            continue
        out = []
        for i, line in enumerate(lines):
            if i in inv_arm:
                m = None
                for m2 in INV.finditer(line):
                    m = m2
                s, e = m.span(2)
                line = line[:s] + '"$%s"' % VAR[inv_arm[i]] + line[e:]
                inv_n += 1
            if i in echo_arm:
                arm = echo_arm[i]
                line = FIG.sub(lambda mm, a=arm: '${%s}s' % VAR[a], line, count=1)
                echo_n += 1
            out.append(line)
        idx = next(j for j, x in enumerate(out) if SET.match(x.rstrip('\n')))
        block = ['\n',
                 '# Timeout bounds - each declared ONCE and interpolated into the abort\n',
                 '# message that explains it, so a changed bound cannot leave prose behind\n',
                 '# still quoting the old one. Three names because the arms are three\n',
                 '# separate decisions, even where two of them share a value today.\n']
        for a in ('BASELINE', 'ROW', 'SELECTOR'):
            if a in vals:
                block.append('%s=%s\n' % (VAR[a], vals[a]))
        out[idx + 1:idx + 1] = block
        with open(f, 'w') as fh:
            fh.write(''.join(out))
        changed += 1
    print("files rewritten: %d   timeout calls bound: %d   messages derived: %d"
          % (changed, inv_n, echo_n))


if __name__ == '__main__':
    main()
