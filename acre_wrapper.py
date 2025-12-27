import sys
import os
import json
import io
import base64
import numpy as np

# Setup paths specifically for ACRE
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ACRE_DIR = os.path.join(BASE_DIR, 'ACRE')
ACRE_SRC_DIR = os.path.join(ACRE_DIR, 'src')

# CRITICAL: Prepend to sys.path so 'import const' finds ACRE's version
sys.path.insert(0, ACRE_DIR)
sys.path.insert(0, ACRE_SRC_DIR)

# Now we can import safely
try:
    from single_generator import SingleGenerator
except ImportError as e:
    print(json.dumps({"error": f"Import failed: {e}", "syspath": sys.path}))
    sys.exit(1)

def main():
    if len(sys.argv) > 1:
        regime = sys.argv[1]
    else:
        regime = 'IID'
        
    try:
        gen = SingleGenerator(ACRE_DIR)
        problem = gen.generate_problem(regime=regime)
        
        # Output strictly JSON
        print(json.dumps({
            "generator_type": "acre",
            "context_scenes": problem["context_scenes"],
            "candidates": problem["candidates"],
            "puzzle_type": problem["puzzle_type"],
            "question_subtype": problem.get("question_subtype", "unknown"),  # Add this field
            "regime": regime
        }))
    except Exception as e:
        import traceback
        traceback.print_exc(file=sys.stderr)
        print(json.dumps({"error": str(e)}))
        sys.exit(1)

if __name__ == '__main__':
    main()
