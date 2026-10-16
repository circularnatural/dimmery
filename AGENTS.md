
# AGENTS.md — Operating contract

Instructions for any AI agent (Claude Code, ChatGPT, MiMo/OpenCode, Codex, etc.) working on this repository. Read this before touching code or documentation.

> 🎓 If any term in this document is unclear (ADR, ARB, SemVer, fitness function, etc.), it's explained in plain language in `docs/GLOSSARY.md`.

## First session: Git and adaptation

Before implementation, run `git rev-parse --show-toplevel`, `git rev-parse --verify HEAD`, and `git status --short`. Confirm that the Git root belongs to this project, not an unrelated parent repository; preserve any existing changes and branch.

If Git is genuinely absent, an implementer must initialize it with `git init -b main`, inspect `.gitignore` and the files to stage for secrets, and create `chore: initial template scaffold` before proceeding with authorized bootstrap work. Use the user's real Git identity. If `.git` exists but HEAD or references are broken, stop and report the recovery requirement. Never reset or amend existing history to satisfy this check, or treat a dirty tree as missing Git.

On a newly generated project, read `docs/FIRST-ADAPTATION.md` and propose that initial adaptation to the user before implementing product features. If available, run `python scripts/project_identity.py --json` from the project directory and include its result in the session context. A failed Git check blocks implementation, not read-only diagnosis.

## Operating roles — declare per project, don't assume

When more than one agent/environment works on the same project, they shouldn't all have the same write permission by default — mixing them without clarifying the role is the most common way to lose traceability ("who actually wrote this?"). This is solved with **two generic roles, not fixed tool names** — which concrete agent occupies each role is a decision for EACH project, not something the template imposes:

- **Implementer:** has permission to write, commit, and run things directly on the repo. Is the one who actually integrates any external contribution following the ingestion protocol below. Can be a single tool or rotate — what matters is that at any given time it's clear who it is.
- **External auditor:** **reads and proposes, doesn't write or commit without explicit permission** for that specific action. Its output is text — a finding, a recommendation, a check — that the implementer evaluates and integrates (or not).
- This isn't hierarchical in the sense of "worth more" — an external auditor can catch bugs the implementer missed (it already happened while building this very template). It's a separation of responsibility: the auditor doesn't change repo state on its own, so there's always a single point where something went from "proposed" to "integrated", and that point is committed with a name and a date.

**Declare the real assignment here, when filling in "What this project is"** — example format (replace with this project's real assignment):

```yaml
roles:
  implementer: "[concrete tool/environment — e.g. Zed + OpenCode/MiMo, or Claude Code, or yourself with no agent]"
  external_auditors: ["[tool 1]", "[tool 2]"]
```

**Why it matters to spell this out instead of assuming a fixed default:** role assignment changes between projects and over time — one project might have Claude Code as the main implementer and another model as an occasional auditor, exactly the reverse of another project. The only thing that should stay stable within a given project is the RULE (implementer writes, auditor doesn't without permission), not which concrete tool occupies each role — so anyone reading this file a year from now, with a different tool ecosystem, understands the role without depending on "Zed" or "ChatGPT" still being the names in use at that time.

## What this project is

[Fill in: 2-3 lines on what it does, for whom, and its real status — not aspirational. See README.md § Current status, which should say the same thing.]

## Documentation structure

- `README.md` — human entry point.
- `AGENTS.md` — this file.
- `CLAUDE.md` — one-line shim pointing here, so Claude Code loads this file reliably (it looks for that filename by its own convention; other agents read `AGENTS.md` directly). Never add rules there — see D-022.
- `CONTRIBUTORS.md` — record of contributions by model/person (see protocol below).
- `governance/DECISION_LOG.md` — Architectural Decision Records (ADRs), one per non-obvious decision.
- `governance/BACKLOG.md` — prioritized pending work (Priority / Important / Nice to have / Future).
- `governance/SESSION_LOG.md` — brief, cumulative session log (one short entry per work block, not the full detail).
- `docs/` — extended specs, exports from other agents/projects, analysis. Includes `docs/STATUS_TEMPLATE.md` — a full snapshot of the project (different from a handoff, which is only one session's delta), useful once handoffs pile up and reading the last one isn't enough anymore. `docs/GLOSSARY.md` translates the technical jargon in this document and the code into plain language.
- `docs/audits/` — the **raw, complete** text of every external auditor review (`AUDIT_YYYY-MM-DD_model.md`), unsummarized. The summary/integration of that review still goes to `governance/DECISION_LOG.md`/`CONTRIBUTORS.md`/`governance/BACKLOG.md` as usual, but the original is kept as-is — a summary can lose nuance or reasoning that turns out to matter later; the raw file doesn't.
- `.opencode/` — OpenCode-specific config: `commands/` (slash commands available as `/name` in the TUI) and `skills/` (reusable agent behavior loaded on demand). Only relevant if using OpenCode; safe to delete if using Claude Code or another tool. Committed to git — project-level config, not personal preferences.
- `scripts/sync_agents_md.py` — regenerates the AGENTS.md family from the `.template/AGENTS.md` canonical.
- `scripts/sync_docs_md.py` — regenerates root `docs/` from the template's `docs/` content.
- `handoffs/` — one file per work session (`HANDOFF_YYYY-MM-DD.md`, or with a timestamp+agent if more than one can happen the same day). Use `handoffs/HANDOFF_TEMPLATE.md` as a base. **Never overwrite another session's handoff.**
  - **Command:** `handoff` (global alias) — creates a handoff in the closest parent repo with `handoffs/`.
  - `handoff --agent "MiMo" --platform "OpenCode Zen"` — override agent and platform.
  - `handoff --project "my-project"` — override project name (default: read from `pyproject.toml`).
  - Multiple handoffs per day are allowed — each gets a `_HHMM` timestamp suffix.
  - **Command:** `resume` (global alias) — resumes from the latest handoff, generates a session resume.
  - `handon` is an optional alias for `resume`.
  - **Canonical scripts:** `~/.local/bin/handoff.py` and `~/.local/bin/session_resume.py` are the master implementations. The `scripts/create_handoff.py` inside each repo is a standalone copy for environments without the global install.
  - `resume --file HANDOFF_YYYY-MM-DD.md` — specific handoff.
  - `resume --raw` — show handoff content without transformation.
  - `resume --full` — handoff + canonical context docs (AGENTS.md, DECISION_LOG, BACKLOG).
  - `resume --copy` — copy result to clipboard.
  - `resume --list` — list available handoffs.

## Conventions

- **Commits:** [Conventional Commits](https://www.conventionalcommits.org/) (`feat(scope):`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`, `experiment:` for code that might go nowhere). Valid scopes live in `governance/commitlint.config.js` — keep it updated as the project grows, don't let commits use undeclared scopes. **Note:** this isn't enforced by a git hook alone (this template doesn't ship Node/husky) — the real check is `python fitness_functions.py`, which catches it after the commit, not before. See the header of `governance/commitlint.config.js`.
- **Versioning:** semver in the `VERSION` file (single source of truth). Never edit it by hand — use `python release.py patch|minor|major|x.y.z`, which also updates `CHANGELOG.md`, commits, and tags.
- **Secrets:** never in code or Markdown. They go in `.env` (gitignored) — `.env.example` documents what each variable is, with no real values.
- **Config over code:** behavior that can vary (routing, catalogs, limits) goes in `config/*.yaml`, not hardcoded in `if/elif`. See `fitness_functions.py` for the config↔code consistency check.
- **Quality gate:** `python check.py` runs ruff + basedpyright + pytest + fitness_functions in a single pass with one exit code — run it before a release instead of remembering 4 separate commands. `--no-types` skips basedpyright only; `--fast` skips both ruff and basedpyright. If CI is ever added, make it call this same script, not duplicate the command list in the CI's YAML.
- **`scripts/agent_session.py` is cooperative coordination, not a real lock** — see the warning at the top of that file before assuming it guarantees collision prevention.
- **Attribution in multi-agent work:** two levels, not one — a "generated by" tag on every file/commit becomes ambiguous as soon as a piece passes through more than one hand (who proposed it vs. who wrote it vs. who reviewed it?):
  - **Day-to-day (regular commits):** closing the message with who generated it (`docs: ... — OpenCode`) is enough — a cheap signal, no need for more on a small change.
  - **Substantive pieces (ADRs, status reports, handoffs, architecture changes):** use explicit roles — `proposed_by` / `implemented_by` / `reviewed_by` / `approved_by` (see the format in `governance/DECISION_LOG.md` § D-000). Don't force all 4 roles if they don't apply; do avoid a flat "generated by X" when X actually only reviewed what someone else proposed.
  - Also register it in `CONTRIBUTORS.md` as documented there.
  - **Agent ≠ model — name both when the model isn't fixed.** "OpenCode" (the ACP tool connected to Zed) can run different underlying models across sessions (e.g. MiMo-V2.5 via OpenCode Zen normally, falling back to Nemotron 3 Ultra via OpenRouter when Zen's free quota runs out — this happened for real, see `governance/DECISION_LOG.md` § D-009). Don't let a model's name (e.g. "MiMo") become an informal stand-in for "whichever model happened to be running that session" — it stops being accurate the moment the model actually changes, and the discrepancy is easy to miss until someone asks. Write `OpenCode, model: X` when it matters which model did the work (it usually does — model quality varies).
  - **Say who you are out loud, now and then (D-022):** at the start of a session, and again after a long gap or a context reset/resume, state plainly which agent you're running as — e.g. *"Working as OpenCode, model: Laguna"* or *"Working as Claude Code"*, whichever one you actually are, named as concretely as the other. This is the live counterpart to the point above: the commit-time "Agent ≠ model" mismatch has happened for real (an agent claiming "MiMo" while the model actually running was Laguna) — saying it out loud in the session gives the human a chance to catch it in the moment, not later while reviewing a commit.
- **Timestamps — separate machine format from human format:**
  - In frontmatter/YAML/logs: ISO 8601 with an explicit timezone (`generated_at: 2026-08-06T21:30:00-03:00`), never just a date with no time if the data matters at that granularity.
  - In prose for human reading: date+time+timezone as text (`2026-08-06 21:30 ART`).
   - **Canonical provider:** `scripts/get_timestamp.py` (module + CLI). All scripts use `get_timestamps()` for consistent ART (UTC-3) output.
- **Cross-platform scripts:** PowerShell (`.ps1`) scripts are allowed in the repo, but only if a bash (`.sh`) equivalent exists alongside. Each must include an OS check that fails with a helpful message if run in the wrong environment. The Python scripts themselves must be cross-platform (use `pathlib`, `platform.system()` for OS-specific behavior, no hardcoded paths). Convention: `scripts/install_commands.ps1` + `scripts/install_commands.sh`.
  - Never relative (`a while ago`, `~21:30` with no further context) in either case — a handoff or report gets read later, sometimes much later, and relative/approximate time loses meaning or actively misleads once time has passed. If a value is genuinely approximate, say so explicitly (`approximate time`), don't fake precision or skip the caveat.
- **`governance/SESSION_LOG.md`** — brief, cumulative record (one short entry per work block: objective, agents, commits, result, main risk/pending item). It's the quick index of "what happened and when" without opening a full handoff — it **doesn't duplicate** the detail that already lives in `handoffs/` or `docs/STATUS_TEMPLATE.md`, it just points to the fact that a session happened.

## Language convention

- **Code in English:** all identifiers (variables, functions, classes, modules), technical filenames, git branches, commit scopes, and code comments are English. The mechanical constraint is ASCII-only (`[A-Za-z0-9_]+`); English is the natural byproduct.
- **Comments:** English primary. Spanish clarification permitted alongside for UX/GUI wording or domain terms (Argentine clinical, AFIP/ARCA) using a greppable tag: `# UX: formato visible al paciente`.
- **UI language:** per-project decision, not a fixed default. Default `es` for personal-use apps; a project targeting English-speaking market overrides via `ui_language` in `config/settings.yaml`. A single UI string never mixes languages.
- **Error messages:** two channels — user-facing (localized to `ui_language`, no file/function names, no stack trace, carries error code like `ERR_AFIP_TIMEOUT`) vs. dev/log-facing (English, full technical detail). Local JSONL structured logging by default; remote telemetry opt-in only.
- **Naming new things:** user's own phrasing as visible name; canonical English term documented separately in `governance/NAMING_GLOSSARY.md`. Confirm before fixing: *"le puse `whatsapp_list`, ¿va?"*.
- **Locale-specific data in English code:** container is English-named (e.g. `patterns_es.yaml`); content stays in whatever language it must match/serialize (Spanish regex, AFIP field names) — never inline-disguised as logic.

## Multi-agent contribution ingestion protocol

When a contribution arrives from another model/agent (pasted by the person, or generated in a different session):

1. **Classify the contribution:**
   - Is it an architecture/direction **decision**? → New `D-XXX` entry in `governance/DECISION_LOG.md`.
   - Is it **code/architecture**? → Evaluate whether to integrate it; document the proposal and the outcome in `CONTRIBUTORS.md`.
   - Is it **documentation/analysis**? → Save it to `docs/` if relevant; register it in `CONTRIBUTORS.md`.
   - Is it a **direction change**? → Decision log + update `governance/BACKLOG.md`.
2. **Register in `CONTRIBUTORS.md`** — a row in the corresponding model's table; if it's a decision, also in the "Decisions by model" table.
3. **Update `CHANGELOG.md`** (`YYYY-MM-DD → what changed — [model]`).
4. **Assess impact on `governance/BACKLOG.md`** — does it add, resolve, or reprioritize pending items?
5. If it's an important architecture decision, also update the most recent status report in `docs/` if that pattern exists in the project.

## Async ARB + ADRs + Fitness Functions

Architecture review pattern without a synchronous meeting — useful when different agents/sessions touch the repo at different times:

- **ADR (Architectural Decision Record):** every non-obvious structural decision goes to `governance/DECISION_LOG.md` with its context and reasoning — not just the what, the why.
- **Fitness Functions:** mechanical, repeatable checks on architectural properties (coupling, minimal test coverage, config↔code consistency, docs-vs-code drift, commit hygiene). They live in `fitness_functions.py`, run with `python fitness_functions.py`.
- **Async ARB (Architecture Review Board):** run `fitness_functions.py` and ask an agent (or review by hand) for an architecture pass **whenever one of these triggers happens** — not on a blind commit counter, because 5 commits could be 5 typos or one big refactor split into steps:
  - before a structural change (a second module of the same kind, a second external integration);
  - before a release (`python check.py` already includes this);
  - when adding a new core dependency;
  - when a fitness function starts failing;
  - or, absent a concrete trigger, every so often if substantial changes have piled up (the "~5 commits" figure is just a rough reminder, not a rule).

  Findings go to `governance/DECISION_LOG.md` (if they're a decision) or `governance/BACKLOG.md` (if they're a task) — never left sitting only in a chat.

## What NOT to do

- Don't describe a capability in present tense in `README.md`/`docs/` if the code is still a stub — use "designed to" or mark the status explicitly (see README § Current status).
- Don't commit `.env`, credentials, or data from `reports/`/`data/` (see `.gitignore`).
- Don't overwrite another session's handoff — each one is a new file.
- Don't leave an architecture decision only in the conversation — if something structural changes, it goes to `governance/DECISION_LOG.md`.
- Don't add a new commit scope without declaring it in `governance/commitlint.config.js` first.



