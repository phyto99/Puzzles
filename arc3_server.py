"""
ARC-AGI-3 session manager.

Each browser session gets a unique session_id. The server holds the env
object in memory and streams rendered PNG frames back on each action.

Endpoints consumed by unified_server.py:
  GET  /api/arc3/envs          -> list of {game_id, title, tags}
  POST /api/arc3/new           -> {session_id, frame_b64, state, levels_completed, win_levels, available_actions}
  POST /api/arc3/step          -> {frame_b64, state, levels_completed, win_levels, available_actions, done}
"""
import base64
import io
import os
import threading
import uuid
import numpy as np

# ── color palette from arc_agi.rendering ──────────────────────────────────────
COLOR_MAP = {
    0:  (255, 255, 255),  # White
    1:  (204, 204, 204),  # Off-white
    2:  (153, 153, 153),  # Light grey
    3:  (102, 102, 102),  # Grey
    4:  ( 51,  51,  51),  # Off black
    5:  (  0,   0,   0),  # Black
    6:  (229,  58, 163),  # Magenta
    7:  (255, 123, 204),  # Magenta light
    8:  (249,  60,  49),  # Red
    9:  ( 30, 147, 255),  # Blue
    10: (136, 216, 241),  # Blue light
    11: (255, 220,   0),  # Yellow
    12: (255, 133,  27),  # Orange
    13: (146,  18,  49),  # Maroon
    14: ( 79, 204,  48),  # Green
    15: (163,  86, 214),  # Purple
}
SCALE = 8   # render each cell as 8×8 px → 512×512 final image


def _frame_to_png_b64(frame_2d: np.ndarray) -> str:
    """Convert a 64×64 int8 palette array to a base64 PNG."""
    from PIL import Image
    h, w = frame_2d.shape
    rgb = np.zeros((h, w, 3), dtype=np.uint8)
    for idx, color in COLOR_MAP.items():
        mask = frame_2d == idx
        rgb[mask] = color
    # upscale with nearest-neighbor
    img = Image.fromarray(rgb, mode="RGB")
    img = img.resize((w * SCALE, h * SCALE), Image.NEAREST)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


# ── Session store ──────────────────────────────────────────────────────────────
_sessions: dict[str, object] = {}
_lock = threading.Lock()
_arcade = None
_envs_cache: list | None = None


def _get_arcade():
    global _arcade
    if _arcade is None:
        from arc_agi import Arcade
        _arcade = Arcade()
    return _arcade


def get_environments() -> list[dict]:
    global _envs_cache
    if _envs_cache is not None:
        return _envs_cache
    arcade = _get_arcade()
    envs = arcade.get_environments()
    _envs_cache = [
        {"game_id": e.game_id, "title": e.title, "tags": e.tags or []}
        for e in envs
    ]
    return _envs_cache


def new_session(game_id: str) -> dict:
    arcade = _get_arcade()
    env = arcade.make(game_id)
    frame_raw = env.reset()
    sid = str(uuid.uuid4())
    with _lock:
        _sessions[sid] = env
    return _build_response(sid, frame_raw)


def step_session(session_id: str, action: int, data: dict | None = None) -> dict:
    from arcengine import GameAction
    with _lock:
        env = _sessions.get(session_id)
    if env is None:
        return {"error": "session_not_found"}
    game_action = GameAction.from_id(action)
    frame_raw = env.step(game_action, data=data or {})
    if frame_raw is None:
        return {"error": "env returned None", "done": True}
    result = _build_response(session_id, frame_raw)
    # Clean up if game won/lost
    if frame_raw.state.value != "NOT_FINISHED":
        with _lock:
            _sessions.pop(session_id, None)
        result["done"] = True
    return result


def _build_response(session_id: str, frame_raw) -> dict:
    frames = frame_raw.frame or []
    frame_b64 = _frame_to_png_b64(frames[0]) if frames else None
    return {
        "session_id":       session_id,
        "frame_b64":        frame_b64,
        "state":            frame_raw.state.value,
        "levels_completed": frame_raw.levels_completed,
        "win_levels":       frame_raw.win_levels,
        "available_actions": list(frame_raw.available_actions or []),
        "full_reset":       frame_raw.full_reset,
        "done":             frame_raw.state.value != "NOT_FINISHED",
    }
