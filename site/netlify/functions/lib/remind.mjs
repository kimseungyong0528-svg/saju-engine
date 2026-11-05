// 결제 이어하기 안내 메일 (2026-11-05 사장님 전권 위임, 손님 시뮬레이션 결과).
// 결제 화면에서 손님이 '(선택) 이어하기 안내 받기'에 직접 체크했을 때만 받는다. 할인 내용은 넣지 않는다(10-27 사장님: 할인 메일 없음).
// 받는 것: 이메일, 보던 상품, 동의 시각, 들어온 곳. 출생 정보·이름은 받지 않는다.
// 보내는 것: 1시간 뒤 1번, 24시간 뒤 1번(최대 2번). 결제하면 바로 지우고, 7일이 지나면 지운다. 메일마다 수신 거부 링크.
import { randomBytes } from 'node:crypto';
import { PRODUCTS } from './intake.mjs';
import { emailHash } from './discounts.mjs';

export const REMIND_STEPS = [1 * 3600_000, 24 * 3600_000];
export const REMIND_KEEP = 7 * 864e5;
const EMAIL_RE = /^[^@\s]{1,64}@[^@\s.]+(\.[^@\s.]+)+$/;

export async function saveRemind(store, body, now = new Date()) {
  const email = String(body?.email || '').trim().toLowerCase().slice(0, 120);
  if (!EMAIL_RE.test(email)) return { ok: false, code: 'EMAIL' };
  const hash = emailHash(email), key = `remind/${hash}`;
  if (body?.consent !== true) { await store.delete(key); return { ok: true, removed: true }; }
  const product = PRODUCTS.find(p => p.id === String(body?.productId || ''));
  if (!product) return { ok: false, code: 'PRODUCT' };
  if (await store.get(`optout/${hash}`)) await store.delete(`optout/${hash}`);   // 다시 직접 동의함
  const old = await store.get(key);
  const from = /^[a-z0-9-]{1,24}$/.test(String(body?.from || '')) ? String(body.from) : '';
  await store.set(key, {
    email, productId: product.id, from, sent: 0,
    consentAt: old?.consentAt || now.toISOString(), startedAt: now.toISOString(),
    token: old?.token || randomBytes(16).toString('hex'),
  });
  return { ok: true };
}

export async function unsubscribe(store, hash, token) {
  if (!/^[a-f0-9]{64}$/.test(String(hash || ''))) return false;
  const rec = await store.get(`remind/${hash}`);
  if (rec && rec.token !== token) return false;
  await store.delete(`remind/${hash}`);
  await store.set(`optout/${hash}`, { at: new Date().toISOString() });
  return true;
}

// 한 시간마다(cleanup.mjs): 보낼 때가 된 안내를 보내고, 결제했거나 오래된 기록은 지운다.
export async function sendReminders(store, services, now = new Date()) {
  let sent = 0;
  for (const key of await store.list('remind/')) {
    const rec = await store.get(key); if (!rec) continue;
    const hash = key.slice('remind/'.length), age = now - new Date(rec.startedAt);
    if (age > REMIND_KEEP || rec.sent >= REMIND_STEPS.length || await store.get(`optout/${hash}`)) { await store.delete(key); continue; }
    const buyer = await store.get(`buyers/${hash}`);
    if (buyer && new Date(buyer.firstPaidAt) >= new Date(rec.startedAt)) { await store.delete(key); continue; }
    if (age < REMIND_STEPS[rec.sent] || !services.sendReminder) continue;
    try {
      await services.sendReminder({ ...rec, hash }, rec.sent + 1);
      await store.set(key, { ...rec, sent: rec.sent + 1, lastSentAt: now.toISOString() });
      sent++;
    } catch (e) { console.error('remind', e?.message); }
  }
  return sent;
}

// 메일 글. 광고성 정보라 제목 앞 '(광고)', 보낸 곳, 수신 거부 방법을 넣는다(정보통신망법 제50조).
export function reminderMail(rec, n, site, productName) {
  const name = productName(rec.productId) || '운명서재 리포트';
  const link = `${site}/p/${rec.productId}/?from=remind${n}`;
  const off = `${site}/api/unsubscribe?h=${rec.hash}&t=${rec.token}`;
  const day = String(rec.consentAt || '').slice(0, 10);
  const subject = n === 1 ? `(광고) 보시던 ${name}, 이어서 보실 수 있어요` : `(광고) ${name} 무료 미리보기, 아직 그대로 있어요`;
  const lines = n === 1 ? [
    '운명서재입니다.', '',
    `결제 직전까지 보셨던 ${name}를 이어서 보실 수 있게 알려 드려요.`,
    '같은 휴대폰·브라우저로 아래 링크를 누르면, 전에 넣으신 내 정보가 남아 있는 경우 바로 채워져요.', '',
    link,
  ] : [
    '운명서재입니다.', '',
    `${name}의 무료 미리보기는 언제든 다시 보실 수 있어요. 결제는 미리보기를 끝까지 보신 뒤에 하셔도 돼요.`, '',
    link, '',
    '이 메일이 마지막 안내예요. 더는 보내지 않아요.',
  ];
  const foot = [
    '',
    `이 메일은 ${day} 결제 화면에서 '이어하기 안내 메일 받기'에 직접 동의하셔서 보내드려요.`,
    `더 받지 않으려면: ${off}`,
    '보낸 곳: 운명서재(상호 김승용) · 서울특별시 서대문구 증가로10길 60-3, 202호 · benedicto528@naver.com · 010-5407-2024',
  ];
  const text = [...lines, ...foot].join('\n');
  const esc = v => String(v).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const html = [...lines.map(l => l === link ? `<p style="margin:14px 0"><a href="${esc(link)}" style="display:inline-block;padding:14px 22px;border-radius:10px;background:#17141a;color:#fff;text-decoration:none;font-weight:700;font-size:17px">${esc(name)} 이어서 보기</a></p>` : l ? `<p style="margin:0 0 8px;font-size:16px;line-height:1.7;color:#222">${esc(l)}</p>` : '<br>'),
    ...foot.map(l => l.startsWith('더 받지') ? `<p style="margin:0 0 6px;font-size:15px;line-height:1.6;color:#444">더 받지 않으려면 <a href="${esc(off)}" style="color:#666">수신 거부</a></p>` : l ? `<p style="margin:0 0 6px;font-size:15px;line-height:1.6;color:#444">${esc(l)}</p>` : '<br>')].join('');
  return { subject, text, html };
}

export function unsubscribePage(ok) {
  return `<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex"><title>운명서재 · 수신 거부</title>
<style>body{margin:0;background:#0b0a09;color:#f4efe4;font-family:sans-serif;display:grid;place-items:center;min-height:100vh;padding:24px;box-sizing:border-box;text-align:center}a{color:#d8bb78}p{line-height:1.7;color:#ddd}</style></head>
<body><main><h1 style="font-size:22px">${ok ? '수신 거부가 끝났어요' : '이미 처리됐거나 잘못된 링크예요'}</h1><p>${ok ? '이어하기 안내 메일을 더는 보내지 않아요.' : '안내 메일이 계속 오면 benedicto528@naver.com 으로 알려 주세요.'}</p><p><a href="/">운명서재로 가기</a></p></main></body></html>`;
}
