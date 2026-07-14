# Installing

Use this when copying the skill to another computer or another agent's skill directory.

## Install Shape

Keep the entire folder together:

```text
english-work-abroad-coach/
  SKILL.md
  agents/openai.yaml
  requirements-dev.txt
  scripts/
  references/
  data/
  tests/
```

Do not copy only `SKILL.md`; the scripts, data files, references, and dependency manifest are part of the skill.

## Bootstrap

Python 3.9 or newer is required; Python 3.12 is recommended. From the skill
folder, first check the selected interpreter:

```bash
python3 --version
python3 scripts/bootstrap.py
```

What it does:

1. Creates `.venv` inside the skill folder.
2. Runs the standard-library runtime smoke test.
3. Runs a quick `today` command to verify the coach script works.

Normal runtime setup does not install third-party packages or require network
access.

It first tries Python's standard `venv` module. If that fails and `uv` is installed, it retries with `uv venv --clear --seed`. This handles Python builds whose `python -m venv` creates a broken environment or leaves a partial `.venv` without pip.

Use a specific Python when needed:

```bash
python3 scripts/bootstrap.py --python /home/user/.local/bin/python3.12
```

If Python is missing or older than 3.9 but `uv` is available, let `uv` install
and locate Python 3.12:

```bash
uv python install 3.12
PYTHON="$(uv python find 3.12)"
"$PYTHON" scripts/bootstrap.py --python "$PYTHON"
```

Windows PowerShell:

```powershell
uv python install 3.12
$python = uv python find 3.12
& $python scripts/bootstrap.py --python $python
.venv\Scripts\python.exe scripts\english_coach.py today --json
```

If neither Python nor `uv` is installed, install `uv` from its official
installer, verify it, and then use the commands above:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uv --version
```

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
uv --version
```

For project development, install PyYAML and run every test with:

```bash
python3 scripts/bootstrap.py --dev
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

`english_coach.py` and normal bootstrap use only the Python standard library.
`requirements-dev.txt` includes PyYAML for repository and external skill
validators; bootstrap installs it only with `--dev`.

Do not rely on global Python packages. Keep `scripts/bootstrap.py` as the single
environment setup entry point.
