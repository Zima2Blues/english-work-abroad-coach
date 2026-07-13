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

Run tests for the current version:

```bash
cd claudecode-codex-opencode
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest discover -s tests -v
```

Validate the skill metadata with Codex's skill validator if available:

```bash
.venv/bin/python /path/to/skill-creator/scripts/quick_validate.py /path/to/claudecode-codex-opencode
```
