#!/usr/bin/env python3
"""Simple per-username task list CLI.

Usage examples:
  python tasks.py --user alice add "Buy milk"
  python tasks.py --user alice list
  python tasks.py --user alice remove 2
  python tasks.py --user alice clear
  python tasks.py interactive   # prompts for username then enters interactive mode
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
import random
import os
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, List


DB_PATH = Path(__file__).parent / "tasks_db.json"


def load_db() -> Dict[str, List[Dict[str, str]]]:
    if not DB_PATH.exists():
        return {}
    try:
        with DB_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
            # migrate older format where user -> list(tasks) into {"tasks": [...], "current": ""}
            for user, val in list(data.items()):
                if isinstance(val, list):
                    data[user] = {"tasks": val, "current": ""}
                elif isinstance(val, dict):
                    # ensure keys exist
                    if "tasks" in val and "current" not in val:
                        val.setdefault("current", "")
            return data
    except Exception:
        return {}


def save_db(db: Dict[str, List[Dict[str, str]]]) -> None:
    with DB_PATH.open("w", encoding="utf-8") as f:
        json.dump(db, f, indent=2, ensure_ascii=False)


def list_tasks(db: Dict[str, List[Dict[str, str]]], user: str, category: str | None = None) -> None:
    rec = db.get(user)
    if rec is None:
        print(f"No tasks for user '{user}'.")
        return
    tasks = rec.get("tasks", []) if isinstance(rec, dict) else rec
    current_id = rec.get("current", "") if isinstance(rec, dict) else ""
    if not tasks:
        print(f"No tasks for user '{user}'.")
        return
    filtered = tasks
    if category:
        filtered = [t for t in tasks if (t.get("category") or "") == category]
        if not filtered:
            print(f"No tasks for category '{category}' for user '{user}'.")
            return
    for i, t in enumerate(filtered, start=1):
        status = "x" if t.get("done") else " "
        created = t.get("created_at", "")
        category = t.get("category", "")
        cat_display = f"[{category}] " if category else ""
        current_marker = ">" if created and current_id and created == current_id else " "
        priority_label = "(!) " if t.get("priority") else ""
        print(f"{i}.[{current_marker}] [{status}] {priority_label}{cat_display}{t.get('text')} (added {created})")


def ensure_user_record(db: Dict[str, object], user: str) -> Dict[str, object]:
    rec = db.get(user)
    if rec is None:
        rec = {"tasks": [], "current": ""}
        db[user] = rec
    elif isinstance(rec, list):
        rec = {"tasks": rec, "current": ""}
        db[user] = rec
    else:
        # ensure keys
        rec.setdefault("tasks", [])
        rec.setdefault("current", "")
    return rec


def add_task(db: Dict[str, List[Dict[str, str]]], user: str, text: str, category: str = "", priority: bool = False) -> None:
    rec = ensure_user_record(db, user)
    task = {
        "text": text,
        "created_at": datetime.utcnow().isoformat(),
        "done": False,
        "category": category or "",
        "priority": bool(priority),
    }
    rec["tasks"].append(task)
    save_db(db)
    print("Added.")
    


def remove_task(db: Dict[str, List[Dict[str, str]]], user: str, index: int) -> None:
    rec = db.get(user)
    if rec is None:
        print(f"No tasks for user '{user}'.")
        return
    tasks = rec.get("tasks", []) if isinstance(rec, dict) else rec
    if index < 1 or index > len(tasks):
        print("Index out of range.")
        return
    removed = tasks.pop(index - 1)
    # clear current if it pointed to removed task
    if isinstance(rec, dict) and rec.get("current") == removed.get("created_at"):
        rec["current"] = ""
    save_db(db)
    print(f"Removed: {removed.get('text')}")


def clear_tasks(db: Dict[str, List[Dict[str, str]]], user: str) -> None:
    rec = ensure_user_record(db, user)
    rec["tasks"] = []
    rec["current"] = ""
    save_db(db)
    print(f"Cleared tasks for '{user}'.")


def mark_done(db: Dict[str, List[Dict[str, str]]], user: str, index: int) -> None:
    rec = db.get(user)
    if rec is None:
        print(f"No tasks for user '{user}'.")
        return
    tasks = rec.get("tasks", []) if isinstance(rec, dict) else rec
    if index < 1 or index > len(tasks):
        print("Index out of range.")
        return
    tasks[index - 1]["done"] = True
    save_db(db)
    print(f"Marked done: {tasks[index-1].get('text')}")


def select_task(db: Dict[str, List[Dict[str, str]]], user: str, index: int) -> None:
    rec = db.get(user)
    if rec is None:
        print(f"No tasks for user '{user}'.")
        return
    tasks = rec.get("tasks", []) if isinstance(rec, dict) else rec
    if index < 1 or index > len(tasks):
        print("Index out of range.")
        return
    chosen = tasks[index - 1]
    rec = ensure_user_record(db, user)
    rec["current"] = chosen.get("created_at", "")
    save_db(db)
    print(f"Selected current task: {chosen.get('text')}")


def show_current(db: Dict[str, List[Dict[str, str]]], user: str) -> None:
    rec = db.get(user)
    if rec is None:
        print(f"No tasks for user '{user}'.")
        return
    rec = ensure_user_record(db, user)
    current_id = rec.get("current", "")
    if not current_id:
        print("No current task set.")
        return
    for i, t in enumerate(rec.get("tasks", []), start=1):
        if t.get("created_at") == current_id:
            status = "x" if t.get("done") else " "
            category = t.get("category", "")
            cat_display = f"[{category}] " if category else ""
            print(f"{i}. [{status}] {cat_display}{t.get('text')} (added {t.get('created_at')})")
            return
    print("Current task not found (it may have been removed).")


def unselect_current(db: Dict[str, List[Dict[str, str]]], user: str) -> None:
    rec = db.get(user)
    if rec is None:
        print(f"No tasks for user '{user}'.")
        return
    rec = ensure_user_record(db, user)
    rec["current"] = ""
    save_db(db)
    print("Cleared current task.")


def recommend_task(db: Dict[str, List[Dict[str, str]]], user: str, style: str) -> None:
    """Recommend a task for `user`.

    style: 'type' -> recommend a task in the same category as current
           'dispersed' -> recommend a task in a different category than current
    The recommended task becomes the new current task.
    """
    rec = db.get(user)
    if rec is None:
        print(f"No tasks for user '{user}'.")
        return
    rec = ensure_user_record(db, user)
    current_id = rec.get("current", "")
    if not current_id:
        # Fallback behavior: no current task set — prefer priority tasks, else pick a random not-done task.
        tasks = rec.get("tasks", [])
        priority_candidates = [t for t in tasks if t.get("priority") and not t.get("done")]
        if priority_candidates:
            chosen = random.choice(priority_candidates)
            rec["current"] = chosen.get("created_at", "")
            save_db(db)
            print(f"No current task set — prioritized fallback recommended and selected: {chosen.get('text')} [{chosen.get('category','')}]")
            return
        candidates = [t for t in tasks if not t.get("done")]
        if not candidates:
            print("No available (not-done) tasks to recommend.")
            return
        chosen = random.choice(candidates)
        rec["current"] = chosen.get("created_at", "")
        save_db(db)
        print(f"No current task set — fallback recommended and selected: {chosen.get('text')} [{chosen.get('category','')}]")
        return
    tasks = rec.get("tasks", [])
    current = None
    for t in tasks:
        if t.get("created_at") == current_id:
            current = t
            break
    if current is None:
        print("Current task not found. It may have been removed.")
        return

    cur_cat = (current.get("category") or "")
    # Priority tasks are always preferred regardless of style
    priority_candidates = [t for t in tasks if t.get("priority") and not t.get("done") and t.get("created_at") != current_id]
    if priority_candidates:
        chosen = random.choice(priority_candidates)
        rec["current"] = chosen.get("created_at", "")
        save_db(db)
        print(f"Recommended and selected priority task: {chosen.get('text')} [{chosen.get('category','')}]")
        return

    # choose candidates depending on style
    if style == "type":
        candidates = [t for t in tasks if (t.get("category") or "") == cur_cat and t.get("created_at") != current_id and not t.get("done")]
    else:
        # dispersed: different category and not done
        candidates = [t for t in tasks if (t.get("category") or "") != cur_cat and not t.get("done")]

    if not candidates:
        print(f"No recommendation found for style '{style}'.")
        return

    # Pick a candidate (random for variety)
    chosen = random.choice(candidates)
    rec["current"] = chosen.get("created_at", "")
    save_db(db)
    print(f"Recommended and selected current task: {chosen.get('text')} [{chosen.get('category','')}]")


def promote_task(db: Dict[str, List[Dict[str, str]]], user: str, index: int) -> None:
    rec = db.get(user)
    if rec is None:
        print(f"No tasks for user '{user}'.")
        return
    rec = ensure_user_record(db, user)
    tasks = rec.get("tasks", [])
    if index < 1 or index > len(tasks):
        print("Index out of range.")
        return
    tasks[index - 1]["priority"] = True
    save_db(db)
    print(f"Promoted task {index} to priority: {tasks[index-1].get('text')}")


def demote_task(db: Dict[str, List[Dict[str, str]]], user: str, index: int) -> None:
    rec = db.get(user)
    if rec is None:
        print(f"No tasks for user '{user}'.")
        return
    rec = ensure_user_record(db, user)
    tasks = rec.get("tasks", [])
    if index < 1 or index > len(tasks):
        print("Index out of range.")
        return
    tasks[index - 1]["priority"] = False
    save_db(db)
    print(f"Demoted task {index} from priority: {tasks[index-1].get('text')}")


def list_priorities(db: Dict[str, List[Dict[str, str]]], user: str) -> None:
    rec = db.get(user)
    if rec is None:
        print(f"No tasks for user '{user}'.")
        return
    rec = ensure_user_record(db, user)
    tasks = rec.get("tasks", [])
    priority_tasks = [(i + 1, t) for i, t in enumerate(tasks) if t.get("priority")]
    if not priority_tasks:
        print(f"No priority tasks for user '{user}'.")
        return
    for idx, t in priority_tasks:
        status = "x" if t.get("done") else " "
        cat = t.get("category", "")
        cat_display = f"[{cat}] " if cat else ""
        print(f"{idx}. [{status}] {cat_display}{t.get('text')} (added {t.get('created_at')})")


def _call_openai_chat(prompt: str) -> str:
    """Call OpenAI Chat Completions API and return assistant content as string.

    Requires environment variable `OPENAI_API_KEY`. Uses `gpt-3.5-turbo`.
    Returns the assistant message text or raises on network/HTTP errors.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set")

    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    system = {
        "role": "system",
        "content": (
            "You are a task-list generator. Given a short user prompt, produce a JSON array of objects. "
            "Each object must have at least a 'text' field and may include 'category' and 'priority' (boolean). "
            "Respond with ONLY valid JSON (the array) and nothing else."
        ),
    }
    user_msg = {"role": "user", "content": prompt}
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [system, user_msg],
        "temperature": 0.7,
        "max_tokens": 800,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=15) as resp:
        body = resp.read().decode("utf-8")
    parsed = json.loads(body)
    # standard response path
    content = parsed.get("choices", [])[0].get("message", {}).get("content", "")
    return content


def generate_list(db: Dict[str, List[Dict[str, str]]], user: str, prompt: str, use_ai: bool = False) -> None:
    """Generate tasks for `user` from `prompt`.

    If `use_ai` is True and `OPENAI_API_KEY` env var is set, the prompt will be sent to OpenAI
    to produce a JSON array of tasks. Otherwise a safe fallback parser splits the prompt into
    list items (by newline or comma).
    """
    rec = ensure_user_record(db, user)

    generated: List[Dict[str, object]] = []

    if use_ai:
        try:
            content = _call_openai_chat(prompt)
        except Exception:
            print("generation failed: no AI available")
            return

        # try to parse the assistant content as JSON array
        try:
            items = json.loads(content)
            if isinstance(items, list):
                for it in items:
                    if isinstance(it, dict) and it.get("text"):
                        generated.append(it)
        except Exception:
            # try to extract JSON substring
            start = content.find("[")
            end = content.rfind("]")
            if start != -1 and end != -1 and end > start:
                try:
                    items = json.loads(content[start : end + 1])
                    if isinstance(items, list):
                        for it in items:
                            if isinstance(it, dict) and it.get("text"):
                                generated.append(it)
                except Exception:
                    pass

        # If AI was requested but parsing returned nothing, treat as failure and stop
        if not generated:
            print("generation failed: no AI available")
            return

    # fallback if nothing generated via AI
    if not generated:
        # simple parsing: split by newline, then commas
        parts: List[str] = []
        if "\n" in prompt:
            parts = [p.strip() for p in prompt.splitlines() if p.strip()]
        elif "," in prompt:
            parts = [p.strip() for p in prompt.split(",") if p.strip()]
        else:
            # split by semicolon or use whole prompt as one item
            if ";" in prompt:
                parts = [p.strip() for p in prompt.split(";") if p.strip()]
            else:
                parts = [prompt.strip()] if prompt.strip() else []

        for p in parts:
            generated.append({"text": p, "category": "", "priority": False})

    # store generated tasks
    added = 0
    for item in generated:
        text = item.get("text")
        if not text:
            continue
        category = item.get("category", "") or ""
        priority = bool(item.get("priority", False))
        add_task(db, user, text, category, priority)
        added += 1

    print(f"Generated and added {added} tasks for user '{user}'.")


def interactive_mode(user: str) -> None:
    db = load_db()
    print(f"Interactive mode for user '{user}'. Type 'help' for commands.")
    # Immediately show priority tasks for this user (not-done)
    rec = db.get(user)
    if rec:
        rec = ensure_user_record(db, user)
        tasks = rec.get("tasks", [])
        priority_tasks = [(i + 1, t) for i, t in enumerate(tasks) if t.get("priority") and not t.get("done")]
        if priority_tasks:
            print("Priority tasks:")
            for idx, t in priority_tasks:
                cat = t.get("category", "")
                cat_display = f"[{cat}] " if cat else ""
                print(f"{idx}. {cat_display}{t.get('text')}")
    while True:
        try:
            cmd = input(f"{user}> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not cmd:
            continue
        parts = cmd.split(maxsplit=1)
        action = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ""

        if action in ("q", "quit", "exit"):
            break
        if action in ("h", "help"):
            print("Commands: add <text>, list, remove <n>, done <n>, select <n>, current, unselect, clear, quit")
            continue
        if action == "add":
            if not arg:
                print("Usage: add <task text>")
                continue
            try:
                cat = input("Category (optional): ").strip()
            except (EOFError, KeyboardInterrupt):
                cat = ""
            try:
                pr = input("Priority? (y/N): ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                pr = ""
            is_priority = pr in ("y", "yes")
            add_task(db, user, arg, cat, is_priority)
            continue
        if action == "list":
            # support: `list` or `list <category>` in interactive mode
            list_tasks(db, user, arg or None)
            continue
        if action == "remove":
            if not arg or not arg.isdigit():
                print("Usage: remove <index>")
                continue
            remove_task(db, user, int(arg))
            continue
        if action == "select":
            if not arg or not arg.isdigit():
                print("Usage: select <index>")
                continue
            select_task(db, user, int(arg))
            continue
        if action == "promote":
            if not arg or not arg.isdigit():
                print("Usage: promote <index>")
                continue
            promote_task(db, user, int(arg))
            continue
        if action == "demote":
            if not arg or not arg.isdigit():
                print("Usage: demote <index>")
                continue
            demote_task(db, user, int(arg))
            continue
        if action == "priorities":
            list_priorities(db, user)
            continue
        if action == "recommend":
            # recommend [style]
            style = arg.strip().lower() if arg else ""
            if not style:
                try:
                    style = input("Style (type/dispersed): ").strip()
                except (EOFError, KeyboardInterrupt):
                    print("No style provided.")
                    continue
            if style not in ("type", "dispersed"):
                print("Invalid style. Use 'type' or 'dispersed'.")
                continue
            recommend_task(db, user, style)
            continue
        if action == "generate":
            # generate <prompt>  (optional ai: provide 'ai' as the second token)
            prompt = arg
            use_ai = False
            if not prompt:
                try:
                    prompt = input("Prompt to generate tasks from: ").strip()
                except (EOFError, KeyboardInterrupt):
                    print("No prompt provided.")
                    continue
            # allow 'generate ai <prompt>' style or ask
            if prompt.startswith("ai "):
                use_ai = True
                prompt = prompt[3:].strip()
            else:
                try:
                    ans = input("Use AI? (y/N): ").strip().lower()
                except (EOFError, KeyboardInterrupt):
                    ans = ""
                use_ai = ans in ("y", "yes")
            generate_list(db, user, prompt, use_ai)
            continue
        if action == "current":
            show_current(db, user)
            continue
        if action == "unselect":
            unselect_current(db, user)
            continue
        if action == "done":
            if not arg or not arg.isdigit():
                print("Usage: done <index>")
                continue
            mark_done(db, user, int(arg))
            continue
        if action == "clear":
            clear_tasks(db, user)
            continue
        print("Unknown command. Type 'help'.")


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Per-user task list CLI")
    parser.add_argument("--user", "-u", help="username (if omitted, interactive mode prompts for it)")

    sub = parser.add_subparsers(dest="cmd")

    p_add = sub.add_parser("add", help="Add a task")
    p_add.add_argument("text", nargs="+", help="Task text")
    p_add.add_argument("--category", "-c", help="Optional category for the task")
    p_add.add_argument("--priority", "-p", action="store_true", help="Mark the new task as priority")

    p_list = sub.add_parser("list", help="List tasks")
    p_list.add_argument("--category", "-c", help="Filter tasks by category")

    p_remove = sub.add_parser("remove", help="Remove task by index")
    p_remove.add_argument("index", type=int, help="1-based index of task to remove")

    p_done = sub.add_parser("done", help="Mark task done by index")
    p_done.add_argument("index", type=int, help="1-based index of task to mark done")

    p_clear = sub.add_parser("clear", help="Clear all tasks for user")

    p_select = sub.add_parser("select", help="Select a task as current by index")
    p_select.add_argument("index", type=int, help="1-based index of task to select as current")

    p_current = sub.add_parser("current", help="Show current task for user")

    p_unselect = sub.add_parser("unselect", help="Clear current task for user")

    p_recommend = sub.add_parser("recommend", help="Recommend a task based on current task and style")
    p_recommend.add_argument("--style", "-s", choices=["type", "dispersed"], help="Recommendation style: type or dispersed")

    p_generate = sub.add_parser("generate", help="Generate tasks from a prompt (AI or fallback)")
    p_generate.add_argument("text", nargs="+", help="Prompt text to generate tasks from")
    p_generate.add_argument("--ai", action="store_true", help="Use AI (requires OPENAI_API_KEY env var)")

    p_promote = sub.add_parser("promote", help="Mark a task as priority by index")
    p_promote.add_argument("index", type=int, help="1-based index of task to promote")

    p_demote = sub.add_parser("demote", help="Unmark a task as priority by index")
    p_demote.add_argument("index", type=int, help="1-based index of task to demote")

    p_priorities = sub.add_parser("priorities", help="List priority tasks for the user")

    p_inter = sub.add_parser("interactive", help="Enter interactive mode (prompts for user if omitted)")

    args = parser.parse_args(argv)

    user = args.user
    if not user and args.cmd != "interactive":
        print("Please provide --user or run the 'interactive' command.")
        return 2

    if args.cmd == "interactive":
        if not user:
            try:
                user = input("Username: ").strip()
            except (EOFError, KeyboardInterrupt):
                return 1
            if not user:
                print("Username required.")
                return 2
        interactive_mode(user)
        return 0

    db = load_db()
    if args.cmd == "add":
        text = " ".join(args.text)
        category = getattr(args, "category", "") or ""
        priority = bool(getattr(args, "priority", False))
        add_task(db, user, text, category, priority)
        return 0
    if args.cmd == "list":
        list_tasks(db, user, getattr(args, "category", None))
        return 0
    if args.cmd == "remove":
        remove_task(db, user, args.index)
        return 0
    if args.cmd == "done":
        mark_done(db, user, args.index)
        return 0
    if args.cmd == "select":
        select_task(db, user, args.index)
        return 0
    if args.cmd == "current":
        show_current(db, user)
        return 0
    if args.cmd == "unselect":
        unselect_current(db, user)
        return 0
    if args.cmd == "recommend":
        style = getattr(args, "style", None)
        if not style:
            try:
                style = input("Style (type/dispersed): ").strip()
            except (EOFError, KeyboardInterrupt):
                print("No style provided.")
                return 1
        if style not in ("type", "dispersed"):
            print("Invalid style. Use 'type' or 'dispersed'.")
            return 2
        recommend_task(db, user, style)
        return 0
    if args.cmd == "generate":
        prompt = " ".join(args.text)
        use_ai = bool(getattr(args, "ai", False))
        generate_list(db, user, prompt, use_ai)
        return 0
    if args.cmd == "promote":
        promote_task(db, user, args.index)
        return 0
    if args.cmd == "demote":
        demote_task(db, user, args.index)
        return 0
    if args.cmd == "priorities":
        list_priorities(db, user)
        return 0
    if args.cmd == "clear":
        clear_tasks(db, user)
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
