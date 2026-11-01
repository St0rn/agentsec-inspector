# Installation validation matrix

Status date: 2026-11-01. “Current workspace” means the Linux development environment used for v1.5.0 source validation. Windows and packaged Linux results must come from GitHub Actions for the exact commit or tag; the last published package proof before v1.5.0 is v1.4.0 ([Windows 41224219837](https://github.com/St0rn/agentsec-inspector/actions/runs/41224219837), [Linux 41224219868](https://github.com/St0rn/agentsec-inspector/actions/runs/41224219868)).

## PowerShell scripts

PowerShell is unavailable in the current Linux workspace. The table therefore does not transfer historical v1.4.0 results to v1.5.0. The Windows workflow parses and analyzes every script, runs Pester in PowerShell 7 and 5.1, builds both installers, and exercises the installation path.

| Script | Syntax | Execution | Error tests | Result | v1.5.0 status before tagged CI |
|---|---|---|---|---|---|
| `install.ps1` | Windows CI required | Windows CI required | Pester + packaged cycle | Pending exact-tag run | Not yet validated |
| `install-dev.ps1` | Windows CI required | Not nominally exercised by package job | Incomplete venv covered by Pester | Pending exact-tag run | Partial by design |
| `check-prerequisites.ps1` | Windows CI required | `-ForBuild` in Windows CI | Strict detection cases in Pester | Pending exact-tag run | Not yet validated |
| `setup-backend.ps1` | Windows CI required | Integrated into build | Missing/incomplete venv cases | Pending exact-tag run | Not yet validated |
| `setup-frontend.ps1` | Windows CI required | Integrated into build | Native process exit handling | Pending exact-tag run | Not yet validated |
| `setup-database.ps1` | Windows CI required | Repeated under PS7 and PS5.1 | Idempotence/integrity | Pending exact-tag run | Not yet validated |
| `start-dev.ps1` | Windows CI required | Not nominally exercised by package job | Static/Pester coverage | Pending exact-tag run | Partial by design |
| `start-production.ps1` | Windows CI required | Exercised through installed desktop verification | Missing package/process cases | Pending exact-tag run | Not yet validated |
| `build-windows.ps1` | Windows CI required | Full build in Windows CI | Missing MSI/NSIS is blocking | Pending exact-tag run | Not yet validated |
| `test-all.ps1` | Windows CI required | Invoked by build | Quality thresholds are blocking | Pending exact-tag run | Not yet validated |
| `verify-installation.ps1` | Windows CI required | MSI ×2 and NSIS ×2 | Auth, process, CORS, DB, CRUD, logs | Pending exact-tag run | Not yet validated |
| `update.ps1` | Windows CI required | Not nominally exercised by package job | Backup/migration/rollback regression | Pending exact-tag run | Partial by design |
| `backup.ps1` | Windows CI required | API backup covered separately | Missing-data regression | Pending exact-tag run | Partial by design |
| `restore.ps1` | Windows CI required | Refusal path in Pester | Confirmation required | Pending exact-tag run | Partial by design |
| `uninstall.ps1` | Windows CI required | After MSI and NSIS | User data preserved by default | Pending exact-tag run | Not yet validated |
| `clean.ps1` | Windows CI required | Not run nominally | Repository-bounded targets | Pending exact-tag run | Partial by design |

## Linux scripts

| Script | Syntax | Execution | Error tests | Result | v1.5.0 status |
|---|---|---|---|---|---|
| `check-prerequisites.sh` | `bash -n` passed | Exercised by lifecycle/build entry points | Missing build tools reported | Expected diagnostic | Validated locally for covered paths |
| `install-dev.sh` | `bash -n` passed | Executed repeatedly by isolated lifecycle tests | Prerequisite and existing-state paths | Passed | Validated locally |
| `setup-database.sh` | `bash -n` passed | Executed repeatedly | Missing environment and idempotence | Passed | Validated locally |
| `start-dev.sh` | `bash -n` passed | Covered by development workflow, not left running | Backend auth/readiness checks | Passed in prior integration; exact package pending | Partial locally |
| `test-all.sh` | `bash -n` passed | Component commands executed directly | Blocking quality thresholds | 101 backend and 56 frontend tests passed | Validated locally |
| `test-scripts.sh` | `bash -n` passed | Executed | Confirmation, downgrade, invalid artifact, preservation/deletion | Passed | Validated locally |
| `backup.sh` | `bash -n` passed | Executed in isolated cycle | Missing data/checksum | Passed | Validated locally |
| `restore.sh` | `bash -n` passed | Executed in isolated cycle | Confirmation/integrity | Passed | Validated locally |
| `install.sh` | `bash -n` passed | Isolated artifact cycle passed; real AppImage requires CI | Missing/invalid artifact and idempotence | Local regression passed | Platform validation pending |
| `verify-installation.sh` | `bash -n` passed | Real AppImage verification requires CI | Invalid artifact/auth/CRUD/log checks | Local regression passed | Platform validation pending |
| `update.sh` | `bash -n` passed | No-change/downgrade paths executed | Downgrade rejected; rollback path covered | Passed for covered paths | Partial locally |
| `uninstall.sh` | `bash -n` passed | Executed in isolation | Preserve by default; explicit deletion confirmation | Passed | Validated locally |
| `build-linux.sh` | `bash -n` passed | Requires platform build dependencies and Rust | Missing prerequisites are blocking | Exact-tag CI pending | Not yet package-validated |
| `start-production.sh` | `bash -n` passed | Real AppImage startup requires CI | Missing installation handled | Exact-tag CI pending | Not yet package-validated |
| `clean.sh` | `bash -n` passed | Not executed | Targets bounded to project outputs | Static only | Static only |

The matrix is updated with exact v1.5.0 run URLs only after the tagged Windows and Linux jobs finish successfully.
