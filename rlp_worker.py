"""
RLP worker — runs as a subprocess for a single puzzle session.
Communicates with rlp_server_wsl.py via stdin/stdout JSON lines.
Isolates each puzzle env so a segfault only kills this process.
"""
import os, sys, json, base64, io

# DISPLAY is inherited from the parent (rlp_server_wsl.py sets it to :99 via Xvfb).
# Only fall back to dummy if Xvfb is not available.
if not os.environ.get("DISPLAY"):
    os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"]  = "dummy"
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "hide"
sys.path.insert(0, "/opt/rlp")

import rlp
import gymnasium as gym
import numpy as np
from PIL import Image

PUZZLE_META = {
    "flood":    "Flood",
    "net":      "Net",
    "flip":     "Flip",
    "fifteen":  "Fifteen",
    "bridges":  "Bridges",
    "loopy":    "Loopy",
    "slant":    "Slant",
    "signpost": "Signpost",
    "untangle": "Untangle",
    "pattern":  "Pattern",
    "rect":     "Rectangles",
    "solo":     "Solo",
    "mines":    "Mines",
}

def _frame_b64(arr):
    img = Image.fromarray(arr.astype(np.uint8)).resize((512, 512), Image.NEAREST)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()

def send(obj):
    sys.stdout.write(json.dumps(obj) + "\n")
    sys.stdout.flush()

def main():
    puzzle = sys.argv[1]
    name   = PUZZLE_META.get(puzzle, puzzle.capitalize())
    env_id = f"rlp/{name}-v0"

    try:
        env = gym.make(env_id, render_mode="rgb_array")
        obs, info = env.reset()
        img = env.render()
        if img is None:
            raise RuntimeError("render() returned None")
        send({"ok": True, "frame_b64": _frame_b64(img),
              "action_space_n": int(env.action_space.n)})
    except Exception as e:
        send({"ok": False, "error": str(e)})
        sys.exit(1)

    # Event loop: one JSON line per action in, one JSON line out
    for raw in sys.stdin:
        raw = raw.strip()
        if not raw:
            continue
        try:
            msg = json.loads(raw)
        except Exception:
            continue
        action = msg.get("action")
        if action is None:
            continue
        try:
            obs, reward, terminated, truncated, info = env.step(int(action))
            img = env.render()
            done = terminated or truncated
            send({"ok": True, "frame_b64": _frame_b64(img),
                  "reward": float(reward), "terminated": bool(terminated),
                  "truncated": bool(truncated), "done": done})
            if done:
                break
        except Exception as e:
            send({"ok": False, "error": str(e)})

    env.close()

if __name__ == "__main__":
    main()
