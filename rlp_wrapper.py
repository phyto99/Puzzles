"""
RLP (Simon Tatham's Portable Puzzle Collection) — WSL subprocess bridge.

Called by unified_server.py via subprocess to avoid Windows/Linux conflicts.

Protocol:
  argv[1]: command — "envs" | "new" | "step"
  argv[2..]: JSON argument

  new:  {"puzzle": "flood"}
        -> {session_id, frame_b64, action_space_n, info}
  step: {"session_id": "...", "action": 3}
        -> {frame_b64, reward, terminated, truncated, info}
  envs: (no args)
        -> [{id, name, description, action_n}]
"""
import base64
import io
import json
import os
import sys
import threading

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "hide"

RLP_PATH = "/opt/rlp"
RLP_ENV  = "/opt/rlp-env/bin/python"

# Must set these before importing rlp/gymnasium
sys.path.insert(0, RLP_PATH)

import rlp
import gymnasium as gym
import numpy as np
from PIL import Image


PUZZLE_META = {
    "flood":     ("Flood",      "Turn the grid the same colour in as few moves as possible."),
    "net":       ("Net",        "Rotate tiles to connect the network."),
    "flip":      ("Flip",       "Flip groups of squares to light them all up."),
    "fifteen":   ("Fifteen",    "Slide tiles into order — the classic 15-puzzle."),
    "bridges":   ("Bridges",    "Connect all islands with bridges without crossings."),
    "loopy":     ("Loopy",      "Draw a single closed loop through the dots."),
    "slant":     ("Slant",      "Draw diagonal lines to form a single connected tree."),
    "signpost":  ("Signpost",   "Follow the arrows to order the squares 1..N."),
    "untangle":  ("Untangle",   "Move the dots so no lines cross."),
    "lights":    ("LightUp",    "Light all squares using the bulbs."),
    "pattern":   ("Pattern",    "Fill cells to match the row/column counts (nonogram)."),
    "rect":      ("Rectangles", "Divide into rectangles each containing its number."),
    "mines":     ("Minesweeper","Classic Minesweeper — find all mines."),
    "solo":      ("Sudoku",     "Fill the grid with numbers — no repeats in row/col/box."),
}

_sessions: dict[str, object] = {}
_lock = threading.Lock()
_session_ctr = 0


def _frame_to_b64(img_array: np.ndarray) -> str:
    img = Image.fromarray(img_array.astype(np.uint8))
    bbox = img.getbbox()
    if bbox:
        img = img.crop(bbox)
    img = img.resize((512, 512), Image.NEAREST)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def cmd_envs():
    result = []
    for internal, (name, desc) in PUZZLE_META.items():
        # Check .so exists before listing
        so = f"/opt/rlp/rlp/lib/lib{internal}.so"
        if not os.path.exists(so):
            continue
        result.append({"id": internal, "name": name, "description": desc})
    return result


def cmd_new(args):
    global _session_ctr
    puzzle = args.get("puzzle", "flood")
    env_id = f"rlp/{PUZZLE_META[puzzle][0]}-v0"
    env = gym.make(env_id, render_mode="rgb_array")
    obs, info = env.reset()
    img = env.render()

    with _lock:
        _session_ctr += 1
        sid = f"rlp_{_session_ctr}"
        _sessions[sid] = {"env": env, "puzzle": puzzle, "steps": 0}

    return {
        "session_id":    sid,
        "frame_b64":     _frame_to_b64(img),
        "action_space_n": int(env.action_space.n),
        "puzzle":        puzzle,
        "name":          PUZZLE_META[puzzle][0],
        "description":   PUZZLE_META[puzzle][1],
    }


def cmd_step(args):
    sid    = args["session_id"]
    action = int(args["action"])

    with _lock:
        sess = _sessions.get(sid)
    if sess is None:
        return {"error": "session_not_found"}

    env = sess["env"]
    obs, reward, terminated, truncated, info = env.step(action)
    img = env.render()
    sess["steps"] += 1
    done = terminated or truncated

    if done:
        with _lock:
            _sessions.pop(sid, None)
        env.close()

    return {
        "session_id": sid,
        "frame_b64":  _frame_to_b64(img),
        "reward":     float(reward),
        "terminated": bool(terminated),
        "truncated":  bool(truncated),
        "done":       done,
        "steps":      sess["steps"],
    }


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "envs"
    arg = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}

    try:
        if cmd == "envs":
            result = cmd_envs()
        elif cmd == "new":
            result = cmd_new(arg)
        elif cmd == "step":
            result = cmd_step(arg)
        else:
            result = {"error": f"unknown command: {cmd}"}
    except Exception as exc:
        import traceback
        result = {"error": str(exc), "traceback": traceback.format_exc()}

    print(json.dumps(result))
