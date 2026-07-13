import json
import os

STATE_FILE = os.path.join(os.path.dirname(__file__), "..", "state", "postgres.json")


def load_state():
    if not os.path.exists(STATE_FILE):
        return {"postgres_version": "", "pg_bigm_version": ""}
    with open(STATE_FILE, "r") as f:
        return json.load(f)


def save_state(state):
    # ディレクトリが存在しない場合は作成
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)
