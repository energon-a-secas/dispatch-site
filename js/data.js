// ── Post loading + validation ────────────────────────────────
// One schema for published posts and desk drafts. The desk imports
// normalizePost so a draft that survives the desk is by construction
// a valid feed entry.

export const KINDS = ['launch', 'feature', 'fix', 'note'];
export const KIND_LABELS = {
  launch: 'Launch',
  feature: 'Feature',
  fix: 'Fix',
  note: 'Note',
};

const DATE_RE = /^\d{4}-\d{2}-\d{2}$/;
// Ids go unencoded into #p= links, element ids, and RSS guids, so they are
// valid by construction rather than escaped at every use site.
const ID_RE = /^[a-z0-9-]+$/;

/**
 * Coerce one raw post into the canonical shape, or return null if it
 * is missing the required fields (id, title, valid date, valid kind).
 */
export function normalizePost(raw) {
  if (!raw || typeof raw !== 'object') return null;
  const id = typeof raw.id === 'string' ? raw.id.trim() : '';
  const title = typeof raw.title === 'string' ? raw.title.trim() : '';
  const date = typeof raw.date === 'string' ? raw.date.trim() : '';
  const kind = KINDS.includes(raw.kind) ? raw.kind : null;
  if (!ID_RE.test(id) || !title || !DATE_RE.test(date) || !kind) return null;

  const body = Array.isArray(raw.body)
    ? raw.body.filter((p) => typeof p === 'string' && p.trim()).map((p) => p.trim())
    : [];
  const links = Array.isArray(raw.links)
    ? raw.links.filter((l) => l && typeof l.label === 'string' && typeof l.url === 'string'
        && /^https?:\/\//.test(l.url))
    : [];
  const tags = Array.isArray(raw.tags)
    ? raw.tags.filter((t) => typeof t === 'string' && t.trim()).map((t) => t.trim())
    : [];

  return {
    id,
    date,
    kind,
    site: typeof raw.site === 'string' && raw.site.trim() ? raw.site.trim() : null,
    title,
    summary: typeof raw.summary === 'string' ? raw.summary.trim() : '',
    body,
    links,
    tags,
  };
}

/** Normalize a whole document: drop invalid posts, sort newest first. */
export function normalizeDoc(doc) {
  const raw = doc && Array.isArray(doc.posts) ? doc.posts : [];
  const posts = raw.map(normalizePost).filter(Boolean);
  posts.sort((a, b) => (a.date === b.date ? (a.id < b.id ? 1 : -1) : (a.date < b.date ? 1 : -1)));
  return posts;
}

/** Fetch the published feed. Throws on network or HTTP failure. */
export async function loadPosts() {
  const res = await fetch('data/posts.json', { cache: 'no-cache' });
  if (!res.ok) throw new Error('posts.json ' + res.status);
  return normalizeDoc(await res.json());
}
