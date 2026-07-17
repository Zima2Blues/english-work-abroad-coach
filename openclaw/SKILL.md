---
name: english-work-abroad-coach
description: "Use in OpenClaw when the user needs an English study plan, a daily task, check-in review, progress summary, or reminder for work-abroad preparation."
metadata:
  openclaw:
    skillKey: english-work-abroad-coach
    displayName: English Work Abroad Coach
    userInvocable: true
    version: "0.2.0"
    homepage: "https://github.com/Zima2Blues/english-work-abroad-coach"
    requires:
      anyBins:
        - python3
        - python
        - uv
---

# English Work Abroad Coach for OpenClaw

Coach practical daily English for overseas work readiness: 30-minute weekdays,
60-minute weekends, visible streaks and missed days, and 50-day milestones
within a 500-day goal.

## First Run

Before running scripts for the first time, run `python3 scripts/bootstrap.py` and then `.venv/bin/python scripts/english_coach.py doctor`; use the repository installation guide if either check needs setup help.

## Workflow

Use `.venv/bin/python scripts/english_coach.py` as the source of truth for
state. Personal plans, check-ins, and reminders are stored in the external
SQLite state directory, not in this skill folder. Request only the tool access
needed for the current action: Python for scripts and web access only for
current external materials.

Read references only when the action requires them:

- `references/plan-system.md` before changing schedules, themes, scoring, or goals.
- `references/material-sources.md` before selecting current sourced material.
- `references/learning-science.md` before changing the learning method.

## Commands

```bash
.venv/bin/python scripts/english_coach.py today --date YYYY-MM-DD
.venv/bin/python scripts/english_coach.py checkin --date YYYY-MM-DD --minutes 30 --theme "current work" --duolingo done --listening "..." --speaking "..." --expressions "a;b;c" --reflection "..."
.venv/bin/python scripts/english_coach.py summary --days 30
.venv/bin/python scripts/english_coach.py reminder --date YYYY-MM-DD
```

Use `init`, `migrate`, `export`, `import`, `plan export`, and `plan update`
only for state setup, transfer, or saved-plan changes. Do not edit the bundled
`data/default-plan.json` template.

## Daily Coaching

For `today`, provide 30/60-minute task blocks, one material or search target,
one speaking prompt, 3-5 reusable expressions, and a check-in request. If
current material cannot be fetched, label the generated B2-level fallback.

For a check-in, persist the date, minutes, theme, listening, speaking or
transcript, expressions, and reflection with `checkin`; correct the English,
score completion/time (20), listening (15), speaking (25), expressions (20),
and reflection/next action (20), then assign tomorrow's task. Favor daily
output and intelligibility over perfect grammar.

For `summary`, report current and longest streaks, missed dates, completion
rate, total minutes, the next 50-day target, and one weekly adjustment.

## Reminder Boundary

`reminder` can prepare a one-shot reminder. Use OpenClaw's scheduler or the
host scheduler only after confirming its mechanism. Do not call the Linux-only
`install_reminder.py`; it is not part of this distribution.
