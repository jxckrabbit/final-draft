from pathlib import Path
import json
import os
import argparse
import tasks

# isolate DB file
tasks.DB_PATH = Path("tmp_ai_db.json")


def fake_ai(prompt: str) -> str:
    """Fallback fake AI response used when no OPENAI_API_KEY is available."""
    return json.dumps([
        {"text": "Vacuum the living room", "category": "cleaning", "priority": False},
        {"text": "Wash the dishes", "category": "kitchen", "priority": False},
        {"text": "Load the washing machine", "category": "laundry", "priority": True},
    ])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-real", action="store_true", help="Force use of the local mock instead of the real OpenAI API")
    parser.add_argument("--prompt", default="generate a list of household tasks", help="Prompt to generate tasks from")
    args = parser.parse_args()

    use_real = False
    if os.environ.get("OPENAI_API_KEY") and not args.no_real:
        use_real = True

    if use_real:
        print("OPENAI_API_KEY detected — using real OpenAI API to generate tasks.")
        # Wrap the real call so we can fall back to the local mock on network/errors
        real_call = tasks._call_openai_chat
        def wrapped_call(prompt: str) -> str:
            try:
                return real_call(prompt)
            except Exception as e:
                print(f"Real AI call failed, falling back to mock: {e}")
                return fake_ai(prompt)
        tasks._call_openai_chat = wrapped_call
    else:
        print("No OPENAI_API_KEY found (or --no-real). Using local mock for AI generation.")
        tasks._call_openai_chat = fake_ai

    print(f"Running generate_list with use_ai=True and prompt '{args.prompt}'...\n")

    db = {}
    tasks.generate_list(db, "ai_test_user", args.prompt, use_ai=True)

    print("\nIn-memory DB for user 'ai_test_user':")
    print(json.dumps(db.get("ai_test_user", {}), indent=2))

    # Show file content written to DB_PATH
    if tasks.DB_PATH.exists():
        print(f"\nContents of {tasks.DB_PATH} on disk:")
        print(tasks.DB_PATH.read_text())
    else:
        print(f"\nNo DB file written at {tasks.DB_PATH}")


if __name__ == "__main__":
    main()
