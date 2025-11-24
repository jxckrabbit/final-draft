# Current task
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

# add with category
python tasks.py --user alice add "Buy milk" --category groceries

# list only tasks in a category
python tasks.py --user alice list --category groceries
```

Current task
```powershell
# select a task as the current one (by index shown in `list`)
python tasks.py --user alice select 2

# show current
python tasks.py --user alice current

# clear current
python tasks.py --user alice unselect
```

# recommend
```powershell
# recommend with style provided on command line
python tasks.py --user alice recommend --style type

# or prompt for style (interactive):
python tasks.py --user alice recommend

# In interactive mode:
python tasks.py interactive
# then: recommend (you will be prompted for style)
```

Fallback behavior
- If there is no current task set, `recommend` will fall back to selecting a random not-done task and set it as the current task.


Interactive mode notes
- In interactive mode you can run `list` or `list <category>` to filter by category.
- When adding (`add <text>`) the CLI will prompt for an optional category.

Data model
- Data is stored in `tasks_db.json` as a mapping of username -> record.
- Each user record is an object: `{"tasks": [...], "current": "<created_at>"}`.
- Tasks have `text`, `created_at` (UTC ISO), `done` flag, and an optional `category` string.

Next steps I can help with:
- add `list --category` to support partial matches or case-insensitive matching
- add an `edit` command to change task text or category
- add unit tests for migration and current-task behavior
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

# add with category
python tasks.py --user alice add "Buy milk" --category groceries
```

# current task
```powershell
# select a task as the current one (by index shown in `list`)
python tasks.py --user alice select 2

# show current
python tasks.py --user alice current

# clear current
python tasks.py --user alice unselect
```

Notes
- Data is stored in `tasks_db.json` as a mapping of username -> list of tasks.
- Tasks have `text`, `created_at` (UTC ISO), `done` flag, and an optional `category` string.

Interactive mode
- When you run `python tasks.py interactive` (or `python tasks.py --user alice interactive`), use `add <text>` to add a task; the CLI will prompt for a category.

Next steps I can help with:
- add search or edit commands
- add tests or packaging
- wire this up to a small GUI or web frontend
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
