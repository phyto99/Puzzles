"""
PuzzleVQA generator.

Wraps the PIL-based pattern classes from PuzzleVQA/generation/data_generation.py.
Each pattern class has make_sample() -> (info_dict, PIL.Image).

info_dict keys: question, answer (str), options (list[str]), explanation
"""
import base64
import io
import os
import random
import sys

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
PVQA_DIR   = os.path.join(BASE_DIR, "PuzzleVQA", "generation")

# PuzzleVQA uses relative font paths so we must chdir into its generation dir.
# We save/restore cwd around each call.
_ORIG_CWD  = os.getcwd()
_CLASSES   = None  # lazy-loaded

# ---------------------------------------------------------------------------
# Monkey-patch random.sample: several PuzzleVQA patterns pass a set to
# random.sample(), which raises TypeError on Python 3.11+.
# Coerce non-sequences to sorted list before delegating.
# ---------------------------------------------------------------------------
_orig_sample = random.sample
def _sample_compat(population, k, **kw):
    if not isinstance(population, (list, tuple, range, bytes, bytearray)):
        population = sorted(population)
    return _orig_sample(population, k, **kw)
random.sample = _sample_compat


def _load_classes():
    global _CLASSES
    if _CLASSES is not None:
        return _CLASSES

    old = os.getcwd()
    try:
        os.chdir(PVQA_DIR)
        if PVQA_DIR not in sys.path:
            sys.path.insert(0, PVQA_DIR)

        from data_generation import (
            CircleSizeNumberPattern,
            ColorGridPattern,
            ColorHexagonPattern,
            ColorNumberHexagonPattern,
            ColorOverlapSquaresPattern,
            ColorSizeCirclePattern,
            GridNumberColorPattern,
            GridNumberPattern,
            PolygonSidesColorPattern,
            PolygonSidesNumberPattern,
            RectangleHeightColorPattern,
            RectangleHeightNumberPattern,
            ShapeMorphPattern,
            ShapeReflectPattern,
            ShapeSizeGridPattern,
            ShapeSizeHexagonPattern,
            SizeCyclePattern,
            SizeGridPattern,
            NumbersTrianglePattern,
            VennPattern,
        )
        _CLASSES = {
            "circle_size_number":       CircleSizeNumberPattern,
            "color_grid":               ColorGridPattern,
            "color_hexagon":            ColorHexagonPattern,
            "color_number_hexagon":     ColorNumberHexagonPattern,
            "color_overlap_squares":    ColorOverlapSquaresPattern,
            "color_size_circle":        ColorSizeCirclePattern,
            "grid_number_color":        GridNumberColorPattern,
            "grid_number":              GridNumberPattern,
            "polygon_sides_color":      PolygonSidesColorPattern,
            "polygon_sides_number":     PolygonSidesNumberPattern,
            "rect_height_color":        RectangleHeightColorPattern,
            "rect_height_number":       RectangleHeightNumberPattern,
            "shape_morph":              ShapeMorphPattern,
            "shape_reflect":            ShapeReflectPattern,
            "shape_size_grid":          ShapeSizeGridPattern,
            "shape_size_hexagon":       ShapeSizeHexagonPattern,
            "size_cycle":               SizeCyclePattern,
            "size_grid":                SizeGridPattern,
            "numbers_triangle":         NumbersTrianglePattern,
            "venn":                     VennPattern,
        }
    finally:
        os.chdir(old)

    return _CLASSES


def _pil_to_b64(img):
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_problem(pattern_key=None):
    try:
        classes = _load_classes()
    except Exception as exc:
        return {"error": f"PuzzleVQA load failed: {exc}"}

    if pattern_key and pattern_key in classes:
        cls = classes[pattern_key]
    else:
        pattern_key, cls = random.choice(list(classes.items()))

    old = os.getcwd()
    try:
        os.chdir(PVQA_DIR)
        instance = cls()
        info, img = instance.make_sample()
    except Exception as exc:
        return {"error": f"PuzzleVQA generation failed ({pattern_key}): {exc}"}
    finally:
        os.chdir(old)

    options = info.get("options", [])
    answer  = info.get("answer", "")
    try:
        target = options.index(answer)
    except ValueError:
        target = 0

    return {
        "generator_type": "puzzlevqa",
        "pattern":        pattern_key,
        "image":          _pil_to_b64(img),
        "question":       info.get("question", ""),
        "choices":        options,
        "target":         target,
        "explanation":    info.get("explanation", ""),
    }
