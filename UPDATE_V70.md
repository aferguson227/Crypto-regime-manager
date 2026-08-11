# CRM V70.0.0 — Resident Runtime & Live Trading Architecture

V70 replaces the collection of independently scheduled background processes with one hidden resident supervisor.

## Runtime ownership
- `CryptoRegimeManager-ResidentRuntime` becomes the single Windows scheduled owner.
- KuCoin Live Data Service and Research Worker run as hidden supervised child processes.
- The Local Agent becomes a low-priority publication job every 15 minutes rather than part of live trading truth.
- Legacy Local Agent and Research Worker scheduled tasks are disabled, not deleted, so rollback remains possible.

## Live-data targets
- resident heartbeat: 2 seconds
- browser/direct runtime target: 5–10 seconds
- KuCoin live heartbeat watchdog: 75 seconds maximum before automatic restart
- order truth target: 20 seconds
- balance target: 30 seconds
- paper-trading target: 30 seconds
- Git/publication: 15 minutes by default

## Installer safety
- resident maintenance mode pauses child writers before upgrades;
- runtime state remains outside Git;
- source release commits exclude `docs/*.json`;
- installer rebases immediately before push if remote read-only refresh commits advanced;
- rollback re-enables the previous scheduled architecture if V70 health verification fails.

## Safety boundary
CRM native live exchange writes remain locked. V70 is a reliability/runtime release, not a direct-execution unlock.


## Portfolio Truth & Decision Consistency

V70 now creates `portfolio_decision_consistency.json` from authoritative Runtime State.

- `Portfolio` is no longer allowed to equal free cash when a recognised live position also exists.
- Total portfolio truth uses the larger of exchange-reported equity and reconstructed cash + live-position market value.
- `Deployable now` is capped by genuinely free KuCoin cash after the remaining DCA reserve.
- If a live strategy has completed all configured safety orders, remaining DCA reserve becomes zero.
- A deployment candidate cannot continue to display a capital blocker when safe deployable cash is already greater than its required capital.
- The My Bots decision banner now models the future automated flow: `current live deal -> next ranked strategy -> final revalidation -> future execution`.
- Direct live execution remains locked.

## Paper Evidence Maturity

Paper strategies now use explicit forward-test maturity:

- Starting: 0 closed deals
- Early forward test: 1–4 closed deals
- Building evidence: 5–19 closed deals
- Meaningful forward evidence: 20+ closed deals

The dashboard reports elapsed forward-test time, current open-deal count and completed paper deals rather than simply saying `Building evidence`.

## Publication Quality

A delayed GitHub/website publication is no longer a live-trading fault when the local V70 resident runtime and KuCoin live heartbeat are current.

The dashboard presents this as `Website snapshot delayed` while live P/L, orders, paper bots and portfolio truth continue from local Runtime State.


## Release/Runtime Metadata Separation

V70 permanently separates software release identity from mutable runtime producer metadata.

Strict release identity:
- `VERSION`
- `app/release.json`
- `config.json` when it declares the app version
- `docs/version.json`
- optional strict release diagnostics metadata

Mutable runtime/publication JSON:
- may temporarily report the CRM version that last generated the snapshot;
- an older producer version is reported as `RUNTIME METADATA REFRESH REQUIRED`;
- it does not invalidate a successfully installed newer CRM release;
- a snapshot claiming a future CRM version remains a hard validation error.

This prevents stale runtime snapshots such as paper portfolio, KuCoin service status,
research status, health outputs or managed-bot state from blocking future software upgrades.


## Idempotent Windows Resident Service Setup

The V70 installer now treats an absent `CryptoRegimeManager-ResidentRuntime`
scheduled task as the normal first-install state.

- task existence is checked before `/End`, `/Change` or `/Delete`;
- first installation no longer fails because the resident task does not exist yet;
- task creation is verified before startup;
- runtime health is verified after startup;
- rollback removes any partially-created resident task and restores the V69 Local Agent
  and Research Worker scheduled tasks;
- the same helper pattern is intended for future V71+ installers.


## Completion-aware installation

V70 may already be present in Git/`VERSION` when a previous installation passed all
source validation and pushed the V70 commit but failed later while creating the
Windows resident task. The installer therefore supports both:

- `69.0.0 -> 70.0.0` full upgrade; and
- `70.0.0 -> 70.0.0` completion/repair mode.

Completion mode reapplies the final V70 service setup idempotently, validates the
repository, commits only any missing V70 completion changes, creates/verifies the
resident task and confirms the resident heartbeat. It does not force a downgrade
to V69 merely because the source release already succeeded.


## Installer Doctor & Transactional Upgrade Engine

V70 now embeds a reusable installer subsystem intended for all future CRM releases.

### Pre-install Doctor
Before any source/runtime mutation it verifies:
- installed version and Git repository;
- semantic source cleanliness;
- runtime-only and untracked generated output;
- LF/CRLF-only noise;
- Python, PowerShell and Task Scheduler availability;
- CRM_Data write access;
- origin/main fetch access;
- resident scheduled-task state;
- a real temporary Windows scheduled-task create/query/run/delete probe.

Known safe conditions are repaired automatically. Unknown semantic source changes remain blockers.

### Persistent transaction state
`C:\Crypto\CRM_Data\Installer\upgrade_state.json` records:
`PRECHECK -> BACKUP_CREATED -> RUNTIME_PAUSED -> CANDIDATE_APPLIED -> VALIDATED -> SERVICE_TESTED -> SOURCE_COMMITTED_AND_PUSHED -> RESIDENT_STARTED -> ACCEPTANCE_PASSED -> COMPLETE`.

A future installer can therefore detect and resume a partial prior upgrade rather than infer state only from VERSION.

### Deployment rehearsal before commit
The candidate V70 runtime is validated and then run through a temporary resident scheduled task before source commit/push. Task Scheduler/service provisioning failures are therefore found before publication.

### Python-native Windows task management
PowerShell is no longer the critical Task Scheduler logic engine. Python executes `schtasks.exe` and classifies return codes directly, so expected `task not found` output cannot become a fatal PowerShell `NativeCommandError`.

### Final acceptance
Installation succeeds only after source validation, resident task creation, resident/KuCoin health, Git alignment and runtime/source separation pass. Legacy schedules remain available disabled for rollback.

### Standalone repair
`TROUBLESHOOT_INSTALL_V70.cmd` runs the same Installer Doctor and applies only recognised safe repairs.


## Installer Doctor V7 regression fix

V7 retains the V6 Installer Doctor architecture and fixes the validation failure observed during completion:
- the legacy resident-task idempotency tests now validate the Python-native `resident_task_manager` contract instead of removed PowerShell helper names;
- duplicate V70 test paths are removed before pytest execution;
- the Windows launcher title no longer contains an unescaped ampersand;
- regression coverage prevents either issue returning in future installer revisions.

No trading permissions or execution controls are changed by this installer revision.

## Installer Doctor V8 regression fix

V8 corrects the final V7 validation boundary error. `Install_V70.cmd` belongs to the
downloadable installer package and is intentionally not copied into the CRM source
repository. Repository pytest validation therefore no longer assumes that launcher
exists under `C:\Crypto\Projects`. The launcher safety check now runs directly from
`install_v70.py` against the downloaded package before any project mutation.

## Installer Doctor V9 full-suite compatibility fix

V9 updates the pre-existing V70 resident-runtime regression test to follow the final
architecture: `SETUP_CRM_RESIDENT.ps1` is a thin wrapper and
`scripts/resident_task_manager.py` owns disabling the LocalAgent and ResearchWorker
legacy scheduled tasks. This preserves the safety requirement while testing the
component that actually implements it.

## Installer Doctor V11 — Background Process Sanitation

V11 adds a pre-install isolation gate aimed at recurring visible Windows console
workers and competing runtime writers. After CRM scheduled tasks are paused, the
installer enumerates Windows processes and stops only command lines that both belong
to C:\Crypto\Projects and match known CRM worker/service markers.

The resident task manager now explicitly owns retirement of the legacy Local Agent
and Research Worker scheduled tasks. Installation records BACKGROUND_SANITIZED before
source synchronization.

## Installer Doctor V13 — Resident Startup Diagnostics & Safe KuCoin Recovery

V13 replaces the generic candidate heartbeat timeout with staged startup diagnosis.

It now distinguishes:
- resident process/heartbeat failure;
- missing KuCoin live-data heartbeat;
- stale KuCoin live-data heartbeat;
- healthy resident + healthy KuCoin live truth.

When the resident is alive but KuCoin truth is stale, the installer records
`C:\Crypto\CRM_Data\Installer\resident_startup_diagnostics.json`, removes stale
maintenance/stop flags, stops only an identified CRM KuCoin live worker, and starts
the KuCoin live worker directly in hidden recovery mode. No exchange orders are
placed and native execution remains locked.

The installer only rolls back after this safe recovery transaction fails.

## Installer Doctor V15 — Candidate Fixture Bootstrap

V15 adds a pre-pytest fixture normalization phase inside the isolated clean-room
candidate. Known deterministic outputs are regenerated through their owning engines.
Remaining release/build/test fixtures that still declare an older CRM version are
migrated to the canonical candidate version. Runtime-only snapshots are not bulk
rewritten and remain excluded from software release identity.

A fixture consistency scan runs before pytest and refuses to start the full suite if
any directly-tested release fixture still disagrees with `VERSION`.

## Installer Doctor V16 — Candidate Execution Context Fix

V16 fixes the clean-room resident rehearsal boundary. Candidate-only modules are now
executed explicitly from `C:\Crypto\CRM_Data\Installer\Candidate` rather than being
resolved through the production Python module path.

The rehearsal now:
- verifies required candidate scripts exist before starting;
- sets `cwd`, `PYTHONPATH` and `CRM_PROJECT_PATH` to the candidate worktree;
- points the temporary scheduled task directly at the candidate `RUN_CRM_RESIDENT.ps1`;
- runs `resident_startup_diagnostics.py` and `crm_resident_control.py` by absolute
  candidate file path;
- re-enters maintenance mode after rehearsal before source promotion.

This prevents `No module named scripts.resident_startup_diagnostics` before production
promotion and keeps the clean-room validation boundary intact.

## Installer Doctor V17 — Direct Candidate Rehearsal

V17 removes Windows Task Scheduler from clean-room candidate rehearsal entirely.
The validated candidate resident is launched directly as a hidden subprocess from
the candidate worktree with candidate-specific `cwd`, `PYTHONPATH` and
`CRM_PROJECT_PATH`.

The installer validates resident and KuCoin live truth, stops the candidate cleanly,
and only uses Task Scheduler later when provisioning the permanent validated
production resident. This removes a Windows scheduling dependency from candidate
validation while retaining the permanent resident task architecture.

## Installer Doctor V18 — Silent Startup & KuCoin First-Heartbeat Gate

V18 keeps candidate and recovery child processes hidden and treats process creation as
only the first startup stage. Candidate acceptance now requires a genuinely fresh
KuCoin runtime artifact after worker launch. A bounded first-heartbeat supervisor records
startup progress in `CRM_Data\Installer\kucoin_first_heartbeat.json` and fails with the
specific `first_heartbeat` stage if live truth is not produced.

Task Scheduler remains outside candidate rehearsal; permanent scheduling occurs only
after validated production promotion.

## Installer Doctor V19 — Runtime State Manager Repair & Verified KuCoin Startup

V19 repairs the deterministic live-service startup defect identified by V18 diagnostics:
`runtime_state_manager.py` called `parse_args()` on the `_SubParsersAction` returned by
`add_subparsers()` instead of on the root `ArgumentParser`.

Before the full candidate test suite, V19 now:
- repairs the parser idempotently;
- verifies the root parser owns `parse_args()`;
- executes `runtime_state_manager --help`;
- executes `runtime_state_manager prepare --help`;
- then runs the complete clean-room suite.

The KuCoin first-heartbeat gate now checks canonical `Runtime\State` before legacy
locations. The resident also includes a three-failures-per-minute circuit breaker so a
deterministic child crash is surfaced instead of restarted indefinitely.


## Installer Doctor V20 — KuCoin Candidate Context Isolation Repair

V19 proved the runtime-state parser repair succeeds inside the clean-room candidate, but the KuCoin worker log still resolved to `C:\Crypto\Projects`. V20 closes that execution-context leak.

- `RUN_KUCOIN_LIVE_SERVICE.ps1` now resolves the active application root from `CRM_PROJECT_PATH`, falling back to its own script directory only for normal production/manual launch.
- The launcher exports that same root to `PYTHONPATH` before runtime preparation and worker start.
- Candidate rehearsal supplies the exact `CRM_PYTHON_EXECUTABLE` used by the installer.
- Runtime-state preparation and `scripts.kucoin_live_data_service` are therefore guaranteed to execute from the same candidate source tree during rehearsal.
- Startup sanitation matches the active project context rather than hard-coding `C:\Crypto\Projects`.
- Existing first-heartbeat, fresh-KuCoin-truth, read-only safety, clean-room validation and transactional rollback gates remain mandatory.
