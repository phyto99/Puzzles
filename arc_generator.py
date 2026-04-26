"""
ARC generator — supports ARC-AGI-1 and ARC-AGI-2.

Submodule layout expected:
    ARC-AGI/data/training/*.json     (400 tasks, original)
    ARC-AGI-2/data/training/*.json   (1000 tasks, harder)
"""
import json
import os
import random

BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
_ROOTS = {
    "arc1": os.path.join(BASE_DIR, "ARC-AGI",   "data"),
    "arc2": os.path.join(BASE_DIR, "ARC-AGI-2",  "data"),
}


# ---------------------------------------------------------------------------
# Task loading
# ---------------------------------------------------------------------------

def _pick_file(version="arc2", split="any"):
    root = _ROOTS.get(version, _ROOTS["arc2"])
    dirs = []
    train = os.path.join(root, "training")
    evalu = os.path.join(root, "evaluation")
    if split in ("any", "train") and os.path.isdir(train):
        dirs.append(train)
    if split in ("any", "eval")  and os.path.isdir(evalu):
        dirs.append(evalu)

    files = []
    for d in dirs:
        files += [os.path.join(d, f) for f in os.listdir(d) if f.endswith(".json")]

    if not files:
        return None, f"No tasks found for {version} in {root}"

    path = random.choice(files)
    with open(path) as fh:
        return json.load(fh), os.path.basename(path).replace(".json", "")


# ---------------------------------------------------------------------------
# Grid helpers
# ---------------------------------------------------------------------------

def _norm(grid):
    return [[int(c) for c in row] for row in grid]


def _perturb(grid, strategy):
    g = [row[:] for row in grid]
    h, w = len(g), len(g[0]) if g else 0
    if strategy == "shift_r" and w > 1:
        for row in g: row.insert(0, row.pop())
    elif strategy == "shift_d" and h > 1:
        g.insert(0, g.pop())
    elif strategy == "flip_h":
        g = [row[::-1] for row in g]
    elif strategy == "flip_v":
        g = g[::-1]
    elif strategy == "color_swap":
        used = list({c for row in g for c in row if c != 0})
        if len(used) >= 2:
            a, b = random.sample(used, 2)
            g = [[b if c == a else a if c == b else c for c in row] for row in g]
    elif strategy == "replace_fg":
        used = list({c for row in g for c in row if c != 0})
        if used:
            old = random.choice(used)
            new = random.choice([x for x in range(1, 10) if x != old])
            g = [[new if c == old else c for c in row] for row in g]
    return g


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_problem(version="arc2", split="any"):
    task, task_id = _pick_file(version, split)
    if task is None:
        return {"error": task_id}

    test_pair   = task["test"][0]
    test_input  = _norm(test_pair["input"])
    correct_out = _norm(test_pair["output"])

    training = [
        {"input": _norm(p["input"]), "output": _norm(p["output"])}
        for p in task["train"][:3]
    ]

    return {
        "generator_type":  "arc",
        "version":         version,
        "task_id":         task_id,
        "training":        training,
        "test_input":      test_input,
        "correct_output":  correct_out,
    }
