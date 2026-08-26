// ── Event handlers ───────────────────────────────────────────
// Feed interactions: filter chips, search, expand/collapse,
// keyboard nav, hash deep links, and the chrome toggle.

import { save } from './state.js';
import { render } from './render.js';
import { $, debounce, showToast } from './utils.js';

/**
 * Show or hide the header + footer. Same trick as sortie-site:
 * site-local header CSS is forbidden fleet-wide and .header-hidden is
 * owned by the kit's scroll handler, so inline display wins over both.
 */
export function applyChrome(on) {
  const header = document.querySelector('.header-bar');
  const footer = document.querySelector('.neo-footer');
  if (header) header.style.display = on ? '' : 'none';
  if (footer) footer.style.display = on ? '' : 'none';
  document.body.dataset.chrome = on ? 'on' : 'off';
}

function toggleChrome(s) {
  s.chrome = !s.chrome;
  applyChrome(s.chrome);
  save(s);
  if (!s.chrome) showToast('Chrome hidden. Press h to bring it back.', 5000);
}

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
  else if (e.key === 'h') { toggleChrome(s); }
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
