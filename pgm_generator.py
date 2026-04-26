"""
PGM-style abstract matrix generator.

Generates 3×3 Raven's Progressive Matrix puzzles using the same rule
vocabulary as DeepMind's PGM dataset (Barrett et al., ICML 2018):

  Rules:   progression, XOR, OR, AND, consistent_union
  Objects: shape, line
  Attrs:   size, color, position, number, type

All panels are rendered as PIL images and returned as base64 PNGs.
8 answer choices (1 correct + 7 distractors), same as PGM.
"""
import base64
import io
import math
import random

from PIL import Image, ImageDraw

# ── Attribute vocabularies ────────────────────────────────────────────────────
SHAPES      = ["circle", "square", "triangle", "pentagon", "hexagon"]
SIZES       = [18, 26, 34, 42]          # radius / half-side in pixels
COLORS      = [30, 80, 130, 180, 220]   # greyscale 0-255
N_OBJECTS   = [1, 2, 3, 4]
ANGLE_STEPS = [0, 45, 90, 135]         # degrees (for lines / oriented shapes)

PANEL_PX  = 80    # each panel is 80×80 px
GRID_GAP  = 4
CANVAS_PX = 3 * PANEL_PX + 4 * GRID_GAP   # 252 px

RULES = ["progression", "xor", "or", "and", "consistent_union"]

# ── Drawing helpers ───────────────────────────────────────────────────────────

def _draw_shape(draw: ImageDraw.Draw, shape: str, cx: int, cy: int,
                size: int, grey: int, angle: int = 0):
    fill  = grey
    outline = max(0, grey - 60)
    if shape == "circle":
        draw.ellipse([cx-size, cy-size, cx+size, cy+size],
                     fill=fill, outline=outline, width=2)
    elif shape == "square":
        pts = _rotate_pts([(cx-size, cy-size),(cx+size, cy-size),
                            (cx+size, cy+size),(cx-size, cy+size)],
                          cx, cy, angle)
        draw.polygon(pts, fill=fill, outline=outline)
    elif shape == "triangle":
        h = int(size * math.sqrt(3))
        pts = _rotate_pts([(cx, cy-size),(cx-h//2, cy+size//2),
                            (cx+h//2, cy+size//2)], cx, cy, angle)
        draw.polygon(pts, fill=fill, outline=outline)
    elif shape == "pentagon":
        pts = _poly_pts(cx, cy, size, 5, angle)
        draw.polygon(pts, fill=fill, outline=outline)
    elif shape == "hexagon":
        pts = _poly_pts(cx, cy, size, 6, angle)
        draw.polygon(pts, fill=fill, outline=outline)
    elif shape == "line":
        rad = math.radians(angle)
        x1 = cx + int(size * math.cos(rad))
        y1 = cy + int(size * math.sin(rad))
        x2 = cx - int(size * math.cos(rad))
        y2 = cy - int(size * math.sin(rad))
        draw.line([x1,y1,x2,y2], fill=outline, width=3)


def _poly_pts(cx, cy, r, n, start_angle=0):
    pts = []
    for i in range(n):
        a = math.radians(start_angle + i * 360 / n)
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def _rotate_pts(pts, cx, cy, angle):
    rad = math.radians(angle)
    cos_a, sin_a = math.cos(rad), math.sin(rad)
    result = []
    for (x, y) in pts:
        dx, dy = x - cx, y - cy
        result.append((cx + dx*cos_a - dy*sin_a, cy + dx*sin_a + dy*cos_a))
    return result


def _positions_for_n(n: int, panel_px=PANEL_PX):
    """Return n (cx,cy) positions arranged in a small grid within the panel."""
    pad = panel_px // 5
    margin = panel_px - 2 * pad
    if n == 1:
        return [(panel_px//2, panel_px//2)]
    elif n == 2:
        return [(pad + margin//4, panel_px//2),
                (pad + 3*margin//4, panel_px//2)]
    elif n == 3:
        return [(pad + i*margin//2, panel_px//2) for i in range(3)]
    else:  # 4
        return [(pad + (i%2)*margin//2, pad + (i//2)*margin//2) for i in range(4)]


def _render_panel(shape, n, size, grey, angle=0) -> Image.Image:
    img = Image.new("L", (PANEL_PX, PANEL_PX), 255)
    draw = ImageDraw.Draw(img)
    positions = _positions_for_n(n)
    for (cx, cy) in positions:
        _draw_shape(draw, shape, cx, cy, size, grey, angle)
    return img


def _assemble_matrix(panels: list[Image.Image]) -> Image.Image:
    """Assemble 9 panel images into a 3×3 grid with gaps."""
    out = Image.new("L", (CANVAS_PX, CANVAS_PX), 200)
    for idx, panel in enumerate(panels):
        row, col = divmod(idx, 3)
        x = GRID_GAP + col * (PANEL_PX + GRID_GAP)
        y = GRID_GAP + row * (PANEL_PX + GRID_GAP)
        out.paste(panel, (x, y))
    # Draw a question-mark in the last slot
    draw = ImageDraw.Draw(out)
    lx = GRID_GAP + 2 * (PANEL_PX + GRID_GAP)
    ly = GRID_GAP + 2 * (PANEL_PX + GRID_GAP)
    draw.rectangle([lx, ly, lx+PANEL_PX, ly+PANEL_PX], fill=240)
    draw.text((lx + PANEL_PX//2, ly + PANEL_PX//2), "?",
              fill=160, anchor="mm")
    return out


def _img_to_b64(img: Image.Image) -> str:
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


# ── Rule engines ──────────────────────────────────────────────────────────────

def _apply_rule(rule: str, vocab: list, seed_row: list[int]) -> list[list[int]]:
    """
    Given a 3-element seed for row 0, return a 3×3 grid of attribute values.
    Each row obeys the rule; rows are independently generated (same rule).
    """
    def one_row(base):
        if rule == "progression":
            step = random.choice([-2,-1,1,2])
            return [base, (base+step)%len(vocab), (base+2*step)%len(vocab)]
        elif rule == "xor":
            b = random.randint(0, len(vocab)-1)
            return [base, b, (base ^ b) % len(vocab)]
        elif rule == "or":
            b = random.randint(0, len(vocab)-1)
            return [base, b, max(base, b)]
        elif rule == "and":
            b = random.randint(0, len(vocab)-1)
            return [base, b, min(base, b)]
        elif rule == "consistent_union":
            a, b = random.sample(range(len(vocab)), 2)
            return [a, b, b]   # rightmost is repeated pattern
        return [base, base, base]

    rows = [one_row(v) for v in seed_row]
    return rows


# ── Main generator ────────────────────────────────────────────────────────────

def generate_problem() -> dict:
    # Pick one rule for each of 1-3 attributes
    n_rules = random.randint(1, 3)
    attrs = random.sample(["size","color","number","angle"], n_rules)

    vocabs = {
        "size":   list(range(len(SIZES))),
        "color":  list(range(len(COLORS))),
        "number": list(range(len(N_OBJECTS))),
        "angle":  list(range(len(ANGLE_STEPS))),
    }
    rules_used  = {a: random.choice(RULES) for a in attrs}
    fixed_shape = random.choice(SHAPES)

    # Generate 3×3 grid of attribute indices
    seeds = {a: [random.randint(0, len(vocabs[a])-1) for _ in range(3)] for a in attrs}
    grids = {a: _apply_rule(rules_used[a], vocabs[a], seeds[a]) for a in attrs}

    # Build 9 panels (8 context + 1 answer)
    panels = []
    for row in range(3):
        for col in range(3):
            size_i  = grids["size"][row][col]   if "size"   in attrs else 1
            color_i = grids["color"][row][col]  if "color"  in attrs else 2
            n_i     = grids["number"][row][col] if "number" in attrs else 0
            angle_i = grids["angle"][row][col]  if "angle"  in attrs else 0
            panel = _render_panel(
                fixed_shape,
                N_OBJECTS[n_i],
                SIZES[size_i],
                COLORS[color_i],
                ANGLE_STEPS[angle_i],
            )
            panels.append(panel)

    correct_panel = panels[8]  # bottom-right = answer

    # Assemble the context (first 8 panels, slot 9 = ?)
    matrix_img = _assemble_matrix(panels[:8] + [Image.new("L",(PANEL_PX,PANEL_PX),255)])

    # Generate 7 distractors by mutating one attribute each
    def mutate():
        r, c = 2, 2
        size_i  = grids["size"][r][c]   if "size"   in attrs else 1
        color_i = grids["color"][r][c]  if "color"  in attrs else 2
        n_i     = grids["number"][r][c] if "number" in attrs else 0
        angle_i = grids["angle"][r][c]  if "angle"  in attrs else 0

        mut_attr = random.choice(["size","color","number","angle"])
        if mut_attr == "size":
            size_i  = (size_i  + random.randint(1,3)) % len(SIZES)
        elif mut_attr == "color":
            color_i = (color_i + random.randint(1,4)) % len(COLORS)
        elif mut_attr == "number":
            n_i     = (n_i     + random.randint(1,3)) % len(N_OBJECTS)
        elif mut_attr == "angle":
            angle_i = (angle_i + random.randint(1,3)) % len(ANGLE_STEPS)

        return _render_panel(fixed_shape, N_OBJECTS[n_i], SIZES[size_i],
                             COLORS[color_i], ANGLE_STEPS[angle_i])

    distractors = [mutate() for _ in range(7)]
    choices = [correct_panel] + distractors
    random.shuffle(choices)
    target = choices.index(correct_panel)

    # Build a human-readable rule description
    rule_desc = "; ".join(f"{a}: {rules_used[a]}" for a in attrs)

    return {
        "generator_type": "pgm",
        "matrix_b64":     _img_to_b64(matrix_img),
        "choices_b64":    [_img_to_b64(c) for c in choices],
        "target":         target,
        "rule_desc":      rule_desc,
        "shape":          fixed_shape,
        "n_attrs":        n_rules,
    }
