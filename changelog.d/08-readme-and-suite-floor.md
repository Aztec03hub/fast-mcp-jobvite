### Added
- `README.md`, written against `documentation/readme-standard.md`, which is `priority: required`:
  all fourteen sections in the prescribed order, a configuration table covering every one of the
  fifteen environment variables the server reads, and copy-paste-runnable examples. It states
  plainly that the server exposes no tool yet and shows `Tools: 0` rather than an example that does
  not run - the standard forbids placeholder prose, and inventing usage would have been worse than
  saying so. (task #8)
- `tests/test_readme.py` enforces the standard from the suite: required sections in order, every
  environment variable read by `config.py` present in the table, every relative link resolving, the
  500-line cap, and no placeholder prose. The standard says a new variable "requires the table to be
  updated in the same PR" - a rule with no enforcement is a rule that decays, so this fails the
  build instead. (task #8)
- `scripts/check-suite-floor.sh` floors the number of passing tests, wired into CI for both the
  default suite and the network arm, with an amputation harness of its own. (task #4, finding L6)
- `scripts/probe-exception-redaction.py` reproduces an unredacted log field in a real child
  process. (task #15)

### Fixed
- A silently-shrinking test suite could not be detected. CI's guard was
  `grep -qE '[1-9][0-9]* passed'`, which is satisfied by `1 passed`, so tests could be deleted,
  renamed out of collection, or deselected by an `addopts` edit with the build staying green.
  Coverage could not catch it either, being a ratio: removing a test together with the code it
  covered can raise it. The network arm had no count check at all, and needed one more than the
  default suite did - it is a matched pair, so a half-collected run leaves the positive arm passing
  alone and proving nothing. (task #4, finding L6)

### Security
- The single log sink redacts `record["message"]` but not `record["exception"]`, and `serialize`
  renders both. Two live producers reach that field: the entry point's own `logger.exception`, and
  the stdlib forwarder, which passes every third-party library's `exc_info` through. Confirmed by a
  committed probe that plants a credential-shaped URL and reads what the process writes; both
  tokens reach the stream in the clear. The fix is tracked with the M-5 work. Exposure is bounded
  by `diagnose=False` and `backtrace=False`, which suppress variable values and extended frames.
  (task #15)
