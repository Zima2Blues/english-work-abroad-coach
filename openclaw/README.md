# OpenClaw Version

This is the OpenClaw v1 adaptation of English Work Abroad Coach.

It keeps the same core learning system and Python utilities as the Claude Code/Codex/opencode version, but the skill entrypoint is written for OpenClaw's skill loading and tool-gating model.

## Setup

From this folder:

```bash
python3 scripts/bootstrap.py
```

Use a specific Python when needed:

```bash
python3 scripts/bootstrap.py --python /path/to/python3.12
```

## Use

Today's task:

```bash
.venv/bin/python scripts/english_coach.py today
```

Progress:

```bash
.venv/bin/python scripts/english_coach.py summary --days 30
```

Check-in:

```bash
.venv/bin/python scripts/english_coach.py checkin \
  --date 2026-07-14 \
  --minutes 30 \
  --theme "current work" \
  --duolingo done \
  --listening "VOA Learning English short clip" \
  --speaking "My main responsibility is building backend services." \
  --expressions "main responsibility; backend services; sync progress" \
  --reflection "I need to speak with fewer pauses."
```

## OpenClaw Install Note

If OpenClaw requires the folder name to match `name: english-work-abroad-coach`, install or symlink this directory under that name in the OpenClaw skills directory.

The skill expects tool access only when needed:

- Python for bundled scripts.
- Web access only when fetching current study materials.
- No secrets or API keys are required for v1.
