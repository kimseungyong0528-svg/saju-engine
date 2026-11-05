// 후기(2026-11-05 사장님 선택 "체험단 후기 30명"). 리포트를 메일로 받은 손님만, 주문 화면에서 남긴다.
// 사장님이 관리 사이트에서 '싣기'를 눌러야 사이트에 보인다(가짜 후기 금지: 실제 주문에서 온 후기만, 글은 고치지 않는다).
// 체험단 무료 코드로 받은 리포트의 후기는 항상 '체험단 무료 제공' 표시를 붙인다(표시광고법 추천·보증 심사지침).
import { ApiError } from './orders.mjs';
import { issueCoupon, TRIAL_MAX } from './discounts.mjs';

const NICK_RE = /^[가-힣A-Za-z0-9 *]{1,8}$/;
const SHOW = 30;

export async function submitReview(store, order, body, now = new Date()) {
  const root = order.parentId ? await store.get(`orders/${order.parentId}`) : order;
  if (!order.emailedAt) throw new ApiError(409, 'REVIEW_AFTER_DELIVERY');
  const stars = Number(body?.stars);
  const text = String(body?.text || '').replace(/\s+/g, ' ').trim();
  const nick = String(body?.nick || '').trim() || '익명';
  if (!Number.isInteger(stars) || stars < 1 || stars > 5) throw new ApiError(400, 'BAD_STARS');
  if (text.length < 10 || text.length > 400) throw new ApiError(400, 'BAD_TEXT');
  if (!NICK_RE.test(nick)) throw new ApiError(400, 'BAD_NICK');
  if (body?.agree !== true) throw new ApiError(400, 'CONSENT_REQUIRED');
  const key = `reviews/${order.id}`, old = await store.get(key);
  if (old && old.status !== 'pending') throw new ApiError(409, 'REVIEW_DONE');
  const rec = { orderId: order.id, productId: order.productId, stars, text, nick, trial: root?.discount?.kind === 'trial',
    status: 'pending', at: old?.at || now.toISOString(), updatedAt: now.toISOString() };
  await store.set(key, rec);
  return { ok: true, status: rec.status };
}

export async function reviewFor(store, orderId) {
  const r = await store.get(`reviews/${orderId}`);
  return r ? { stars: r.stars, text: r.text, nick: r.nick, status: r.status } : null;
}

const pub = r => ({ productId: r.productId, stars: r.stars, text: r.text, nick: r.nick, trial: Boolean(r.trial), date: String(r.at || '').slice(0, 10) });

// 사이트에 싣는 후기: 사장님이 '싣기'한 것만, 최신순.
export async function publicReviews(store, productId) {
  const all = [];
  for (const k of await store.list('reviews/')) {
    const r = await store.get(k);
    if (r?.status === 'approved' && (!productId || r.productId === productId)) all.push(r);
  }
  all.sort((a, b) => String(b.at).localeCompare(String(a.at)));
  const list = all.slice(0, SHOW).map(pub);
  const avg = all.length ? Math.round(all.reduce((s, r) => s + r.stars, 0) / all.length * 10) / 10 : null;
  return { count: all.length, avg, trialCount: all.filter(r => r.trial).length, reviews: list };
}

// ── 관리 사이트(사장님) ──
export async function studioReviews(store) {
  const all = [];
  for (const k of await store.list('reviews/')) { const r = await store.get(k); if (r) all.push(r); }
  all.sort((a, b) => String(b.at).localeCompare(String(a.at)));
  return { reviews: all };
}

export async function moderateReview(store, orderId, action, now = new Date()) {
  if (!/^[a-f0-9-]{36}$/.test(orderId || '')) throw new ApiError(404, 'NO_REVIEW');
  const r = await store.get(`reviews/${orderId}`);
  if (!r) throw new ApiError(404, 'NO_REVIEW');
  if (action === 'delete') { await store.delete(`reviews/${orderId}`); return { ok: true }; }
  if (!['approve', 'hide'].includes(action)) throw new ApiError(400, 'BAD_ACTION');
  await store.set(`reviews/${orderId}`, { ...r, status: action === 'approve' ? 'approved' : 'hidden', moderatedAt: now.toISOString() });
  return { ok: true };
}

export async function trialCodes(store) {
  const codes = [];
  for (const k of await store.list('coupons/TRY-')) { const c = await store.get(k); if (c?.kind === 'trial') codes.push(c); }
  codes.sort((a, b) => String(a.createdAt).localeCompare(String(b.createdAt)));
  return codes;
}

export async function issueTrialCodes(store, count, site, now = new Date()) {
  const n = Number(count);
  if (!Number.isInteger(n) || n < 1 || n > 10) throw new ApiError(400, 'BAD_COUNT');
  const have = (await trialCodes(store)).length;
  if (have + n > TRIAL_MAX) throw new ApiError(400, 'TRIAL_LIMIT');
  const made = [];
  for (let i = 0; i < n; i++) made.push(await issueCoupon(store, 'trial', now));
  const base = String(site || 'https://unmyeong-saju.com').replace(/\/$/, '');
  return { codes: made.map(c => ({ code: c.code, url: `${base}/?coupon=${c.code}&from=trial` })), total: have + n, max: TRIAL_MAX };
}
