"""
MARVEL generator.

Loads pre-rendered panel images from the MARVEL submodule
(github.com/1171-jpg/MARVEL_AVR) and returns them as base64 PNGs
alongside the answer index.

Panel file layout inside MARVEL/Panel_data/:
    question_{id}_{i}.png   — context panels (variable count)
    answer_{id}_{0-3}.png   — 4 answer choices (0-indexed)

Label JSON layout (MARVEL/Json_data/{id}/{id}_label.json):
    { "answer": <1-indexed int>, "pattern": ..., "task_configuration": ...,
      "explanation": ..., "avr_question": ... }
"""
import base64
import json
import os
import random

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
PANEL_DIR   = os.path.join(BASE_DIR, "MARVEL", "Panel_data")
JSON_DIR    = os.path.join(BASE_DIR, "MARVEL", "Json_data")
LABEL_FILE  = os.path.join(BASE_DIR, "MARVEL", "marvel_label.json")


def _b64(path):
    with open(path, "rb") as fh:
        return base64.b64encode(fh.read()).decode()


def _load_index():
    """Return list of valid puzzle IDs (those with all 4 answer panels present)."""
    with open(LABEL_FILE) as fh:
        labels = json.load(fh)

    valid = []
    for item in labels:
        pid = item["id"]
        # check answer panels exist
        if all(os.path.exists(os.path.join(PANEL_DIR, f"answer_{pid}_{i}.png"))
               for i in range(4)):
            valid.append(item)
    return valid


_INDEX = None  # lazy-loaded


def _get_index():
    global _INDEX
    if _INDEX is None:
        _INDEX = _load_index()
    return _INDEX


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_problem(pattern=None):
    """
    pattern: optional filter — one of 'Temporal Movement', 'Spatial Relationship',
             'Quantities', '2D-Geometry', '3D-Geometry', 'Mathematical'
    """
    index = _get_index()
    if not index:
        return {"error": "MARVEL submodule not found or Panel_data missing. "
                         "Run: git submodule update --init MARVEL"}

    pool = [x for x in index if pattern is None or x["pattern"] == pattern]
    if not pool:
        pool = index

    item = random.choice(pool)
    pid  = item["id"]

    # Context panels (question_N_0 .. question_N_k)
    context_panels = []
    i = 0
    while True:
        p = os.path.join(PANEL_DIR, f"question_{pid}_{i}.png")
        if not os.path.exists(p):
            break
        context_panels.append(_b64(p))
        i += 1

    # 4 answer choices
    choices = [_b64(os.path.join(PANEL_DIR, f"answer_{pid}_{j}.png"))
               for j in range(4)]

    # answer is 1-indexed in the JSON → convert to 0-indexed
    target = item["answer"] - 1

    return {
        "generator_type":     "marvel",
        "puzzle_id":          pid,
        "pattern":            item["pattern"],
        "task_configuration": item["task_configuration"],
        "question":           item["avr_question"],
        "explanation":        item.get("explanation", ""),
        "context_panels":     context_panels,
        "choices":            choices,
        "target":             target,
    }
