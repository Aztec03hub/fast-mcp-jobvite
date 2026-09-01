# EVIDENCE: the tally-shape container (#120)

Measured on main at 0ca0558.
Regenerate: see the loop at the bottom of this file.

## Which tally phrase each harness SOURCE contains
```
check-body-cap-amputation.sh                   NONE
check-body-cap-controls.sh                     fired
check-critical-coverage-amputation.sh          anchors
check-harness-anchors-controls.sh              fired
check-log-redaction-amputation.sh              anchors
check-pytest-bounded.sh                        NONE
check-suite-floor-amputation.sh                NONE
check-suite-floor.sh                           NONE
check-u0-test-controls.sh                      fired
check-u1-boot-amputation.sh                    NONE
check-u1-boot-controls.sh                      fired
check-u1-pid1-shutdown.sh                      NONE
check-u10-write-amputation.sh                  anchors
check-u10-write-controls.sh                    fired
check-u11-advisory-controls.sh                 fired
check-u12-jobfeed-amputation.sh                anchors
check-u12-jobfeed-controls.sh                  fired
check-u14-arguments-amputation.sh              anchors
check-u14-arguments-controls.sh                fired
check-u15-gate-amputation.sh                   NONE
check-u15-gate-controls.sh                     fired
check-u3-audit-amputation.sh                   NONE
check-u3-audit-controls.sh                     killed
check-u4-client-amputation.sh                  NONE
check-u4-client-controls.sh                    killed
check-u5-jobs-amputation.sh                    anchors
check-u5-jobs-controls.sh                      fired
check-u6-paging-amputation.sh                  anchors
check-u6-paging-controls.sh                    fired
check-u7-resilience-amputation.sh              anchors
check-u7-resilience-controls.sh                fired
check-u8-candidates-amputation.sh              anchors
check-u8-candidates-controls.sh                fired
check-u9-http-amputation.sh                    anchors
check-u9-http-controls.sh                      fired
```

## Totals
```
scripts printing "controls fired" : 14
scripts printing "RESULT: killed" : 2
scripts printing "ANCHORS APPLIED": 10
```

## Flags ci.yml actually passes to scripts/ci-harness-gate.sh
```
      9 --controls-fired
      5 --amputation
      3 --row-re
      3 --min-rows
      2 --result-killed
      2 --anchors-applied
      1 --require
```

## Regenerate
```sh
for f in $(git ls-files 'scripts/check-*.sh'); do
  grep -l 'controls fired\|RESULT: .*killed\|ANCHORS APPLIED' "$f"; done
```
