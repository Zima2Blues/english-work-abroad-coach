---
name: english-work-abroad-coach
description: "Use when the user needs an English study plan, a daily task, check-in review, progress summary, or reminder for work-abroad preparation."
---

# English Work Abroad Coach

Coach daily English for overseas work readiness. Keep the routine practical for
a full-time worker: 30 minutes on weekdays, 60 minutes on weekends, repeated
input and output, visible streaks and missed days, and 50-day milestones within
a 500-day goal.

## First Run

Before running scripts on a new machine, run `python3 scripts/bootstrap.py` and then `.venv/bin/python scripts/english_coach.py doctor`; read `references/installing.md` only when setup, migration, backup, or Linux reminder details are needed.

## Commands

Run commands from the skill folder, preferably with `.venv/bin/python`. The
coach stores personal state in an external SQLite state directory; use
`--state-dir /path/to/state` when the user needs an explicit shared location.

```bash
.venv/bin/python scripts/english_coach.py today --date YYYY-MM-DD
.venv/bin/python scripts/english_coach.py checkin --date YYYY-MM-DD --minutes 30 --theme "current work" --duolingo done --listening "..." --speaking "..." --expressions "a;b;c" --reflection "..."
.venv/bin/python scripts/english_coach.py summary --date YYYY-MM-DD --days 30
.venv/bin/python scripts/english_coach.py reminder --date YYYY-MM-DD
```

Use `init`, `migrate`, `export`, and `import` only for state setup or transfer.
Use `plan export` and `plan update` to change a saved plan; do not edit the
read-only `data/default-plan.json` template.

## Coaching Flow

### Plan

Before changing schedule, themes, scoring, or goals, read
`references/plan-system.md`. Keep plans realistic: Duolingo is a warm-up, not
the main practice; every day includes listening, shadowing or retelling,
output, and review.

### Daily Task

Run `today` and give the selected 30/60-minute task blocks, one material
suggestion or search target, one speaking prompt, 3-5 reusable expressions,
and the check-in format. Read `references/material-sources.md` only when the
user requests current sourced material. Without web access, provide a clearly
labelled B2-level fallback passage.

### Check-In

When the user sends a check-in, extract the date, minutes, theme, listening,
speaking or transcript, expressions, and reflection. Run `checkin`, correct
the English concisely, score completion/time (20), listening (15), speaking
(25), reusable expressions (20), and reflection/next action (20), then assign
tomorrow's task. Prioritize daily output, intelligibility, and reuse over
perfect grammar.

### Progress

Run `summary --days 7`, `30`, `50`, or `500` as appropriate. Report current
and longest streaks, missed dates, completion rate, total minutes, the next
50-day target, and one concrete adjustment for the next week.

### Reminder

`reminder` works while an agent is invoked. For a Linux desktop systemd timer,
first confirm `doctor` and then follow `references/installing.md` for
`scripts/install_reminder.py`. The timer uses the external state directory;
agents cannot wake themselves when no session is running.

## Learning Rules

Read `references/learning-science.md` only when changing the learning method.
Preserve spaced and retrieval practice, comprehensible input before output,
daily spoken or written output, and work-abroad scenarios such as introductions,
project stories, meetings, problem solving, async updates, and interviews.

## Check-In Format

Ask for date, 30/60-minute duration, theme, Duolingo status, listening
material, speaking content or transcript, reusable expressions, an unmet
expression, and a short reflection. Ask the user to request supervision,
correction, and tomorrow's task.
