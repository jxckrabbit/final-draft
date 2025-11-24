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

# add priority
```powershell
python tasks.py --user alice add "Pay rent" --category finances --priority
```

# promote/demote/priorities
```powershell
# promote an existing task by index to priority
python tasks.py --user alice promote 3

# demote (remove priority) from a task
python tasks.py --user alice demote 3

# list priority tasks for a user
python tasks.py --user alice priorities
```

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

Priority behavior
- Tasks marked with `--priority` (or answered `y` at interactive add) are shown immediately when you enter interactive mode for a user.
- `recommend` always prefers available priority tasks first, regardless of the chosen style.


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

Generate (AI + fallback)
```powershell
# Generate tasks from a prompt using fallback parsing:
python tasks.py --user alice generate "Buy groceries, Call Bob, Clean desk"

# Use AI to generate tasks (requires OPENAI_API_KEY env var):
setx OPENAI_API_KEY "your_api_key_here"
python tasks.py --user alice generate "Weekend chores: clean, laundry, grocery list" --ai

# Interactive: run `python tasks.py interactive` then type:
#   generate  (you will be prompted for the prompt and whether to use AI)
```
