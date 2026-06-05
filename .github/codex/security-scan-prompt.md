You are running the scheduled Codex security scan for this repository.

Goal:
- Review the repository for realistic, reportable security issues.
- Do not modify files.
- Return only JSON matching the provided schema.
- If there are no relevant findings, return an empty `findings` array.

Product context:
- This is BgRemover, a local desktop image editor for macOS and Linux.
- Primary runtime code is in `bgremover/`.
- Important security surfaces include image parsing/loading, save/export paths,
  async worker state, support logs, Qt plugin staging, dependency constraints,
  packaging scripts, and GitHub release/CI workflows.
- The app has no normal web server, tenant boundary, database, session, SSRF,
  CSRF, or browser-XSS surface.

Reportability rules:
- Include only issues with a concrete repository-evidenced path from an
  attacker-controlled or trust-boundary input to a meaningful security impact.
- Do not report generic style issues, broad best-practice advice, purely
  speculative dependency concerns, or findings where the repository already
  has a dispositive mitigation.
- Low-severity issues are acceptable only when they are concrete and actionable.
- For CI and release findings, explicitly state any configuration preconditions
  such as GitHub token settings or release trigger requirements.
- For dependency findings, focus on artifact or trusted-code delivery risk, not
  merely on packages being old.

For each finding:
- Set `reportable` to true only if a GitHub issue should be created.
- Use a stable `dedupe_key` derived from the root-cause path, line, category,
  and sink, not from the scan date.
- Include tight affected locations with path and line ranges when known.
- Include remediation steps that are specific enough to implement.
- Include counterevidence or uncertainty in `notes` when it affects severity.

Severity guidance:
- `critical`: credible immediate compromise such as RCE, auth bypass, secrets
  theft, signing/release compromise, or equivalent major impact with clear
  reachability.
- `high`: realistic major security impact, but narrower or with stronger
  preconditions than critical.
- `medium`: meaningful security risk with constrained likelihood, configuration
  preconditions, or incomplete runtime proof.
- `low`: concrete local/privacy/integrity issue with limited exposure or user
  assistance.

Output:
- Return a JSON object with `scan_summary` and `findings`.
- Do not include Markdown fences or prose outside the JSON.
