#!/bin/bash
echo "=== Testing flood ==="
curl -s -X POST http://localhost:5011/new \
  -H 'Content-Type: application/json' \
  -d '{"puzzle":"flood"}' | python3 -c "
import sys, json
d = json.load(sys.stdin)
print('session:', d.get('session_id'), 'n:', d.get('action_space_n'), 'err:', d.get('error'))
"

echo "=== Testing net ==="
curl -s -X POST http://localhost:5011/new \
  -H 'Content-Type: application/json' \
  -d '{"puzzle":"net"}' | python3 -c "
import sys, json
d = json.load(sys.stdin)
print('session:', d.get('session_id'), 'n:', d.get('action_space_n'), 'err:', d.get('error'))
"

echo "=== Testing fifteen ==="
curl -s -X POST http://localhost:5011/new \
  -H 'Content-Type: application/json' \
  -d '{"puzzle":"fifteen"}' | python3 -c "
import sys, json
d = json.load(sys.stdin)
print('session:', d.get('session_id'), 'n:', d.get('action_space_n'), 'err:', d.get('error'))
"
echo "=== Done ==="
