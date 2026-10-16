# Vulnerabilities

Known security and reliability disclosures for this project.

## Dependencies

### Not fixed

| Severity | Advisory                                                                                                                                                                  | Component | Notes                                                                                        |
| -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------- | -------------------------------------------------------------------------------------------- |
| High     | [CVE-2024-23342](https://osv.dev/vulnerability/CVE-2024-23342) / [GHSA-wj6h-64fc-37mp](https://github.com/tlsfuzzer/python-ecdsa/security/advisories/GHSA-wj6h-64fc-37mp) | ecdsa     | Upstream won’t-fix (Minerva timing side-channel). Brought in via `home-assistant-chip-core`. |

### False positives

Reported against Debian `openssl 3.0.20-1~deb12u2`, which is already marked **fixed** as reported on ([Docker Scout](https://scout.docker.com/)).

| Severity | Advisory       | Component | Report |
| -------- | -------------- | --------- | ------ |
| Critical | CVE-2026-34182 | openssl   | [URL](https://scout.docker.com/vulnerabilities/id/CVE-2026-34182?s=debian&n=openssl&ns=debian&t=deb&osn=debian&osv=12&vr=%3C3.0.20-1~deb12u2) |
| High     | CVE-2026-34180 | openssl   | [URL](https://scout.docker.com/vulnerabilities/id/CVE-2026-34180?s=debian&n=openssl&ns=debian&t=deb&osn=debian&osv=12&vr=%3C3.0.20-1~deb12u2) |
| High     | CVE-2026-45445 | openssl   | [URL](https://scout.docker.com/vulnerabilities/id/CVE-2026-45445?s=debian&n=openssl&ns=debian&t=deb&osn=debian&osv=12&vr=%3C3.0.20-1~deb12u2) |
| High     | CVE-2026-45447 | openssl   | [URL](https://scout.docker.com/vulnerabilities/id/CVE-2026-45447?s=debian&n=openssl&ns=debian&t=deb&osn=debian&osv=12&vr=%3C3.0.20-1~deb12u2) |
| High     | CVE-2026-7383  | openssl   | [URL](https://scout.docker.com/vulnerabilities/id/CVE-2026-7383?s=debian&n=openssl&ns=debian&t=deb&osn=debian&osv=12&vr=%3C3.0.20-1~deb12u2) |
| High     | CVE-2026-9076  | openssl   | [URL](https://scout.docker.com/vulnerabilities/id/CVE-2026-9076?s=debian&n=openssl&ns=debian&t=deb&osn=debian&osv=12&vr=%3C3.0.20-1~deb12u2) |

### Force overrides

Transitive dashboard packages forced via `dashboard/package.json` `overrides`:

| Advisory            | Package              | Override |
| ------------------- | -------------------- | -------- |
| CVE-2026-33750      | brace-expansion      | 5.0.8    |
| CVE-2024-21538      | cross-spawn          | 7.0.6    |
| CVE-2026-26996      | minimatch            | 10.2.6   |
| CVE-2026-27903      | minimatch            | 10.2.6   |
| CVE-2026-27904      | minimatch            | 10.2.6   |
| CVE-2024-45296      | path-to-regexp       | 3.3.0    |
| CVE-2026-33671      | picomatch            | 4.0.4    |
| GHSA-5C6J-R48X-RMVQ | serialize-javascript | 7.0.7    |

## Code reliability

Static analysis findings retained from upstream Matter server / project sources.

| ID  | Category    | Severity | Summary                                              | Affected Locations                                                                                                                                                                                                                                                                                                                                      |
| --- | ----------- | -------- | ---------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 2.1 | Security    | Major    | Path traversal in diagnostic/example scripts         | • scripts/beautify_diagnostics.py, line 18<br>• scripts/example.py, line 63                                                                                                                                                                                                                                                                                |
| 2.4 | Reliability | Major    | Dataclass attributes missing type annotations        | • matter_server/common/custom_clusters.py, line 179<br>• matter_server/common/custom_clusters.py, line 202<br>• matter_server/common/custom_clusters.py, line 227<br>• matter_server/common/custom_clusters.py, line 250<br>• matter_server/common/custom_clusters.py, line 273                                                                                     |
| 2.5 | Reliability | Major    | `asyncio.CancelledError` not re-raised after cleanup | • matter_server/server/client_handler.py, line 122                                                                                                                                                                                                                                                                                                      |
| 2.6 | Reliability | Major    | Fire-and-forget asyncio tasks not retained           | • matter_server/server/client_handler.py, line 173<br>• matter_server/server/device_controller.py, line 1315<br>• matter_server/server/device_controller.py, line 1617<br>• matter_server/server/device_controller.py, line 1643<br>• matter_server/server/device_controller.py, line 1680<br>• matter_server/server/server.py, line 281<br>• scripts/example.py, line 84 |
| 2.7 | Reliability | Major    | Deprecated `datetime.utcnow()`                       | • matter_server/server/device_controller.py, line 638<br>• matter_server/server/device_controller.py, line 640                                                                                                                                                                                                                                             |
| 2.8 | Reliability | Minor    | Non-robust shell test in setup script                |<br>• scripts/setup.sh, line 11                                                                                                                                                                                                                                                                                                                             |
