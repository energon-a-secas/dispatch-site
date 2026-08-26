// ── Shared utilities ─────────────────────────────────────────
// Small, pure helper functions used across multiple modules.

/** Cached element lookup by ID. */
const _els = {};
export function $(id) {
  return _els[id] || (_els[id] = document.getElementById(id));
}

/** Escape HTML special characters. */
export function escHtml(str) {
  if (str === null || str === undefined) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

/** Show a temporary toast notification. Pass a longer ms for toasts that
    carry an instruction rather than a confirmation. */
let _toastTimer = null;
export function showToast(msg, ms = 2000) {
  let el = document.getElementById('app-toast');
  if (!el) {
    el = document.createElement('div');
    el.id = 'app-toast';
    el.className = 'toast';
    // role=status implies aria-live=polite; the region must exist before the
    // text lands or screen readers never announce it.
    el.setAttribute('role', 'status');
    document.body.appendChild(el);
  }
  requestAnimationFrame(() => {
    el.textContent = msg;
    el.classList.add('visible');
  });
  clearTimeout(_toastTimer);
  _toastTimer = setTimeout(() => el.classList.remove('visible'), ms);
}

/** Simple debounce. */
export function debounce(fn, ms) {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), ms);
  };
}

const SHORT_MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

/** "2026-08-25" → "Aug 25, 2026". Parsed by hand: `new Date('YYYY-MM-DD')`
    is UTC midnight and shifts a day in western timezones. */
export function fmtDate(iso) {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso || '');
  if (!m) return iso || '';
  return SHORT_MONTHS[parseInt(m[2], 10) - 1] + ' ' + parseInt(m[3], 10) + ', ' + m[1];
}
