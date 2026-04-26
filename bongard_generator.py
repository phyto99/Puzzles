"""
Bongard puzzle generator — pure Python, no image dependencies.

Each puzzle: 6 positive examples (left) and 6 negative examples (right)
share a hidden rule. A test image is shown; the player picks Left or Right.

All images are SVG strings encoded as data: URIs so the browser renders
them directly with no additional dependencies.
"""
import base64
import math
import random

W, H, PAD = 160, 160, 10   # SVG canvas dimensions


# ---------------------------------------------------------------------------
# SVG primitives
# ---------------------------------------------------------------------------

def _svg(objects, border="#999"):
    parts = [
        f'<svg width="{W}" height="{H}" xmlns="http://www.w3.org/2000/svg">',
        f'<rect width="{W}" height="{H}" fill="#fff" '
        f'stroke="{border}" stroke-width="1.5"/>',
    ]
    for o in objects:
        x, y, r = o["x"], o["y"], o["r"]
        fill   = o.get("color", "#111") if o.get("filled", True) else "none"
        stroke = o.get("color", "#111")
        sw     = 2.5
        rot    = o.get("rot", 0)
        shape  = o["shape"]

        if shape == "circle":
            parts.append(
                f'<circle cx="{x}" cy="{y}" r="{r}" '
                f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'
            )
        elif shape == "square":
            s = r * 2
            tf = f' transform="rotate({rot},{x},{y})"' if rot else ""
            parts.append(
                f'<rect x="{x-r}" y="{y-r}" width="{s}" height="{s}" '
                f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{tf}/>'
            )
        elif shape == "triangle":
            h3 = r * math.sqrt(3) / 2
            pts = f"{x},{y-r} {x-h3},{y+r/2} {x+h3},{y+r/2}"
            tf = f' transform="rotate({rot},{x},{y})"' if rot else ""
            parts.append(
                f'<polygon points="{pts}" '
                f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{tf}/>'
            )
        elif shape == "cross":
            t = max(3, r // 3)
            parts.append(
                f'<rect x="{x-t}" y="{y-r}" width="{2*t}" height="{2*r}" '
                f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'
            )
            parts.append(
                f'<rect x="{x-r}" y="{y-t}" width="{2*r}" height="{2*t}" '
                f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'
            )
        elif shape == "diamond":
            pts = f"{x},{y-r} {x+r},{y} {x},{y+r} {x-r},{y}"
            parts.append(
                f'<polygon points="{pts}" '
                f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'
            )

    parts.append("</svg>")
    return "\n".join(parts)


def _uri(svg_str):
    b64 = base64.b64encode(svg_str.encode()).decode()
    return f"data:image/svg+xml;base64,{b64}"


# ---------------------------------------------------------------------------
# Object placement helper
# ---------------------------------------------------------------------------

BASIC_SHAPES = ["circle", "square", "triangle"]
ALL_SHAPES   = ["circle", "square", "triangle", "cross", "diamond"]


def _place(n, shape_fn, size_fn, filled_fn, color_fn="#111"):
    """Place n non-overlapping objects in the canvas, return object list."""
    objs, placed = [], []

    for _ in range(n):
        for _ in range(60):
            r = size_fn()
            x = random.randint(PAD + r, W - PAD - r)
            y = random.randint(PAD + r, H - PAD - r)
            if all(math.hypot(x - px, y - py) >= r + pr + 6
                   for px, py, pr in placed):
                placed.append((x, y, r))
                objs.append({
                    "shape":  shape_fn(),
                    "x": x, "y": y, "r": r,
                    "filled": filled_fn(),
                    "color":  color_fn() if callable(color_fn) else color_fn,
                    "rot":    random.randint(0, 30),
                })
                break

    return objs


# Reusable size lambdas
_LG  = lambda: random.randint(34, 50)
_SM  = lambda: random.randint(10, 20)
_MD  = lambda: random.randint(18, 34)
_YES = lambda: True
_NO  = lambda: False


# ---------------------------------------------------------------------------
# Rule definitions
# ---------------------------------------------------------------------------

def _one_of(shapes):
    return lambda: random.choice(shapes)


def _same_shape_pos():
    shape = random.choice(BASIC_SHAPES)
    return _place(random.randint(2, 4), lambda s=shape: s, _MD, _YES)


def _mixed_shape_neg():
    """Ensure at least 2 different shapes appear."""
    while True:
        objs = _place(random.randint(3, 5), _one_of(BASIC_SHAPES), _MD, _YES)
        shapes_used = {o["shape"] for o in objs}
        if len(shapes_used) >= 2:
            return objs


def _even_pos():
    n = random.choice([2, 4])
    return _place(n, _one_of(BASIC_SHAPES), _MD, _YES)


def _odd_neg():
    n = random.choice([1, 3, 5])
    return _place(n, _one_of(BASIC_SHAPES), _MD, _YES)


RULES = [
    {
        "name": "all_circles",
        "hint": "Left: only circles  |  Right: no circles",
        "pos": lambda: _place(random.randint(1, 4), lambda: "circle", _MD, _YES),
        "neg": lambda: _place(random.randint(1, 4), _one_of(["square", "triangle"]), _MD, _YES),
    },
    {
        "name": "all_squares",
        "hint": "Left: only squares  |  Right: no squares",
        "pos": lambda: _place(random.randint(1, 4), lambda: "square", _MD, _YES),
        "neg": lambda: _place(random.randint(1, 4), _one_of(["circle", "triangle"]), _MD, _YES),
    },
    {
        "name": "all_triangles",
        "hint": "Left: only triangles  |  Right: no triangles",
        "pos": lambda: _place(random.randint(1, 4), lambda: "triangle", _MD, _YES),
        "neg": lambda: _place(random.randint(1, 4), _one_of(["circle", "square"]), _MD, _YES),
    },
    {
        "name": "single_shape",
        "hint": "Left: exactly one shape  |  Right: three or more shapes",
        "pos": lambda: _place(1, _one_of(ALL_SHAPES), _LG, _YES),
        "neg": lambda: _place(random.randint(3, 5), _one_of(BASIC_SHAPES), _SM, _YES),
    },
    {
        "name": "filled_vs_hollow",
        "hint": "Left: filled shapes  |  Right: hollow (outline) shapes",
        "pos": lambda: _place(random.randint(2, 4), _one_of(BASIC_SHAPES), _MD, _YES),
        "neg": lambda: _place(random.randint(2, 4), _one_of(BASIC_SHAPES), _MD, _NO),
    },
    {
        "name": "large_vs_small",
        "hint": "Left: large shapes  |  Right: small shapes",
        "pos": lambda: _place(random.randint(1, 2), _one_of(BASIC_SHAPES), _LG, _YES),
        "neg": lambda: _place(random.randint(4, 6), _one_of(BASIC_SHAPES), _SM, _YES),
    },
    {
        "name": "even_vs_odd",
        "hint": "Left: even number of shapes  |  Right: odd number of shapes",
        "pos": _even_pos,
        "neg": _odd_neg,
    },
    {
        "name": "same_shape_type",
        "hint": "Left: all shapes are the same type  |  Right: mixed shape types",
        "pos": _same_shape_pos,
        "neg": _mixed_shape_neg,
    },
    {
        "name": "symmetric_pair",
        "hint": "Left: exactly two shapes  |  Right: exactly one shape",
        "pos": lambda: _place(2, _one_of(BASIC_SHAPES), _MD, _YES),
        "neg": lambda: _place(1, _one_of(BASIC_SHAPES), _LG, _YES),
    },
    {
        "name": "complex_shapes",
        "hint": "Left: crosses or diamonds  |  Right: circles, squares, or triangles",
        "pos": lambda: _place(random.randint(1, 3), _one_of(["cross", "diamond"]), _MD, _YES),
        "neg": lambda: _place(random.randint(1, 3), _one_of(BASIC_SHAPES), _MD, _YES),
    },
]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_problem():
    rule = random.choice(RULES)

    left_images  = [_uri(_svg(rule["pos"]())) for _ in range(6)]
    right_images = [_uri(_svg(rule["neg"]())) for _ in range(6)]

    test_group = random.choice(["left", "right"])
    test_objs  = rule["pos"]() if test_group == "left" else rule["neg"]()
    test_image = _uri(_svg(test_objs, border="#555"))

    return {
        "generator_type":    "bongard",
        "rule_name":         rule["name"],
        "hint":              rule["hint"],   # revealed after the player answers
        "left_images":       left_images,
        "right_images":      right_images,
        "test_image":        test_image,
        "test_belongs_to":   test_group,
    }
