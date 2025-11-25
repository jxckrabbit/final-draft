import json
import os
import random
import importlib
from pathlib import Path
from datetime import datetime

import pytest

import tasks


@pytest.fixture(autouse=True)
def reset_module(monkeypatch, tmp_path):
    # Point DB_PATH to a temporary file for isolation
    tmp_db = tmp_path / "tasks_db.json"
    monkeypatch.setattr(tasks, "DB_PATH", tmp_db)
    # Ensure random is deterministic for tests that rely on randomness
    random.seed(0)
    yield


def test_ensure_user_record_creates():
    db = {}
    rec = tasks.ensure_user_record(db, "alice")
    assert isinstance(rec, dict)
    assert "tasks" in rec and isinstance(rec["tasks"], list)
    assert db["alice"] is rec


def test_load_db_malformed_file(tmp_path):
    p = tmp_path / "tasks_db.json"
    p.write_text("not a json")
    # monkeypatch tasks.DB_PATH to this path
    tasks.DB_PATH = p
    data = tasks.load_db()
    assert data == {}


def test_add_and_list_and_save_and_load(capsys):
    db = {}
    tasks.add_task(db, "bob", "Buy milk", category="home", priority=True)
    # listing should show the added task
    tasks.list_tasks(db, "bob")
    out = capsys.readouterr().out
    assert "Buy milk" in out
    assert "home" in out or "[home]" in out
    assert "(!)" in out
    # save happened; the DB_PATH file should exist and load_db should read it
    loaded = tasks.load_db()
    assert "bob" in loaded


def test_list_no_user(capsys):
    db = {}
    tasks.list_tasks(db, "charlie")
    out = capsys.readouterr().out
    assert "No tasks for user 'charlie'." in out


def test_remove_invalid_and_valid_behaviour(capsys):
    db = {}
    tasks.add_task(db, "dan", "one")
    tasks.remove_task(db, "dan", 5)
    out = capsys.readouterr().out
    assert "Index out of range." in out
    # remove valid
    tasks.remove_task(db, "dan", 1)
    out2 = capsys.readouterr().out
    assert "Removed:" in out2


def test_remove_clears_current():
    db = {}
    tasks.add_task(db, "eve", "first")
    tasks.add_task(db, "eve", "second")
    tasks.select_task(db, "eve", 1)
    rec = db["eve"]
    assert rec.get("current") != ""
    tasks.remove_task(db, "eve", 1)
    rec2 = db["eve"]
    assert rec2.get("current", "") == ""


def test_mark_done_and_edge_cases(capsys):
    db = {}
    tasks.add_task(db, "flo", "t")
    tasks.mark_done(db, "flo", 1)
    assert db["flo"]["tasks"][0]["done"] is True
    tasks.mark_done(db, "flo", 5)
    out = capsys.readouterr().out
    assert "Index out of range." in out


def test_select_show_unselect_current(capsys):
    db = {}
    tasks.add_task(db, "gail", "taskA")
    tasks.select_task(db, "gail", 1)
    tasks.show_current(db, "gail")
    out = capsys.readouterr().out
    assert "taskA" in out
    tasks.unselect_current(db, "gail")
    out2 = capsys.readouterr().out
    assert "Cleared current task." in out2


def test_show_current_when_missing(capsys):
    db = {}
    tasks.add_task(db, "hank", "t1")
    # select then remove -> current missing
    tasks.select_task(db, "hank", 1)
    tasks.remove_task(db, "hank", 1)
    tasks.show_current(db, "hank")
    out = capsys.readouterr().out
    assert "Current task not found" in out or "No current task set." in out


def test_recommend_priority_and_styles():
    db = {}
    tasks.add_task(db, "ivy", "low")
    tasks.add_task(db, "ivy", "urgent", priority=True)
    tasks.select_task(db, "ivy", 1)
    tasks.recommend_task(db, "ivy", "type")
    cur = db["ivy"]["current"]
    assert any(t["created_at"] == cur and t["text"] == "urgent" for t in db["ivy"]["tasks"])


def test_promote_demote_and_list_priorities(capsys):
    db = {}
    tasks.add_task(db, "john", "a")
    tasks.promote_task(db, "john", 1)
    out = capsys.readouterr().out
    assert "Promoted task" in out
    tasks.list_priorities(db, "john")
    out2 = capsys.readouterr().out
    assert "a" in out2
    tasks.demote_task(db, "john", 1)
    out3 = capsys.readouterr().out
    assert "Demoted task" in out3


def test_generate_list_fallback_and_ai(monkeypatch, capsys):
    db = {}
    tasks.generate_list(db, "kate", "one, two", use_ai=False)
    out = capsys.readouterr().out
    assert "Generated and added 2 tasks" in out
    assert len(db["kate"]["tasks"]) == 2

    # AI path: mock _call_openai_chat
    def fake_ai(prompt):
        return '[{"text": "AI task", "category": "ai", "priority": true}]'

    monkeypatch.setattr(tasks, "_call_openai_chat", fake_ai)
    tasks.generate_list(db, "kate", "ai prompt", use_ai=True)
    out2 = capsys.readouterr().out
    assert "Generated and added 1 tasks" in out2
    assert any(t["text"] == "AI task" for t in db["kate"]["tasks"]) 


def test__call_openai_chat_raises_without_key(monkeypatch):
    # Ensure OPENAI_API_KEY not set
    if "OPENAI_API_KEY" in os.environ:
        del os.environ["OPENAI_API_KEY"]
    with pytest.raises(RuntimeError):
        tasks._call_openai_chat("hello")


def test_load_db_migrates_older_format(tmp_path):
    p = tmp_path / "tasks_db.json"
    # older format: user -> list of tasks
    now = datetime.utcnow().isoformat()
    older = {"liz": [{"text": "oldtask", "created_at": now, "done": False}]}
    p.write_text(json.dumps(older))
    tasks.DB_PATH = p
    data = tasks.load_db()
    assert isinstance(data.get("liz"), dict)
    assert "tasks" in data["liz"]
    assert data["liz"].get("current", "") == ""
