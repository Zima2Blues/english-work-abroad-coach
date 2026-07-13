# Installing

Use this when copying the skill to another computer or another agent's skill directory.

## Install Shape

Keep the entire folder together:

```text
english-work-abroad-coach/
  SKILL.md
  agents/openai.yaml
  requirements.txt
  scripts/
  references/
  data/
  tests/
```

Do not copy only `SKILL.md`; the scripts, data files, references, and dependency manifest are part of the skill.

## Bootstrap

From the skill folder:

```bash
python3 scripts/bootstrap.py
```

What it does:

1. Creates `.venv` inside the skill folder.
2. Installs packages from `requirements.txt`.
3. Runs the bundled tests.
4. Runs a quick `today` command to verify the coach script works.

It first tries Python's standard `venv` module. If that fails and `uv` is installed, it retries with `uv venv --clear --seed`. This handles Python builds whose `python -m venv` creates a broken environment or leaves a partial `.venv` without pip.

Use a specific Python when needed:

```bash
python3 scripts/bootstrap.py --python /home/user/.local/bin/python3.12
```

Preview without changing the machine:

```bash
python3 scripts/bootstrap.py --dry-run
```

After bootstrap, use:

```bash
.venv/bin/python scripts/english_coach.py today
.venv/bin/python scripts/english_coach.py summary --days 30
```

## Daily Reminder

Install a user-level systemd reminder timer:

```bash
.venv/bin/python scripts/install_reminder.py --time 21:00
```

What it writes:

```text
~/.config/systemd/user/english-work-abroad-coach.service
~/.config/systemd/user/english-work-abroad-coach.timer
```

What it runs:

```bash
.venv/bin/python scripts/reminder_runner.py --root /path/to/english-work-abroad-coach
```

The runner appends to `data/reminder.log`. If `notify-send` is available in the user session, it also sends a desktop notification when the daily check-in is missing.

Useful commands:

```bash
systemctl --user status english-work-abroad-coach.timer
systemctl --user list-timers english-work-abroad-coach.timer
systemctl --user disable --now english-work-abroad-coach.timer
```

## Current Dependencies

`english_coach.py` and `bootstrap.py` use only the Python standard library. `requirements.txt` includes `PyYAML` so bundled or official skill validation tools that parse YAML can run in the local virtual environment.

Do not rely on global Python packages. If a future version adds material-fetching or notification libraries, add them to `requirements.txt` and keep `scripts/bootstrap.py` as the single installation entry point.
