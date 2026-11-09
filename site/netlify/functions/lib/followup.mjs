// 발송 뒤 따라가는 일(자청 기획안 E-2·E-4·F-3, 2026-11-05).
// E-2 리포트를 보낸 다음 날 후기 요청 메일 한 번(주문마다 한 번, 할인·가격 없음). 링크는 서명돼 있어 그 주문에만 후기를 남길 수 있다.
// E-4 지금까지 보낸 리포트 수(실제 발송 수만). 50권이 넘어야 화면에 보인다.
// F-3 소식 받기에 동의한 분께만 보내는 소식 메일(제목에 (광고), 메일마다 그만 받기 링크). 사장님이 관리 사이트에서 누른다.
import { createHmac } from 'node:crypto';
import { ApiError, productName, sameSecret } from './orders.mjs';
import { submitReview } from './reviews.mjs';

export const ASK_AFTER_HOURS = 22;
export const COUNTER_MIN = 50;
const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

export const reviewSig = (env, id) => createHmac('sha256', String(env.WORKER_SECRET || '')).update('review:' + id).digest('hex').slice(0, 32);
const siteOf = env => String(env.SITE_URL || 'https://unmyeong-saju.com').replace(/\/$/, '');

// 발송(deliverPdf) 때 부른다: 다음 날 후기 요청 예약 + 보낸 리포트 수 +1
export async function afterDelivered(store, order, now = new Date()) {
  const s = (await store.get('stats/delivered')) || { n: 0 };
  await store.set('stats/delivered', { n: (s.n || 0) + 1, at: now.toISOString() });
  if (order.parentId || order.testOnly) return;   // 묶음은 본 주문 하나로 한 번만
  const due = new Date(now.getTime() + ASK_AFTER_HOURS * 3600_000).toISOString().slice(0, 13);
  await store.set(`reviewask/${due}/${order.id}`, { orderId: order.id });
}

function askMail(order, env) {
  const site = siteOf(env), name = order.mailName || '고객', product = String(productName(order.productId) || '사주').replace(/^금월선녀의\s*/, '');
  const link = `${site}/review.html?o=${order.id}&s=${reviewSig(env, order.id)}&from=rv`;
  const lines = [`${name}님, 운명서재예요.`, `어제 보내 드린 ${product} 리포트, 어떠셨어요?`,
    '맞았던 것, 아쉬웠던 것 한 줄이면 충분해요. 좋은 말만 써 달라고 하지 않아요. 사장님이 전부 직접 읽어요.',
    `후기 남기기: ${link}`, '', '이 메일은 리포트를 받으신 분께 한 번만 보내요.', `운명서재 ${site} · 김승용 · 사업자등록번호 101-69-00805`];
  const text = lines.join('\n');
  const html = `<div style="font-family:'Apple SD Gothic Neo','Malgun Gothic',sans-serif;max-width:560px;margin:0 auto;color:#1d1d1f;font-size:17px;line-height:1.7">
<p style="margin:0 0 6px;font-size:20px;font-weight:700">${esc(lines[0])}</p><p style="margin:0 0 6px">${esc(lines[1])}</p><p style="margin:0 0 18px">${esc(lines[2])}</p>
<p style="margin:0 0 22px"><a href="${esc(link)}" style="display:inline-block;background:#e9c35a;color:#1d1d1f;font-weight:700;padding:12px 20px;border-radius:10px;text-decoration:none">후기 남기기</a></p>
<p style="margin:0 0 4px;font-size:15px;color:#555">${esc(lines[5])}</p><p style="margin:0;font-size:15px;color:#555">${esc(lines[6])}</p></div>`;
  return { to: [order.email], subject: `[운명서재] ${name}님, ${product} 리포트 어떠셨어요?`, text, html };
}

// 한 시간마다(cleanup): 때가 된 후기 요청을 보낸다. 환불·이미 후기를 쓴 주문은 건너뛴다.
export async function sendDueAsks(store, services, env, now = new Date()) {
  if (!services.sendMail) return 0;
  const hour = now.toISOString().slice(0, 13);
  let sent = 0;
  for (const k of await store.list('reviewask/')) {
    const due = k.split('/')[1];
    if (due > hour) continue;
    const id = k.split('/')[2];
    const o = await store.get(`orders/${id}`);
    await store.delete(k);
    if (!o || !o.email || !o.emailedAt || o.status === 'refunded' || o.status === 'refund_pending' || await store.get(`reviews/${id}`)) continue;
    try { await services.sendMail(askMail(o, env), `review-ask-${id}`); sent++; } catch (e) { console.error('review ask', e?.message); }
  }
  return sent;
}

// 메일 속 링크로 여는 후기 화면(review.html)
export async function reviewByLink(store, env, method, q, body) {
  const id = String(q.o || ''), s = String(q.s || '');
  if (!/^[a-f0-9-]{36}$/.test(id) || !sameSecret(s, reviewSig(env, id))) throw new ApiError(403, 'BAD_LINK');
  const order = await store.get(`orders/${id}`);
  if (!order) throw new ApiError(404, 'ORDER_NOT_FOUND');
  if (method === 'GET') {
    const r = await store.get(`reviews/${id}`);
    return { productName: productName(order.productId), canReview: Boolean(order.emailedAt), review: r ? { stars: r.stars, text: r.text, nick: r.nick, status: r.status } : null };
  }
  return submitReview(store, order, body);
}

// 지금까지 보낸 리포트 수. 처음 한 번은 주문 기록에서 센다.
export async function deliveredCount(store) {
  let s = await store.get('stats/delivered');
  if (!s) {
    let n = 0;
    for (const k of await store.list('orders/')) { const o = await store.get(k); if (o?.emailedAt && !o.testOnly) n++; }
    s = { n, at: new Date().toISOString(), counted: true };
    await store.set('stats/delivered', s);
  }
  return s.n || 0;
}

// F-3 소식 메일: 동의한 분(leads/)께만. 한 번에 40통까지, 다음 번은 이어서(cursor).
export async function sendNews(leadStore, services, env, { subject, body, cursor = '' }, now = new Date()) {
  const sub = String(subject || '').trim(), text = String(body || '').trim();
  if (!sub || sub.length > 60 || !text || text.length > 2000) throw new ApiError(400, 'BAD_NEWS');
  if (!services.sendMail) throw new ApiError(503, 'MAIL_NOT_READY');
  const keys = (await leadStore.list('leads/')).sort().filter(k => !cursor || k > cursor);
  const site = siteOf(env);
  let sent = 0, last = cursor;
  for (const k of keys.slice(0, 40)) {
    const L = await leadStore.get(k); last = k;
    if (!L?.email || !L.token) continue;
    const stop = `${site}/api/leads/stop?id=${k.slice(6)}&t=${L.token}`;
    const t = `${text}\n\n소식 받기에 동의하신 분께만 보내는 메일이에요. 그만 받기: ${stop}\n운명서재 ${site} · 김승용 · 사업자등록번호 101-69-00805`;
    const html = `<div style="font-family:'Apple SD Gothic Neo','Malgun Gothic',sans-serif;max-width:560px;margin:0 auto;color:#1d1d1f;font-size:17px;line-height:1.7">${text.split('\n').map(l => l ? `<p style="margin:0 0 8px">${esc(l)}</p>` : '<br>').join('')}<p style="margin:18px 0 4px;font-size:15px;color:#555">소식 받기에 동의하신 분께만 보내는 메일이에요. <a href="${esc(stop)}">그만 받기</a></p><p style="margin:0;font-size:15px;color:#555">운명서재 ${esc(site)} · 김승용 · 사업자등록번호 101-69-00805</p></div>`;
    try { await services.sendMail({ to: [L.email], subject: `(광고) ${sub}`, text: t, html }, `news-${now.toISOString().slice(0, 10)}-${k.slice(6, 20)}`); sent++; } catch (e) { console.error('news', e?.message); }
  }
  return { sent, next: keys.length > 40 ? last : null, total: keys.length };
}
