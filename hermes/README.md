# Hermes Version

This is the Hermes v1 adaptation of English Work Abroad Coach.

It keeps the same core learning system and Python utilities as the Claude Code/Codex/opencode version, but the skill entrypoint is written for Hermes' skill and automation model.

## Setup

Use Python 3.9 or newer. From this folder:

```bash
python3 scripts/bootstrap.py
```

Use a specific Python when needed:

```bash
python3 scripts/bootstrap.py --python /path/to/python3.12
```

Normal bootstrap installs no third-party runtime packages. For development
metadata validation and the complete test suite, run:

```bash
python3 scripts/bootstrap.py --dev
```

If Python 3.9+ is unavailable:

```bash
uv python install 3.12
PYTHON="$(uv python find 3.12)"
"$PYTHON" scripts/bootstrap.py --python "$PYTHON"
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

## Hermes Install Note

Install or symlink this folder into the Hermes skill directory as `english-work-abroad-coach`. A common path is:

```bash
~/.hermes/skills/english-work-abroad-coach
```

`SKILL.md` includes `metadata.hermes.blueprint` as a default 21:00 daily reminder automation. If your Hermes installation uses a different scheduler schema, keep the prompt and command semantics and adapt the metadata fields.

The skill expects tool access only when needed:

- Python for bundled scripts.
- Web access only when fetching current study materials.
- No secrets or API keys are required for v1.
