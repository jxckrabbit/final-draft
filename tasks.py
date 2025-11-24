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
from pathlib import Path
from typing import Dict, List


DB_PATH = Path(__file__).parent / "tasks_db.json"


def load_db() -> Dict[str, List[Dict[str, str]]]:
    if not DB_PATH.exists():
        return {}
    try:
        with DB_PATH.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_db(db: Dict[str, List[Dict[str, str]]]) -> None:
    with DB_PATH.open("w", encoding="utf-8") as f:
        json.dump(db, f, indent=2, ensure_ascii=False)


def list_tasks(db: Dict[str, List[Dict[str, str]]], user: str) -> None:
    tasks = db.get(user, [])
    if not tasks:
        print(f"No tasks for user '{user}'.")
        return
    for i, t in enumerate(tasks, start=1):
        status = "x" if t.get("done") else " "
        created = t.get("created_at", "")
        category = t.get("category", "")
        cat_display = f"[{category}] " if category else ""
        print(f"{i}. [{status}] {cat_display}{t.get('text')} (added {created})")


def add_task(db: Dict[str, List[Dict[str, str]]], user: str, text: str, category: str = "") -> None:
    tasks = db.setdefault(user, [])
    tasks.append({
        "text": text,
        "created_at": datetime.utcnow().isoformat(),
        "done": False,
        "category": category or "",
    })
    save_db(db)
    print("Added.")


def remove_task(db: Dict[str, List[Dict[str, str]]], user: str, index: int) -> None:
    tasks = db.get(user, [])
    if not tasks:
        print(f"No tasks for user '{user}'.")
        return
    if index < 1 or index > len(tasks):
        print("Index out of range.")
        return
    removed = tasks.pop(index - 1)
    save_db(db)
    print(f"Removed: {removed.get('text')}")


def clear_tasks(db: Dict[str, List[Dict[str, str]]], user: str) -> None:
    if user in db:
        db[user] = []
        save_db(db)
    print(f"Cleared tasks for '{user}'.")


def mark_done(db: Dict[str, List[Dict[str, str]]], user: str, index: int) -> None:
    tasks = db.get(user, [])
    if not tasks:
        print(f"No tasks for user '{user}'.")
        return
    if index < 1 or index > len(tasks):
        print("Index out of range.")
        return
    tasks[index - 1]["done"] = True
    save_db(db)
    print(f"Marked done: {tasks[index-1].get('text')}")


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
            print("Commands: add <text>, list, remove <n>, done <n>, clear, quit")
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
            list_tasks(db, user)
            continue
        if action == "remove":
            if not arg or not arg.isdigit():
                print("Usage: remove <index>")
                continue
            remove_task(db, user, int(arg))
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

    p_remove = sub.add_parser("remove", help="Remove task by index")
    p_remove.add_argument("index", type=int, help="1-based index of task to remove")

    p_done = sub.add_parser("done", help="Mark task done by index")
    p_done.add_argument("index", type=int, help="1-based index of task to mark done")

    p_clear = sub.add_parser("clear", help="Clear all tasks for user")

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
        list_tasks(db, user)
        return 0
    if args.cmd == "remove":
        remove_task(db, user, args.index)
        return 0
    if args.cmd == "done":
        mark_done(db, user, args.index)
        return 0
    if args.cmd == "clear":
        clear_tasks(db, user)
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
