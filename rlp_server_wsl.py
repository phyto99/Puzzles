"""
RLP Flask server — runs inside WSL Ubuntu.

Each puzzle session runs as an isolated subprocess (rlp_worker.py).
A segfault in a puzzle's C extension only kills that worker, not Flask.

Uses Xvfb for a real virtual framebuffer so SDL_ttf works (needed by puzzles
that render text: Net, Fifteen, Loopy, Signpost, Pattern, Solo, Mines).
Falls back to dummy driver if Xvfb is not installed.

Start with:
  /opt/rlp-env/bin/python rlp_server_wsl.py

Exposes:
  GET  /envs           -> list of available puzzles
  POST /new            -> {puzzle} -> {session_id, frame_b64, action_space_n, ...}
  POST /step           -> {session_id, action} -> {frame_b64, reward, done, ...}
  POST /reset          -> {session_id} -> {frame_b64, action_space_n}
"""
import json
import os
import subprocess
import sys
import threading
import time
import shutil

os.environ["SDL_AUDIODRIVER"]  = "dummy"
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "hide"

_xvfb_proc = None

def _start_xvfb():
    """Start Xvfb on :99 if available. Returns the DISPLAY value to use."""
    global _xvfb_proc
    if not shutil.which("Xvfb"):
        print("Xvfb not found — falling back to SDL dummy driver", flush=True)
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        return None
    # Kill any stale Xvfb on :99
    subprocess.run(["pkill", "-f", "Xvfb :99"], capture_output=True)
    time.sleep(0.3)
    _xvfb_proc = subprocess.Popen(
        ["Xvfb", ":99", "-screen", "0", "1280x1024x24", "-ac"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    time.sleep(0.8)   # give Xvfb time to start
    os.environ["DISPLAY"] = ":99"
    os.environ.pop("SDL_VIDEODRIVER", None)   # let SDL use X11
    print("Xvfb started on :99", flush=True)
    return ":99"

_display = _start_xvfb()

from flask import Flask, jsonify, request

app = Flask(__name__)

PUZZLE_META = {
    "flood":    ("Flood",        "Turn the grid the same colour in as few flood-fills as possible."),
    "net":      ("Net",          "Rotate tiles to connect all endpoints to the centre."),
    "flip":     ("Flip",         "Flip groups of squares to light them all up at once."),
    "fifteen":  ("Fifteen",      "Slide tiles into order — the classic 15-puzzle."),
    "bridges":  ("Bridges",      "Connect all islands with bridges. No crossings allowed."),
    "loopy":    ("Loopy",        "Draw a single closed loop through the grid dots."),
    "slant":    ("Slant",        "Draw diagonals to form a single connected tree with no loops."),
    "signpost": ("Signpost",     "Follow the arrows to number the squares 1 to N."),
    "untangle": ("Untangle",     "Move the dots so that no two edges cross."),
    "pattern":  ("Pattern",      "Shade cells to match the row/column clue counts (nonogram)."),
    "rect":     ("Rectangles",   "Divide the grid into rectangles each containing its number."),
    "solo":     ("Sudoku",       "Fill the grid: no number repeated in any row, column, or box."),
    "mines":    ("Minesweeper",  "Reveal cells — avoid the mines. Classic Minesweeper."),
}

PYTHON = sys.executable
WORKER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rlp_worker.py")

_sessions: dict = {}   # sid -> {"proc": Popen, "puzzle": str, "steps": int, "action_space_n": int}
_lock = threading.Lock()
_ctr  = 0


def _kill_session(sess):
    """Terminate a worker subprocess, ignoring errors."""
    try:
        sess["proc"].stdin.close()
    except Exception:
        pass
    try:
        sess["proc"].terminate()
    except Exception:
        pass


def _worker_readline(proc, timeout=15):
    """Read one JSON line from the worker, with a timeout guard."""
    import select, io
    fd = proc.stdout.fileno()
    ready, _, _ = select.select([proc.stdout], [], [], timeout)
    if not ready:
        return None, "worker timed out"
    line = proc.stdout.readline()
    if not line:
        return None, "worker exited unexpectedly"
    try:
        return json.loads(line), None
    except Exception as e:
        return None, f"bad JSON from worker: {e}"


def _new_worker(puzzle):
    """Spawn a fresh worker subprocess for the given puzzle. Returns (sid, data) or raises."""
    global _ctr
    proc = subprocess.Popen(
        [PYTHON, WORKER, puzzle],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        bufsize=1,          # line-buffered
    )
    data, err = _worker_readline(proc, timeout=20)
    if err:
        proc.terminate()
        raise RuntimeError(err)
    if not data.get("ok"):
        proc.terminate()
        raise RuntimeError(data.get("error", "worker failed"))

    with _lock:
        _ctr += 1
        sid = f"rlp_{_ctr}"
        _sessions[sid] = {
            "proc":          proc,
            "puzzle":        puzzle,
            "steps":         0,
            "action_space_n": data["action_space_n"],
        }
    return sid, data


@app.route("/envs")
def envs():
    result = []
    for puzzle_id, (name, desc) in PUZZLE_META.items():
        if os.path.exists(f"/opt/rlp/rlp/lib/lib{puzzle_id}.so"):
            result.append({"id": puzzle_id, "name": name, "description": desc})
    return jsonify(result)


@app.route("/new", methods=["POST"])
def new_session():
    body   = request.json or {}
    puzzle = body.get("puzzle", "flood")
    if puzzle not in PUZZLE_META:
        return jsonify({"error": f"unknown puzzle: {puzzle}"}), 400

    # Kill all existing workers (one active session at a time is fine for UI use)
    with _lock:
        old = list(_sessions.values())
        _sessions.clear()
    for sess in old:
        _kill_session(sess)

    try:
        sid, data = _new_worker(puzzle)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({
        "session_id":     sid,
        "frame_b64":      data["frame_b64"],
        "action_space_n": data["action_space_n"],
        "puzzle":         puzzle,
        "name":           PUZZLE_META[puzzle][0],
        "description":    PUZZLE_META[puzzle][1],
    })


@app.route("/step", methods=["POST"])
def step():
    body   = request.json or {}
    sid    = body.get("session_id")
    action = body.get("action")
    if sid is None or action is None:
        return jsonify({"error": "session_id and action required"}), 400

    with _lock:
        sess = _sessions.get(sid)
    if sess is None:
        return jsonify({"error": "session_not_found"}), 404

    proc = sess["proc"]
    if proc.poll() is not None:
        with _lock:
            _sessions.pop(sid, None)
        return jsonify({"error": "worker crashed"}), 500

    try:
        proc.stdin.write(json.dumps({"action": int(action)}) + "\n")
        proc.stdin.flush()
    except Exception as e:
        return jsonify({"error": f"write to worker failed: {e}"}), 500

    data, err = _worker_readline(proc, timeout=15)
    if err:
        with _lock:
            _sessions.pop(sid, None)
        return jsonify({"error": err}), 500
    if not data.get("ok"):
        return jsonify({"error": data.get("error", "step error")}), 500

    sess["steps"] += 1
    done = data.get("done", False)
    if done:
        with _lock:
            _sessions.pop(sid, None)
        _kill_session(sess)

    return jsonify({
        "session_id": sid,
        "frame_b64":  data["frame_b64"],
        "reward":     data.get("reward", 0.0),
        "terminated": data.get("terminated", False),
        "truncated":  data.get("truncated", False),
        "done":       done,
        "steps":      sess["steps"],
    })


@app.route("/reset", methods=["POST"])
def reset_session():
    body = request.json or {}
    sid  = body.get("session_id")
    puzzle = "flood"
    if sid:
        with _lock:
            sess = _sessions.pop(sid, None)
        if sess:
            puzzle = sess["puzzle"]
            _kill_session(sess)
    # Reuse same puzzle type for reset
    body["puzzle"] = puzzle
    return new_session()


if __name__ == "__main__":
    port = int(os.environ.get("RLP_PORT", 5011))
    print(f"RLP WSL server on http://localhost:{port}", flush=True)
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
