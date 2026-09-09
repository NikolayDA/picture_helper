[Deutsch](../../../RECOMMENDATIONS.md) · **English** · [Español](../es/RECOMMENDATIONS.md) · [Français](../fr/RECOMMENDATIONS.md) · [Українська](../uk/RECOMMENDATIONS.md) · [简体中文](../zh/RECOMMENDATIONS.md)

# Code Analysis & Ranked Recommendations: BgRemover

## Rating Scale

| Symbol | Priority | Meaning |
|--------|----------|---------|
| 🔴 | Critical | Bugs, crashes, or data loss |
| 🟠 | High | Clear impact on reliability or maintainability |
| 🟡 | Medium | Useful improvement for quality, readability, or testability |
| 🟢 | Low | Optional polish or process improvement |

## Current Status (2026-09-09, v2.9.0 published, open inventory fully audited)

**Daily audit 2026-09-09 (state `dd6c572`):** All 56 open issues reviewed; the
fifteen new ones (#1031–#1045) are now in the triage table. What is substantively new
is process epic #1032 with eleven work packages: the window `85eeea4^..dd6c572` holds
156 mainline commits, 28 of them (18 %) consisting solely of triage upkeep – that is,
of the very table this entry is updating (#1032 counts 27; the difference is one commit
that also touches the archive). #1040 wants to abolish it together with the
live-check workflow; until then it remains the valid contract, and the live check has
been red since 2026-09-08 for exactly that reason (run 34282863300) without a single
code change. The only new finding that affects the evidence base is #1031 (priority
0): a stale non-editable `bgremover` makes subprocess tests started by file path
measure foreign code – the dangerous direction being a test that turns **green** that
way. #1044 (test gap for #1004/#1005, coverage 93 %) and #1045 (missing `#1023`
reference in the CHANGELOG) are two small PRs that can be done immediately. No new
product defect and no 🔴 finding.

**Release assessment: v2.10.0 is recommended.** Since `v2.9.0` (2026-08-29) there are
83 first-parent commits, twelve of them touching product code. `[Unreleased]` therefore
carries a full minor scope: EufyMake target profile v2 with the Studio 4.3.3 preflight
(#681/#691), the confirmed flatbed size 335 × 420 mm (#971), project DPI as PNG `pHYs`
(#996), the Qt jump to 6.11 (#994, about ten advisories including CVE-2025-10728 and
CVE-2025-10729) and four 3D fixes (#1002, #1004, #1023, #1024), of which #1024 repairs a
segmentation fault. Two reasons argue against waiting further: the security effect of the
Qt jump only reaches users with the artifact, and the raised glibc floor (aarch64 2.39,
x86_64 2.34) is a platform change that deserves to be published and announced. The COLOR
tone engine (#693 ff.) is **not** a reason to wait – it is the scope after this one.
Before the candidate build (item 1 of #1045, the `#1023` reference in the CHANGELOG, is
done): runbook steps 1/2 via `scripts/prepare_release.py 2.10.0`, including
the editorial `TODO(release)` gaps (`NOTES-01`). The same run also supplies the still
missing end-to-end evidence for #914 and #918.

**EufyMake #681/#687–#691:** The reproducible set contains 42 single fixtures and seven unchanged real export packages (schema 5). The 29 mandatory print-free import cells are complete both in the historical Studio 4.2.2 baseline and in the full 4.3.3 regression run; I-09 (`.empf`) remains non-blocking.
All 13/13 prepared native projects load and twelve active projects reach Preview. This proves the GUI and project preparation, but no physical HEIGHT, size, gloss, or registration effect. The E1 measurements for #688–#690 and #687's closeout review remain open.

Unchanged and closed: **N1/N2/N4/N5/N6/N7/N8**, **O1–O8**, everything completed since **2026-06-25**, releases v2.7.0–v2.9.0, epic #741 with its eleven sub-issues, epic #805 with #806–#811, #817, and #821; newly closed since the last sync: #943 (PR #944), #692 (PR #947), plus the ANLEITUNG review #963 with #964–#966, #968, and #969 (PR #972) and #967 (PR #973), plus the test-suite audit #949 (PR #977) and the PDF guard #974 (PR #979), plus the staged heartbeat escalation #958 (PR #981), plus the documentation sync #982 (PR #984), plus the label-carrier follow-up #975 (PR #986), plus the triage-table follow-up #995 (PR #997), plus the dead-code removal #992/#993 (PR #998), plus the Qt upgrade #994 (details: Previous Rounds).

Open items: one row per issue in the triage table below. Neither the count nor the rows are maintained by hand as of #821 – `scripts/recommendations_live_check.py --write` updates all six versions from the GitHub live state, while the rating columns stay editorial work.

## Open GitHub Issues — Triage Status

| # | Title | Relevance | Complexity | Recommended model (effort) | Next step |
|---|-------|-----------|------------|------------------------------|-----------|
| [#681](https://github.com/NikolayDA/picture_helper/issues/681) | [Epic] EufyMake target profile – validate Height/Gloss/mm-DPI | 🟠 High (correctness of the main export target) | 🔴 High (5 sub-issues, needs physical hardware) | – (epic) | Profile integration and all 29 mandatory print-free cells are done; I-09 is non-blocking. Hardware tests #688–#690 and closeout review remain |
| [#687](https://github.com/NikolayDA/picture_helper/issues/687) | Assumption inventory, manufacturer sources, test matrix | 🟠 High (binding foundation for #688–#691) | 🔴 High (repository material complete; remainder needs real hardware) | – (no agent; needs real EufyMake hardware) | Blocked (external) – 17/18 acceptance criteria and all 29 mandatory import cells are done. Only closeout review after #688–#690 remains |
| [#688](https://github.com/NikolayDA/picture_helper/issues/688) | Validate HEIGHT bit depth/semantics on real hardware | 🟠 High (directly affects relief height) | 🔴 High (physical printer, fixtures, measurement log) | – (no agent; needs real EufyMake hardware) | Blocked (external) – including the direct I-14 filter/normalization pair, all preflights are complete; physical precision, filtering, relief, and mm measurements remain |
| [#689](https://github.com/NikolayDA/picture_helper/issues/689) | Validate mm/DPI, target size, positioning contract | 🟠 High (print size/registration) | 🔴 High (physical measurements, control motifs) | – (no agent; needs real hardware) | Blocked (external) – the Studio contract including crop and HEIGHT aspect-ratio handling is proven. Only physical registration, measurements, and tolerances remain |
| [#690](https://github.com/NikolayDA/picture_helper/issues/690) | Validate gloss/clear-coat semantics | 🟡 Medium (gloss is already flagged "experimental" in code) | 🔴 High (physical prints, material consumption) | – (no agent; needs real hardware) | Blocked (external) – native `Gloss Varnish` ink mode is preflighted; cell-specific registration and physical polarity, intensity, and material effect remain |
| [#691](https://github.com/NikolayDA/picture_helper/issues/691) | Integrate versioned target profile into validator/writer/dialog/docs | 🟠 High (hardens the production export path) | 🟢 Low for release-critical remainder; 🔴 hardware for closeout | Sonnet, medium + later hardware | Release-ready implementation – profile v2 is the default for Studio 4.3.3/firmware 4.0.9; profile v1 remains frozen and selectable. After #688–#690, review only the evidence status and create another profile version for new semantics |
| [#682](https://github.com/NikolayDA/picture_helper/issues/682) | [Epic] COLOR tonal/grayscale engine | 🟡 Medium-high (roadmap foundation for laser, not an active bug) | 🔴 High (4 remaining sub-issues: core→UI→integration→acceptance) | – (epic) | In progress – ADR #692 is approved; the core #693 comes next |
| [#693](https://github.com/NikolayDA/picture_helper/issues/693) | Qt-free core: histogram/grayscale/levels/gamma | 🟡 Medium-high | 🟡 Medium (extends `color_ops.py`, well isolated and testable) | Sonnet, high | Ready to start – ADR #692 (PR #947) supplies the data contract; implement and test the core against its formulas |
| [#694](https://github.com/NikolayDA/picture_helper/issues/694) | Live preview + UI for histogram/levels/gamma | 🟡 Medium | 🟡 Medium-high (Qt UI, debounce/generation guard like the height preview) | Sonnet, high | Blocked – waits on core #693 |
| [#695](https://github.com/NikolayDA/picture_helper/issues/695) | Layer/selection/history/project integration | 🟡 Medium | 🟠 High (many state transitions: undo/redo, selection, dirty state) | Opus, high | Blocked – waits on #693/#694 |
| [#696](https://github.com/NikolayDA/picture_helper/issues/696) | Performance/E2E/docs/laser-interface acceptance | 🟡 Medium (closeout gate, not a new feature) | 🟠 High (benchmark suite, E2E, docs, adapter contract) | Opus, high | Blocked – closeout issue after #695 |
| [#882](https://github.com/NikolayDA/picture_helper/issues/882) | [Epic] BgRemover in the Mac App Store | 🟡 Medium-high (new distribution channel, not a current product defect) | 🔴 High (licensing, sandbox, packaging, store, release governance) | – (Epic) | Blocked – decide #883 first, treating Qt/code licensing and the model artifact's unresolved provenance/rights separately |
| [#883](https://github.com/NikolayDA/picture_helper/issues/883) | [MAS] Licensing strategy: PySide6 vs. Riverbank and relicensing | 🟠 High (hard blocker for all technical MAS work) | 🔴 High (license/owner decision, possible Qt port, residual risk) | Opus, high + owner/legal review | Ready – write ADR/owner decision and prove source, license, and redistribution rights for the exact `u2net.onnx`, or choose a replacement model |
| [#884](https://github.com/NikolayDA/picture_helper/issues/884) | [MAS] Apple Developer Program enrollment | 🟠 High (blocks certificates and store access) | 🟢 Low (manual account/payment step) | – (no agent; account holder) | Blocked (external) – settle account type, enrollment/2FA, and renewal; a free app needs no Paid Apps Agreement, but traders may still need payment-account details (#904) |
| [#885](https://github.com/NikolayDA/picture_helper/issues/885) | [MAS] Signing identities, App ID, and provisioning profile | 🟠 High (prerequisite for a signed store build) | 🟡 Medium (owner secrets plus bundle-ID/packaging contract) | – (no agent; account holder/admin) | Blocked – waits for #884; then create certificates, explicit App ID/profile, and freeze the bundle ID |
| [#886](https://github.com/NikolayDA/picture_helper/issues/886) | [MAS] Define and apply App Sandbox entitlements | 🟠 High (mandatory store and runtime prerequisite) | 🟠 High (all Mach-O files, packaging and hardware evidence) | Opus, high | Blocked – waits for licensing decision #883; then implement minimal entitlements and artifact/hardware tests |
| [#887](https://github.com/NikolayDA/picture_helper/issues/887) | [MAS] Sandbox-compatible inference child process | 🟠 High (core AI function must run in the store build) | 🔴 High (spawn/helper signing, two-key rule, real sandbox) | Opus, high | Blocked – waits for #886; decide re-exec/helper and prove the AI self-check on hardware |
| [#888](https://github.com/NikolayDA/picture_helper/issues/888) | [MAS] Security-scoped bookmarks for files and directories | 🟠 High (Recent Files and Quick Save otherwise break after restart) | 🟠 High (persistent grants, images/projects/directories, channel gating) | Opus, high | Blocked – waits for #886; implement the bookmark contract and test the sandboxed restart case |
| [#889](https://github.com/NikolayDA/picture_helper/issues/889) | [MAS] Sandbox-safe writes and EufyMake export | 🟠 High (save/export paths and potential data integrity) | 🔴 High (atomicity across multiple paths and Powerbox grants) | Opus, high | Blocked – waits for #886; design grant-safe atomic writes/extensions/target selection and test on hardware |
| [#890](https://github.com/NikolayDA/picture_helper/issues/890) | [MAS] AI model cache in the sandbox container | 🟡 Medium (deterministic model path in the store channel) | 🟡 Medium (isolated path contract plus migration decision) | Sonnet, high | Blocked – waits for #886 and couples to #893; set `U2NET_HOME` explicitly and decide migration |
| [#891](https://github.com/NikolayDA/picture_helper/issues/891) | [MAS] Distribution-channel flag and update-check gating | 🟠 High (App Store rule 2.4.5, no self-updates) | 🟠 Medium-high (central flag across menu, settings, workers, hooks) | Sonnet, high | Blocked – waits for #883; then add the channel contract and negative-test MAS network/UI paths |
| [#892](https://github.com/NikolayDA/picture_helper/issues/892) | [MAS] Remove AiInstallDialog and bundle the AI backend | 🟠 High (no installing executable code in the store) | 🟡 Medium (channel gating plus binding packaging test) | Sonnet, high | Blocked – waits for #891; gate dialog/menu and prove bundled rembg/onnxruntime |
| [#893](https://github.com/NikolayDA/picture_helper/issues/893) | [MAS] Bundle u2net or download it at first launch | 🟠 High (review risk and AI functionality) | 🟠 High (product/review decision, packaging or new i18n flow) | Opus, high | Blocked – before choosing a variant, prove the exact model's source/license/redistribution rights through #883 or choose a replacement; then #890/#891 and sandbox verification |
| [#894](https://github.com/NikolayDA/picture_helper/issues/894) | [MAS] Choose Briefcase vs. py2app packaging | 🟠 High (determines technical channel viability) | 🟠 High (open-ended signed sandbox/upload spike) | Opus, high | Blocked – waits for #883; run Briefcase spike, test py2app fallback, record ADR |
| [#895](https://github.com/NikolayDA/picture_helper/issues/895) | [MAS] onedir app, inside-out signing, Qt store cleanup | 🟠 High (central executable store build) | 🔴 High (all binaries, Qt, provisioning, upload validation) | Opus, high | Blocked – after #885/#886/#894, implement build, choose fail-closed `AppTransaction` or receipt validation, and validate without ITMS errors |
| [#896](https://github.com/NikolayDA/picture_helper/issues/896) | [MAS] Info.plist and complete icon set | 🟡 Medium-high (store metadata and platform contract) | 🟡 Medium (required keys, architecture target, deterministic assets) | Sonnet, high | Blocked – waits for #895; decide minimum OS/architecture/document types and add plist/icon tests |
| [#897](https://github.com/NikolayDA/picture_helper/issues/897) | [MAS] Signed productbuild PKG and Transporter upload | 🟠 High (submittable store artifact) | 🟠 High (second signature, build automation, manual first upload) | Opus, high + account holder | Blocked – waits for #885/#895/#896; build reproducible PKG and capture delivery log |
| [#898](https://github.com/NikolayDA/picture_helper/issues/898) | [MAS] Release CI, six-artifact contract, and PKG scan | 🟠 High (fail-closed release integrity) | 🔴 High (CI secrets, contract, unpacker, malware/path scan) | Opus, high | Blocked – waits for #895/#897; extend MAS leg, contract, payload scan, and regression tests together |
| [#899](https://github.com/NikolayDA/picture_helper/issues/899) | [MAS] Sandboxed acceptance smokes on real hardware | 🟠 High (binding runtime evidence for core paths) | 🔴 High (PKG, AI spawn, Powerbox, 3D, evidence schema) | Opus, high + macOS hardware | Blocked (external) – after #898 run on self-hosted ARM64; add valid and, where reproducible, invalid app-download evidence to the schema |
| [#900](https://github.com/NikolayDA/picture_helper/issues/900) | [MAS] TestFlight beta for macOS | 🟠 High (early review and foreign-device evidence) | 🟡 Medium (manual ASC/tester coordination) | – (no agent; account holder and tester) | Blocked (external) – waits for #897/#901; verify AI, files, and 3D on another device |
| [#901](https://github.com/NikolayDA/picture_helper/issues/901) | [MAS] App Store Connect record and six-language metadata | 🟠 High (name, listing, submission prerequisite) | 🟠 Medium-high (owner steps plus six localized metadata sets) | Sonnet, high + account holder | Blocked – waits for #884/#885; reserve name, version/upload texts, set rating/storefronts |
| [#902](https://github.com/NikolayDA/picture_helper/issues/902) | [MAS] 16:10 store screenshot set | 🟡 Medium-high (required listing material) | 🟡 Medium (reproducible formats, alpha check, language decision) | Sonnet, high | Blocked – waits for representative build #895; extend automation for store resolutions and verify the set |
| [#903](https://github.com/NikolayDA/picture_helper/issues/903) | [MAS] Privacy Policy and App Privacy answers | 🟠 High (mandatory store and in-app requirement) | 🟡 Medium (policy, hosting, i18n link, owner questionnaire) | Sonnet, high + owner | Blocked – waits for channel/model decisions #891/#893; host/link policy and prove “Data Not Collected” |
| [#904](https://github.com/NikolayDA/picture_helper/issues/904) | [MAS] EU DSA status, legal notice, and GPSR review | 🟠 High (EU storefronts and public legal duties) | 🟠 Medium-high (owner classification, verification, legal risk) | – (no agent; owner/legal review) | Blocked (external) – after #884 document trader status, public contact details, any required payment-account details, and DDG/GPSR ownership/follow-up |
| [#905](https://github.com/NikolayDA/picture_helper/issues/905) | [MAS] Extend release governance for the store channel | 🟠 High (prevents a channel outside the fail-closed contract) | 🟠 High (runbook, checklist, contract, path policy, six changelogs) | Opus, high | Blocked – accompanies #898/#899; raise all governance contracts/tests to six artifacts before submission |
| [#906](https://github.com/NikolayDA/picture_helper/issues/906) | [MAS] Initial submission and review round | 🟠 High (manual publication gate) | 🔴 High (many dependencies, residual risks, Apple communication) | – (no agent; release owner) | Blocked (external) – after #896/#897/#899/#901–#905 preflight including app-download validation, submit, and record results/follow-ups |
| [#907](https://github.com/NikolayDA/picture_helper/issues/907) | [MAS] Operations plan for renewal, updates, and channels | 🟡 Medium-high (long-term availability and channel separation) | 🟡 Medium (runbook, ownership, reminders, channel matrix) | Opus, high + owner | Blocked – draft early, finalize after #906; bind renewal/update/web routines into operations |
| [#914](https://github.com/NikolayDA/picture_helper/issues/914) | [Epic] Release process: runners, automated evidence, main freeze | 🟠 High (release operations; implementation largely done) | 🟢 Low (one event-bound proof) | – (epic) | Almost done – the first scheduled dry run on 2026-09-03 completed successfully (run 33737226157); only the end-to-end proof including #918 at the next real release remains |
| [#918](https://github.com/NikolayDA/picture_helper/issues/918) | Release ref instead of a main freeze (ADR + fail-closed safeguards) | 🟠 High (`main` stays mergeable during a release) | 🟢 Low (code, docs, and ruleset are in place) | – (no agent; next release run) | Blocked (external) – reopened on 2026-08-31 after its completion check; PR #936 and the active ruleset 21941216 are documented, only a run whose post-release acceptance demonstrably started on `release/vX.Y.Z` is missing |
| [#939](https://github.com/NikolayDA/picture_helper/issues/939) | Operations: self-hosted runners (heartbeat alert channel) | 🟡 Medium (operations channel, no product code) | 🟢 Low (observation only) | – (no agent; repo owner) | Permanently open – do not close (`RUNNER_HEARTBEAT_ISSUE`); the FAIL of 2026-08-31 was the planned alert-path test, and the cleanup step is done (scheduled run 33496675995 green, x86_64 skipped, Mac and Pi passed) |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | Restore OpenAI quota for the manual Codex security check | 🟢 Low (blocks only an optional manual scan) | 🟢 Low (purely operational, no code) | – (no agent; repo owner: billing) | Blocked (external) – the last run (29233060507, 2026-07-13) proves no successful scan; billing/quota still unresolved |
| [#1043](https://github.com/NikolayDA/picture_helper/issues/1043) | Trim `docs/PROZESSE_UML.md` down to the happy path | 🟡 Medium (773 lines and 30 diamonds; duplicates the runbook's restart matrix) | 🟡 Medium (four diagrams plus references into the runbook and the ADRs) | Sonnet, high | Blocked – the last work package; waits for #1040, #1035, #1036, #1037 and #1041 |
| [#1042](https://github.com/NikolayDA/picture_helper/issues/1042) | Switch the analysis commands (`.claude/commands/analyze-*`) to GitHub issues | 🟡 Medium (analysis results land where the open inventory is kept) | 🟢 Low (five command files) | Sonnet, medium | Blocked – waits for #1040; recommended in the same PR |
| [#1041](https://github.com/NikolayDA/picture_helper/issues/1041) | `make pr-ready`: detect drift duties from the diff | 🟡 Medium (replaces six manual decision diamonds with one command) | 🟠 Medium-high (new strictly typed script, NUL-separated paths, renames, Python 3.10 matrix) | Opus, high | Blocked – waits for #1040; sensible only after #1036 and #1037, because two duties then disappear entirely |
| [#1040](https://github.com/NikolayDA/picture_helper/issues/1040) | Remove the recommendations live triage (table, status, workflow, guards) | 🟠 High (the epic's biggest lever: 2,123 lines of mechanics and no more red runs from an issue state change) | 🟡 Medium (six language versions, script, workflow, 42 test functions in three files, leftover references in `TESTING.md` and `docs/PROZESSE_UML.md`) | Opus, high | Blocked – waits for #1033; recommended atomically together with #1042 |
| [#1039](https://github.com/NikolayDA/picture_helper/issues/1039) | Owner script for the release dispatches instead of copying run IDs by hand | 🟡 Medium (manual work in the release flow, no product risk) | 🟡 Medium (run-ID/artifact resolution via the API, strictly typed, network-dependent to test) | Sonnet, high | Deferred – the epic deliberately puts this after the next real release; until then the manual path is the reference for #914/#918 |
| [#1038](https://github.com/NikolayDA/picture_helper/issues/1038) | Path filters for CodeQL, dependency audit and license check on pull requests | 🟢 Low (saves CI time, no quality or risk gain) | 🟢 Low (three `paths-ignore` blocks) | Sonnet, medium | Ready for PR – uncritical because none of the three runs is a required check (the only required check is `Lightweight PR checks`) |
| [#1037](https://github.com/NikolayDA/picture_helper/issues/1037) | Path policy: unknown paths warn instead of blocking | 🟠 High (the gate runs on every PR; 22 policy changes in the measured window) | 🟡 Medium (policy version 17→18, ADR addendum, `prepare_release.py`, freeze document, tests) | Opus, high | Ready for PR – the release gates stay untouched: classification is unchanged, only the block goes away. Evidence via the next dry run |
| [#1035](https://github.com/NikolayDA/picture_helper/issues/1035) | Repository settings: squash-only, auto-delete branches, one automatic reviewer | 🟡 Medium (less merge and review noise, no product impact) | 🟢 Low (settings and connector configuration, no code) | – (no agent; repo owner) | Ready to start (owner) – the live comparison of 2026-09-09 confirms all four current values; the `chatgpt-codex-connector` auto-review setting is only visible in the connector configuration |
| [#1034](https://github.com/NikolayDA/picture_helper/issues/1034) | Issue forms for the desktop app instead of GitHub's default templates | 🟡 Medium (report quality; browser/smartphone fields do not fit a PyQt6 app) | 🟢 Low (two YAML forms plus `config.yml`) | Sonnet, medium | Ready for PR – independent of #1033/#1040 and can be slotted in at any time |
| [#1033](https://github.com/NikolayDA/picture_helper/issues/1033) | Move triage content into the issues, introduce priority/blocker labels | 🟠 High (hard prerequisite for #1040; otherwise the curated texts are lost) | 🟡 Medium (no code, but every open issue needs a label and 41 need a takeover comment) | Sonnet, high | Ready to start – pure issue curation via the API, not a PR; cutover inventory on 2026-09-09 is 56 open issues, not the 54 noted in the issue |
| [#1032](https://github.com/NikolayDA/picture_helper/issues/1032) | [Epic] Process slimming: triage moves to GitHub, fewer drift duties | 🟠 High (28 of 156 mainline commits in the measured window are pure triage upkeep) | 🔴 High (eleven work packages #1033–#1043 with order and dependencies) | – (epic) | In progress – order #1033 → #1040 (+#1042) → #1041/#1043; #1031 takes priority 0 ahead of it |

### Recommended Next

1. **#1031** (priority 0) – the provenance check in the SessionStart hook; without it a
   green subprocess test may have checked old code.
2. **#1044** and **#1045** – done: the #1004/#1005 test gap in
   `tests/test_preview3d_controller.py` and the missing `#1023` reference in six
   CHANGELOG versions.
3. **Start v2.10.0** – the scope is in `[Unreleased]`; runbook steps 1/2 via
   `scripts/prepare_release.py 2.10.0`. That run also closes the outstanding end-to-end
   evidence for #914 and #918.
4. **#1033 → #1040 (+#1042)** – start the process slimming; #1034, #1035, #1037 and
   #1038 are independent and can be slotted in at any time (#1036 is done).
5. **#693** (Qt-free core) – ADR #692 is approved; #694, #695 and #696 follow in that
   order.
6. **#883** – decide Qt/code licensing and prove rights/provenance for the exact
   `u2net.onnx`, or choose a clearly licensed replacement model.
7. After device/material approval, perform the remaining physical measurements for
   **#689** together with the remainder of #687, #688 and #690; then review profile v2's
   evidence status. Profile v1 stays frozen, and new or contradictory semantics require
   another profile version.

## Previous Rounds

Detailed protocols since v2.2: [RECOMMENDATIONS-2026-v2.2-v2.9.en.md](../../history/RECOMMENDATIONS-2026-v2.2-v2.9.en.md).

Historical findings and work logs (rounds 1–5): [RECOMMENDATIONS-2026-pre-v2.2.en.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.en.md).
