# Per-user Tasks CLI

This is a small command-line tool to store task lists per username.

Files
- `tasks.py`: CLI script. Creates `tasks_db.json` beside the script to persist data.

Quick usage (PowerShell):

```powershell
# interactive mode (prompts for username)
python tasks.py interactive

# or specify a user and add/list/remove/clear
python tasks.py --user alice add "Buy milk"
python tasks.py --user alice list
python tasks.py --user alice remove 1
python tasks.py --user alice done 2
python tasks.py --user alice clear
```

Notes
- Data is stored in `tasks_db.json` as a mapping of username -> list of tasks.
- Tasks have `text`, `created_at` (UTC ISO), and `done` flag.

If you'd like, I can:
- add search or edit commands
- add tests or packaging
- wire this up to a small GUI or web frontend
