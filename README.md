# English Work Abroad Coach

A versioned collection of English-learning agent skills for daily study toward future overseas work.

Release: 0.2.0

The Claude Code / Codex / opencode version is the primary tested version. OpenClaw and Hermes are available as platform-specific 0.2.0 adaptations.

## Runtime Prerequisite

The bundled scripts require Python 3.9 or newer; Python 3.12 is recommended.
Normal bootstrap creates a local `.venv` without installing third-party runtime
packages. If the machine has no suitable Python, install Python 3.12 with `uv`:

```bash
uv python install 3.12
cd claudecode-codex-opencode
PYTHON="$(uv python find 3.12)"
"$PYTHON" scripts/bootstrap.py --python "$PYTHON"
```

See `claudecode-codex-opencode/references/installing.md` for `uv` installation
and Windows PowerShell commands.

## Versions

```text
english-work-abroad-coach/
  README.md
  claudecode-codex-opencode/   # current working Agent Skill
  openclaw/                    # OpenClaw 0.2.0 adaptation
  hermes/                      # Hermes 0.2.0 adaptation
```

## Release Archives

Build sanitized, self-contained archives from the repository root:

```bash
claudecode-codex-opencode/.venv/bin/python tools/build_release.py --all --output-dir dist
```

This creates `english-work-abroad-coach-0.2.0-claudecode-codex-opencode.zip`,
`english-work-abroad-coach-0.2.0-openclaw.zip`, and
`english-work-abroad-coach-0.2.0-hermes.zip`. Each archive unpacks to an
`english-work-abroad-coach/` skill directory and omits virtual environments,
caches, and personal state.

Local builds do not require a license. Before creating a public GitHub Release,
the repository owner must add an explicit license; until then,
`tools/build_release.py --publish-check` exits with
`LICENSE file is required for public release`.

## Agent Install

Give one of these prompts to your agent. The agent should clone this repository, run the bootstrap script for the matching version, and install that version into the local skill directory as `english-work-abroad-coach`.

Repository:

```text
https://github.com/Zima2Blues/english-work-abroad-coach.git
```

### Claude Code / Codex / opencode

```text
Install the English Work Abroad Coach skill from https://github.com/Zima2Blues/english-work-abroad-coach.git.

Use the claudecode-codex-opencode version. Clone or update the repo locally, ensure Python 3.9+ is selected, run `python3 scripts/bootstrap.py` inside `claudecode-codex-opencode/`, then install or symlink that folder as `english-work-abroad-coach` in this agent's skills directory. If Python 3.9+ is unavailable, use the repository's uv Python 3.12 instructions. Verify it with `.venv/bin/python scripts/english_coach.py today`.
```

Typical install commands:

```bash
git clone https://github.com/Zima2Blues/english-work-abroad-coach.git ~/.local/share/english-work-abroad-coach
cd ~/.local/share/english-work-abroad-coach/claudecode-codex-opencode
python3 scripts/bootstrap.py

mkdir -p ~/.codex/skills
ln -sfn ~/.local/share/english-work-abroad-coach/claudecode-codex-opencode ~/.codex/skills/english-work-abroad-coach
```

For Claude Code, use `~/.claude/skills/english-work-abroad-coach` instead of `~/.codex/skills/english-work-abroad-coach`. For opencode, use the skill directory configured by that installation.

### OpenClaw

```text
Install the English Work Abroad Coach skill from https://github.com/Zima2Blues/english-work-abroad-coach.git.

Use the openclaw version. Clone or update the repo locally, ensure Python 3.9+ is selected, run `python3 scripts/bootstrap.py` inside `openclaw/`, then install or symlink that folder as `english-work-abroad-coach` in OpenClaw's skills directory. If Python 3.9+ is unavailable, use the repository's uv Python 3.12 instructions. Verify it with `.venv/bin/python scripts/english_coach.py today`.
```

### Hermes

```text
Install the English Work Abroad Coach skill from https://github.com/Zima2Blues/english-work-abroad-coach.git.

Use the hermes version. Clone or update the repo locally, ensure Python 3.9+ is selected, run `python3 scripts/bootstrap.py` inside `hermes/`, then install or symlink that folder as `english-work-abroad-coach` in `~/.hermes/skills/`. If Python 3.9+ is unavailable, use the repository's uv Python 3.12 instructions. Verify it with `.venv/bin/python scripts/english_coach.py today`.
```

Typical Hermes commands:

```bash
git clone https://github.com/Zima2Blues/english-work-abroad-coach.git ~/.local/share/english-work-abroad-coach
cd ~/.local/share/english-work-abroad-coach/hermes
python3 scripts/bootstrap.py

mkdir -p ~/.hermes/skills
ln -sfn ~/.local/share/english-work-abroad-coach/hermes ~/.hermes/skills/english-work-abroad-coach
```

If the target machine already has a clone, update it instead of recloning:

```bash
cd ~/.local/share/english-work-abroad-coach
git pull --ff-only
```

## Claude Code / Codex / opencode Version

`claudecode-codex-opencode/` contains the working Agent Skill for Claude Code, Codex, and opencode.

It can:

- Generate daily English tasks for a full-time worker schedule.
- Use a 30-minute weekday plan and a 60-minute weekend plan.
- Track check-ins, missed days, current streak, longest streak, and completion rate.
- Maintain a 50-day cycle system inside a 500-day long-term goal.
- Apply scientific learning guidance: spaced practice, retrieval practice, comprehensible input, shadowing, output, and feedback.
- Create a local `.venv` without adding runtime dependencies to system Python.
- Install a user-level `systemd` timer for daily reminders.

## Current Version Layout

```text
claudecode-codex-opencode/
  SKILL.md
  agents/openai.yaml
  requirements-dev.txt
  scripts/
    bootstrap.py
    english_coach.py
    install_reminder.py
    reminder_runner.py
  references/
  data/
  tests/
```

## Distribution Development

The shared scripts, dependency manifest, and learning references in
`claudecode-codex-opencode/` are the canonical source for all distributions.
After changing a shared file, update OpenClaw and Hermes with:

```bash
claudecode-codex-opencode/.venv/bin/python tools/sync_distributions.py --write
```

Check for accidental platform drift without writing files:

```bash
claudecode-codex-opencode/.venv/bin/python tools/sync_distributions.py --check
```

The synchronization whitelist excludes platform `SKILL.md` files, metadata,
tests, and runtime data.

## OpenClaw Version

`openclaw/` contains the OpenClaw 0.2.0 adaptation. It keeps the same Python coach utilities and learning references, but uses an OpenClaw-specific `SKILL.md` with `metadata.openclaw` fields and tool-gating guidance.

OpenClaw setup:

```bash
cd openclaw
python3 scripts/bootstrap.py
```

OpenClaw validation:

```bash
python3 scripts/bootstrap.py --dev
```

The skill name inside `SKILL.md` remains `english-work-abroad-coach`. If an agent requires the folder name to match the skill name, copy or symlink `openclaw/` into that agent's skill directory as `english-work-abroad-coach`.

## Hermes Version

`hermes/` contains the Hermes 0.2.0 adaptation. It keeps the same Python coach utilities and learning references, but uses a Hermes-specific `SKILL.md` with `metadata.hermes` tags and a default 21:00 daily reminder blueprint.

Hermes setup:

```bash
cd hermes
python3 scripts/bootstrap.py
```

Hermes validation:

```bash
python3 scripts/bootstrap.py --dev
```

Install or symlink this folder into the Hermes skill directory as `english-work-abroad-coach`, for example:

```bash
ln -s /path/to/english-work-abroad-coach/hermes ~/.hermes/skills/english-work-abroad-coach
```

## Setup

From the repository root:

```bash
cd claudecode-codex-opencode
python3 scripts/bootstrap.py
```

To use a specific Python:

```bash
python3 scripts/bootstrap.py --python /path/to/python3.12
```

Normal bootstrap creates `.venv`, runs the runtime smoke test, and installs no
third-party packages. Add `--dev` to install `requirements-dev.txt` and run all
development tests.

## Basic Usage

Show today's task:

```bash
cd claudecode-codex-opencode
.venv/bin/python scripts/english_coach.py today
```

Show reminder state:

```bash
.venv/bin/python scripts/english_coach.py reminder
```

Record a check-in:

```bash
.venv/bin/python scripts/english_coach.py checkin \
  --date 2026-07-13 \
  --minutes 30 \
  --theme "professional self-introduction" \
  --duolingo done \
  --listening "VOA Learning English short clip" \
  --speaking "I currently work as a software developer." \
  --expressions "I currently work as; my main responsibility is; work abroad" \
  --reflection "I need to speak more fluently."
```

Show progress:

```bash
.venv/bin/python scripts/english_coach.py summary --days 30
```

## Daily Reminder

Install a daily Linux desktop reminder at 21:00:

```bash
cd claudecode-codex-opencode
.venv/bin/python scripts/install_reminder.py --time 21:00
```

Check timer status:

```bash
systemctl --user status english-work-abroad-coach.timer
```

Disable the reminder:

```bash
systemctl --user disable --now english-work-abroad-coach.timer
```

## Skill Installation

Copy or symlink the current version into the skill directory used by your agent.

Common locations:

- Claude Code: `~/.claude/skills/english-work-abroad-coach`
- Codex: `~/.codex/skills/english-work-abroad-coach` or `~/.agents/skills/english-work-abroad-coach`
- opencode: use the same Agent Skills folder shape if your install supports skills

Example:

```bash
ln -s /path/to/english-work-abroad-coach/claudecode-codex-opencode ~/.codex/skills/english-work-abroad-coach
```

If the tool cannot auto-discover the skill, invoke it by path and ask the agent to read `SKILL.md`.

## Runtime State

Each distribution keeps only the read-only `data/default-plan.json` template.
Personal plans, check-ins, progress, and reminder logs live outside the skill
folder in the per-user SQLite state directory (`coach.db` plus reminder log).
Use `--state-dir` or `ENGLISH_COACH_HOME` when several installed variants must
share the same state. This keeps personal learning history out of GitHub and
survives a skill reinstall.

## Validation

Run every distribution test and the repository's local skill metadata validator:

```bash
uv python install 3.12
PYTHON="$(uv python find 3.12)"
"$PYTHON" claudecode-codex-opencode/scripts/bootstrap.py \
  --root claudecode-codex-opencode \
  --python "$PYTHON" \
  --dev
claudecode-codex-opencode/.venv/bin/python tools/verify_project.py \
  --python claudecode-codex-opencode/.venv/bin/python
```

To add an external official skill validator, pass its local path explicitly:

```bash
claudecode-codex-opencode/.venv/bin/python tools/verify_project.py \
  --python claudecode-codex-opencode/.venv/bin/python \
  --validator "$SKILL_VALIDATOR"
```

The staged engineering roadmap is in
[`docs/plans/2026-07-14-development-optimization-plan.md`](docs/plans/2026-07-14-development-optimization-plan.md).
