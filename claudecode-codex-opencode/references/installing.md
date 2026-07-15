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

The `data/` folder contains only the read-only `default-plan.json` template.
Your plan, check-ins, backups, and reminder log are stored outside the skill
folder, so updating or reinstalling the skill does not overwrite them.

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
.venv/bin/python scripts/english_coach.py init
.venv/bin/python scripts/english_coach.py today
.venv/bin/python scripts/english_coach.py summary --days 30
```

## State And Backups

By default, state is kept in the platform user-state directory:

- Linux: `$XDG_STATE_HOME/english-work-abroad-coach`, or
  `~/.local/state/english-work-abroad-coach`.
- macOS: `~/Library/Application Support/EnglishWorkAbroadCoach`.
- Windows: `%LOCALAPPDATA%/EnglishWorkAbroadCoach`.

Use `--state-dir /path/to/state` for a specific location, or set
`ENGLISH_COACH_HOME` to use the same state on all installed skill variants.

To upgrade from a pre-SQLite skill copy, keep the old folder intact and run:

```bash
.venv/bin/python scripts/english_coach.py migrate \
  --legacy-root /path/to/old/english-work-abroad-coach
```

Migration copies the old plan, check-ins, and reminder log without modifying
the old folder. A malformed check-in line is reported with its line number and
causes the command to return a nonzero status after the valid lines are copied.

Create a portable backup before moving to another device:

```bash
.venv/bin/python scripts/english_coach.py export --output english-coach-backup.json
.venv/bin/python scripts/english_coach.py import --input english-coach-backup.json
```

Import refuses to replace a nonempty state directory. To merge another device's
backup, use `import --merge`; an imported check-in replaces an existing
check-in with the same date. `init` refuses to overwrite a saved plan unless
you add `--force`, which writes a backup under the state directory first.

Export and edit a plan only through the command interface:

```bash
.venv/bin/python scripts/english_coach.py plan export --output my-plan.json
.venv/bin/python scripts/english_coach.py plan update --input my-plan.json
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

The runner appends to `reminder.log` in the user state directory. If
`notify-send` is available in the user session, it also sends a desktop
notification when the daily check-in is missing.

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
