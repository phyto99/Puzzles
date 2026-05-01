/**
 * ai-call.js — Universal AI provider support for Neurevo standalone exercises.
 *
 * Handles: OpenRouter, OpenAI, Anthropic (different request/response format),
 * Google Gemini (OpenAI-compat endpoint), Groq, Ollama (local), and custom.
 *
 * Injects a #ai-keymodal and #ai-nobanner into the page on load.
 * Requires: a #btn-key button and a #no-key-banner element in the host page.
 *
 * Usage: call window.callAI(action, payload) — returns parsed JSON object.
 */

(function () {
  const LS_KEY = 'neurevo_ai_v3';

  // ── Provider registry ────────────────────────────────────────────────────
  // Each entry: { label, endpoint, defaultModel, authHeader(key), buildBody(model,msgs), parseContent(data), jsonSupport }
  const PROVIDERS = {
    openrouter: {
      label: 'OpenRouter (recommended — 300+ models, CORS-native)',
      endpoint: 'https://openrouter.ai/api/v1/chat/completions',
      defaultModel: 'openai/gpt-4o-mini',
      modelHint: 'e.g. openai/gpt-4o-mini, anthropic/claude-3-5-haiku, google/gemini-flash-1.5',
      authHeader: key => ({ 'Authorization': `Bearer ${key}` }),
      buildBody: (model, msgs) => ({ model, messages: msgs, response_format: { type: 'json_object' }, temperature: 0.7 }),
      parseContent: d => d.choices[0].message.content,
    },
    openai: {
      label: 'OpenAI',
      endpoint: 'https://api.openai.com/v1/chat/completions',
      defaultModel: 'gpt-4o-mini',
      modelHint: 'gpt-4o-mini, gpt-4o, gpt-4-turbo',
      authHeader: key => ({ 'Authorization': `Bearer ${key}` }),
      buildBody: (model, msgs) => ({ model, messages: msgs, response_format: { type: 'json_object' }, temperature: 0.7 }),
      parseContent: d => d.choices[0].message.content,
    },
    anthropic: {
      label: 'Anthropic (Claude)',
      endpoint: 'https://api.anthropic.com/v1/messages',
      defaultModel: 'claude-3-5-haiku-20241022',
      modelHint: 'claude-3-5-haiku-20241022, claude-3-5-sonnet-20241022',
      // anthropic-dangerous-direct-browser-access enables CORS from browser
      authHeader: key => ({
        'x-api-key': key,
        'anthropic-version': '2023-06-01',
        'anthropic-dangerous-direct-browser-access': 'true',
      }),
      // Anthropic uses a different request shape (messages API, no response_format)
      buildBody: (model, msgs) => ({
        model,
        max_tokens: 1024,
        system: 'You are a cognitive training AI assistant. Always respond with valid JSON only — no markdown, no prose, just the JSON object.',
        messages: msgs,
      }),
      // Anthropic response: { content: [{ type: 'text', text: '...' }] }
      parseContent: d => d.content[0].text,
    },
    gemini: {
      label: 'Google Gemini (OpenAI-compat)',
      endpoint: 'https://generativelanguage.googleapis.com/v1beta/openai/chat/completions',
      defaultModel: 'gemini-2.0-flash',
      modelHint: 'gemini-2.0-flash, gemini-1.5-pro',
      authHeader: key => ({ 'Authorization': `Bearer ${key}` }),
      buildBody: (model, msgs) => ({ model, messages: msgs, response_format: { type: 'json_object' }, temperature: 0.7 }),
      parseContent: d => d.choices[0].message.content,
    },
    groq: {
      label: 'Groq',
      endpoint: 'https://api.groq.com/openai/v1/chat/completions',
      defaultModel: 'llama-3.3-70b-versatile',
      modelHint: 'llama-3.3-70b-versatile, mixtral-8x7b-32768',
      authHeader: key => ({ 'Authorization': `Bearer ${key}` }),
      buildBody: (model, msgs) => ({ model, messages: msgs, response_format: { type: 'json_object' }, temperature: 0.7 }),
      parseContent: d => d.choices[0].message.content,
    },
    ollama: {
      label: 'Ollama (local)',
      endpoint: 'http://localhost:11434/v1/chat/completions',
      defaultModel: 'llama3.2',
      modelHint: 'llama3.2, mistral, phi3 — must have OLLAMA_ORIGINS=* set',
      // Ollama's OpenAI-compat layer accepts Bearer "ollama" as a dummy token
      authHeader: () => ({ 'Authorization': 'Bearer ollama' }),
      buildBody: (model, msgs) => ({ model, messages: msgs, response_format: { type: 'json_object' }, temperature: 0.7 }),
      parseContent: d => d.choices[0].message.content,
    },
    custom: {
      label: 'Custom endpoint',
      endpoint: '',
      defaultModel: '',
      modelHint: 'depends on your endpoint',
      authHeader: key => ({ 'Authorization': `Bearer ${key}` }),
      buildBody: (model, msgs) => ({ model, messages: msgs, response_format: { type: 'json_object' }, temperature: 0.7 }),
      parseContent: d => d.choices[0].message.content,
    },
  };

  // ── Prompt builders (all actions, both exercises) ─────────────────────────
  const SYS = 'You are a cognitive training AI assistant. Respond only with valid JSON — no markdown fences, no prose.';

  function buildMessages(action, payload) {
    const user = buildUserPrompt(action, payload);
    return [{ role: 'user', content: `${SYS}\n\n${user}` }];
  }

  function buildUserPrompt(action, payload) {
    switch (action) {
      // ── Vocabulary Builder ────────────────────────────────────────────
      case 'generateText':
        return `Generate a ${payload.targetLength || 300}-word educational text at ${payload.difficulty || 'moderate'} difficulty that naturally incorporates these vocabulary words: ${(payload.targetWords || []).join(', ')}.\nReturn JSON: {"text":"..."}`;

      case 'generateQuizQuestions':
        return `Generate ${payload.numQuestions || 5} multiple-choice comprehension questions about this text:\n\n${payload.text}\n\nReturn JSON: {"questions":[{"id":"q1","question":"...","options":["A","B","C","D"],"correctAnswer":0}]}`;

      case 'generateWritingPrompt':
        return `Generate a 100–150 word writing prompt that encourages use of these vocabulary words: ${(payload.targetWords || []).join(', ')}.\nReturn JSON: {"prompt":"..."}`;

      case 'getWritingFeedback':
        return `Evaluate this writing response.\nPrompt given: ${payload.prompt}\nUser response: ${payload.userWriting}\nTarget vocabulary words: ${(payload.targetWords || []).join(', ')}\n\nReturn JSON: {"feedback":{"score":80,"strengths":["..."],"suggestions":["..."]}}`;

      // ── Kvashchev Problem Solving ─────────────────────────────────────
      case 'generateProblem':
        return `Generate a Kvashchev creative problem-solving task.\nPrinciple: "${payload.principle}"\nDomain: "${payload.domain}"\nDifficulty: "${payload.difficulty}"\nMinimum solutions expected: ${payload.minSolutions || 5}\n\nReturn JSON: {"problem":"...","expectedSolutions":["...","...","..."],"hints":["...","..."],"constraints":["..."]}`;

      case 'evaluateSolution':
        return `Evaluate this solution for a creative problem-solving task.\nProblem: ${payload.problem}\nUser's response: ${payload.user_response}\nExpected solution approaches: ${(payload.expected_solutions || []).join('; ')}\n\nReturn JSON: {"originality":7,"completeness":6,"feasibility":8,"divergentThinking":7}`;

      case 'generateFeedback':
        return `Give comprehensive feedback for this problem-solving session.\nProblem: ${payload.problem}\nPrinciple practised: ${payload.principle}\nSolutions submitted:\n${payload.all_solutions}\nEvaluation scores so far: ${payload.evaluation_scores}\n\nReturn JSON: {"originality":7,"completeness":6,"feasibility":8,"divergentThinking":7,"strengths":["..."],"blindSpots":["..."],"probingQuestions":["..."],"generalFeedback":"..."}`;

      default:
        return JSON.stringify({ action, payload });
    }
  }

  // ── Core call function ────────────────────────────────────────────────────
  window.callAI = async function (action, payload) {
    const cfg = getCfg();
    if (!cfg.key && cfg.provider !== 'ollama') {
      throw new Error('No API key set. Click "🔑 API Key" in the top bar.');
    }

    const p = PROVIDERS[cfg.provider] || PROVIDERS.custom;
    const endpoint = (cfg.provider === 'custom' ? cfg.endpoint : p.endpoint) || p.endpoint;
    const model = cfg.model || p.defaultModel;
    const msgs = buildMessages(action, payload);

    const resp = await fetch(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...p.authHeader(cfg.key || ''),
      },
      body: JSON.stringify(p.buildBody(model, msgs)),
    });

    if (!resp.ok) {
      const err = await resp.json().catch(() => ({}));
      const msg = err?.error?.message || err?.error?.type || JSON.stringify(err?.error || err);
      throw new Error(`${p.label || cfg.provider} request failed (${resp.status}): ${msg}`);
    }

    const data = await resp.json();
    const raw = p.parseContent(data);
    if (!raw) throw new Error('Empty response from API');

    // Strip markdown fences if model ignored the instruction
    const clean = raw.replace(/^```(?:json)?\s*/i, '').replace(/\s*```$/i, '').trim();
    try {
      return JSON.parse(clean);
    } catch {
      throw new Error(`Model returned invalid JSON: ${clean.substring(0, 120)}`);
    }
  };

  // ── localStorage helpers ──────────────────────────────────────────────────
  function getCfg() {
    try { return JSON.parse(localStorage.getItem(LS_KEY) || '{}'); } catch { return {}; }
  }
  function saveCfg(cfg) {
    localStorage.setItem(LS_KEY, JSON.stringify(cfg));
  }
  window.getAICfg = getCfg;

  // ── Modal HTML injection ──────────────────────────────────────────────────
  function injectModal() {
    const providerOptions = Object.entries(PROVIDERS)
      .map(([k, v]) => `<option value="${k}">${v.label}</option>`)
      .join('');

    const html = `
<div id="ai-keymodal" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,.78);z-index:400;align-items:center;justify-content:center;padding:1rem">
  <div style="background:var(--card);border:1px solid var(--border);border-radius:12px;padding:1.5rem;max-width:440px;width:100%;transition:background-color .25s,border-color .25s;max-height:90vh;overflow-y:auto">
    <div style="font-family:'Cinzel',serif;font-size:1rem;color:var(--bright);margin-bottom:.3rem">AI Provider</div>
    <p style="font-size:.8rem;color:var(--muted);margin-bottom:1.1rem;line-height:1.55">
      Your key is stored in <code style="font-size:.78rem;background:var(--surface);padding:1px 4px;border-radius:3px">localStorage</code> and sent only to the endpoint you choose — never anywhere else.
      <br><strong style="color:var(--text)">OpenRouter is recommended</strong> — one key, 300+ models, CORS-native.
    </p>

    <div style="margin-bottom:.7rem">
      <label for="aip-provider">Provider</label>
      <select id="aip-provider" onchange="window._aipOnProviderChange()">
        ${providerOptions}
      </select>
    </div>

    <div id="aip-key-row" style="margin-bottom:.7rem">
      <label for="aip-key">API Key</label>
      <input type="password" id="aip-key" placeholder="Paste your key here" autocomplete="off">
    </div>

    <div style="margin-bottom:.7rem">
      <label for="aip-model" id="aip-model-label">Model</label>
      <input type="text" id="aip-model" placeholder="">
      <div id="aip-model-hint" style="font-size:.72rem;color:var(--muted);margin-top:.2rem"></div>
    </div>

    <div id="aip-ep-row" style="display:none;margin-bottom:.7rem">
      <label for="aip-endpoint">Endpoint URL</label>
      <input type="text" id="aip-endpoint" placeholder="https://your-host/v1/chat/completions">
    </div>

    <div id="aip-note-ollama" style="display:none;background:rgba(67,56,202,.07);border:1px solid rgba(67,56,202,.22);border-radius:6px;padding:.55rem .75rem;font-size:.78rem;color:var(--muted);margin-bottom:.75rem;line-height:1.55">
      Ollama must be running locally with <code style="font-size:.76rem;background:var(--surface);padding:1px 3px;border-radius:2px">OLLAMA_ORIGINS="*"</code> set to allow browser access.
    </div>

    <div style="display:flex;gap:.5rem;margin-top:1rem">
      <button onclick="window._aipSave()" style="flex:1;display:inline-flex;align-items:center;justify-content:center;padding:.45rem 1rem;border-radius:6px;font-size:.8125rem;font-weight:500;cursor:pointer;border:1px solid var(--accent);background:var(--accent);color:#fff;font-family:inherit;transition:background .18s">Save</button>
      <button onclick="window._aipClose()" style="display:inline-flex;align-items:center;padding:.45rem .85rem;border-radius:6px;font-size:.8125rem;font-weight:500;cursor:pointer;border:1px solid var(--border);background:transparent;color:var(--text);font-family:inherit;transition:all .18s">Cancel</button>
    </div>
  </div>
</div>`;

    document.body.insertAdjacentHTML('beforeend', html);

    // Close on backdrop click
    document.getElementById('ai-keymodal').addEventListener('click', e => {
      if (e.target === document.getElementById('ai-keymodal')) window._aipClose();
    });
  }

  // ── Modal open/close/save ─────────────────────────────────────────────────
  window._aipOpen = function () {
    const cfg = getCfg();
    const provider = cfg.provider || 'openrouter';
    const p = PROVIDERS[provider] || PROVIDERS.openrouter;
    document.getElementById('aip-provider').value = provider;
    document.getElementById('aip-key').value = cfg.key || '';
    document.getElementById('aip-model').value = cfg.model || p.defaultModel;
    document.getElementById('aip-model').placeholder = p.defaultModel;
    document.getElementById('aip-model-hint').textContent = p.modelHint || '';
    document.getElementById('aip-endpoint').value = cfg.endpoint || '';
    _updateProviderUI(provider);
    document.getElementById('ai-keymodal').style.display = 'flex';
  };

  window._aipClose = function () {
    document.getElementById('ai-keymodal').style.display = 'none';
  };

  window._aipOnProviderChange = function () {
    const provider = document.getElementById('aip-provider').value;
    const p = PROVIDERS[provider];
    document.getElementById('aip-model').value = p.defaultModel;
    document.getElementById('aip-model').placeholder = p.defaultModel;
    document.getElementById('aip-model-hint').textContent = p.modelHint || '';
    _updateProviderUI(provider);
  };

  function _updateProviderUI(provider) {
    document.getElementById('aip-ep-row').style.display = provider === 'custom' ? 'block' : 'none';
    document.getElementById('aip-key-row').style.display = provider === 'ollama' ? 'none' : 'block';
    document.getElementById('aip-note-ollama').style.display = provider === 'ollama' ? 'block' : 'none';
  }

  window._aipSave = function () {
    const provider = document.getElementById('aip-provider').value;
    const cfg = {
      provider,
      key:      document.getElementById('aip-key').value.trim(),
      model:    document.getElementById('aip-model').value.trim() || PROVIDERS[provider]?.defaultModel || '',
      endpoint: provider === 'custom' ? document.getElementById('aip-endpoint').value.trim() : '',
    };
    saveCfg(cfg);
    window._aipClose();
    updateBanner();
  };

  function updateBanner() {
    const banner = document.getElementById('no-key-banner');
    if (!banner) return;
    const cfg = getCfg();
    const hasKey = cfg.key || cfg.provider === 'ollama';
    banner.style.display = hasKey ? 'none' : 'flex';
  }

  // ── Wire up btn-key ───────────────────────────────────────────────────────
  document.addEventListener('DOMContentLoaded', () => {
    injectModal();
    const btn = document.getElementById('btn-key');
    if (btn) btn.addEventListener('click', window._aipOpen);
    updateBanner();
  });

})();
