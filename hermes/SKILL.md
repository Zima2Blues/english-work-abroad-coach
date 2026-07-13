---
name: english-work-abroad-coach
description: "Use in Hermes when the user wants a daily English coach for working abroad: plan 30/60-minute study, generate tasks or materials, review check-ins, track streaks and missed days, summarize progress, or maintain 50/500-day goals."
metadata:
  hermes:
    displayName: English Work Abroad Coach
    version: "0.1.0"
    homepage: "https://github.com/Zima2Blues/english-work-abroad-coach"
    tags:
      - english-learning
      - work-abroad
      - daily-coach
      - streaks
    requires:
      anyBins:
        - python3
        - python
    blueprint:
      id: daily-english-reminder
      title: Daily English Reminder
      schedule:
        cron: "0 21 * * *"
        timezone: "local"
      prompt: "Use the English Work Abroad Coach skill to generate today's reminder, today's study task, and the check-in template."
      command: "python3 scripts/reminder_runner.py --root ${HERMES_SKILL_DIR}"
---

# English Work Abroad Coach for Hermes

## Purpose

Use this Hermes skill as a daily English coach for overseas work readiness. It keeps a 30-minute weekday plan, a 60-minute weekend plan, Duolingo-style streak tracking, visible missed days, and 50/500-day goals.

## First-Time Setup

From this skill folder:

```bash
python3 scripts/bootstrap.py
```

If the machine has a preferred Python:

```bash
python3 scripts/bootstrap.py --python /path/to/python3.12
```

The bootstrap step creates a local `.venv`, installs `requirements.txt`, and runs tests. Do not install packages into the system Python unless the user explicitly asks.

## Hermes Usage

When Hermes invokes this skill:

1. Read `data/plan.json` for the current 30/60-minute plan and 50/500-day goal state.
2. Use `scripts/english_coach.py` for deterministic task generation, check-in persistence, and progress summaries.
3. Read `references/learning-science.md` before changing the learning method.
4. Read `references/material-sources.md` before selecting or generating daily materials.
5. Read `references/plan-system.md` before changing weekly themes, scoring, cycles, or goals.

The `metadata.hermes.blueprint` block is the default daily automation suggestion: at 21:00 local time, Hermes can run the reminder prompt and optionally call `scripts/reminder_runner.py`. If the local Hermes installation uses a different scheduler schema, preserve the prompt and command semantics while adapting the field names.

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
--root /path/to/hermes
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

If web access is available and the user asks for current materials, fetch one suitable source using `references/material-sources.md`. If web access is unavailable, generate a B2-level fallback passage and state that it is generated.

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

This Hermes v1 includes `scripts/reminder_runner.py` for one-shot reminders and declares a default `metadata.hermes.blueprint` schedule. Let Hermes or the host scheduler own recurring execution. Do not install the Linux `systemd` timer from the Claude Code/Codex/opencode version in this folder.

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
