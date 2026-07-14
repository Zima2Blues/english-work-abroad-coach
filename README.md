# English Work Abroad Coach

A versioned collection of English-learning agent skills for daily study toward future overseas work.

The Claude Code / Codex / opencode version is the primary tested version. OpenClaw v1 and Hermes v1 are also available as platform-specific adaptations.

## Versions

```text
english-work-abroad-coach/
  README.md
  claudecode-codex-opencode/   # current working Agent Skill
  openclaw/                    # OpenClaw v1 adaptation
  hermes/                      # Hermes v1 adaptation
```

## Agent Install

Give one of these prompts to your agent. The agent should clone this repository, run the bootstrap script for the matching version, and install that version into the local skill directory as `english-work-abroad-coach`.

Repository:

```text
https://github.com/Zima2Blues/english-work-abroad-coach.git
```

### Claude Code / Codex / opencode

```text
Install the English Work Abroad Coach skill from https://github.com/Zima2Blues/english-work-abroad-coach.git.

Use the claudecode-codex-opencode version. Clone or update the repo locally, run `python3 scripts/bootstrap.py` inside `claudecode-codex-opencode/`, then install or symlink that folder as `english-work-abroad-coach` in this agent's skills directory. Verify it with `.venv/bin/python scripts/english_coach.py today`.
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

Use the openclaw version. Clone or update the repo locally, run `python3 scripts/bootstrap.py` inside `openclaw/`, then install or symlink that folder as `english-work-abroad-coach` in OpenClaw's skills directory. Verify it with `.venv/bin/python scripts/english_coach.py today`.
```

### Hermes

```text
Install the English Work Abroad Coach skill from https://github.com/Zima2Blues/english-work-abroad-coach.git.

Use the hermes version. Clone or update the repo locally, run `python3 scripts/bootstrap.py` inside `hermes/`, then install or symlink that folder as `english-work-abroad-coach` in `~/.hermes/skills/`. Verify it with `.venv/bin/python scripts/english_coach.py today`.
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
- Install dependencies into a local `.venv` instead of system Python.
- Install a user-level `systemd` timer for daily reminders.

## Current Version Layout

```text
claudecode-codex-opencode/
  SKILL.md
  agents/openai.yaml
  requirements.txt
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

`openclaw/` contains the OpenClaw v1 adaptation. It keeps the same Python coach utilities and learning references, but uses an OpenClaw-specific `SKILL.md` with `metadata.openclaw` fields and tool-gating guidance.

OpenClaw setup:

```bash
cd openclaw
python3 scripts/bootstrap.py
```

OpenClaw validation:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest discover -s tests -v
```

The skill name inside `SKILL.md` remains `english-work-abroad-coach`. If an agent requires the folder name to match the skill name, copy or symlink `openclaw/` into that agent's skill directory as `english-work-abroad-coach`.

## Hermes Version

`hermes/` contains the Hermes v1 adaptation. It keeps the same Python coach utilities and learning references, but uses a Hermes-specific `SKILL.md` with `metadata.hermes` tags and a default 21:00 daily reminder blueprint.

Hermes setup:

```bash
cd hermes
python3 scripts/bootstrap.py
```

Hermes validation:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest discover -s tests -v
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

The bootstrap script creates `.venv`, installs dependencies from `requirements.txt`, and runs self-tests.

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

## Runtime Data

The repository keeps templates under each version's `data/`, but personal runtime records are ignored by git:

- `*/data/checkins.jsonl`
- `*/data/reminder.log`
- `.venv/`

This keeps private learning history and local environment files out of GitHub.

## Validation

Run every distribution test and the repository's local skill metadata validator:

```bash
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
