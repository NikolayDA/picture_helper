[Deutsch](../../../RECOMMENDATIONS.md) · **English** · [Español](../es/RECOMMENDATIONS.md) · [Français](../fr/RECOMMENDATIONS.md) · [Українська](../uk/RECOMMENDATIONS.md) · [简体中文](../zh/RECOMMENDATIONS.md)

# Code Analysis & Ranked Recommendations: BgRemover

## Rating Scale

| Symbol | Priority | Meaning |
|--------|----------|---------|
| 🔴 | Critical | Bugs, crashes, or data loss |
| 🟠 | High | Clear impact on reliability or maintainability |
| 🟡 | Medium | Useful improvement for quality, readability, or testability |
| 🟢 | Low | Optional polish or process improvement |

## Current Status (2026-09-03, v2.9.0 published, open inventory fully audited)

**Daily audit 2026-09-02 (state `91b32b4`):** All 42 open issues were checked
against code, merges, comments, and—within the Mac App Store epic—current
primary sources. Status corrections are now recorded in #681, #688, #691,
#682/#693, #914/#918, and #949. New substantive findings: the separate
`u2net.onnx` artifact is not proven Apache-2.0 (#883/#893), Apple may require
payment-account details from traders even for a free app (#884/#904), and
app-download validation must be explicitly chosen and tested in #895/#899/#906.
No new product defect and no 🔴 finding.

**Follow-up audit 2026-09-03 (state `e7c379d`):** New PRs #955–#957 were
checked against the open items. PR #956 deliberately corrected the EufyMake
profile's bad evidence reference within the still-unreleased v1 and added
snapshot/bundle guards, resolving the former release-critical #691 item. #955
only affects test-suite documentation and #957 release scripts; neither changes
the EufyMake empirical findings.

**Release assessment: no candidate started yet.** Since `v2.9.0` (2026-08-29)
there are 34 mainline commits at the audited `e7c379d` state. With PR #953 (versioned EufyMake target profile,
16-bit HEIGHT default, profile and X/Y DPI display in the dialog, manifest
provenance) `[Unreleased]` holds its first user-visible entry; everything else
is release automation, documentation, and governance. Whether **v2.10.0** ships
with #953 alone or together with the COLOR tone engine (#693/#694 from epic
#682, ADR #692) is an owner decision. PR #956 corrected the bad evidence
reference with an explicit v1 decision and Golden/bundle guards. #691
therefore adds no release blocker; the normal release gate remains authoritative.

**EufyMake #681/#687–#691:** PRs #948, #951–#953, #956, and #959–#961 are merged. Schema 5 contains 42 single fixtures and seven unchanged real export packages. All 29 mandatory print-free import cells are complete in Studio 4.2.2. In addition to native 8-/16-bit HEIGHT, COLOR/HEIGHT crop coupling, and `Gloss Varnish`, the run proves that different pixel dimensions with the same aspect ratio are accepted while a different HEIGHT aspect ratio is rejected with `Depth image ratio does not match the original image`. I-14 adds a directly generated, non-prefiltered 256/128-pixel edge/impulse pair; both variants passed import preflight. I-09 (`.empf`) remains non-blocking. Only physical E1 measurements for #688–#690 and #687's closeout review remain.

Unchanged and closed: **N1/N2/N4/N5/N6/N7/N8**, **O1–O8**, everything completed since **2026-06-25**, releases v2.7.0–v2.9.0, epic #741 with its eleven sub-issues, epic #805 with #806–#811, #817, and #821; newly closed since the last sync: #943 (PR #944), #692 (PR #947), plus the ANLEITUNG review #963 with #964–#966, #968, and #969 (PR #972) and #967 (PR #973), plus the test-suite audit #949 (PR #977) and the PDF guard #974 (PR #979), plus the staged heartbeat escalation #958 (details: Previous Rounds).

Open items: one row per issue in the triage table below. Neither the count nor the rows are maintained by hand as of #821 – `scripts/recommendations_live_check.py --write` updates all six versions from the GitHub live state, while the rating columns stay editorial work.

## Open GitHub Issues — Triage Status

| # | Title | Relevance | Complexity | Recommended model (effort) | Next step |
|---|-------|-----------|------------|------------------------------|-----------|
| [#681](https://github.com/NikolayDA/picture_helper/issues/681) | [Epic] EufyMake target profile – validate Height/Gloss/mm-DPI | 🟠 High (correctness of the main export target) | 🔴 High (5 sub-issues, needs physical hardware) | – (epic) | Profile integration and all 29 mandatory print-free cells are done; I-09 is non-blocking. Hardware tests #688–#690 and closeout review remain |
| [#687](https://github.com/NikolayDA/picture_helper/issues/687) | Assumption inventory, manufacturer sources, test matrix | 🟠 High (binding foundation for #688–#691) | 🔴 High (repository material complete; remainder needs real hardware) | – (no agent; needs real EufyMake hardware) | Blocked (external) – 17/18 acceptance criteria and all 29 mandatory import cells are done. Only closeout review after #688–#690 remains |
| [#688](https://github.com/NikolayDA/picture_helper/issues/688) | Validate HEIGHT bit depth/semantics on real hardware | 🟠 High (directly affects relief height) | 🔴 High (physical printer, fixtures, measurement log) | – (no agent; needs real EufyMake hardware) | Blocked (external) – including the direct I-14 filter/normalization pair, all preflights are complete; physical precision, filtering, relief, and mm measurements remain |
| [#689](https://github.com/NikolayDA/picture_helper/issues/689) | Validate mm/DPI, target size, positioning contract | 🟠 High (print size/registration) | 🔴 High (physical measurements, control motifs) | – (no agent; needs real hardware) | Blocked (external) – the Studio contract including crop and HEIGHT aspect-ratio handling is proven. Only physical registration, measurements, and tolerances remain |
| [#690](https://github.com/NikolayDA/picture_helper/issues/690) | Validate gloss/clear-coat semantics | 🟡 Medium (gloss is already flagged "experimental" in code) | 🔴 High (physical prints, material consumption) | – (no agent; needs real hardware) | Blocked (external) – native `Gloss Varnish` ink mode is preflighted; cell-specific registration and physical polarity, intensity, and material effect remain |
| [#691](https://github.com/NikolayDA/picture_helper/issues/691) | Integrate versioned target profile into validator/writer/dialog/docs | 🟠 High (hardens the production export path) | 🟢 Low for release-critical remainder; 🔴 hardware for closeout | Sonnet, medium + later hardware | Release-ready implementation – PR #953 integrates profile v1 and PR #956 fixes the evidence reference with an explicit v1 decision and guards; only later promotion after #688–#690 remains |
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
| [#914](https://github.com/NikolayDA/picture_helper/issues/914) | [Epic] Release process: runners, automated evidence, main freeze | 🟠 High (release operations; implementation largely done) | 🟢 Low (two time/event-bound proofs) | – (epic) | Almost done – the first scheduled dry run at 2026-09-03 04:40 UTC and an end-to-end proof including #918 at the next real release remain |
| [#918](https://github.com/NikolayDA/picture_helper/issues/918) | Release ref instead of a main freeze (ADR + fail-closed safeguards) | 🟠 High (`main` stays mergeable during a release) | 🟢 Low (code, docs, and ruleset are in place) | – (no agent; next release run) | Blocked (external) – reopened on 2026-08-31 after its completion check; PR #936 and the active ruleset 21941216 are documented, only a run whose post-release acceptance demonstrably started on `release/vX.Y.Z` is missing |
| [#939](https://github.com/NikolayDA/picture_helper/issues/939) | Operations: self-hosted runners (heartbeat alert channel) | 🟡 Medium (operations channel, no product code) | 🟢 Low (observation only) | – (no agent; repo owner) | Permanently open – do not close (`RUNNER_HEARTBEAT_ISSUE`); the FAIL of 2026-08-31 was the planned alert-path test, and the cleanup step is done (scheduled run 33496675995 green, x86_64 skipped, Mac and Pi passed) |
| [#975](https://github.com/NikolayDA/picture_helper/issues/975) | eufymake: rebuild and rebind label carriers 04 and 10 | 🟡 Medium (two test fields unlabelled on the carton; no blocker for the other eleven) | 🟢 Low (the generator is already fixed; only the data follow-up is open) | – (no agent; needs macOS with Arial) | Blocked (external) – Liberation Sans produces different bytes on Linux; rebuild carriers, rebind in Studio, update `projects.json` |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | Restore OpenAI quota for the manual Codex security check | 🟢 Low (blocks only an optional manual scan) | 🟢 Low (purely operational, no code) | – (no agent; repo owner: billing) | Blocked (external) – the last run (29233060507, 2026-07-13) proves no successful scan; billing/quota still unresolved |

### Recommended Next

1. **#693** (Qt-free core) – ADR #692 is approved; #694, #695, and #696 follow in that order.
2. **#949** – make the four changes, then recapture the baseline with platform and optional dependencies.
3. **#883** – decide Qt/code licensing and prove rights/provenance for the exact `u2net.onnx`,
   or choose a clearly licensed replacement model.
4. After device/material approval, perform the remaining physical measurements for **#689**
   together with the remainder of #687, #688, and #690; native HEIGHT/Gloss paths and I-08 are preflighted. Then close out #691:
   promote profile v1, or create v2 if the results contradict it.

## Previous Rounds

Detailed protocols since v2.2: [RECOMMENDATIONS-2026-v2.2-v2.9.en.md](../../history/RECOMMENDATIONS-2026-v2.2-v2.9.en.md).

Historical findings and work logs (rounds 1–5): [RECOMMENDATIONS-2026-pre-v2.2.en.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.en.md).
