// ── Event handlers ───────────────────────────────────────────
// Feed interactions: filter chips, search, expand/collapse,
// keyboard nav, and hash deep links. The H chrome toggle is the
// NeoKeys kit's now (js/neokeys/, initialised from app.js).

import { render } from './render.js';
import { $, debounce } from './utils.js';

function setOpen(s, id) {
  s.openId = s.openId === id ? null : id;
  if (s.openId) {
    history.replaceState(null, '', '#p=' + encodeURIComponent(s.openId));
  } else {
    history.replaceState(null, '', location.pathname + location.search);
  }
  render(s);
  // The innerHTML rebuild destroyed the toggle that was just activated;
  // put focus back on the same story so keyboard flow and the
  // aria-expanded announcement survive the re-render.
  const el = document.getElementById('post-' + id);
  if (el) {
    const toggle = el.querySelector('.post__toggle');
    if (toggle) toggle.focus({ preventScroll: true });
    if (s.openId) el.scrollIntoView({ block: 'nearest' });
  }
}

/** Open the story named by a #p= hash, if it exists in the feed. */
export function openFromHash(s) {
  const m = /[#&]p=([^&]+)/.exec(location.hash);
  if (!m) return;
  let id;
  try { id = decodeURIComponent(m[1]); } catch { return; } // malformed %-escape in an external URL
  if (!s.posts.some((p) => p.id === id)) return;
  s.openId = id;
  render(s);
  const el = document.getElementById('post-' + id);
  if (el) el.scrollIntoView({ block: 'start' });
}

function isTyping() {
  const el = document.activeElement;
  return el && (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA' || el.isContentEditable);
}

function moveFocus(delta) {
  const toggles = Array.from(document.querySelectorAll('.post__toggle'));
  if (!toggles.length) return;
  const i = toggles.indexOf(document.activeElement);
  const next = i === -1
    ? (delta > 0 ? 0 : toggles.length - 1)
    : Math.min(toggles.length - 1, Math.max(0, i + delta));
  toggles[next].focus();
  toggles[next].scrollIntoView({ block: 'nearest' });
}

function onKeydown(s, e) {
  if (e.metaKey || e.ctrlKey || e.altKey) return;
  if (e.key === 'Escape' && s.openId) { setOpen(s, s.openId); return; }
  if (isTyping()) return;
  if (e.key === 'j') { e.preventDefault(); moveFocus(1); }
  else if (e.key === 'k') { e.preventDefault(); moveFocus(-1); }
  else if (e.key === '/') { e.preventDefault(); $('feedSearch').focus(); }
}

export function bindEvents(s) {
  $('feedChips').addEventListener('click', (e) => {
    const chip = e.target.closest('[data-filter]');
    if (!chip) return;
    s.filter = chip.dataset.filter;
    render(s);
    const active = document.querySelector('#feedChips [data-filter="' + s.filter + '"]');
    if (active) active.focus();
  });

  $('feedSearch').addEventListener('input', debounce((e) => {
    s.query = e.target.value;
    render(s);
  }, 120));

  $('feed').addEventListener('click', (e) => {
    const toggle = e.target.closest('.post__toggle');
    if (toggle) setOpen(s, toggle.dataset.id);
  });

  window.addEventListener('hashchange', () => openFromHash(s));
  document.addEventListener('keydown', (e) => onKeydown(s, e));
}
