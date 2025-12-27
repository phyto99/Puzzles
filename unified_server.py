import io
import base64
import numpy as np
import cv2
import os
import sys
import importlib.util
import subprocess
import json
from flask import Flask, render_template, jsonify, request
from types import SimpleNamespace

# Define base paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAVEN_DIR = os.path.join(BASE_DIR, 'raven-datasets/I-RAVEN')

# Initialize Flask
template_dir = os.path.join(BASE_DIR, 'templates')
app = Flask(__name__, template_folder=template_dir)

@app.after_request
def add_header(r):
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    return r

# --- RAVEN (In-Process) ---
_raven_standard = None
_raven_mesh = None

def load_raven_logic():
    if RAVEN_DIR not in sys.path:
        sys.path.append(RAVEN_DIR)
    
    spec = importlib.util.spec_from_file_location("raven_generator", os.path.join(RAVEN_DIR, 'single_generator.py'))
    mod = importlib.util.module_from_spec(spec)
    sys.modules["raven_generator"] = mod
    spec.loader.exec_module(mod)
    return mod

def get_raven_standard():
    global _raven_standard
    if _raven_standard is None:
        raven_mod = load_raven_logic()
        args = SimpleNamespace(
            num_samples=1, save_dir=".", seed=None, fuse=0, val=2, test=2,
            position=True, position_train_set_rule="Constant",
            color=True, color_train_set_rule="Constant",
            type=True, type_train_set_rule="Constant",
            size=True, size_train_set_rule="Constant",
            mesh=0,
            configurations="center_single,distribute_four,distribute_nine,left_center_single_right_center_single,up_center_single_down_center_single,in_center_single_out_center_single,in_distribute_four_out_center_single"
        )
        _raven_standard = raven_mod.RavenGenerator(args=args)
    return _raven_standard

def get_raven_mesh():
    global _raven_mesh
    if _raven_mesh is None:
        raven_mod = load_raven_logic()
        args = SimpleNamespace(
            num_samples=1, save_dir=".", seed=None, fuse=0, val=2, test=2,
            position=True, position_train_set_rule="Constant",
            color=True, color_train_set_rule="Constant",
            type=True, type_train_set_rule="Constant",
            size=True, size_train_set_rule="Constant",
            mesh=2,
            configurations="center_single,distribute_four,distribute_nine,left_center_single_right_center_single,up_center_single_down_center_single,in_center_single_out_center_single,in_distribute_four_out_center_single"
        )
        _raven_mesh = raven_mod.RavenGenerator(args=args)
    return _raven_mesh

def encode_image(img_array):
    if img_array.max() <= 1.0:
        img_array = (img_array * 255).astype(np.uint8)
    else:
        img_array = img_array.astype(np.uint8)
    _, buffer = cv2.imencode('.png', img_array)
    return base64.b64encode(buffer).decode('utf-8')

# --- ACRE (Subprocess) ---
def get_acre_via_subprocess(regime):
    script_path = os.path.join(BASE_DIR, 'acre_wrapper.py')
    
    try:
        result = subprocess.run(
            [sys.executable, script_path, regime],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode != 0:
            print(f"ACRE Subprocess Error:\n{result.stderr}")
            return {"error": "ACRE generation failed (subprocess error)"}
            
        try:
            data = json.loads(result.stdout)
            return data
        except json.JSONDecodeError:
            print(f"ACRE Invalid JSON:\n{result.stdout}")
            return {"error": "Invalid JSON from ACRE generator"}
            
    except Exception as e:
        print(f"Subprocess exception: {e}")
        return {"error": str(e)}

@app.route('/')
def index():
    return render_template('app_v2.html')

@app.route('/api/get_puzzle', methods=['GET', 'POST'])
def get_puzzle():
    try:
        gen_type = request.args.get('generator_type') or (request.json and request.json.get('generator_type')) or 'raven'
        
        if request.json and 'regime' in request.json and not request.args.get('generator_type'):
            gen_type = 'acre'
            
        if gen_type == 'raven':
            subtype = request.args.get('type') or (request.json and request.json.get('type')) or 'standard'
            if subtype == 'mesh':
                gen = get_raven_mesh()
            else:
                gen = get_raven_standard()
            
            res = gen.generate_single()
            panels = [encode_image(p) for p in res["panels"]]
            return jsonify({
                "generator_type": "raven",
                "panels": panels,
                "target": res["target"],
                "config_name": res["config_name"]
            })
            
        elif gen_type == 'acre':
            regime = request.args.get('regime') or (request.json and request.json.get('regime')) or 'IID'
            return jsonify(get_acre_via_subprocess(regime))
            
        else:
            return jsonify({"error": "Unknown type"}), 400

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = 5010
    print("=" * 60)
    print(f"Unified Server Running on http://localhost:{port}")
    print("ACRE mode: Subprocess Isolation (Bulletproof)")
    print("=" * 60)
    app.run(host='0.0.0.0', port=port, debug=True)
