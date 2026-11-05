// 발송 뒤 따라가는 일(자청 기획안 E-2·E-4·F-3): 다음 날 후기 요청 한 번, 서명 링크로만 후기, 50권 넘어야 카운터, 소식 메일은 동의한 분께 (광고)와 그만 받기.
import test from 'node:test';
import assert from 'node:assert/strict';
import { makeApi, memoryStore } from '../netlify/functions/lib/api.mjs';
import { sendDueAsks, reviewSig, sendNews, deliveredCount } from '../netlify/functions/lib/followup.mjs';

const ENV = { TOSS_CLIENT_KEY: 'live_ck', TOSS_SECRET_KEY: 'live_sk', GH_DISPATCH_TOKEN: 'gh', WORKER_SECRET: 'worker-secret', RESEND_API_KEY: 're', SITE_URL: 'https://unmyeong-saju.com' };
const place = { status: 'known', countryCode: 'KR', countryName: '대한민국', regionChoice: '1100000000', regionCode: '1100000000', districtCode: '1111000000', city: '종로구', inputMode: 'list', referenceEra: 'unknown' };
const self = { name: '김테스트', sex: 'female', birth: '1995-03-12', calendar: 'solar', timeAccuracy: 'exact', time: '06:30', birthPlace: place };
const draft = { self, answers: { occupation: '직장에 다니고 있어요' }, question: '앞으로 일은?', email: 'buyer@example.com', productId: 'lifetime' };

function setup() {
  const store = memoryStore(), mails = [];
  const services = { tossConfirm: async () => ({ ok: true }), startWorker: async () => {}, sendEmail: async () => 'm', sendMail: async (m, key) => { mails.push({ ...m, key }); return 'id'; } };
  const api = makeApi({ store, services, env: ENV, leadStore: store });
  const call = (method, p, body, headers = {}) => api(new Request('https://x.test' + p, { method, headers: { ...(body && !(body instanceof Uint8Array) ? { 'Content-Type': 'application/json' } : {}), ...headers }, body: body instanceof Uint8Array ? body : body ? JSON.stringify(body) : undefined }));
  return { store, mails, services, call };
}
async function delivered(t) {
  const b = await (await t.call('POST', '/api/orders', draft, { 'Idempotency-Key': 'key-' + Math.random().toString(36).slice(2) })).json();
  await t.call('POST', `/api/orders/${b.orderId}/confirm`, { paymentKey: 'pk', amount: b.amount }, { Authorization: 'Bearer ' + b.accessToken });
  await t.call('POST', `/api/internal/orders/${b.orderId}/result`, new Uint8Array([37, 80, 68, 70]), { 'x-worker-secret': 'worker-secret' });
  return b;
}

test('후기 요청: 보낸 다음 날 한 번만, 할인 없이, 서명 링크로', async () => {
  const t = setup(); const b = await delivered(t);
  assert.equal(await sendDueAsks(t.store, t.services, ENV, new Date()), 0, '바로는 안 보낸다');
  const later = new Date(Date.now() + 23 * 3600_000);
  assert.equal(await sendDueAsks(t.store, t.services, ENV, later), 1);
  assert.equal(await sendDueAsks(t.store, t.services, ENV, later), 0, '한 번만');
  const m = t.mails[0];
  assert.deepEqual(m.to, ['buyer@example.com']); assert.match(m.subject, /어떠셨어요/);
  assert.ok(!/할인|쿠폰|\d,\d{3}원/.test(m.text));
  assert.ok(m.text.includes(`/review.html?o=${b.orderId}&s=${reviewSig(ENV, b.orderId)}`));
});

test('후기 링크: 서명이 맞아야만, 남기면 싣기 대기', async () => {
  const t = setup(); const b = await delivered(t);
  const bad = await t.call('GET', `/api/review-link?o=${b.orderId}&s=00`); assert.equal(bad.status, 403);
  const q = `/api/review-link?o=${b.orderId}&s=${reviewSig(ENV, b.orderId)}`;
  const g = await (await t.call('GET', q)).json(); assert.equal(g.canReview, true);
  const r = await t.call('POST', q, { stars: 4, text: '좋은 달이 언제인지 알게 돼서 좋았어요.', nick: '', agree: true });
  assert.equal(r.status, 200);
  assert.equal((await t.store.get(`reviews/${b.orderId}`)).status, 'pending');
  // 이미 후기를 남긴 주문엔 요청 메일을 안 보낸다
  const t2 = setup(); const b2 = await delivered(t2);
  await t2.call('POST', `/api/review-link?o=${b2.orderId}&s=${reviewSig(ENV, b2.orderId)}`, { stars: 5, text: '열 글자가 넘는 후기입니다.', agree: true });
  assert.equal(await sendDueAsks(t2.store, t2.services, ENV, new Date(Date.now() + 23 * 3600_000)), 0);
});

test('보낸 리포트 수: 50권이 넘어야 보인다', async () => {
  const t = setup(); await delivered(t);
  assert.equal(await deliveredCount(t.store), 1);
  assert.equal((await (await t.call('GET', '/api/stats/public')).json()).delivered, null);
  await t.store.set('stats/delivered', { n: 57 });
  assert.equal((await (await t.call('GET', '/api/stats/public')).json()).delivered, 57);
});

test('소식 메일: 동의한 분께만, 제목에 (광고), 그만 받기 링크', async () => {
  const t = setup();
  await t.store.set('leads/' + 'a'.repeat(40), { email: 'n@x.com', token: 'tok1', name: '가' });
  const r = await sendNews(t.store, t.services, ENV, { subject: '2027 신년운세 소식', body: '내용입니다' });
  assert.equal(r.sent, 1);
  const m = t.mails[0]; assert.equal(m.subject, '(광고) 2027 신년운세 소식'); assert.deepEqual(m.to, ['n@x.com']);
  assert.ok(m.text.includes('/api/leads/stop?id=' + 'a'.repeat(40) + '&t=tok1'));
  await assert.rejects(sendNews(t.store, t.services, ENV, { subject: '', body: 'x' }));
});
