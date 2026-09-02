[Deutsch](../../../RECOMMENDATIONS.md) · **English** · [Español](../es/RECOMMENDATIONS.md) · [Français](../fr/RECOMMENDATIONS.md) · [Українська](../uk/RECOMMENDATIONS.md) · [简体中文](../zh/RECOMMENDATIONS.md)

# Code Analysis & Ranked Recommendations: BgRemover

## Rating Scale

| Symbol | Priority | Meaning |
|--------|----------|---------|
| 🔴 | Critical | Bugs, crashes, or data loss |
| 🟠 | High | Clear impact on reliability or maintainability |
| 🟡 | Medium | Useful improvement for quality, readability, or testability |
| 🟢 | Low | Optional polish or process improvement |

## Current Status (2026-09-02, v2.9.0 published, open inventory fully audited)

**Daily audit 2026-09-02 (state `1ec9d96`):** 42 open issues checked against
the GitHub live state. The triage table had been wrong in all six versions
since 2026-08-30 – `recommendations-live-check` has been red ever since:
**#914**, **#918**, **#939**, and **#949** were missing, and **#692** was
still listed as open (closed on 2026-09-01 via PR #947). The daily audit of
2026-08-31 also listed #918 as closed; it had been reopened the same day after
its completion check and now only awaits the next real release run. This round
corrects both. Newly assessed: #949 (test-suite audit, four actionable test
changes, no production defect), #939 (permanent heartbeat alert channel, do
not close), and the epic bracket #914. No new 🔴 finding.

**Release assessment: no new release is due.** Since `v2.9.0` (2026-08-29)
there are 25 mainline commits – exclusively release automation, documentation,
and governance; `[Unreleased]` is empty, and inside the `bgremover/` package
only the evidence hook `update_check_probe.py` (#917) changed. A candidate
build would carry no user-visible content. Intended scope for a later
**v2.10.0**: the COLOR tone/grayscale engine (#693/#694 from epic #682) on top
of the now-approved ADR #692, optionally plus #949.

**EufyMake #681/#687–#691:** fixtures, protocol templates, and approved test governance are reflected in the issues; the open PR #948 raises the set to 34 fixtures and adds the constant-RGB alpha/coverage cell, a dimension-matched COLOR/HEIGHT pair, a pixel-exact HEIGHT registration map, and a pre-import inspector anchored by a trusted manifest hash. Two Studio 4.2.2 import paths are documented without printing. #687 is at 16/18 criteria; only I-06 (folder/manifest) and the closeout review after the real tests remain. For the separate Spot UV path, the manufacturer-backed hypothesis is black = gloss and white = no gloss. Full 16-bit use, `pHYs` priority, grayscale-to-mm mapping, and gloss intensity remain hardware questions in #688–#690.

Unchanged and closed: **N1/N2/N4/N5/N6/N7/N8**, **O1–O8**, everything completed since **2026-06-25**, releases v2.7.0–v2.9.0, epic #741 with its eleven sub-issues, epic #805 with #806–#811, #817, and #821; newly closed since the last sync: #943 (PR #944) and #692 (PR #947) (details: Previous Rounds).

Open items: one row per issue in the triage table below. Neither the count nor the rows are maintained by hand as of #821 – `scripts/recommendations_live_check.py --write` updates all six versions from the GitHub live state, while the rating columns stay editorial work.

## Open GitHub Issues — Triage Status

| # | Title | Relevance | Complexity | Recommended model (effort) | Next step |
|---|-------|-----------|------------|------------------------------|-----------|
| [#681](https://github.com/NikolayDA/picture_helper/issues/681) | [Epic] EufyMake target profile – validate Height/Gloss/mm-DPI | 🟠 High (correctness of the main export target) | 🔴 High (5 sub-issues, needs physical hardware) | – (epic) | #687 preparation is at 16/18 AC; I-06 and closeout review remain, while profile integration #691 waits on real tests #688–#690 |
| [#687](https://github.com/NikolayDA/picture_helper/issues/687) | Assumption inventory, manufacturer sources, test matrix | 🟠 High (binding foundation for #688–#691) | 🔴 High (own deliverables done; fixture/test-cell gaps from #688–#690 open, remainder needs real hardware) | – (no agent; needs real EufyMake hardware) | Blocked (external) – 16/18 acceptance criteria done; open: I-06 for folder/manifest and the closeout review after real tests #688–#690 |
| [#688](https://github.com/NikolayDA/picture_helper/issues/688) | Validate HEIGHT bit depth/semantics on real hardware | 🟠 High (directly affects relief height) | 🔴 High (physical printer, fixtures, measurement log) | – (no agent; needs real EufyMake hardware) | In review + blocked (external) – PR #948 completes repository preparation with 34 fixtures, matched I-08 landmarks, the constant-RGB alpha cell I-13, and a trusted pre-import report; two controlled Studio 4.2.2 import paths are documented. The remaining import matrix and safe physical E1 print, relief, and mm measurements remain open |
| [#689](https://github.com/NikolayDA/picture_helper/issues/689) | Validate mm/DPI, target size, positioning contract | 🟠 High (print size/registration) | 🔴 High (physical measurements, control motifs) | – (no agent; needs real hardware) | Blocked (external) + groundwork open – whether the Studio import dialog derives the start size from `pHYs`/DPI is unproven (N10, EM-F04); on top of that, cell I-06 references the fixture manifest instead of a real export manifest, and non-square DPI are neither tested nor excluded with a stated reason |
| [#690](https://github.com/NikolayDA/picture_helper/issues/690) | Validate gloss/clear-coat semantics | 🟡 Medium (gloss is already flagged "experimental" in code) | 🔴 High (physical prints, material consumption) | – (no agent; needs real hardware) | Blocked (external) + groundwork open – the groundwork from #687 is only partial: exactly one gloss cell (I-10), no alpha/coverage fixtures, no differing gloss dimensions, gloss × HEIGHT not crossed |
| [#691](https://github.com/NikolayDA/picture_helper/issues/691) | Integrate versioned target profile into validator/writer/dialog/docs | 🟠 High (hardens the production export path) | 🟠 High (cross-cutting across eufymake_export/_validate/_writer + UI) | Opus, high | Blocked – waits on #688–#690 |
| [#682](https://github.com/NikolayDA/picture_helper/issues/682) | [Epic] COLOR tonal/grayscale engine | 🟡 Medium-high (roadmap foundation for laser, not an active bug) | 🔴 High (4 remaining sub-issues: core→UI→integration→acceptance) | – (epic) | In progress – ADR #692 is approved; the core #693 comes next |
| [#693](https://github.com/NikolayDA/picture_helper/issues/693) | Qt-free core: histogram/grayscale/levels/gamma | 🟡 Medium-high | 🟡 Medium (extends `color_ops.py`, well isolated and testable) | Sonnet, high | Ready to start – ADR #692 (PR #947) supplies the data contract; implement and test the core against its formulas |
| [#694](https://github.com/NikolayDA/picture_helper/issues/694) | Live preview + UI for histogram/levels/gamma | 🟡 Medium | 🟡 Medium-high (Qt UI, debounce/generation guard like the height preview) | Sonnet, high | Blocked – waits on core #693 |
| [#695](https://github.com/NikolayDA/picture_helper/issues/695) | Layer/selection/history/project integration | 🟡 Medium | 🟠 High (many state transitions: undo/redo, selection, dirty state) | Opus, high | Blocked – waits on #693/#694 |
| [#696](https://github.com/NikolayDA/picture_helper/issues/696) | Performance/E2E/docs/laser-interface acceptance | 🟡 Medium (closeout gate, not a new feature) | 🟠 High (benchmark suite, E2E, docs, adapter contract) | Opus, high | Blocked – closeout issue after #695 |
| [#882](https://github.com/NikolayDA/picture_helper/issues/882) | [Epic] BgRemover in the Mac App Store | 🟡 Medium-high (new distribution channel, not a current product defect) | 🔴 High (licensing, sandbox, packaging, store, release governance) | – (Epic) | Blocked – create and decide the licensing strategy as the concrete phase-0 subtask first |
| [#883](https://github.com/NikolayDA/picture_helper/issues/883) | [MAS] Licensing strategy: PySide6 vs. Riverbank and relicensing | 🟠 High (hard blocker for all technical MAS work) | 🔴 High (license/owner decision, possible Qt port, residual risk) | Opus, high + owner/legal review | Ready – write the ADR and owner decision; create a separate port issue if PySide6 is chosen |
| [#884](https://github.com/NikolayDA/picture_helper/issues/884) | [MAS] Apple Developer Program enrollment | 🟠 High (blocks certificates and store access) | 🟢 Low (manual account/payment step) | – (no agent; account holder) | Blocked (external) – choose account type, complete enrollment/2FA, and assign renewal ownership |
| [#885](https://github.com/NikolayDA/picture_helper/issues/885) | [MAS] Signing identities, App ID, and provisioning profile | 🟠 High (prerequisite for a signed store build) | 🟡 Medium (owner secrets plus bundle-ID/packaging contract) | – (no agent; account holder/admin) | Blocked – waits for #884; then create certificates, explicit App ID/profile, and freeze the bundle ID |
| [#886](https://github.com/NikolayDA/picture_helper/issues/886) | [MAS] Define and apply App Sandbox entitlements | 🟠 High (mandatory store and runtime prerequisite) | 🟠 High (all Mach-O files, packaging and hardware evidence) | Opus, high | Blocked – waits for licensing decision #883; then implement minimal entitlements and artifact/hardware tests |
| [#887](https://github.com/NikolayDA/picture_helper/issues/887) | [MAS] Sandbox-compatible inference child process | 🟠 High (core AI function must run in the store build) | 🔴 High (spawn/helper signing, two-key rule, real sandbox) | Opus, high | Blocked – waits for #886; decide re-exec/helper and prove the AI self-check on hardware |
| [#888](https://github.com/NikolayDA/picture_helper/issues/888) | [MAS] Security-scoped bookmarks for files and directories | 🟠 High (Recent Files and Quick Save otherwise break after restart) | 🟠 High (persistent grants, images/projects/directories, channel gating) | Opus, high | Blocked – waits for #886; implement the bookmark contract and test the sandboxed restart case |
| [#889](https://github.com/NikolayDA/picture_helper/issues/889) | [MAS] Sandbox-safe writes and EufyMake export | 🟠 High (save/export paths and potential data integrity) | 🔴 High (atomicity across multiple paths and Powerbox grants) | Opus, high | Blocked – waits for #886; design grant-safe atomic writes/extensions/target selection and test on hardware |
| [#890](https://github.com/NikolayDA/picture_helper/issues/890) | [MAS] AI model cache in the sandbox container | 🟡 Medium (deterministic model path in the store channel) | 🟡 Medium (isolated path contract plus migration decision) | Sonnet, high | Blocked – waits for #886 and couples to #893; set `U2NET_HOME` explicitly and decide migration |
| [#891](https://github.com/NikolayDA/picture_helper/issues/891) | [MAS] Distribution-channel flag and update-check gating | 🟠 High (App Store rule 2.4.5, no self-updates) | 🟠 Medium-high (central flag across menu, settings, workers, hooks) | Sonnet, high | Blocked – waits for #883; then add the channel contract and negative-test MAS network/UI paths |
| [#892](https://github.com/NikolayDA/picture_helper/issues/892) | [MAS] Remove AiInstallDialog and bundle the AI backend | 🟠 High (no installing executable code in the store) | 🟡 Medium (channel gating plus binding packaging test) | Sonnet, high | Blocked – waits for #891; gate dialog/menu and prove bundled rembg/onnxruntime |
| [#893](https://github.com/NikolayDA/picture_helper/issues/893) | [MAS] Bundle u2net or download it at first launch | 🟠 High (review risk and AI functionality) | 🟠 High (product/review decision, packaging or new i18n flow) | Opus, high | Blocked – waits for #890/#891 and licensing decision #883; document, implement, and sandbox-verify the chosen variant |
| [#894](https://github.com/NikolayDA/picture_helper/issues/894) | [MAS] Choose Briefcase vs. py2app packaging | 🟠 High (determines technical channel viability) | 🟠 High (open-ended signed sandbox/upload spike) | Opus, high | Blocked – waits for #883; run Briefcase spike, test py2app fallback, record ADR |
| [#895](https://github.com/NikolayDA/picture_helper/issues/895) | [MAS] onedir app, inside-out signing, Qt store cleanup | 🟠 High (central executable store build) | 🔴 High (all binaries, Qt, provisioning, upload validation) | Opus, high | Blocked – waits for #885/#886/#894; implement the chosen build path and validate without ITMS errors |
| [#896](https://github.com/NikolayDA/picture_helper/issues/896) | [MAS] Info.plist and complete icon set | 🟡 Medium-high (store metadata and platform contract) | 🟡 Medium (required keys, architecture target, deterministic assets) | Sonnet, high | Blocked – waits for #895; decide minimum OS/architecture/document types and add plist/icon tests |
| [#897](https://github.com/NikolayDA/picture_helper/issues/897) | [MAS] Signed productbuild PKG and Transporter upload | 🟠 High (submittable store artifact) | 🟠 High (second signature, build automation, manual first upload) | Opus, high + account holder | Blocked – waits for #885/#895/#896; build reproducible PKG and capture delivery log |
| [#898](https://github.com/NikolayDA/picture_helper/issues/898) | [MAS] Release CI, six-artifact contract, and PKG scan | 🟠 High (fail-closed release integrity) | 🔴 High (CI secrets, contract, unpacker, malware/path scan) | Opus, high | Blocked – waits for #895/#897; extend MAS leg, contract, payload scan, and regression tests together |
| [#899](https://github.com/NikolayDA/picture_helper/issues/899) | [MAS] Sandboxed acceptance smokes on real hardware | 🟠 High (binding runtime evidence for core paths) | 🔴 High (PKG, AI spawn, Powerbox, 3D, evidence schema) | Opus, high + macOS hardware | Blocked (external) – waits for #898; add acceptance path and run on self-hosted ARM64 |
| [#900](https://github.com/NikolayDA/picture_helper/issues/900) | [MAS] TestFlight beta for macOS | 🟠 High (early review and foreign-device evidence) | 🟡 Medium (manual ASC/tester coordination) | – (no agent; account holder and tester) | Blocked (external) – waits for #897/#901; verify AI, files, and 3D on another device |
| [#901](https://github.com/NikolayDA/picture_helper/issues/901) | [MAS] App Store Connect record and six-language metadata | 🟠 High (name, listing, submission prerequisite) | 🟠 Medium-high (owner steps plus six localized metadata sets) | Sonnet, high + account holder | Blocked – waits for #884/#885; reserve name, version/upload texts, set rating/storefronts |
| [#902](https://github.com/NikolayDA/picture_helper/issues/902) | [MAS] 16:10 store screenshot set | 🟡 Medium-high (required listing material) | 🟡 Medium (reproducible formats, alpha check, language decision) | Sonnet, high | Blocked – waits for representative build #895; extend automation for store resolutions and verify the set |
| [#903](https://github.com/NikolayDA/picture_helper/issues/903) | [MAS] Privacy Policy and App Privacy answers | 🟠 High (mandatory store and in-app requirement) | 🟡 Medium (policy, hosting, i18n link, owner questionnaire) | Sonnet, high + owner | Blocked – waits for channel/model decisions #891/#893; host/link policy and prove “Data Not Collected” |
| [#904](https://github.com/NikolayDA/picture_helper/issues/904) | [MAS] EU DSA status, legal notice, and GPSR review | 🟠 High (EU storefronts and public legal duties) | 🟠 Medium-high (owner classification, verification, legal risk) | – (no agent; owner/legal review) | Blocked (external) – waits for #884; declare trader status and document DDG/GPSR owner/follow-up |
| [#905](https://github.com/NikolayDA/picture_helper/issues/905) | [MAS] Extend release governance for the store channel | 🟠 High (prevents a channel outside the fail-closed contract) | 🟠 High (runbook, checklist, contract, path policy, six changelogs) | Opus, high | Blocked – accompanies #898/#899; raise all governance contracts/tests to six artifacts before submission |
| [#906](https://github.com/NikolayDA/picture_helper/issues/906) | [MAS] Initial submission and review round | 🟠 High (manual publication gate) | 🔴 High (many dependencies, residual risks, Apple communication) | – (no agent; release owner) | Blocked (external) – after #896/#897/#899/#901–#905 run pre-submission, submit, record result/follow-ups |
| [#907](https://github.com/NikolayDA/picture_helper/issues/907) | [MAS] Operations plan for renewal, updates, and channels | 🟡 Medium-high (long-term availability and channel separation) | 🟡 Medium (runbook, ownership, reminders, channel matrix) | Opus, high + owner | Blocked – draft early, finalize after #906; bind renewal/update/web routines into operations |
| [#914](https://github.com/NikolayDA/picture_helper/issues/914) | [Epic] Release process: runners, automated evidence, main freeze | 🟠 High (release operations; 8 of 9 work packages done) | 🟡 Medium (only the #918 remainder) | – (epic) | Almost done – all that is left is the success criterion "`main` stays mergeable", which the next real release run proves via #918 |
| [#918](https://github.com/NikolayDA/picture_helper/issues/918) | Release ref instead of a main freeze (ADR + fail-closed safeguards) | 🟠 High (`main` stays mergeable during a release) | 🟢 Low (code, docs, and ruleset are in place) | – (no agent; next release run) | Blocked (external) – reopened on 2026-08-31 after its completion check; PR #936 and the active ruleset 21941216 are documented, only a run whose post-release acceptance demonstrably started on `release/vX.Y.Z` is missing |
| [#939](https://github.com/NikolayDA/picture_helper/issues/939) | Operations: self-hosted runners (heartbeat alert channel) | 🟡 Medium (operations channel, no product code) | 🟢 Low (observation only) | – (no agent; repo owner) | Permanently open – do not close (`RUNNER_HEARTBEAT_ISSUE`); the FAIL of 2026-08-31 was the planned alert-path test, and the cleanup step is done (scheduled run 33496675995 green, x86_64 skipped, Mac and Pi passed) |
| [#949](https://github.com/NikolayDA/picture_helper/issues/949) | Test-suite audit 2026-09-02 (RESOURCES drift, CropOverlay, coverage gaps) | 🟡 Medium (test quality and drift protection, no production defect) | 🟢 Low-medium (four clearly scoped test changes, no production change) | Sonnet, medium | Ready to start – derive the `RESOURCES.md` expectations from the real `uses:` lines, move `test_crop_overlay.py` to `set_position()`/`crop_rect()`, and cover the rectangle branch of `crop_image()` and the non-RGBA branch of `adjust_color()` |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | Restore OpenAI quota for the manual Codex security check | 🟢 Low (blocks only an optional manual scan) | 🟢 Low (purely operational, no code) | – (no agent; repo owner: billing) | Blocked (external) – the last run (29233060507, 2026-07-13) proves no successful scan; billing/quota still unresolved |

### Recommended Next

1. **#693** (Qt-free core) – ADR #692 is approved, so the COLOR epic #682 is ready to start;
   #694, #695, and #696 follow in that order.
2. **#949** – four small, clearly scoped test changes with no production risk; a good parallel
   PR alongside the epic.
3. Review and merge **#948**; then, before the next Studio/printer session, close the remaining
   gaps from #689/#690 (gloss cells, a real export manifest for I-06) and run #687 (remainder),
   #688, #689, and #690 in one bundled session.
4. **#883** (MAS licensing strategy) decides the Mac App Store path #882 –
   without that owner decision the whole chain #884–#907 stays blocked.

## Previous Rounds

Detailed protocols since v2.2: [RECOMMENDATIONS-2026-v2.2-v2.9.en.md](../../history/RECOMMENDATIONS-2026-v2.2-v2.9.en.md).

Historical findings and work logs (rounds 1–5): [RECOMMENDATIONS-2026-pre-v2.2.en.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.en.md).
