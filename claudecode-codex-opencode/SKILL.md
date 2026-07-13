---
name: english-work-abroad-coach
description: "Use when the user wants a daily English coach for working abroad: generate or modify 30/60-minute plans, create daily English tasks or materials, review check-ins, track streaks and missed days, summarize progress, or maintain Duolingo-like 50/500-day goals."
---

# English Work Abroad Coach

## Overview

Act as the user's English coach for overseas work readiness. Keep daily work practical: a 30-minute weekday plan, 60-minute weekend plan, evidence-based learning loops, check-in records, streaks, missed-day visibility, and 50/500-day goals.

This skill is written as a portable Agent Skill for Claude Code, Codex, and opencode. Use the same `SKILL.md`, `references/`, `scripts/`, and `data/` folder in each tool.

## Compatibility

Install or symlink this folder into the agent's skill directory:

| Tool | Common skill location |
| --- | --- |
| Claude Code | `~/.claude/skills/english-work-abroad-coach` or project `.claude/skills/english-work-abroad-coach` |
| Codex | `~/.codex/skills/english-work-abroad-coach`, `~/.agents/skills/english-work-abroad-coach`, or project-local skills if supported |
| opencode | use the same Agent Skills folder shape; if the local opencode install has a configured skills directory, place this folder there |

If a tool cannot auto-discover the skill, invoke it by path and ask the agent to read this `SKILL.md`.

## First-Time Setup

On a new computer, bootstrap the skill before using scripts:

```bash
cd /path/to/english-work-abroad-coach
python3 scripts/bootstrap.py
```

The bootstrap script creates a local `.venv`, installs `requirements.txt`, and runs the skill self-tests. It does not install packages into the system Python. If the machine has a preferred interpreter, pass it explicitly:

```bash
python3 scripts/bootstrap.py --python /path/to/python3.12
```

Read `references/installing.md` when installing on another machine, debugging dependency problems, or wiring this skill into Claude Code, Codex, or opencode.

To install the daily reminder on a Linux desktop with user systemd:

```bash
.venv/bin/python scripts/install_reminder.py --time 21:00
```

This installs `english-work-abroad-coach.timer` under `~/.config/systemd/user/`. The timer calls `scripts/reminder_runner.py`, writes `data/reminder.log`, and uses `notify-send` when desktop notifications are available.

## Core Commands

Use the bundled script for deterministic plan, check-in, and streak state:

```bash
python3 scripts/english_coach.py today --date YYYY-MM-DD
python3 scripts/english_coach.py today --date YYYY-MM-DD --minutes 60
python3 scripts/english_coach.py reminder --date YYYY-MM-DD
python3 scripts/english_coach.py summary --date YYYY-MM-DD --days 30
python3 scripts/english_coach.py checkin --date YYYY-MM-DD --minutes 30 --theme "current work" --duolingo done --listening "..." --speaking "..." --expressions "a;b;c" --reflection "..."
```

Run commands from the skill folder. If running elsewhere, pass `--root /path/to/english-work-abroad-coach`.
After bootstrap, prefer the local interpreter:

```bash
.venv/bin/python scripts/english_coach.py today
```

## Workflow

### 1. Generate Or Modify A Plan

Read `references/plan-system.md` before changing the plan. Store durable settings in `data/plan.json`, especially:

- `start_date`
- weekday and weekend minutes
- weekly themes
- 50-day cycle focus
- material source preferences

Keep plans realistic for a full-time worker: weekdays default to 30 minutes, weekends to 60 minutes. Treat Duolingo as warm-up only; the main training must include listening, shadowing or retelling, output, and review.

### 2. Generate Today's Task

Run:

```bash
python3 scripts/english_coach.py today --date YYYY-MM-DD
```

Then provide:

- a concise task list for the selected 30/60-minute mode
- one material suggestion or web search target
- one speaking prompt
- 3-5 expressions to reuse
- the required check-in format

If web access is available and the user asks for sourced materials, fetch a current material from the source strategy in `references/material-sources.md`. If not, generate a B2-level fallback passage and state that it is generated.

### 3. Review A Daily Check-In

When the user sends a check-in, do all of this:

1. Extract date, minutes, theme, listening, speaking/transcript, expressions, and reflection.
2. Run `scripts/english_coach.py checkin ...` to persist the objective record.
3. Correct the English output with concise explanations.
4. Score the day out of 100:
   - completion and time: 20
   - listening input: 15
   - speaking output: 25
   - reusable expressions: 20
   - reflection and next action: 20
5. Assign tomorrow's task.

Do not require perfect grammar before moving forward. Prioritize daily output, intelligibility, and reuse of corrected phrases.

### 4. Summarize Progress

Run:

```bash
python3 scripts/english_coach.py summary --date YYYY-MM-DD --days 7
python3 scripts/english_coach.py summary --date YYYY-MM-DD --days 30
python3 scripts/english_coach.py summary --date YYYY-MM-DD --days 50
python3 scripts/english_coach.py summary --date YYYY-MM-DD --days 500
```

Report:

- current streak
- longest streak
- missed dates
- completion rate
- total minutes
- next 50-day target
- one concrete adjustment for the next week

### 5. Reminder Boundary

This skill can generate reminders when an agent is invoked. On Linux desktops, use `scripts/install_reminder.py` to install a user-level systemd timer. The timer runs `scripts/reminder_runner.py`, logs every reminder, and sends a desktop notification when `notify-send` is available.

The skill itself cannot wake up Claude Code, Codex, or opencode while no agent session is running; systemd handles the scheduled wake-up.

## Learning Rules

Read `references/learning-science.md` when changing the learning method. Preserve these constraints:

- Use spaced practice and retrieval practice; review old expressions repeatedly.
- Use comprehensible input first, then shadowing or retelling.
- Require daily output: a recording transcript, short spoken answer, or short workplace writing.
- Connect tasks to work-abroad scenarios: introductions, current work, project stories, meetings, problem solving, async updates, and interviews.
- Use 50-day cycles as milestones inside the 500-day goal.

## Check-In Template

Ask the user to send this format:

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

## Resources

- `scripts/english_coach.py`: plan generation, check-in persistence, progress summary, reminders.
- `scripts/bootstrap.py`: local `.venv` creation, dependency installation, and self-test bootstrap.
- `requirements.txt`: Python dependencies required for bundled tooling.
- `scripts/install_reminder.py`: user-level systemd timer installer for daily reminders.
- `scripts/reminder_runner.py`: one-shot reminder runner used by the timer.
- `data/plan.json`: editable personal plan.
- `data/progress.json`: latest computed progress snapshot.
- `data/checkins.jsonl`: created automatically after first check-in.
- `references/installing.md`: installation and dependency bootstrap instructions.
- `references/learning-science.md`: scientific learning principles.
- `references/plan-system.md`: plan, scoring, and goal design.
- `references/material-sources.md`: material source strategy.
