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
    if not rec:
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
        print(f"{i}.[{current_marker}] [{status}] {cat_display}{t.get('text')} (added {created})")


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


def add_task(db: Dict[str, List[Dict[str, str]]], user: str, text: str, category: str = "") -> None:
    rec = ensure_user_record(db, user)
    task = {
        "text": text,
        "created_at": datetime.utcnow().isoformat(),
        "done": False,
        "category": category or "",
    }
    rec["tasks"].append(task)
    save_db(db)
    print("Added.")


def remove_task(db: Dict[str, List[Dict[str, str]]], user: str, index: int) -> None:
    rec = db.get(user)
    if not rec:
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
    if not rec:
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
    if not rec:
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
    if not rec:
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
    if not rec:
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
    if not rec:
        print(f"No tasks for user '{user}'.")
        return
    rec = ensure_user_record(db, user)
    current_id = rec.get("current", "")
    if not current_id:
        # Fallback behavior: no current task set — pick a random not-done task as recommendation.
        tasks = rec.get("tasks", [])
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


def interactive_mode(user: str) -> None:
    db = load_db()
    print(f"Interactive mode for user '{user}'. Type 'help' for commands.")
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
            add_task(db, user, arg, cat)
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
        add_task(db, user, text, category)
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
    if args.cmd == "clear":
        clear_tasks(db, user)
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
