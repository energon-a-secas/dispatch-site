// ── State management ─────────────────────────────────────────
// Shared mutable state object. Embed mode (?embed=1) never touches
// storage: an embedded Dispatch shows the feed, not the visitor's
// read-state (same convention as proctor-site).

const STORAGE_KEY = 'dispatch-state';

const params = new URLSearchParams(location.search);
const embed = params.has('embed');

function embedLimit() {
  const n = parseInt(params.get('limit'), 10);
  if (Number.isNaN(n)) return 4;
  return Math.min(10, Math.max(1, n));
}

export const state = {
  posts: [],        // published posts, newest first (data.js normalizes)
  error: false,     // posts.json failed to load
  filter: 'all',    // all | launch | feature | fix | note
  query: '',
  openId: null,     // id of the expanded story, one at a time
  embed,
  limit: embedLimit(),
  chrome: true,     // header + footer visible; `h` toggles (sortie pattern)
  lastSeen: null,   // newest post date already seen on a previous visit
  prevSeen: null,   // snapshot of lastSeen at load, drives the NEW badges
};

/** Load persisted prefs. Only chrome + lastSeen survive reloads. */
export function loadSaved(s) {
  if (s.embed) return;
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return;
    const saved = JSON.parse(raw);
    if (typeof saved.chrome === 'boolean') s.chrome = saved.chrome;
    if (typeof saved.lastSeen === 'string') s.lastSeen = saved.lastSeen;
  } catch { /* ignore corrupted data */ }
}

/** Persist current prefs to localStorage. */
export function save(s) {
  if (s.embed) return;
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({
      chrome: s.chrome,
      lastSeen: s.lastSeen,
    }));
  } catch { /* quota exceeded or private browsing */ }
}
