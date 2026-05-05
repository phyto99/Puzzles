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
from flask import Flask, render_template, jsonify, request, send_from_directory
from types import SimpleNamespace

# Define base paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAVEN_DIR = os.path.join(BASE_DIR, 'raven-datasets/I-RAVEN')

# Initialize Flask
template_dir  = os.path.join(BASE_DIR, 'templates')
trainers_dir  = os.path.join(BASE_DIR, 'trainers')
app = Flask(__name__, template_folder=template_dir)

@app.route('/trainers/<path:filename>')
def serve_trainer(filename):
    return send_from_directory(trainers_dir, filename)

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

@app.route('/recommendations')
def recommendations():
    return render_template('recommendations.html')

@app.route('/entropy-philosophy')
def entropy_philosophy():
    import re, os
    md_path = os.path.join(os.path.dirname(__file__), 'ENTROPY_PHILOSOPHY.md')
    try:
        with open(md_path, 'r', encoding='utf-8') as f:
            raw = f.read()
    except FileNotFoundError:
        raw = '# Not found\n\nENTROPY_PHILOSOPHY.md missing.'

    # Minimal markdown → HTML (no deps required)
    def md_to_html(text):
        lines = text.split('\n')
        html = []
        in_pre = False
        in_table = False
        for line in lines:
            if line.startswith('```'):
                if in_pre:
                    html.append('</code></pre>')
                    in_pre = False
                else:
                    html.append('<pre><code>')
                    in_pre = True
                continue
            if in_pre:
                html.append(line.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;'))
                continue
            # Table rows
            if line.startswith('|'):
                if not in_table:
                    html.append('<table>')
                    in_table = True
                cells = [c.strip() for c in line.strip('|').split('|')]
                tag = 'th' if '---' not in line else None
                if tag is None:
                    continue
                html.append('<tr>' + ''.join(f'<{tag}>{c}</{tag}>' for c in cells) + '</tr>')
                continue
            else:
                if in_table:
                    html.append('</table>')
                    in_table = False
            # Headings
            m = re.match(r'^(#{1,4})\s+(.*)', line)
            if m:
                lvl = len(m.group(1))
                html.append(f'<h{lvl}>{m.group(2)}</h{lvl}>')
                continue
            # HR
            if re.match(r'^---+$', line.strip()):
                html.append('<hr>')
                continue
            # Blank line
            if not line.strip():
                html.append('<p></p>')
                continue
            # Inline: bold, code, italic
            line = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', line)
            line = re.sub(r'`([^`]+)`', r'<code>\1</code>', line)
            line = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', line)
            # List item
            if re.match(r'^[-*]\s+', line):
                html.append(f'<li>{line[2:]}</li>')
            elif re.match(r'^\d+\.\s+', line):
                html.append(f'<li>{re.sub(r"^\d+\.\s+", "", line)}</li>')
            else:
                html.append(f'<p>{line}</p>')
        if in_table:
            html.append('</table>')
        if in_pre:
            html.append('</code></pre>')
        return '\n'.join(html)

    body = md_to_html(raw)
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: #0e0e0e; color: #e8e8e8; font-family: "Segoe UI", system-ui, sans-serif;
         font-size: 14px; line-height: 1.7; padding: 28px 28px 60px; max-width: 860px; }}
  h1 {{ font-size: 20px; font-weight: 700; margin: 28px 0 6px; color: #fff; }}
  h2 {{ font-size: 14px; font-weight: 600; text-transform: uppercase; letter-spacing: .07em;
        color: #1D9E75; margin: 28px 0 10px; border-bottom: 1px solid #222; padding-bottom: 6px; }}
  h3 {{ font-size: 13px; font-weight: 600; color: #aaa; margin: 18px 0 6px; }}
  h4 {{ font-size: 12px; color: #777; margin: 12px 0 4px; }}
  p  {{ color: #bbb; margin-bottom: 8px; }}
  li {{ color: #bbb; margin: 3px 0 3px 22px; list-style: disc; }}
  code {{ background: #1a1a1a; color: #c8e6c9; padding: 1px 5px; border-radius: 3px;
          font-family: monospace; font-size: 12px; }}
  pre {{ background: #111; border: 1px solid #222; border-radius: 5px; padding: 14px 16px;
         overflow-x: auto; margin: 12px 0; }}
  pre code {{ background: none; padding: 0; color: #a5d6a7; font-size: 12px; }}
  table {{ border-collapse: collapse; width: 100%; margin: 12px 0; }}
  th, td {{ border: 1px solid #2a2a2a; padding: 6px 12px; text-align: left; font-size: 13px; }}
  th {{ background: #181818; color: #aaa; font-weight: 600; }}
  td {{ color: #bbb; }}
  hr {{ border: none; border-top: 1px solid #222; margin: 20px 0; }}
  strong {{ color: #e8e8e8; }}
</style>
</head>
<body>{body}</body>
</html>'''

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
                "config_name": res["config_name"],
                "rule_info": res.get("rule_info", []),
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
        action_data = None
        if body.get('x') is not None and body.get('y') is not None:
            action_data = {'x': int(body['x']), 'y': int(body['y'])}
        return jsonify(step_session(sid, int(action), action_data))
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
