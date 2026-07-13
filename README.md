# English Work Abroad Coach

A portable Agent Skill for daily English learning toward future overseas work.

This repository contains one skill, `english-work-abroad-coach`, designed for Claude Code, Codex, and opencode. It generates daily 30/60-minute study tasks, tracks check-ins and streaks, supports 50-day and 500-day goals, and can install a local desktop reminder on Linux.

## What It Does

- Generates daily English tasks for a full-time worker schedule.
- Uses a 30-minute weekday plan and a 60-minute weekend plan.
- Tracks check-ins, missed days, current streak, longest streak, and completion rate.
- Keeps a 50-day cycle system inside a 500-day long-term goal.
- Provides scientific learning guidance: spaced practice, retrieval practice, comprehensible input, shadowing, output, and feedback.
- Installs dependencies into a local `.venv` instead of system Python.
- Supports a user-level `systemd` timer for daily reminders.

## Project Layout

```text
english-work-abroad-coach/
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

## Setup

From the repository root:

```bash
cd english-work-abroad-coach
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

Copy or symlink `english-work-abroad-coach/` into the skill directory used by your agent.

Common locations:

- Claude Code: `~/.claude/skills/english-work-abroad-coach`
- Codex: `~/.codex/skills/english-work-abroad-coach` or `~/.agents/skills/english-work-abroad-coach`
- opencode: use the same Agent Skills folder shape if your install supports skills

If the tool cannot auto-discover the skill, invoke it by path and ask the agent to read `SKILL.md`.

## Runtime Data

The repository keeps templates under `data/`, but personal runtime records are ignored by git:

- `english-work-abroad-coach/data/checkins.jsonl`
- `english-work-abroad-coach/data/reminder.log`
- `english-work-abroad-coach/.venv/`

This keeps private learning history and local environment files out of GitHub.

## Validation

Run tests:

```bash
cd english-work-abroad-coach
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest discover -s tests -v
```

Validate the skill metadata with Codex's skill validator if available:

```bash
.venv/bin/python /path/to/skill-creator/scripts/quick_validate.py /path/to/english-work-abroad-coach
```
