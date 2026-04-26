"""
Visual Analogy puzzle generator — A : B :: C : ?

Classic IQ-test format: observe the A→B transformation, apply it to C.
4 multiple-choice answers (1 correct + 3 distractors).

Transformations are purely attribute-based (no random positioning matters):
  fill_toggle, size_up, size_down, count_add, count_sub,
  shape_change, color_shift, add_border, double_fill
"""
import base64
import math
import random

W, H, PAD = 160, 160, 12
CX, CY = W // 2, H // 2

SHAPES   = ["circle", "square", "triangle", "cross", "diamond"]
COLORS   = ["#111111", "#1a3caa", "#aa1a1a", "#1a8a1a", "#8a5a00", "#7a1a8a"]
SIZES_R  = {"sm": (10, 17), "md": (19, 28), "lg": (33, 48)}

# ── SVG primitives ─────────────────────────────────────────────────────────────

def _shape_el(shape, x, y, r, filled, color, rot=0):
    fill   = color if filled else "none"
    stroke = color
    sw     = 2.5
    if shape == "circle":
        return f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'
    elif shape == "square":
        tf = f' transform="rotate({rot},{x},{y})"' if rot else ""
        return f'<rect x="{x-r}" y="{y-r}" width="{r*2}" height="{r*2}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{tf}/>'
    elif shape == "triangle":
        h3  = r * math.sqrt(3) / 2
        pts = f"{x},{y-r} {x-h3:.1f},{y+r/2:.1f} {x+h3:.1f},{y+r/2:.1f}"
        tf  = f' transform="rotate({rot},{x},{y})"' if rot else ""
        return f'<polygon points="{pts}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{tf}/>'
    elif shape == "cross":
        t = max(3, r // 3)
        return (f'<rect x="{x-t}" y="{y-r}" width="{2*t}" height="{2*r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'
                f'<rect x="{x-r}" y="{y-t}" width="{2*r}" height="{2*t}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')
    elif shape == "diamond":
        pts = f"{x},{y-r} {x+r},{y} {x},{y+r} {x-r},{y}"
        return f'<polygon points="{pts}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'
    return ""


def _place_shapes(n, shape, size_key, filled, color):
    """Return list of (x, y, r, rot) for n non-overlapping shapes."""
    r_lo, r_hi = SIZES_R[size_key]
    placed, result = [], []
    for _ in range(n):
        for _ in range(120):
            r = random.randint(r_lo, r_hi)
            x = random.randint(PAD + r, W - PAD - r)
            y = random.randint(PAD + r, H - PAD - r)
            if all(math.hypot(x - px, y - py) >= r + pr + 7 for px, py, pr in placed):
                placed.append((x, y, r))
                rot = random.randint(0, 35) if shape in ("square", "triangle") else 0
                result.append((x, y, r, rot))
                break
    return result


def _render(cfg):
    """Render a config dict to an SVG data URI."""
    n      = cfg["n"]
    shape  = cfg["shape"]
    size   = cfg["size"]
    filled = cfg["filled"]
    color  = cfg["color"]
    border = cfg.get("border", False)

    pts  = _place_shapes(n, shape, size, filled, color)
    els  = [_shape_el(shape, x, y, r, filled, color, rot) for x, y, r, rot in pts]

    if border:
        b_inset = 6
        els.insert(0, f'<rect x="{b_inset}" y="{b_inset}" '
                       f'width="{W-2*b_inset}" height="{H-2*b_inset}" '
                       f'fill="none" stroke="#444" stroke-width="3" rx="4"/>')

    inner = "\n".join(els)
    svg = (f'<svg width="{W}" height="{H}" xmlns="http://www.w3.org/2000/svg">'
           f'<rect width="{W}" height="{H}" fill="#fff" stroke="#bbb" stroke-width="1.5"/>'
           f'{inner}</svg>')
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()


# ── Transformations ─────────────────────────────────────────────────────────────

def _other_shape(current):
    others = [s for s in SHAPES if s != current]
    return random.choice(others)

def _other_color(current):
    others = [c for c in COLORS if c != current]
    return random.choice(others)

SIZE_UP   = {"sm": "md", "md": "lg", "lg": "lg"}
SIZE_DOWN = {"sm": "sm", "md": "sm", "lg": "md"}

def _apply(cfg, transform):
    c = dict(cfg)
    if   transform == "fill_toggle":   c["filled"] = not c["filled"]
    elif transform == "size_up":       c["size"]   = SIZE_UP[c["size"]]
    elif transform == "size_down":     c["size"]   = SIZE_DOWN[c["size"]]
    elif transform == "count_add":     c["n"]      = min(c["n"] + 1, 5)
    elif transform == "count_sub":     c["n"]      = max(c["n"] - 1, 1)
    elif transform == "count_double":  c["n"]      = min(c["n"] * 2, 6)
    elif transform == "shape_change":  c["shape"]  = _other_shape(c["shape"])
    elif transform == "color_change":  c["color"]  = _other_color(c["color"])
    elif transform == "add_border":    c["border"] = not c.get("border", False)
    elif transform == "fill_to_hollow":c["filled"] = False
    elif transform == "fill_to_solid": c["filled"] = True
    return c


ALL_TRANSFORMS = [
    "fill_toggle", "size_up", "size_down",
    "count_add", "count_sub", "count_double",
    "shape_change", "color_change", "add_border",
]

# Transforms that are sometimes degenerate (size_up on "lg" = no change) — skip them
def _is_degenerate(cfg, transform):
    if transform == "size_up"    and cfg["size"] == "lg": return True
    if transform == "size_down"  and cfg["size"] == "sm": return True
    if transform == "count_sub"  and cfg["n"]    == 1:    return True
    if transform == "count_add"  and cfg["n"]    == 5:    return True
    if transform == "count_double" and cfg["n"]  >= 4:    return True
    return False


def _make_base_cfg(exclude_shape=None, exclude_color=None):
    shape = random.choice([s for s in SHAPES if s != exclude_shape] if exclude_shape else SHAPES)
    color = random.choice([c for c in COLORS if c != exclude_color] if exclude_color else COLORS)
    return {
        "n":      random.randint(1, 4),
        "shape":  shape,
        "size":   random.choice(["sm", "md", "lg"]),
        "filled": random.choice([True, False]),
        "color":  color,
        "border": False,
    }


# ── Public API ─────────────────────────────────────────────────────────────────

def generate_problem():
    # Pick a valid (non-degenerate) transformation
    for _ in range(50):
        cfg_a = _make_base_cfg()
        valid = [t for t in ALL_TRANSFORMS if not _is_degenerate(cfg_a, t)]
        if valid:
            transform = random.choice(valid)
            break
    else:
        cfg_a = _make_base_cfg()
        transform = "fill_toggle"

    cfg_b = _apply(cfg_a, transform)

    # C should differ from A in at least one attribute (makes puzzle interesting)
    for _ in range(20):
        cfg_c = _make_base_cfg(exclude_shape=cfg_a["shape"] if random.random() < .5 else None)
        if cfg_c != cfg_a and not _is_degenerate(cfg_c, transform):
            break

    cfg_d_correct = _apply(cfg_c, transform)

    # Distractors: apply DIFFERENT transforms to C (each must differ visually from correct)
    distractor_cfgs = []
    used = {transform}
    other_transforms = [t for t in ALL_TRANSFORMS if t not in used]
    random.shuffle(other_transforms)
    for t in other_transforms:
        if _is_degenerate(cfg_c, t):
            continue
        d = _apply(cfg_c, t)
        # Ensure distractor differs from correct answer
        if d != cfg_d_correct:
            distractor_cfgs.append(d)
        if len(distractor_cfgs) == 3:
            break

    # Fallback: mutate one attribute of correct answer
    while len(distractor_cfgs) < 3:
        d = dict(cfg_d_correct)
        attr = random.choice(["shape", "filled", "size", "n", "color"])
        if   attr == "shape":  d["shape"]  = _other_shape(d["shape"])
        elif attr == "filled": d["filled"] = not d["filled"]
        elif attr == "size":   d["size"]   = random.choice(["sm","md","lg"])
        elif attr == "n":      d["n"]       = max(1, d["n"] + random.choice([-1, 1]))
        elif attr == "color":  d["color"]  = _other_color(d["color"])
        if d != cfg_d_correct and d not in distractor_cfgs:
            distractor_cfgs.append(d)

    img_a = _render(cfg_a)
    img_b = _render(cfg_b)
    img_c = _render(cfg_c)
    img_d = _render(cfg_d_correct)

    choices = [_render(dc) for dc in distractor_cfgs] + [img_d]
    random.shuffle(choices)
    target = choices.index(img_d)

    return {
        "generator_type": "analogy",
        "img_a":          img_a,
        "img_b":          img_b,
        "img_c":          img_c,
        "choices":        choices,
        "target":         target,
        "transform":      transform,   # revealed after answer
    }
