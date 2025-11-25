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
# Per-user Tasks CLI

A small command-line tool to store task lists per username. Tasks are persisted to a JSON file (`tasks_db.json` by default, next to `tasks.py`).

**Quick Usage (PowerShell)**

- Interactive mode (prompts for username):

```
python tasks.py interactive
```

- Command-line mode (specify a user):

```
python tasks.py --user alice add "Buy milk"
python tasks.py --user alice list
python tasks.py --user alice remove 1
python tasks.py --user alice done 2
python tasks.py --user alice clear
python tasks.py --user alice select 2
python tasks.py --user alice current
python tasks.py --user alice unselect
python tasks.py --user alice promote 3
python tasks.py --user alice demote 3
python tasks.py --user alice priorities
python tasks.py --user alice recommend --style type
python tasks.py --user alice generate "Buy groceries, Call Bob" --ai
```

**Notes:**
- `--ai` for `generate` requires `OPENAI_API_KEY` environment variable.
- `generate` falls back to simple parsing when AI is not available.

**Files**
- `tasks.py`: main CLI and task management functions.
- `tests/test_tasks.py`: pytest suite covering functions and edge/bad-data cases.
- `run_generate_ai.py`: helper script to exercise `generate_list` using the real API when available or a local mock.

**How the data is stored**
- `tasks_db.json` maps username -> record. A record is an object: `{"tasks": [...], "current": "<created_at>"}`.
- Each task is an object with keys: `text`, `created_at` (UTC ISO string), `done` (boolean), `category` (optional string), and `priority` (boolean).

**Functions in `tasks.py`**

- **`load_db`**: Load the JSON DB from `tasks_db.json`. Returns a dict mapping usernames to records. If the file is missing or unreadable, returns `{}`. It migrates older formats where a user pointed to a plain list of tasks and converts them to the current `{ "tasks": [...], "current": "" }` shape.
	- Usage: called internally at startup; you can call it to inspect the raw DB file.

- **`save_db`**: Persist a Python dict to `tasks_db.json` with pretty JSON formatting.
	- Usage: called after mutating the `db` in other functions.

- **`list_tasks(db, user, category=None)`**: Print tasks for `user`. If `category` is provided, filters to that category. Shows index, current marker, done status, priority marker, category and when added.
	- Example: `list_tasks(db, "alice")` or via CLI `python tasks.py --user alice list --category groceries`.

- **`ensure_user_record(db, user)`**: Ensure `db` has a record object for `user`. If missing or in an old list format, create/convert it to `{ "tasks": [], "current": "" }` and return the record.
	- Useful to call when you are about to mutate a user's tasks.

- **`add_task(db, user, text, category="", priority=False)`**: Add a new task object to `user` with `created_at` set to current UTC ISO timestamp. Saves DB after adding.
	- CLI usage: `python tasks.py --user alice add "Do laundry" --category home --priority`.

- **`remove_task(db, user, index)`**: Remove the 1-based indexed task for `user`. If the removed task was the `current` task, clears `current`. Saves DB after removal.
	- Example: `remove_task(db, "alice", 2)` or `python tasks.py --user alice remove 2`.

- **`clear_tasks(db, user)`**: Remove all tasks for `user` and clear the current marker. Saves DB.
	- CLI: `python tasks.py --user alice clear`.

- **`mark_done(db, user, index)`**: Mark a task as done (sets `done` to `True`). Saves DB.
	- CLI: `python tasks.py --user alice done 2`.

- **`select_task(db, user, index)`**: Mark a task as the `current` task for `user` (stores the task's `created_at` in the record's `current` field). Saves DB.
	- CLI: `python tasks.py --user alice select 1`.

- **`show_current(db, user)`**: Print the currently selected task for `user`. If `current` is unset or the referenced task was removed, shows an appropriate message.
	- CLI: `python tasks.py --user alice current`.

- **`unselect_current(db, user)`**: Clear the `current` marker for `user` and save DB.
	- CLI: `python tasks.py --user alice unselect`.

- **`recommend_task(db, user, style)`**: Recommend and select a new `current` task for `user`. `style` can be `'type'` (same category as current) or `'dispersed'` (different category). Priority tasks (non-done and with `priority=True`) are always preferred. If no current is set, it falls back to prioritizing priority tasks or choosing a random not-done task.
	- CLI: `python tasks.py --user alice recommend --style dispersed`.

- **`promote_task(db, user, index)`**: Mark a task's `priority` field as `True`. Saves DB.
	- CLI: `python tasks.py --user alice promote 3`.

- **`demote_task(db, user, index)`**: Mark a task's `priority` field as `False`. Saves DB.

- **`list_priorities(db, user)`**: Print all tasks for `user` that are marked as priority.
	- CLI: `python tasks.py --user alice priorities`.

- **`_call_openai_chat(prompt)`**: Internal helper that calls the OpenAI Chat Completions API and returns the assistant content as a string. Requires `OPENAI_API_KEY` environment variable. The script expects the assistant to return only a JSON array of task objects (each with at least a `text` field).
	- Note: This is an internal helper; network errors or missing keys will raise exceptions. The calling code catches errors and falls back when appropriate.

- **`generate_list(db, user, prompt, use_ai=False)`**: Generate tasks from `prompt` for `user`. When `use_ai=True`, the prompt is sent to the AI (via `_call_openai_chat`) and the assistant response parsed as JSON; if parsing fails or the AI path errors, the function reports failure. When `use_ai=False` or AI isn't available, a safe fallback parser splits the prompt on newlines, commas, or semicolons and creates one task per item.
	- CLI examples:
		- Fallback parsing: `python tasks.py --user alice generate "Buy milk, Take out trash"`
		- AI parsing: `python tasks.py --user alice generate "Weekend chores" --ai` (requires `OPENAI_API_KEY`)

- **`interactive_mode(user)`**: Enter an interactive REPL for `user`. Available commands (short list): `add <text>`, `list [<category>]`, `remove <n>`, `done <n>`, `select <n>`, `current`, `unselect`, `clear`, `promote <n>`, `demote <n>`, `priorities`, `recommend`, `generate`, `quit`.
	- Start it: `python tasks.py interactive` or `python tasks.py --user alice interactive`.

- **`main(argv=None)`**: CLI entrypoint. Sets up `argparse` subcommands for all user-facing actions documented above and dispatches to the appropriate function. When run as `__main__`, `main()` is executed.

**Testing**

- Run the test suite with `pytest`:

```
python -m pytest -q
```

- `tests/test_tasks.py` (included) covers:
	- Creation and migration of DB records (`load_db`, `ensure_user_record`).
	- Adding/removing tasks, edge cases (index out of range), and that `remove` clears `current` when appropriate.
	- Marking done, selecting/unselecting current tasks, showing the current task.
	- Recommendation logic including priority selection and styles.
	- Promote/demote and listing priorities.
	- `generate_list` both in fallback mode and by mocking AI output.
	- `_call_openai_chat` raising when `OPENAI_API_KEY` is not present (tested indirectly by mocking).

**`run_generate_ai.py`**

- Helper script that exercises `generate_list` with `use_ai=True`.
- Behavior:
	- Uses the real OpenAI API if `OPENAI_API_KEY` is set and `--no-real` is not passed.
	- If the real API call fails (network, rate-limit, parsing), it falls back to a local mock so the run still produces tasks.
- Usage:

```
# Force mock even if API key exists
python run_generate_ai.py --no-real

# Change the prompt
python run_generate_ai.py --prompt "generate a list of household tasks"
```

**Development notes & next steps**

- Consider adding a small integration test that runs `run_generate_ai.py` with `--no-real` to verify end-to-end behavior without network access.
- Add a `requirements.txt` or `pyproject.toml` if you want pinned dependencies for CI.
- Add GitHub Actions to run `pytest` on push/PR.

If you'd like, I can commit the README, the tests, and the helper script, and open a PR for you.
- Data is stored in `tasks_db.json` as a mapping of username -> list of tasks.
