// 주문 서버 시험: 실제 결제·이메일·깃허브 없이 가짜 서비스로 처음부터 끝까지 돌려 본다.
import test from 'node:test';
import assert from 'node:assert/strict';
import { makeApi, memoryStore } from '../netlify/functions/lib/api.mjs';
import { eraseOld, flagStuck } from '../netlify/functions/lib/orders.mjs';

const ENV = { TOSS_CLIENT_KEY: 'test_ck', TOSS_SECRET_KEY: 'test_sk', GH_DISPATCH_TOKEN: 'gh', WORKER_SECRET: 'worker-secret', RESEND_API_KEY: 're', OWNER_EMAIL: 'Buyer@example.com' };
const place = { status: 'known', countryCode: 'KR', countryName: '대한민국', regionChoice: '1100000000', regionCode: '1100000000', districtCode: '1111000000', city: '종로구', inputMode: 'list', referenceEra: 'unknown' };
const self = { name: '김테스트', sex: 'female', birth: '1995-03-12', calendar: 'solar', timeAccuracy: 'exact', time: '06:30', birthPlace: place };
const draft = { self, answers: { occupation: '직장에 다니고 있어요' }, question: '앞으로 일은?', email: 'buyer@example.com' };

function setup(overrides = {}) {
  const store = memoryStore();
  const calls = { confirm: [], dispatch: [], email: [], owner: [] };
  const services = {
    tossConfirm: async a => { calls.confirm.push(a); return overrides.tossFail ? { ok: false, code: 'REJECT_CARD_COMPANY' } : { ok: true }; },
    startWorker: async id => { calls.dispatch.push(id); },
    sendEmail: async (o, pdf) => { calls.email.push({ to: o.email, bytes: pdf.byteLength, n: o.resends || 0, name: o.payload?.self?.name || o.mailName }); },
    notifyOwner: async (o, note) => { calls.owner.push(note); },
  };
  const api = makeApi({ store, services, env: overrides.env || ENV });
  const call = (method, path, { body, headers = {}, raw } = {}) => api(new Request('https://x.test' + path, {
    method, headers: { ...(body ? { 'Content-Type': 'application/json' } : {}), ...headers },
    body: raw ?? (body ? JSON.stringify(body) : undefined),
  }));
  return { store, calls, call };
}

async function order(t, extra = {}) {
  const r = await t.call('POST', '/api/orders', { body: { ...draft, productId: 'lifetime', ...extra }, headers: { 'Idempotency-Key': 'key-' + Math.random().toString(36).slice(2) } });
  return { r, body: await r.json() };
}

test('시험 키일 때 사장님 이메일이 아닌 주문은 결제창까지만 열고 결과는 만들지 않는다', async () => {
  let t = setup();
  let { r, body } = await order(t, { email: 'someone@example.com' });
  assert.equal(r.status, 201);
  const c = await t.call('POST', `/api/orders/${body.orderId}/confirm`, { body: { paymentKey: 'pk', amount: body.amount }, headers: { Authorization: 'Bearer ' + body.accessToken } });
  const v = await c.json();
  assert.equal(c.status, 200); assert.equal(v.status, 'test_paid');
  assert.equal(t.calls.dispatch.length, 0); assert.equal(t.calls.confirm.length, 1);
  assert.equal((await t.store.get(`orders/${body.orderId}`)).payload, undefined);
  ({ r } = await order(t, { email: ' buyer@EXAMPLE.com ' })); assert.equal(r.status, 201);
  t = setup({ env: { ...ENV, TOSS_CLIENT_KEY: 'live_ck', TOSS_SECRET_KEY: 'live_sk' } });
  ({ r } = await order(t, { email: 'someone@example.com' })); assert.equal(r.status, 201);
});

test('payment-config: 키가 다 있어야 결제가 열린다', async () => {
  let t = setup();
  let c = await (await t.call('GET', '/api/payment-config')).json();
  assert.equal(c.customerAnalysisReady, true); assert.equal(c.clientKey, 'test_ck'); assert.equal(c.productNames.lifetime, '금월선녀의 평생사주');
  t = setup({ env: { ...ENV, RESEND_API_KEY: '' } });
  c = await (await t.call('GET', '/api/payment-config')).json();
  assert.equal(c.customerAnalysisReady, false); assert.equal(c.clientKey, '');
});

test('payment-config: 정식 키는 live, 위젯 키·섞인 키는 결제를 열지 않는다', async () => {
  const cfg = async env => (await (await setup({ env: { ...ENV, ...env } }).call('GET', '/api/payment-config')).json());
  let c = await cfg({ TOSS_CLIENT_KEY: 'live_ck_abc ', TOSS_SECRET_KEY: 'live_sk_abc' });
  assert.equal(c.customerAnalysisReady, true); assert.equal(c.paymentMode, 'live'); assert.equal(c.clientKey, 'live_ck_abc');
  assert.ok(!JSON.stringify(c).includes('live_sk'));
  c = await cfg({ TOSS_CLIENT_KEY: 'live_gck_abc', TOSS_SECRET_KEY: 'live_gsk_abc' });
  assert.equal(c.customerAnalysisReady, false); assert.equal(c.keyProblem, 'TOSS_WIDGET_KEY');
  c = await cfg({ TOSS_CLIENT_KEY: 'live_ck_abc', TOSS_SECRET_KEY: 'test_sk_abc' });
  assert.equal(c.customerAnalysisReady, false); assert.equal(c.keyProblem, 'TOSS_KEY_MIXED');
});

test('접수 확인: 바른 입력은 결제 허용, 사이트와 같은 기준 버전', async () => {
  const t = setup();
  const d = await (await t.call('POST', '/api/intake/assess', { body: { ...draft, productId: 'lifetime' } })).json();
  assert.equal(d.policyVersion, 'kr-c-2026-10-10.2'); assert.equal(d.paymentAllowed, true); assert.equal(d.status, 'eligible');
  assert.match(d.inputFingerprint, /^[a-f0-9]{64}$/); assert.equal(d.payload, undefined);
});

test('접수 확인: 시간 모름이면 안내 문구를 붙여 허용', async () => {
  const t = setup();
  const d = await (await t.call('POST', '/api/intake/assess', { body: { ...draft, self: { ...self, timeAccuracy: 'unknown', time: undefined }, productId: 'lifetime' } })).json();
  assert.equal(d.paymentAllowed, true); assert.ok(d.disclosures.some(x => x.includes('태어난 시간')));
});

test('접수 확인: 두 사람 상품은 상대방 생일이 없으면 막는다', async () => {
  const t = setup();
  const d = await (await t.call('POST', '/api/intake/assess', { body: { ...draft, productId: 'reunion', answers: {} } })).json();
  assert.equal(d.paymentAllowed, false); assert.equal(d.code, 'PARTNER_BIRTH_REQUIRED');
});

test('주문: 금액은 서버 가격, 없는 할인 코드·이메일 오류는 거절, 같은 키는 같은 주문', async () => {
  const t = setup({ env: { ...ENV, TOSS_CLIENT_KEY: 'live_ck', TOSS_SECRET_KEY: 'live_sk' } });
  const { r, body } = await order(t);
  assert.equal(r.status, 201); assert.equal(body.amount, 49800); assert.match(body.orderId, /^[a-f0-9-]{36}$/);
  assert.equal((await order(t, { discount: 5000 })).body.amount, 49800);   // 화면이 보낸 할인값은 무시
  assert.equal((await order(t, { coupon: 'UNMYEONG5000' })).body.code, 'COUPON_INVALID');
  assert.equal((await order(t, { email: 'nope' })).body.code, 'EMAIL_REQUIRED');
  const h = { 'Idempotency-Key': 'same-key-123' };
  const a = await (await t.call('POST', '/api/orders', { body: { ...draft, productId: 'lifetime' }, headers: h })).json();
  const b = await (await t.call('POST', '/api/orders', { body: { ...draft, productId: 'lifetime' }, headers: h })).json();
  assert.equal(a.orderId, b.orderId);
});

test('주문 상태: 접근 열쇠가 틀리면 못 본다', async () => {
  const t = setup();
  const { body } = await order(t);
  assert.equal((await t.call('GET', `/api/orders/${body.orderId}`, { headers: { Authorization: 'Bearer wrong' } })).status, 403);
  const v = await (await t.call('GET', `/api/orders/${body.orderId}`, { headers: { Authorization: 'Bearer ' + body.accessToken } })).json();
  assert.equal(v.status, 'awaiting_payment'); assert.equal(v.emailHint, 'b***@example.com'); assert.equal(v.payload, undefined);
});

test('금액이 다르면 결제를 승인하지 않는다', async () => {
  const t = setup();
  const { body: o } = await order(t);
  const auth = { Authorization: 'Bearer ' + o.accessToken };
  // 금액이 다르면 승인하지 않는다
  const bad = await t.call('POST', `/api/orders/${o.orderId}/confirm`, { body: { paymentKey: 'pk', amount: 100 }, headers: auth });
  assert.equal((await bad.json()).code, 'AMOUNT_MISMATCH'); assert.equal(t.calls.confirm.length, 0);
});

test('결제 승인 성공 흐름', async () => {
  const t = setup();
  const { body: o } = await order(t);
  const auth = { Authorization: 'Bearer ' + o.accessToken };
  let v = await (await t.call('POST', `/api/orders/${o.orderId}/confirm`, { body: { paymentKey: 'pk_1', amount: 49800 }, headers: auth })).json();
  assert.equal(v.status, 'queued'); assert.deepEqual(t.calls.dispatch, [o.orderId]);
  // 같은 승인 요청이 두 번 와도 한 번만 처리
  await t.call('POST', `/api/orders/${o.orderId}/confirm`, { body: { paymentKey: 'pk_1', amount: 49800 }, headers: auth });
  assert.equal(t.calls.confirm.length, 1);
  // 작업 쪽: 비밀값 없으면 거절
  assert.equal((await t.call('GET', `/api/internal/orders/${o.orderId}`)).status, 403);
  const w = { 'X-Worker-Secret': 'worker-secret' };
  const job = await (await t.call('GET', `/api/internal/orders/${o.orderId}`, { headers: w })).json();
  assert.equal(job.payload.self.name, '김테스트'); assert.equal(job.productId, 'lifetime');
  v = await (await t.call('POST', `/api/internal/orders/${o.orderId}/status`, { body: { status: 'processing' }, headers: w })).json();
  assert.equal(v.status, 'processing');
  v = await (await t.call('POST', `/api/internal/orders/${o.orderId}/result`, { raw: new Uint8Array([37, 80, 68, 70, 1, 2, 3]), headers: { ...w, 'Content-Type': 'application/pdf' } })).json();
  assert.equal(v.status, 'email_accepted'); assert.equal(v.pdfAvailable, true); assert.equal(t.calls.email.length, 1);
  const pdf = await t.call('GET', `/api/orders/${o.orderId}/pdf`, { headers: auth });
  assert.ok(pdf.headers.get('content-disposition').includes(encodeURIComponent('김테스트님의 평생사주 - 금월선녀의 운명서재.pdf')));
  assert.equal((await (await t.call('GET', `/api/orders/${o.orderId}`, { headers: auth })).json()).fileName, '김테스트님의 평생사주 - 금월선녀의 운명서재.pdf');
  assert.equal(pdf.headers.get('content-type'), 'application/pdf'); assert.equal((await pdf.arrayBuffer()).byteLength, 7);
  // 다시 보내기: 같은 키는 한 번, 최대 3번
  const rk = { ...auth, 'Idempotency-Key': 'r1' };
  await t.call('POST', `/api/orders/${o.orderId}/resend`, { body: {}, headers: rk });
  await t.call('POST', `/api/orders/${o.orderId}/resend`, { body: {}, headers: rk });
  assert.equal(t.calls.email.length, 2);
  for (const k of ['r2', 'r3']) await t.call('POST', `/api/orders/${o.orderId}/resend`, { body: {}, headers: { ...auth, 'Idempotency-Key': k } });
  const over = await t.call('POST', `/api/orders/${o.orderId}/resend`, { body: {}, headers: { ...auth, 'Idempotency-Key': 'r4' } });
  assert.equal((await over.json()).code, 'RESEND_LIMIT'); assert.equal(t.calls.email.length, 4);
  // 메일 서비스가 중복으로 보고 버리지 않게 보낼 때마다 번호가 다르고, 이름도 그대로 나간다
  assert.deepEqual(t.calls.email.map(e => e.n), [0, 1, 2, 3]);
  assert.ok(t.calls.email.every(e => e.name === '김테스트'));
});

test('카드 거절이면 결제 실패, 작업 시작 안 함', async () => {
  const t = setup({ tossFail: true });
  const { body: o } = await order(t);
  const r = await t.call('POST', `/api/orders/${o.orderId}/confirm`, { body: { paymentKey: 'pk', amount: 49800 }, headers: { Authorization: 'Bearer ' + o.accessToken } });
  assert.equal(r.status, 402); assert.equal(t.calls.dispatch.length, 0);
});

test('보류되면 사장님께 알림', async () => {
  const t = setup();
  const { body: o } = await order(t);
  await t.call('POST', `/api/orders/${o.orderId}/confirm`, { body: { paymentKey: 'pk', amount: 49800 }, headers: { Authorization: 'Bearer ' + o.accessToken } });
  const v = await (await t.call('POST', `/api/internal/orders/${o.orderId}/status`, { body: { status: 'held', note: 'PDF 작성 실패' }, headers: { 'X-Worker-Secret': 'worker-secret' } })).json();
  assert.equal(v.status, 'held'); assert.deepEqual(t.calls.owner, ['PDF 작성 실패']);
});

test('메일 첨부 PDF 이름은 "이름님의 상품 - 금월선녀의 운명서재.pdf"', async () => {
  const { realServices } = await import('../netlify/functions/lib/services.mjs');
  let sent;
  const svc = realServices({ RESEND_API_KEY: 're' }, async (url, init) => { sent = JSON.parse(init.body); return new Response('{}', { status: 200 }); });
  await svc.sendEmail({ id: 'x', email: 'a@b.c', productId: 'romance', payload: { self: { name: '김민지' } } }, new Uint8Array([1]));
  assert.equal(sent.attachments[0].filename, '김민지님의 연애사주 - 금월선녀의 운명서재.pdf');
});

test('8개 상품 모두 서버 접수 확인이 된다', async () => {
  const t = setup();
  for (const productId of ['lifetime', 'romance', 'reunion', 'intimate', 'wealth', 'career', 'business', 'health']) {
    const r = await t.call('POST', '/api/intake/assess', { body: { productId, self, partner: self, answers: {} } });
    assert.equal(r.status, 200, productId);
  }
});

test('결제 뒤 1시간 넘게 멈춘 주문은 자동으로 한 번 다시 돌리고, 그래도 멈추면 사장님께 한 번만 알림', async () => {
  const t = setup();
  const { body: o } = await order(t);
  const { body: unpaid } = await order(t);
  await t.call('POST', `/api/orders/${o.orderId}/confirm`, { body: { paymentKey: 'pk', amount: 49800 }, headers: { Authorization: 'Bearer ' + o.accessToken } });
  t.calls.owner.length = 0; t.calls.dispatch.length = 0;
  const services = { startWorker: async id => { t.calls.dispatch.push(id); }, notifyOwner: async (ord, note) => { t.calls.owner.push(ord.id); } };
  const at = h => new Date(Date.now() + h * 3_600_000);
  assert.equal(await flagStuck(t.store, services, at(0.5)), 0);
  assert.equal(await flagStuck(t.store, services, at(2)), 1); // 자동 재실행 1번
  assert.deepEqual(t.calls.dispatch, [o.orderId]); assert.deepEqual(t.calls.owner, []);
  assert.equal((await t.store.get(`orders/${o.orderId}`)).status, 'queued');
  assert.equal(await flagStuck(t.store, services, at(2.5)), 0);
  assert.equal(await flagStuck(t.store, services, at(3.5)), 1); // 그래도 멈춤 → 알림
  assert.equal(await flagStuck(t.store, services, at(5)), 0); // 다시 돌리거나 알리지 않음
  assert.deepEqual(t.calls.dispatch, [o.orderId]); assert.deepEqual(t.calls.owner, [o.orderId]); assert.ok(unpaid.orderId);
});

test('발송 보류(held)된 주문은 1시간 뒤 자동으로 한 번만 다시 만든다', async () => {
  const t = setup();
  const { body: o } = await order(t);
  await t.call('POST', `/api/orders/${o.orderId}/confirm`, { body: { paymentKey: 'pk', amount: 49800 }, headers: { Authorization: 'Bearer ' + o.accessToken } });
  const W = { 'X-Worker-Secret': 'worker-secret' };
  await t.call('POST', `/api/internal/orders/${o.orderId}/status`, { body: { status: 'held', note: '글 검사: 점수' }, headers: W });
  assert.equal((await t.store.get(`orders/${o.orderId}`)).status, 'held');
  t.calls.dispatch.length = 0;
  const services = { startWorker: async id => { t.calls.dispatch.push(id); }, notifyOwner: async () => {} };
  const at = h => new Date(Date.now() + h * 3_600_000);
  assert.equal(await flagStuck(t.store, services, at(2)), 1);
  assert.deepEqual(t.calls.dispatch, [o.orderId]);
  // 다시 돌린 작업이 또 보류하면 더는 자동으로 돌리지 않는다(보류 알림은 이미 감)
  const held = await t.store.get(`orders/${o.orderId}`);
  held.status = 'held'; held.updatedAt = at(2.2).toISOString(); await t.store.set(`orders/${o.orderId}`, held);
  assert.equal(await flagStuck(t.store, services, at(5)), 0);
  assert.deepEqual(t.calls.dispatch, [o.orderId]);
});

test('작업 시작(dispatch)이 실패해 retry로 남은 주문도 자동으로 다시 시작한다', async () => {
  const t = setup();
  const { body: o } = await order(t);
  await t.call('POST', `/api/orders/${o.orderId}/confirm`, { body: { paymentKey: 'pk', amount: 49800 }, headers: { Authorization: 'Bearer ' + o.accessToken } });
  const x = await t.store.get(`orders/${o.orderId}`); x.status = 'retry'; await t.store.set(`orders/${o.orderId}`, x);
  const sent = [];
  assert.equal(await flagStuck(t.store, { startWorker: async id => { sent.push(id); }, notifyOwner: async () => {} }, new Date(Date.now() + 2 * 3_600_000)), 1);
  assert.deepEqual(sent, [o.orderId]);
});

test('개인정보 지우기: 발송 즉시 출생 정보 삭제, PDF는 7일 뒤 삭제, 미결제 주문은 하루 뒤 만료', async () => {
  const t = setup();
  const { body: a } = await order(t);
  const { body: b } = await order(t);
  await t.call('POST', `/api/orders/${a.orderId}/confirm`, { body: { paymentKey: 'pk', amount: 49800 }, headers: { Authorization: 'Bearer ' + a.accessToken } });
  await t.call('POST', `/api/internal/orders/${a.orderId}/result`, { raw: new Uint8Array([1, 2]), headers: { 'X-Worker-Secret': 'worker-secret' } });
  // 메일이 나가면 출생 정보·질문은 바로 사라지고, PDF와 다시 보내기는 남는다
  let A = await t.store.get(`orders/${a.orderId}`);
  assert.equal(A.status, 'email_accepted'); assert.equal(A.payload, undefined); assert.equal(A.disclosures, undefined);
  assert.ok(await t.store.getBytes(`pdf/${a.orderId}`));
  assert.equal((await t.call('GET', `/api/internal/orders/${a.orderId}`, { headers: { 'X-Worker-Secret': 'worker-secret' } })).status, 410);
  const resent = await t.call('POST', `/api/orders/${a.orderId}/resend`, { body: {}, headers: { Authorization: 'Bearer ' + a.accessToken, 'Idempotency-Key': 'x1' } });
  assert.equal(resent.status, 200); assert.equal(t.calls.email.length, 2);
  // 6일째: PDF 그대로
  await eraseOld(t.store, new Date(Date.now() + 6 * 86_400_000));
  assert.ok(await t.store.getBytes(`pdf/${a.orderId}`));
  const later = new Date(Date.now() + 8 * 86_400_000);
  await eraseOld(t.store, later); // b: 만료, a: PDF 지움
  await eraseOld(t.store, new Date(later.getTime() + 8 * 86_400_000)); // b도 지움
  A = await t.store.get(`orders/${a.orderId}`); const B = await t.store.get(`orders/${b.orderId}`);
  assert.equal(A.status, 'erased'); assert.equal(await t.store.getBytes(`pdf/${a.orderId}`), null);
  assert.equal(B.status, 'erased'); assert.equal(B.payload, undefined); assert.equal(A.email, 'buyer@example.com'); // 거래 기록은 남김
});

test('결제 승인은 접근 열쇠 없이도 된다(브라우저 저장값이 사라진 경우)', async () => {
  const t = setup();
  const { body: o } = await order(t);
  const v = await (await t.call('POST', `/api/orders/${o.orderId}/confirm`, { body: { paymentKey: 'pk', amount: 49800 } })).json();
  assert.equal(v.status, 'queued'); assert.equal(v.amount, undefined); assert.equal(t.calls.dispatch.length, 1);
  assert.equal((await t.call('GET', `/api/orders/${o.orderId}`)).status, 403);
});

test('들어온 곳(from): 주문에 저장하고, 결제되면 달마다 들어온 곳별로 센다', async () => {
  const t = setup();
  const pay = async extra => {
    const { body } = await order(t, extra);
    await t.call('POST', `/api/orders/${body.orderId}/confirm`, { body: { paymentKey: 'pk', amount: body.amount }, headers: { Authorization: 'Bearer ' + body.accessToken } });
    return t.store.get(`orders/${body.orderId}`);
  };
  const a = await pay({ from: 'dn' });
  assert.equal(a.source, 'dn');
  const b = await pay({ from: 'BAD value!<script>' });
  assert.equal(b.source, undefined);
  await pay({ from: 'dn' });
  const month = new Date(Date.now() + 9 * 3600_000).toISOString().slice(0, 7);
  const stats = await t.store.get(`stats/sources/${month}`);
  assert.equal(stats.dn.orders, 2); assert.equal(stats.dn.amount, a.amount * 2);
  assert.equal(stats.direct.orders, 1);
});

test('메일 도착 확인: Resend 알림(서명 확인)으로 도착·튕김을 주문에 남기고, 튕기면 사장님께 알림 (P-IT-2)', async () => {
  const { createHmac } = await import('node:crypto');
  const secret = 'whsec_' + Buffer.from('test-secret-key-123').toString('base64');
  const t = setup({ env: { ...ENV, RESEND_WEBHOOK_SECRET: secret } });
  // 이 시험에서는 보낸 메일 번호를 돌려준다
  let n = 0;
  const { body: a } = await order(t);
  await t.call('POST', `/api/orders/${a.orderId}/confirm`, { body: { paymentKey: 'pk', amount: 49800 }, headers: { Authorization: 'Bearer ' + a.accessToken } });
  t.calls.owner.length = 0;
  // setup의 sendEmail은 번호를 돌려주지 않으므로, 번호를 돌려주는 가짜로 바꿔 끼운다
  const { deliverPdf, mailEvent, verifyMailWebhook } = await import('../netlify/functions/lib/orders.mjs');
  const services = { sendEmail: async () => `re_${++n}`, notifyOwner: async (o, note, kind) => { t.calls.owner.push(kind); } };
  await deliverPdf(t.store, services, await t.store.get(`orders/${a.orderId}`), new Uint8Array([1, 2]));
  assert.deepEqual((await t.store.get(`orders/${a.orderId}`)).mailIds, ['re_1']);
  const sign = (body, ts = Math.floor(Date.now() / 1000), id = 'msg_1') => ({
    'svix-id': id, 'svix-timestamp': String(ts),
    'svix-signature': 'v1,' + createHmac('sha256', Buffer.from(secret.slice(6), 'base64')).update(`${id}.${ts}.${body}`).digest('base64'),
  });
  const ev = type => JSON.stringify({ type, data: { email_id: 're_1' } });
  // 서명이 틀리거나 오래된 알림은 받지 않는다
  assert.equal((await t.call('POST', '/api/mail-events', { raw: ev('email.delivered'), headers: { ...sign(ev('email.delivered')), 'svix-signature': 'v1,xxxx' } })).status, 401);
  assert.equal((await t.call('POST', '/api/mail-events', { raw: ev('email.delivered'), headers: sign(ev('email.delivered'), Math.floor(Date.now() / 1000) - 3600) })).status, 401);
  // 도착함
  assert.equal((await t.call('POST', '/api/mail-events', { raw: ev('email.delivered'), headers: sign(ev('email.delivered')) })).status, 200);
  assert.equal((await t.store.get(`orders/${a.orderId}`)).mailStatus, 'delivered');
  // 늦게 온 '늦어짐'은 '도착함'을 덮지 않는다
  await mailEvent(t.store, services, JSON.parse(ev('email.delivery_delayed')));
  assert.equal((await t.store.get(`orders/${a.orderId}`)).mailStatus, 'delivered');
  // 튕김 → 기록 + 사장님 알림
  await mailEvent(t.store, services, JSON.parse(ev('email.bounced')));
  assert.equal((await t.store.get(`orders/${a.orderId}`)).mailStatus, 'bounced');
  assert.deepEqual(t.calls.owner.concat(), ['bounced']);
  // 모르는 메일 번호는 무시
  assert.equal(await mailEvent(t.store, services, { type: 'email.delivered', data: { email_id: 're_x' } }), null);
  assert.equal(verifyMailWebhook('', new Headers(), ''), false);
  // 비밀값이 없으면 꺼져 있다
  const off = setup();
  assert.equal((await off.call('POST', '/api/mail-events', { raw: ev('email.delivered'), headers: sign(ev('email.delivered')) })).status, 404);
});
