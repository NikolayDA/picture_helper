[Deutsch](../../../RECOMMENDATIONS.md) · **English** · [Español](../es/RECOMMENDATIONS.md) · [Français](../fr/RECOMMENDATIONS.md) · [Українська](../uk/RECOMMENDATIONS.md) · [简体中文](../zh/RECOMMENDATIONS.md)

# Code Analysis & Ranked Recommendations: BgRemover

## Rating Scale

| Symbol | Priority | Meaning |
|--------|----------|---------|
| 🔴 | Critical | Bugs, crashes, or data loss |
| 🟠 | High | Clear impact on reliability or maintainability |
| 🟡 | Medium | Useful improvement for quality, readability, or testability |
| 🟢 | Low | Optional polish or process improvement |

## Current Status (2026-08-31, v2.9.0 published, open inventory fully audited)

**Daily audit 2026-08-31 (state `551d055`):** The twelve PRs merged today
(#927–#932, #935–#938, #940, and #941) and the issues they closed (#918–#923,
#933, and #934) were reviewed: the complete merge diffs, review follow-ups,
and, where present, their regression tests. The release ref and retry paths,
security report, runner heartbeat/dry run, preparation scaffold, and Qt/GL
preflight are implemented consistently. The adversarial re-check in the
review of PR #942, however, surfaced five concrete residual findings in the
process scripts – verified and bundled as follow-up issue #943 (triage row
below).

**Routine check 2026-08-30 (delta after the full audit):** The 39 open issues
fully and adversarially checked against `main` (product state `411d47c`) on
2026-08-29 are unchanged; HEAD `1d31f2a` only adds documentation afterward.
The updated descriptions #681/#882/#905/#906 and the fixture/test-cell gaps in
the EufyMake real-world tests #688–#690 therefore remain correctly visible.
New #912 was checked separately against the Qt advisory and the pinned
artifact: CVSS 4.0 is 6.3, not 6.8, and vulnerable `QtCore5Compat` is not
shipped. #912 was corrected and closed as “not affected”; no false accepted-
risk entry and no new 🔴 finding.

**Addendum 2026-08-29:** v2.9.0 is published. Hardware acceptance passed on
macOS arm64 and Linux arm64 with real GPU renderers, tag and publication are
verified byte for byte against the approval manifest, and `PUBLIC-DOWNLOAD-01`
and `UPDATE-01` are satisfied. #881 is therefore closed; the deliberately
paused Linux x86_64 criteria remain visibly `PENDING`. #878 was implemented by
PR #908; this closeout sync closes the issue and removes it from all six
current triage tables.

**Routine check 2026-08-28:** The GitHub live comparison adds the previously
missing open issues **#878**, **#881**, **#882**, and the newly created MAS
sub-issues **#883–#907**. At that point, #878 was intended to close the gap
between the standard/expert UI and the user guide, including current
screenshots and PDF; implementation has since been completed by PR #908.
#881 is the binding acceptance and publication record
for 2.9.0; candidate build and pre-check are green, while hardware acceptance
and human approvals remain open. #882 collects the Mac App Store path as a
blocked epic; #883–#907 make its licensing, account, sandbox, packaging, store, and operations
phases concrete. The licensing strategy must be decided before technical
work. No new 🔴 finding is open.

**EufyMake #681/#687–#691:** the 31 fixtures, protocol templates, and approved test governance are now reflected in the issues. #687 is at 16/18 criteria; only I-06 (folder/manifest) and the closeout review after the real tests remain. For the separate Spot UV path, the manufacturer-backed hypothesis is black = gloss and white = no gloss. Full 16-bit use, `pHYs` priority, grayscale-to-mm mapping, and gloss intensity remain hardware questions in #688–#690.

Unchanged and closed: **N1/N2/N4/N5/N6/N7/N8**, **O1–O8**, everything completed since **2026-06-25**, releases v2.7.0–v2.8.0, epic #741 with its eleven sub-issues, epic #805 with #806–#811, #817, and #821; newly closed since the last sync: #836 (PR #844), #837 (PR #838), #839 (PR #846), #849 (PR #851), #841 (closed by the owner), #847 (PR #852), #866 (PR #870/#871), #869 (PR #873), #881 (closed by the owner), and #878 (PR #908/#910) (details: Previous Rounds).

Open items: one row per issue in the triage table below. Neither the count nor the rows are maintained by hand as of #821 – `scripts/recommendations_live_check.py --write` updates all six versions from the GitHub live state, while the rating columns stay editorial work.

## Open GitHub Issues — Triage Status

| # | Title | Relevance | Complexity | Recommended model (effort) | Next step |
|---|-------|-----------|------------|------------------------------|-----------|
| [#681](https://github.com/NikolayDA/picture_helper/issues/681) | [Epic] EufyMake target profile – validate Height/Gloss/mm-DPI | 🟠 High (correctness of the main export target) | 🔴 High (5 sub-issues, needs physical hardware) | – (epic) | #687 preparation is at 16/18 AC; I-06 and closeout review remain, while profile integration #691 waits on real tests #688–#690 |
| [#687](https://github.com/NikolayDA/picture_helper/issues/687) | Assumption inventory, manufacturer sources, test matrix | 🟠 High (binding foundation for #688–#691) | 🔴 High (own deliverables done; fixture/test-cell gaps from #688–#690 open, remainder needs real hardware) | – (no agent; needs real EufyMake hardware) | Blocked (external) – 16/18 acceptance criteria done; open: I-06 for folder/manifest and the closeout review after real tests #688–#690 |
| [#688](https://github.com/NikolayDA/picture_helper/issues/688) | Validate HEIGHT bit depth/semantics on real hardware | 🟠 High (directly affects relief height) | 🔴 High (physical printer, fixtures, measurement log) | – (no agent; needs real EufyMake hardware) | Blocked (external) + groundwork open – fixtures/protocol templates from #687 are in place, but alpha/coverage has neither a fixture nor a test cell (all COLOR fixtures are opaque) and a COLOR/HEIGHT pair with the same pixel dimensions is missing (I-02/I-08 confounded); add both before the test day |
| [#689](https://github.com/NikolayDA/picture_helper/issues/689) | Validate mm/DPI, target size, positioning contract | 🟠 High (print size/registration) | 🔴 High (physical measurements, control motifs) | – (no agent; needs real hardware) | Blocked (external) + groundwork open – whether the Studio import dialog derives the start size from `pHYs`/DPI is unproven (N10, EM-F04); on top of that, cell I-06 references the fixture manifest instead of a real export manifest, and non-square DPI are neither tested nor excluded with a stated reason |
| [#690](https://github.com/NikolayDA/picture_helper/issues/690) | Validate gloss/clear-coat semantics | 🟡 Medium (gloss is already flagged "experimental" in code) | 🔴 High (physical prints, material consumption) | – (no agent; needs real hardware) | Blocked (external) + groundwork open – the groundwork from #687 is only partial: exactly one gloss cell (I-10), no alpha/coverage fixtures, no differing gloss dimensions, gloss × HEIGHT not crossed |
| [#691](https://github.com/NikolayDA/picture_helper/issues/691) | Integrate versioned target profile into validator/writer/dialog/docs | 🟠 High (hardens the production export path) | 🟠 High (cross-cutting across eufymake_export/_validate/_writer + UI) | Opus, high | Blocked – waits on #688–#690 |
| [#682](https://github.com/NikolayDA/picture_helper/issues/682) | [Epic] COLOR tonal/grayscale engine | 🟡 Medium-high (roadmap foundation for laser, not an active bug) | 🔴 High (5 sub-issues, ADR→core→UI→integration→acceptance) | – (epic) | In progress – start #692 first |
| [#692](https://github.com/NikolayDA/picture_helper/issues/692) | ADR + data contract for tone/histogram/grayscale ops | 🟠 High (sets the contract for the whole epic) | 🟡 Medium (architecture decision, no implementation) | Opus, high | Ready to start |
| [#693](https://github.com/NikolayDA/picture_helper/issues/693) | Qt-free core: histogram/grayscale/levels/gamma | 🟡 Medium-high | 🟡 Medium (extends `color_ops.py`, well isolated and testable) | Sonnet, high | Blocked – waits on ADR #692 |
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
| [#943](https://github.com/NikolayDA/picture_helper/issues/943) | Review follow-up 2026-08-31: five robustness findings in process scripts | 🟠 High (heartbeat reports PASS without proven readiness) | 🟡 Medium (four scripts, isolated fixes with regression tests) | Sonnet, high | Ready – heartbeat conclusions first, then dispatch marker, prepare_release (downgrade/write order), and scanner OSError |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | Restore OpenAI quota for the manual Codex security check | 🟢 Low (blocks only an optional manual scan) | 🟢 Low (purely operational, no code) | – (no agent; repo owner: billing) | Blocked (external) – the last run (29233060507, 2026-07-13) proves no successful scan; billing/quota still unresolved |

### Recommended Next

1. **#692** (ADR) opens the COLOR epic #682.
2. Before the next Studio/printer session, first close the fixture/test-cell gaps documented in
   #688–#690 (alpha/coverage, a COLOR/HEIGHT pair of equal size, gloss cells, a real export
   manifest for I-06); then run #687 (remainder), #688, #689, and #690 in one bundled session.
3. **#883** (MAS licensing strategy) decides the Mac App Store path #882 –
   without that owner decision the whole chain #884–#907 stays blocked.

## Previous Rounds

Detailed protocols since v2.2: [RECOMMENDATIONS-2026-v2.2-v2.9.en.md](../../history/RECOMMENDATIONS-2026-v2.2-v2.9.en.md).

Historical findings and work logs (rounds 1–5): [RECOMMENDATIONS-2026-pre-v2.2.en.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.en.md).
