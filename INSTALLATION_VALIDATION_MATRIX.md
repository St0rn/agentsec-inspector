# Installation validation matrix

Status date: 2026-11-01. “Current workspace” means the Linux development environment used for v1.5.0 source validation. Packaged results come from the exact `v1.5.0` tag workflows: [Windows 41293107640](https://github.com/St0rn/agentsec-inspector/actions/runs/41293107640) and [Linux 41293107481](https://github.com/St0rn/agentsec-inspector/actions/runs/41293107481), both for commit `a5a694a3ca37232790affa17e700a64b29b5dd11`.

## PowerShell scripts

PowerShell is unavailable in the current Linux workspace. The exact-tag Windows workflow parsed and analyzed every script, ran Pester in PowerShell 7 and 5.1, built both installers, and exercised their installation paths.

| Script | Syntax | Execution | Error tests | Result | v1.5.0 status |
|---|---|---|---|---|---|
| `install.ps1` | Passed | MSI ×2 and NSIS ×2 | Pester + packaged cycle | Passed | Validated on Windows |
| `install-dev.ps1` | Passed | Not nominally exercised by package job | Incomplete venv covered by Pester | Static/error paths passed | Partial by design |
| `check-prerequisites.ps1` | Passed | `-ForBuild` compiler/SDK probe | Strict detection cases in Pester | Passed | Validated on Windows |
| `setup-backend.ps1` | Passed | Integrated into build | Missing/incomplete venv cases | Passed in build path | Validated for build path |
| `setup-frontend.ps1` | Passed | Integrated into build | Native process exit handling | Passed in build path | Validated for build path |
| `setup-database.ps1` | Passed | Repeated under PS7 and PS5.1 tests | Idempotence/integrity | Passed | Validated for covered paths |
| `start-dev.ps1` | Passed | Not nominally exercised by package job | Static/Pester coverage | Static/error paths passed | Partial by design |
| `start-production.ps1` | Passed | Exercised through installed desktop verification | Missing package/process cases | Passed | Validated on Windows |
| `build-windows.ps1` | Passed | Full x64 MSI/NSIS build | Missing artifacts are blocking | Passed | Validated on Windows |
| `test-all.ps1` | Passed | Invoked by build | Quality thresholds are blocking | Passed | Validated on Windows |
| `verify-installation.ps1` | Passed | MSI ×2 and NSIS ×2 | Auth, process, CORS, DB, CRUD, logs | Passed four times | Validated on Windows |
| `update.ps1` | Passed | Not nominally exercised by package job | Backup/migration/rollback regression | Static/error paths passed | Partial by design |
| `backup.ps1` | Passed | API backup covered separately | Missing-data regression | Static/error paths passed | Partial by design |
| `restore.ps1` | Passed | Refusal path in Pester | Confirmation required | Static/error paths passed | Partial by design |
| `uninstall.ps1` | Passed | After MSI and NSIS | User data preserved by default | Passed twice | Validated on Windows |
| `clean.ps1` | Passed | Not run nominally | Repository-bounded targets | Static/error paths passed | Partial by design |

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
| `install.sh` | `bash -n` and ShellCheck passed | Exact-tag AppImage installed twice | Missing/invalid artifact and idempotence | Passed locally and in CI | Validated on Linux |
| `verify-installation.sh` | `bash -n` and ShellCheck passed | Exact-tag AppImage verified twice | Invalid artifact/auth/CRUD/log checks | Passed locally and in CI | Validated on Linux |
| `update.sh` | `bash -n` passed | No-change/downgrade paths executed | Downgrade rejected; rollback path covered | Passed for covered paths | Partial locally |
| `uninstall.sh` | `bash -n` passed | Executed in isolation | Preserve by default; explicit deletion confirmation | Passed | Validated locally |
| `build-linux.sh` | `bash -n` and ShellCheck passed | AppImage and DEB built on Ubuntu 22.04 | Missing prerequisites are blocking | Passed in exact-tag CI | Validated on Linux |
| `start-production.sh` | `bash -n` and ShellCheck passed | Exercised by packaged verification | Missing installation handled | Passed in exact-tag CI | Validated on Linux |
| `clean.sh` | `bash -n` passed | Not executed | Targets bounded to project outputs | Static only | Static only |

The release was assembled only after both exact-tag jobs succeeded: [publication run 41294325538](https://github.com/St0rn/agentsec-inspector/actions/runs/41294325538), [release v1.5.0](https://github.com/St0rn/agentsec-inspector/releases/tag/v1.5.0), and [published SHA-256 file](https://github.com/St0rn/agentsec-inspector/releases/download/v1.5.0/SHA256SUMS.txt).
