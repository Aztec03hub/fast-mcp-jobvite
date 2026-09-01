# EVIDENCE: the 47 blank-END citation sites (#126)

Measured on main at 8270487, against the freeze 5d17cd7.
Regenerate with: python3 docs/reviews/check-design-citation-shape.py

## Every site, as the checker reports it
```
  47  ends on a BLANK line (one line too long)
        docs/reviews/check-design-citation-shape.py:45  DESIGN.md:373-383
        scripts/check-u10-write-amputation.sh:229  DESIGN.md:1134-1144
        scripts/check-u10-write-controls.sh:303  DESIGN.md:1134-1144
        scripts/check-u7-resilience-amputation.sh:280  DESIGN.md:674-680
        scripts/check-u7-resilience-controls.sh:216  DESIGN.md:373-383
        scripts/check-u7-resilience-controls.sh:430  DESIGN.md:674-680
        scripts/check-u7-resilience-controls.sh:461  DESIGN.md:678-680
        src/fast_mcp_jobvite/approval.py:386  DESIGN.md:1134-1144
        src/fast_mcp_jobvite/audit.py:6  DESIGN.md:649-654
        src/fast_mcp_jobvite/config.py:67  DESIGN.md:207-213
        src/fast_mcp_jobvite/config.py:230  DESIGN.md:1663-1669
        src/fast_mcp_jobvite/services/jobvite_client.py:624  DESIGN.md:386-391
        src/fast_mcp_jobvite/services/jobvite_client.py:699  DESIGN.md:373-383
        src/fast_mcp_jobvite/services/jobvite_client.py:909  DESIGN.md:373-383
        src/fast_mcp_jobvite/tools/candidates.py:13  DESIGN.md:207-238
        src/fast_mcp_jobvite/tools/candidates.py:233  DESIGN.md:1134-1144
        src/fast_mcp_jobvite/utils/redaction.py:96  DESIGN.md:312-319
        src/fast_mcp_jobvite/utils/redaction.py:149  DESIGN.md:1143-1144
        tests/credentialed/test_search_jobs_live.py:7  DESIGN.md:1310-1313
        tests/test_approval_write.py:994  DESIGN.md:1134-1144
        tests/test_boot.py:100  DESIGN.md:1451-1453
        tests/test_boot.py:123  DESIGN.md:905-907
        tests/test_boot.py:169  DESIGN.md:1004-1009
        tests/test_config.py:1  DESIGN.md:984-1030
        tests/test_config.py:5  DESIGN.md:1451-1453
        tests/test_config.py:144  DESIGN.md:992-1009
        tests/test_config.py:211  DESIGN.md:901-907
        tests/test_config.py:218  DESIGN.md:905-907
        tests/test_config.py:375  DESIGN.md:873-877
        tests/test_config.py:616  DESIGN.md:1028-1030
        tests/test_fixture_path.py:16  DESIGN.md:1332-1338
        tests/test_http_hardening.py:506  DESIGN.md:906-907
        tests/test_http_hardening.py:710  DESIGN.md:1451-1453
        tests/test_jobvite_client.py:152  DESIGN.md:1451-1453
        tests/test_jobvite_client.py:578  DESIGN.md:1451-1453
        tests/test_manifest.py:152  DESIGN.md:1310-1313
        tests/test_manifest.py:181  DESIGN.md:1451-1453
        tests/test_markers.py:6  DESIGN.md:1318-1323
        tests/test_markers.py:109  DESIGN.md:1310-1313
        tests/test_resilience.py:1  DESIGN.md:354-383
        tests/test_resilience.py:570  DESIGN.md:373-383
        tests/test_resilience.py:576  DESIGN.md:373-383
        tests/test_resilience.py:1234  DESIGN.md:678-680
        tests/test_server.py:185  DESIGN.md:992-1009
        tests/test_tools_job_feed.py:544  DESIGN.md:312-314
        tests/test_tools_jobs.py:312  DESIGN.md:692-698
        tests/test_tools_jobs.py:380  DESIGN.md:692-698

```

## Grouped by END line - this is the decision unit
```
end 1009   sites=3   ranges: 1004-1009 992-1009 992-1009
end 1030   sites=2   ranges: 984-1030 1028-1030
end 1144   sites=6   ranges: 1134-1144 1134-1144 1134-1144 1134-1144 1143-1144 1134-1144
end 1313   sites=3   ranges: 1310-1313 1310-1313 1310-1313
end 1323   sites=1   ranges: 1318-1323
end 1338   sites=1   ranges: 1332-1338
end 1453   sites=6   ranges: 1451-1453 1451-1453 1451-1453 1451-1453 1451-1453 1451-1453
end 1669   sites=1   ranges: 1663-1669
end 213    sites=1   ranges: 207-213
end 238    sites=1   ranges: 207-238
end 314    sites=1   ranges: 312-314
end 319    sites=1   ranges: 312-319
end 383    sites=7   ranges: 373-383 373-383 373-383 373-383 354-383 373-383 373-383
end 391    sites=1   ranges: 386-391
end 654    sites=1   ranges: 649-654
end 680    sites=4   ranges: 674-680 674-680 678-680 678-680
end 698    sites=2   ranges: 692-698 692-698
end 877    sites=1   ranges: 873-877
end 907    sites=4   ranges: 905-907 901-907 905-907 906-907
```
