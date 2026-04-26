import io
import base64
import numpy as np
import cv2
import os
import sys
import importlib.util
import subprocess
import json
import threading
import urllib.request
import urllib.error
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

# ── RLP (Simon Tatham Puzzles) — WSL proxy ───────────────────────────────────
RLP_WSL_PORT = 5011
_rlp_proc    = None
_rlp_lock    = threading.Lock()
_rlp_ip      = None   # discovered WSL IP

def _get_wsl_ip():
    """Return the WSL2 Ubuntu IP address (changes on restart)."""
    global _rlp_ip
    try:
        r = subprocess.run(['wsl', '-d', 'Ubuntu', 'hostname', '-I'],
                           capture_output=True, text=True, timeout=5)
        ip = r.stdout.strip().split()[0]
        _rlp_ip = ip
        return ip
    except Exception:
        return _rlp_ip or '127.0.0.1'

def _rlp_base():
    return f"http://{_get_wsl_ip()}:{RLP_WSL_PORT}"

def _start_rlp_server():
    """Kill any existing RLP process on the port and launch a fresh one in WSL."""
    global _rlp_proc
    with _rlp_lock:
        # Kill tracked process if still alive
        if _rlp_proc is not None:
            try: _rlp_proc.terminate()
            except Exception: pass
            _rlp_proc = None
        # Also kill anything occupying the port inside WSL (handles externally-started servers)
        try:
            subprocess.run(
                ['wsl', '-d', 'Ubuntu', 'fuser', '-k', f'{RLP_WSL_PORT}/tcp'],
                capture_output=True, timeout=5
            )
        except Exception:
            pass
        import time; time.sleep(0.8)   # let the port free up

        script   = os.path.join(BASE_DIR, 'rlp_server_wsl.py')
        wsl_path = script.replace('\\', '/').replace('C:', '/mnt/c').replace('c:', '/mnt/c')
        try:
            flags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            _rlp_proc = subprocess.Popen(
                ['wsl', '-d', 'Ubuntu', '/opt/rlp-env/bin/python', wsl_path],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                creationflags=flags
            )
        except Exception as e:
            print(f"Could not start RLP server: {e}")
            return False
    import time; time.sleep(3.5)   # wait for Flask to be ready
    return True

def _rlp_request(path, body=None):
    url = _rlp_base() + path
    try:
        if body is None:
            req = urllib.request.Request(url)
        else:
            data = json.dumps(body).encode()
            req  = urllib.request.Request(url, data=data,
                                          headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read()), None
    except urllib.error.URLError as e:
        return None, str(e)
    except Exception as e:
        return None, str(e)

def _ensure_rlp():
    data, _ = _rlp_request('/envs')
    if data is not None:
        return None   # already up
    ok = _start_rlp_server()
    if not ok:
        return "Failed to start RLP WSL server"
    data, err = _rlp_request('/envs')
    if data is None:
        return f"RLP server did not respond: {err}"
    return None

@app.route('/api/rlp/envs')
def rlp_envs():
    err = _ensure_rlp()
    if err:
        return jsonify({"error": err}), 503
    data, e = _rlp_request('/envs')
    if e:
        return jsonify({"error": e}), 502
    return jsonify(data)

@app.route('/api/rlp/new', methods=['POST'])
def rlp_new():
    err = _ensure_rlp()
    if err:
        return jsonify({"error": err}), 503
    body = request.json or {}
    data, e = _rlp_request('/new', body)
    if e:
        # WSL server may have crashed — kill it, restart, and retry once
        print(f"RLP /new failed ({e}), restarting WSL server…")
        ok = _start_rlp_server()
        if ok:
            data, e = _rlp_request('/new', body)
    if e:
        return jsonify({"error": e}), 502
    return jsonify(data)

@app.route('/api/rlp/step', methods=['POST'])
def rlp_step():
    body = request.json or {}
    data, e = _rlp_request('/step', body)
    if e:
        return jsonify({"error": e}), 502
    return jsonify(data)

@app.route('/api/rlp/reset', methods=['POST'])
def rlp_reset():
    body = request.json or {}
    data, e = _rlp_request('/reset', body)
    if e:
        return jsonify({"error": e}), 502
    return jsonify(data)


@app.route('/')
def index():
    return render_template('app_v2.html')

@app.route('/contribute')
def contribute():
    return render_template('contribute.html')

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

        elif gen_type == 'clevr':
            if BASE_DIR not in sys.path:
                sys.path.insert(0, BASE_DIR)
            from clevr_generator import generate_problem
            return jsonify(generate_problem())

        elif gen_type == 'arc':
            if BASE_DIR not in sys.path:
                sys.path.insert(0, BASE_DIR)
            from arc_generator import generate_problem
            version = request.args.get('version') or (request.json and request.json.get('version')) or 'arc2'
            return jsonify(generate_problem(version=version))

        elif gen_type == 'marvel':
            if BASE_DIR not in sys.path:
                sys.path.insert(0, BASE_DIR)
            from marvel_generator import generate_problem
            pattern = request.args.get('pattern') or (request.json and request.json.get('pattern')) or None
            return jsonify(generate_problem(pattern=pattern))

        elif gen_type == 'puzzlevqa':
            if BASE_DIR not in sys.path:
                sys.path.insert(0, BASE_DIR)
            from puzzlevqa_generator import generate_problem
            pattern_key = request.args.get('pattern') or (request.json and request.json.get('pattern')) or None
            return jsonify(generate_problem(pattern_key=pattern_key))

        elif gen_type == 'bongard':
            if BASE_DIR not in sys.path:
                sys.path.insert(0, BASE_DIR)
            from bongard_generator import generate_problem
            return jsonify(generate_problem())

        elif gen_type == 'pgm':
            if BASE_DIR not in sys.path:
                sys.path.insert(0, BASE_DIR)
            from pgm_generator import generate_problem
            return jsonify(generate_problem())

        else:
            return jsonify({"error": "Unknown type"}), 400

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# ── ARC-AGI-3 endpoints ────────────────────────────────────────────────────────
@app.route('/api/arc3/envs', methods=['GET'])
def arc3_envs():
    try:
        if BASE_DIR not in sys.path:
            sys.path.insert(0, BASE_DIR)
        from arc3_server import get_environments
        return jsonify(get_environments())
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/arc3/new', methods=['POST'])
def arc3_new():
    try:
        if BASE_DIR not in sys.path:
            sys.path.insert(0, BASE_DIR)
        from arc3_server import new_session
        game_id = (request.json or {}).get('game_id')
        if not game_id:
            return jsonify({"error": "game_id required"}), 400
        return jsonify(new_session(game_id))
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/arc3/step', methods=['POST'])
def arc3_step():
    try:
        if BASE_DIR not in sys.path:
            sys.path.insert(0, BASE_DIR)
        from arc3_server import step_session
        body = request.json or {}
        sid    = body.get('session_id')
        action = body.get('action')
        if sid is None or action is None:
            return jsonify({"error": "session_id and action required"}), 400
        return jsonify(step_session(sid, int(action)))
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    port = 5010
    print("=" * 60)
    print(f"Unified Server Running on http://localhost:{port}")
    print("ACRE mode: Subprocess Isolation (Bulletproof)")
    print("=" * 60)
    app.run(host='0.0.0.0', port=port, debug=True, use_reloader=False)
