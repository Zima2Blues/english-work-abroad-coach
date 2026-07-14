---
name: english-work-abroad-coach
description: "Use in OpenClaw when the user wants a daily English coach for working abroad: plan 30/60-minute study, generate tasks or materials, review check-ins, track streaks and missed days, summarize progress, or maintain 50/500-day goals."
metadata:
  openclaw:
    skillKey: english-work-abroad-coach
    displayName: English Work Abroad Coach
    userInvocable: true
    version: "0.1.0"
    homepage: "https://github.com/Zima2Blues/english-work-abroad-coach"
    requires:
      anyBins:
        - python3
        - python
        - uv
---

# English Work Abroad Coach for OpenClaw

## Purpose

Use this OpenClaw skill as a daily English coach for overseas work readiness. It keeps the same learning system as the Claude Code/Codex/opencode version, but its instructions assume OpenClaw's skill loading model and tool-gating boundaries.

## First-Time Setup

Use Python 3.9 or newer. From this skill folder:

```bash
python3 scripts/bootstrap.py
```

If the machine has a preferred Python:

```bash
python3 scripts/bootstrap.py --python /path/to/python3.12
```

Normal bootstrap creates a local `.venv`, runs the standard-library smoke test,
and installs no third-party packages. Use `python3 scripts/bootstrap.py --dev`
only for development metadata validation. If Python 3.9+ is unavailable:

```bash
uv python install 3.12
PYTHON="$(uv python find 3.12)"
"$PYTHON" scripts/bootstrap.py --python "$PYTHON"
```

## OpenClaw Usage

When OpenClaw invokes this skill:

1. Read `data/plan.json` for the current 30/60-minute plan and 50/500-day goal state.
2. Use `scripts/english_coach.py` for deterministic task generation, check-in persistence, and progress summaries.
3. Read `references/learning-science.md` before changing the learning method.
4. Read `references/material-sources.md` before selecting or generating daily materials.
5. Read `references/plan-system.md` before changing weekly themes, scoring, cycles, or goals.

OpenClaw should request only the tool access needed for the current action:

- `python3` or `.venv/bin/python` for local scripts.
- Web access only when fetching current study materials from external sources.
- No shell access is needed for ordinary coaching replies if the user only wants explanation.

## Core Commands

Run from the skill folder:

```bash
.venv/bin/python scripts/english_coach.py today
.venv/bin/python scripts/english_coach.py reminder
.venv/bin/python scripts/english_coach.py summary --days 30
.venv/bin/python scripts/english_coach.py checkin --date YYYY-MM-DD --minutes 30 --theme "current work" --duolingo done --listening "..." --speaking "..." --expressions "a;b;c" --reflection "..."
```

If running from another directory, pass:

```bash
--root /path/to/openclaw
```

## Daily Coaching Flow

### Generate A Task

Use:

```bash
.venv/bin/python scripts/english_coach.py today --date YYYY-MM-DD
```

Then give the user:

- 30/60-minute task blocks.
- One material source or search target.
- One speaking prompt.
- 3-5 reusable expressions.
- The check-in format.

### Review A Check-In

When the user sends a check-in:

1. Extract date, minutes, theme, listening, speaking/transcript, expressions, and reflection.
2. Persist it with `scripts/english_coach.py checkin`.
3. Correct the English output with concise explanations.
4. Score the day out of 100 using `references/plan-system.md`.
5. Assign tomorrow's task.

Prioritize daily output and intelligibility over perfect grammar.

### Summarize Progress

Use:

```bash
.venv/bin/python scripts/english_coach.py summary --days 7
.venv/bin/python scripts/english_coach.py summary --days 30
.venv/bin/python scripts/english_coach.py summary --days 50
.venv/bin/python scripts/english_coach.py summary --days 500
```

Report current streak, longest streak, missed dates, completion rate, total minutes, next 50-day target, and one concrete adjustment.

## Reminder Boundary

This OpenClaw v1 includes `scripts/reminder_runner.py` for one-shot reminders, but it does not install a scheduler. Integrate it with OpenClaw's scheduler or the host system only after confirming the target reminder mechanism.

## Check-In Template

Ask the user to send:

```text
英语打卡 Day X
日期：
今天用时：30/60 分钟
今天主题：
多邻国：完成/未完成
听力材料：
口语内容或转写：
今天学到的表达：
1.
2.
3.
我想表达但不会说的是：
复盘：
请监督、纠错，并安排明天任务。
```
