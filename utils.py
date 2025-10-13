import os
import json

VERBOSE = True

def load_trials():
    candidates = [
        os.path.join(os.path.dirname(__file__), "..", "results", "ste_trials.json"),
        os.path.join(os.path.dirname(__file__), "..", "Exploration", "results", "ste_trials.json"),
        os.path.join(os.path.dirname(__file__), "results", "ste_trials.json"),
        "ste_trials.json",
    ]
    for p in candidates:
        p = os.path.abspath(p)
        try:
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
                demos = [t for t in data if t.get("success", False)]
                if VERBOSE:
                    print(f"[load_trials] loaded {len(demos)} successful trials from: {p}")
                return demos
        except FileNotFoundError:
            continue
    raise FileNotFoundError(
        "找不到 ste_trials.json，請確認 Exploration 是否已產出 results/ste_trials.json。"
    )
