"""
CLEVR generator — pure Python, no Blender needed.

Scene format is intentionally identical to ACRE so the same Three.js
renderScene() function in the frontend can render both without changes.

Question types (matching real CLEVR families):
  count        — "How many [filtered] objects [spatial relation]?"
  exist        — "Is there a [filtered] object [spatial relation]?"
  query_*      — "What {color|size|material|shape} is [unique object]?"
  compare_attr — "Do [obj1] and [obj2] have the same {color|size|material|shape}?"
  compare_int  — "Are there more [filter1] objects than [filter2] objects?"
  integer      — "What number of objects are [relation] the [unique object]?"
"""
import random
import math

COLORS    = ["gray", "red", "blue", "green", "brown", "purple", "cyan", "yellow"]
SHAPES    = ["cube", "sphere", "cylinder"]
MATERIALS = ["rubber", "metal"]
SIZES     = {"small": 0.35, "large": 0.70}

# Spatial relation names & lambdas (A rel B)
RELATIONS = {
    "left of":    lambda A, B: A["position"][0] < B["position"][0],
    "right of":   lambda A, B: A["position"][0] > B["position"][0],
    "in front of":lambda A, B: A["position"][1] < B["position"][1],
    "behind":     lambda A, B: A["position"][1] > B["position"][1],
}


# ---------------------------------------------------------------------------
# Scene generation
# ---------------------------------------------------------------------------

def _generate_scene(n=None):
    if n is None:
        n = random.randint(3, 7)

    objects, placed = [], []

    for _ in range(n):
        for _ in range(50):
            size_name = random.choice(["small", "large"])
            r = SIZES[size_name]
            x = random.uniform(-2.6, 2.6)
            y = random.uniform(-2.6, 2.6)
            if all(math.hypot(x - px, y - py) >= r + pr + 0.25
                   for px, py, pr in placed):
                placed.append((x, y, r))
                objects.append({
                    "shape":      random.choice(SHAPES),
                    "color":      random.choice(COLORS),
                    "size":       r,
                    "_size_name": size_name,
                    "material":   random.choice(MATERIALS),
                    "position":   [round(x, 2), round(y, 2)],
                    "rotation":   random.randint(0, 359),
                })
                break

    return objects


# ---------------------------------------------------------------------------
# Reference helpers
# ---------------------------------------------------------------------------

def _desc(o, attrs=("color", "shape")):
    """Human-readable object description using given attributes."""
    parts = []
    if "size" in attrs:
        parts.append(o["_size_name"])
    if "material" in attrs:
        parts.append(o["material"])
    if "color" in attrs:
        parts.append(o["color"])
    if "shape" in attrs:
        parts.append(o["shape"])
    return " ".join(parts)


def _unique(objects, pred):
    """Return the unique object matching pred, or None if 0 or >1 match."""
    matches = [o for o in objects if pred(o)]
    return matches[0] if len(matches) == 1 else None


def _filter(objects, color=None, shape=None, size=None, material=None):
    return [o for o in objects
            if (color is None     or o["color"]      == color)
            and (shape is None    or o["shape"]       == shape)
            and (size is None     or o["_size_name"]  == size)
            and (material is None or o["material"]    == material)]


def _count_distractors(correct, n_range=8):
    pool = [i for i in range(max(0, correct - 3), correct + n_range + 1) if i != correct]
    random.shuffle(pool)
    return [str(c) for c in pool[:3]]


def _make_choices(answer, distractors):
    seen, choices = set(), []
    for c in [answer] + distractors:
        s = str(c)
        if s not in seen:
            seen.add(s)
            choices.append(s)
        if len(choices) == 4:
            break
    while len(choices) < 4:
        choices.append(f"_{len(choices)}")
    random.shuffle(choices)
    return choices, choices.index(str(answer))


# ---------------------------------------------------------------------------
# Question generators (each returns (text, answer, distractors, type) or None)
# ---------------------------------------------------------------------------

def _q_count_total(objects):
    n = len(objects)
    return f"How many objects are in the scene?", str(n), _count_distractors(n), "count"


def _q_count_filter(objects):
    """Count objects matching a random attribute."""
    attr = random.choice(["color", "shape", "material", "size"])
    if attr == "color":
        val = random.choice(COLORS)
        cnt = sum(1 for o in objects if o["color"] == val)
        return f"How many {val} objects are there?", str(cnt), _count_distractors(cnt), "count"
    elif attr == "shape":
        val = random.choice(SHAPES)
        cnt = sum(1 for o in objects if o["shape"] == val)
        return f"How many {val}s are there?", str(cnt), _count_distractors(cnt), "count"
    elif attr == "material":
        val = random.choice(MATERIALS)
        cnt = sum(1 for o in objects if o["material"] == val)
        return f"How many {val} objects are there?", str(cnt), _count_distractors(cnt), "count"
    else:
        val = random.choice(["small", "large"])
        cnt = sum(1 for o in objects if o["_size_name"] == val)
        return f"How many {val} objects are there?", str(cnt), _count_distractors(cnt), "count"


def _q_count_filter2(objects):
    """Count objects matching two attributes."""
    color = random.choice(COLORS)
    material = random.choice(MATERIALS)
    cnt = sum(1 for o in objects if o["color"] == color and o["material"] == material)
    return (f"How many {color} {material} objects are there?",
            str(cnt), _count_distractors(cnt), "count")


def _q_count_spatial(objects):
    """How many objects are [relation] the [unique obj]?"""
    rel_name, rel_fn = random.choice(list(RELATIONS.items()))
    anchor = _unique(objects, lambda o: True)  # try to find a uniquely-describable anchor
    # Find a uniquely-described anchor (color+shape)
    random.shuffle(objects)
    for anchor in objects:
        others = [o for o in objects if o is not anchor]
        dup = [o for o in others if o["color"] == anchor["color"] and o["shape"] == anchor["shape"]]
        if not dup:
            cnt = sum(1 for o in others if rel_fn(o, anchor))
            return (f"How many objects are {rel_name} the {anchor['color']} {anchor['shape']}?",
                    str(cnt), _count_distractors(cnt), "count_spatial")
    return None


def _q_exist_simple(objects):
    """Is there a [color] [shape]?"""
    color = random.choice(COLORS)
    shape = random.choice(SHAPES)
    exists = any(o["color"] == color and o["shape"] == shape for o in objects)
    return (f"Is there a {color} {shape}?",
            "yes" if exists else "no",
            ["no" if exists else "yes", "maybe", "unknown"], "exist")


def _q_exist_filter2(objects):
    """Is there a [size] [material] [shape]?"""
    size = random.choice(["small", "large"])
    mat  = random.choice(MATERIALS)
    shape = random.choice(SHAPES)
    exists = any(o["_size_name"] == size and o["material"] == mat and o["shape"] == shape
                 for o in objects)
    return (f"Is there a {size} {mat} {shape}?",
            "yes" if exists else "no",
            ["no" if exists else "yes", "maybe", "unknown"], "exist")


def _q_exist_spatial(objects):
    """Is there a [color] object [relation] the [anchor]?"""
    rel_name, rel_fn = random.choice(list(RELATIONS.items()))
    random.shuffle(objects)
    for anchor in objects:
        others = [o for o in objects if o is not anchor]
        dup = [o for o in others if o["color"] == anchor["color"] and o["shape"] == anchor["shape"]]
        if dup:
            continue
        query_color = random.choice(COLORS)
        exists = any(o["color"] == query_color and rel_fn(o, anchor) for o in others)
        return (f"Is there a {query_color} object {rel_name} the {anchor['color']} {anchor['shape']}?",
                "yes" if exists else "no",
                ["no" if exists else "yes", "maybe", "unknown"], "exist_spatial")
    return None


def _q_query_color(objects):
    """What color is the [size] [shape]?"""
    random.shuffle(objects)
    for o in objects:
        others_same = [x for x in objects if x is not o and
                       x["_size_name"] == o["_size_name"] and x["shape"] == o["shape"]]
        if not others_same:
            other_colors = [c for c in COLORS if c != o["color"]]
            random.shuffle(other_colors)
            return (f"What color is the {o['_size_name']} {o['shape']}?",
                    o["color"], other_colors[:3], "query_color")
    return None


def _q_query_material(objects):
    """What is the [color] [shape] made of?"""
    random.shuffle(objects)
    for o in objects:
        others_same = [x for x in objects if x is not o and
                       x["color"] == o["color"] and x["shape"] == o["shape"]]
        if not others_same:
            other_mat = "metal" if o["material"] == "rubber" else "rubber"
            return (f"What is the {o['color']} {o['shape']} made of?",
                    o["material"], [other_mat, "plastic", "glass"], "query_material")
    return None


def _q_query_size(objects):
    """What size is the [color] [material] [shape]?"""
    random.shuffle(objects)
    for o in objects:
        others_same = [x for x in objects if x is not o and
                       x["color"] == o["color"] and x["material"] == o["material"]
                       and x["shape"] == o["shape"]]
        if not others_same:
            other_size = "large" if o["_size_name"] == "small" else "small"
            return (f"What size is the {o['color']} {o['material']} {o['shape']}?",
                    o["_size_name"], [other_size, "medium", "tiny"], "query_size")
    return None


def _q_query_shape(objects):
    """What shape is the [color] [material] object? (only if unique)"""
    random.shuffle(objects)
    for o in objects:
        others_same = [x for x in objects if x is not o and
                       x["color"] == o["color"] and x["material"] == o["material"]]
        if not others_same:
            other_shapes = [s for s in SHAPES if s != o["shape"]]
            return (f"What shape is the {o['color']} {o['material']} object?",
                    o["shape"], other_shapes + ["pyramid"], "query_shape")
    return None


def _q_query_spatial(objects):
    """What color is the [size] object that is [relation] the [anchor]?"""
    rel_name, rel_fn = random.choice(list(RELATIONS.items()))
    random.shuffle(objects)
    for anchor in objects:
        others = [o for o in objects if o is not anchor]
        dup = [o for o in others if o["color"] == anchor["color"] and o["shape"] == anchor["shape"]]
        if dup:
            continue
        size = random.choice(["small", "large"])
        candidates = [o for o in others if o["_size_name"] == size and rel_fn(o, anchor)]
        if len(candidates) == 1:
            obj = candidates[0]
            other_colors = [c for c in COLORS if c != obj["color"]]
            random.shuffle(other_colors)
            return (f"What color is the {size} object that is {rel_name} the {anchor['color']} {anchor['shape']}?",
                    obj["color"], other_colors[:3], "query_spatial")
    return None


def _q_compare_same_attr(objects):
    """Do [obj1] and [obj2] have the same {color|material|size}?"""
    if len(objects) < 2:
        return None
    attr = random.choice(["color", "material", "size"])
    random.shuffle(objects)
    # Find two uniquely-identifiable objects
    for i, A in enumerate(objects):
        for B in objects[i+1:]:
            dup_a = [o for o in objects if o is not A and o["color"]==A["color"] and o["shape"]==A["shape"]]
            dup_b = [o for o in objects if o is not B and o["color"]==B["color"] and o["shape"]==B["shape"]]
            if dup_a or dup_b:
                continue
            if attr == "color":
                same = A["color"] == B["color"]
                return (f"Do the {A['color']} {A['shape']} and the {B['color']} {B['shape']} have the same color?",
                        "yes" if same else "no",
                        ["no" if same else "yes", "maybe", "unknown"], "compare_attr")
            elif attr == "material":
                same = A["material"] == B["material"]
                return (f"Are the {A['color']} {A['shape']} and the {B['color']} {B['shape']} made of the same material?",
                        "yes" if same else "no",
                        ["no" if same else "yes", "maybe", "unknown"], "compare_attr")
            else:
                same = A["_size_name"] == B["_size_name"]
                return (f"Are the {A['color']} {A['shape']} and the {B['color']} {B['shape']} the same size?",
                        "yes" if same else "no",
                        ["no" if same else "yes", "maybe", "unknown"], "compare_attr")
    return None


def _q_compare_counts(objects):
    """Are there more [filter1] objects than [filter2] objects?"""
    kind = random.choice(["material", "size", "shape"])
    if kind == "material":
        a, b = "rubber", "metal"
        ca = sum(1 for o in objects if o["material"] == a)
        cb = len(objects) - ca
        q = f"Are there more {a} than {b} objects?"
    elif kind == "size":
        a, b = "large", "small"
        ca = sum(1 for o in objects if o["_size_name"] == a)
        cb = len(objects) - ca
        q = f"Are there more {a} than {b} objects?"
    else:
        a, b = random.sample(SHAPES, 2)
        ca = sum(1 for o in objects if o["shape"] == a)
        cb = sum(1 for o in objects if o["shape"] == b)
        q = f"Are there more {a}s than {b}s?"
    answer = "yes" if ca > cb else ("equal" if ca == cb else "no")
    dists = ["no", "yes", "equal"]
    dists = [d for d in dists if d != answer]
    return q, answer, dists[:3], "compare_int"


def _q_same_as_chain(objects):
    """What {color} is the object that is the same {material} as the [anchor]?"""
    random.shuffle(objects)
    query_attrs = [("material", "color"), ("color", "shape"), ("material", "shape"),
                   ("size", "color"), ("color", "material")]
    random.shuffle(query_attrs)
    for match_attr, query_attr in query_attrs:
        for anchor in objects:
            dup = [o for o in objects if o is not anchor and
                   o["color"] == anchor["color"] and o["shape"] == anchor["shape"]]
            if dup:
                continue
            anchor_val = anchor["_size_name"] if match_attr == "size" else anchor[match_attr]
            matching = [o for o in objects if o is not anchor and
                        (o["_size_name"] if match_attr == "size" else o[match_attr]) == anchor_val]
            if len(matching) == 1:
                target = matching[0]
                if query_attr == "size":
                    ans = target["_size_name"]
                    dists = [s for s in ["small", "large"] if s != ans] + ["medium"]
                elif query_attr == "color":
                    ans = target["color"]
                    dists = [c for c in COLORS if c != ans][:3]
                elif query_attr == "material":
                    ans = target["material"]
                    dists = [m for m in MATERIALS if m != ans] + ["plastic", "glass"]
                else:  # shape
                    ans = target["shape"]
                    dists = [s for s in SHAPES if s != ans] + ["pyramid"]
                attr_noun = {"material": "material", "color": "color",
                             "size": "size", "shape": "shape"}
                match_desc = {"material": match_attr, "color": match_attr,
                              "size": match_attr, "shape": match_attr}[match_attr]
                q = (f"What {query_attr} is the object that has the same "
                     f"{match_attr} as the {anchor['color']} {anchor['shape']}?")
                return q, ans, random.sample(dists, min(3, len(dists))), "chain"
    return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

_Q_GENERATORS = [
    _q_count_total,
    _q_count_filter,
    _q_count_filter,       # weighted 2x
    _q_count_filter2,
    _q_count_spatial,
    _q_exist_simple,
    _q_exist_filter2,
    _q_exist_spatial,
    _q_query_color,
    _q_query_color,        # weighted 2x
    _q_query_material,
    _q_query_size,
    _q_query_shape,
    _q_query_spatial,
    _q_compare_same_attr,
    _q_compare_counts,
    _q_same_as_chain,
    _q_same_as_chain,      # weighted 2x (hardest, most interesting)
]


def generate_problem():
    objects = _generate_scene()

    # Try question generators in shuffled order until one succeeds
    generators = _Q_GENERATORS[:]
    random.shuffle(generators)
    result = None
    for gen in generators:
        r = gen(objects)
        if r is not None:
            result = r
            break

    if result is None:
        # Fallback: trivial count
        result = _q_count_total(objects)

    q_text, answer, distractors, qtype = result
    choices, target = _make_choices(answer, distractors)

    clean = [{k: v for k, v in o.items() if not k.startswith("_")}
             for o in objects]

    return {
        "generator_type": "clevr",
        "scene":          {"objects": clean, "light_state": "off"},
        "question":       q_text,
        "question_type":  qtype,
        "choices":        choices,
        "target":         target,
    }
