/**
 * theme.js — Tint + Brightness appearance system
 *
 * Tint 0   = Lichess  (warm brown-black, like lichess.org dark)
 * Tint 50  = Pure     (neutral grey-black, zero colour cast)
 * Tint 100 = Discord  (cool blue-black, like Discord dark)
 *
 * Brightness 0   = AMOLED  (pure black)
 * Brightness 33  = Dark    (deep space — the default)
 * Brightness 66  = Ash     (lighter dark)
 * Brightness 100 = Light
 *
 * The tint sets the base HUE of the dark backgrounds.
 * Layer offsets (surface / card / border) are equal across R,G,B —
 * they add no extra colour of their own.
 * Text colours (--text, --muted, --bright) are neutral grey — no colour cast.
 */

const THEME = (() => {
  const LS_KEY = 'neurevo_theme';

  // Base bg colour at Dark (33) for each anchor — deep, close to black.
  // These match real apps: lichess.org dark, neutral grey, Discord #1e1f22.
  const ANCHORS = {
    lichess:  { r: 14, g: 12, b: 10 },   // warm brown-black
    pure:     { r:  8, g:  8, b:  8 },   // perfectly neutral (no blue cast)
    discord:  { r: 10, g: 11, b: 18 },   // cool blue-black
  };

  // Equal offsets for each surface layer — no colour injected by layering.
  const OFF = { surface: 7, card: 14, border: 29 };

  function lerp(a, b, t) { return Math.round(a + (b - a) * t); }

  function lerpRGB(c1, c2, t) {
    return {
      r: lerp(c1.r, c2.r, t),
      g: lerp(c1.g, c2.g, t),
      b: lerp(c1.b, c2.b, t),
    };
  }

  function addOff(c, o) { return { r: c.r + o, g: c.g + o, b: c.b + o }; }

  function rgb(c) { return `rgb(${c.r},${c.g},${c.b})`; }

  // Interpolate base bg colour from tint (0–100)
  function tintBase(tint) {
    if (tint <= 50) return lerpRGB(ANCHORS.lichess, ANCHORS.pure,    tint / 50);
    return                lerpRGB(ANCHORS.pure,    ANCHORS.discord, (tint - 50) / 50);
  }

  function computeVars(tint, brightness) {
    const base = tintBase(tint);

    // Dark-level values for each layer
    const darkBg     = base;
    const darkSurf   = addOff(base, OFF.surface);
    const darkCard   = addOff(base, OFF.card);
    const darkBorder = addOff(base, OFF.border);

    let bg, surface, card, border;

    if (brightness <= 33) {
      // AMOLED (0) → Dark (33)
      const t = brightness / 33;
      const black = { r: 0, g: 0, b: 0 };
      bg     = lerpRGB(black, darkBg,                      t);
      surface= lerpRGB(black, darkSurf,                    t);
      card   = lerpRGB(black, darkCard,                    t);
      border = lerpRGB({ r: 18, g: 18, b: 18 }, darkBorder, t);
    } else if (brightness <= 66) {
      // Dark (33) → Ash (66)
      const t = (brightness - 33) / 33;
      const lift = 18;
      bg     = lerpRGB(darkBg,     addOff(darkBg,     lift), t);
      surface= lerpRGB(darkSurf,   addOff(darkSurf,   lift), t);
      card   = lerpRGB(darkCard,   addOff(darkCard,   lift), t);
      border = lerpRGB(darkBorder, addOff(darkBorder, lift), t);
    } else {
      // Ash (66) → Light (100)
      const t = (brightness - 66) / 34;
      const ashBg     = addOff(darkBg,     18);
      const ashSurf   = addOff(darkSurf,   18);
      const ashCard   = addOff(darkCard,   18);
      const ashBorder = addOff(darkBorder, 18);
      bg     = lerpRGB(ashBg,     { r: 240, g: 240, b: 240 }, t);
      surface= lerpRGB(ashSurf,   { r: 248, g: 248, b: 248 }, t);
      card   = lerpRGB(ashCard,   { r: 255, g: 255, b: 255 }, t);
      border = lerpRGB(ashBorder, { r: 208, g: 208, b: 212 }, t);
    }

    const clamp = c => ({
      r: Math.min(255, Math.max(0, c.r)),
      g: Math.min(255, Math.max(0, c.g)),
      b: Math.min(255, Math.max(0, c.b)),
    });
    bg = clamp(bg); surface = clamp(surface);
    card = clamp(card); border = clamp(border);

    // Floor so separators stay visible at all brightnesses
    const borderMin = 26;
    border.r = Math.max(border.r, borderMin);
    border.g = Math.max(border.g, borderMin);
    border.b = Math.max(border.b, borderMin);

    const isLight = brightness > 75;
    const text   = isLight ? { r: 25,  g: 25,  b: 25  } : { r: 224, g: 224, b: 224 };
    const muted  = isLight ? { r: 100, g: 100, b: 100 } : { r: 120, g: 120, b: 120 };
    const bright = isLight ? { r: 10,  g: 10,  b: 10  } : { r: 245, g: 245, b: 245 };

    return {
      '--bg':      rgb(bg),
      '--surface': rgb(surface),
      '--card':    rgb(card),
      '--border':  rgb(border),
      '--text':    rgb(text),
      '--muted':   rgb(muted),
      '--bright':  rgb(bright),
      '--accent':  '#3730a3',
      '--accent2': '#4338ca',
    };
  }

  function applyVars(tint, brightness) {
    const vars = computeVars(tint, brightness);
    const root = document.documentElement;
    Object.entries(vars).forEach(([k, v]) => root.style.setProperty(k, v));
  }

  function load() {
    try {
      const s = localStorage.getItem(LS_KEY);
      return s ? JSON.parse(s) : { tint: 50, brightness: 33 };
    } catch { return { tint: 50, brightness: 33 }; }
  }

  function save(tint, brightness) {
    localStorage.setItem(LS_KEY, JSON.stringify({ tint, brightness }));
  }

  function init() {
    const { tint, brightness } = load();
    applyVars(tint, brightness);
    return { tint, brightness };
  }

  function update(tint, brightness) {
    applyVars(tint, brightness);
    save(tint, brightness);
  }

  return { init, update, load, computeVars };
})();

window.THEME = THEME;
