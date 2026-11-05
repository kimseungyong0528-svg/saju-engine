// 체험단 무료 코드와 후기(2026-11-05). 코드 하나로 한 권만 무료, 한 번만. 후기는 받은 주문만, 사장님이 싣기 전엔 안 보이고, 체험단 후기엔 '무료 제공' 표시.
import test from 'node:test';
import assert from 'node:assert/strict';
import { makeApi, memoryStore } from '../netlify/functions/lib/api.mjs';
import { issueTrialCodes, moderateReview } from '../netlify/functions/lib/reviews.mjs';

const ENV = { TOSS_CLIENT_KEY: 'live_ck', TOSS_SECRET_KEY: 'live_sk', GH_DISPATCH_TOKEN: 'gh', WORKER_SECRET: 'worker-secret', RESEND_API_KEY: 're', SITE_URL: 'https://unmyeong-saju.com' };
const place = { status: 'known', countryCode: 'KR', countryName: '대한민국', regionChoice: '1100000000', regionCode: '1100000000', districtCode: '1111000000', city: '종로구', inputMode: 'list', referenceEra: 'unknown' };
const self = { name: '김테스트', sex: 'female', birth: '1995-03-12', calendar: 'solar', timeAccuracy: 'exact', time: '06:30', birthPlace: place };
const draft = { self, answers: { occupation: '직장에 다니고 있어요' }, question: '앞으로 일은?', email: 'trial@example.com' };

function setup() {
  const store = memoryStore();
  const calls = { toss: [], dispatch: [], email: [] };
  const services = {
    tossConfirm: async a => { calls.toss.push(a); return { ok: true }; },
    startWorker: async id => { calls.dispatch.push(id); },
    sendEmail: async o => { calls.email.push(o.id); return 'm1'; },
  };
  const api = makeApi({ store, services, env: ENV });
  const call = (method, path, body, headers = {}) => api(new Request('https://x.test' + path, {
    method, headers: { ...(body ? { 'Content-Type': 'application/json' } : {}), ...headers }, body: body instanceof Uint8Array ? body : body ? JSON.stringify(body) : undefined,
  }));
  const order = async extra => {
    const r = await call('POST', '/api/orders', { ...draft, productId: 'lifetime', ...extra }, { 'Idempotency-Key': 'key-' + Math.random().toString(36).slice(2) });
    return { r, b: await r.json() };
  };
  return { store, calls, call, order };
}

test('체험단 코드: 리포트 한 권 0원, 토스 없이 승인되어 바로 작성, 코드는 한 번만', async () => {
  const t = setup();
  const { codes } = await issueTrialCodes(t.store, 2, ENV.SITE_URL);
  assert.equal(codes.length, 2); assert.match(codes[0].code, /^TRY-/); assert.match(codes[0].url, /\?coupon=TRY-.*&from=trial$/);
  const q = await (await t.call('POST', '/api/quote', { productId: 'newyear', email: 'trial@example.com', coupon: codes[0].code })).json();
  assert.equal(q.amount, 0); assert.equal(q.discount.percent, 100); assert.equal(q.discount.label, '체험단 무료 제공');
  const { r, b } = await t.order({ coupon: codes[0].code });
  assert.equal(r.status, 201, JSON.stringify(b)); assert.equal(b.amount, 0);
  const c = await t.call('POST', `/api/orders/${b.orderId}/confirm`, { paymentKey: 'trial', amount: 0 }, { Authorization: 'Bearer ' + b.accessToken });
  assert.equal(c.status, 200); assert.equal((await c.json()).status, 'queued');
  assert.equal(t.calls.toss.length, 0, '0원 체험단 주문은 토스에 보내지 않는다');
  assert.deepEqual(t.calls.dispatch, [b.orderId]);
  // 같은 코드 다시: 견적에서 틀린 코드, 주문도 안 된다
  const q2 = await (await t.call('POST', '/api/quote', { productId: 'romance', email: 'x@example.com', coupon: codes[0].code })).json();
  assert.ok(q2.notes.includes('COUPON_INVALID')); assert.equal(q2.amount, 29800);
  assert.equal((await t.order({ coupon: codes[0].code, email: 'x@example.com' })).r.status, 400);
  // 체험단 무료는 첫 구매로 치지 않고, 온 곳 통계는 '체험단'으로 따로
  assert.equal((await t.store.list('buyers/')).length, 0);
  const month = new Date(Date.now() + 9 * 3600_000).toISOString().slice(0, 7);
  assert.deepEqual((await t.store.get(`stats/sources/${month}`)).trial, { orders: 1, amount: 0 });
});

test('체험단 코드로 두 주문을 만들어도 승인은 하나만', async () => {
  const t = setup();
  const { codes } = await issueTrialCodes(t.store, 1, ENV.SITE_URL);
  const a = (await t.order({ coupon: codes[0].code })).b, b = (await t.order({ coupon: codes[0].code, email: 'other@example.com' })).b;
  assert.equal((await t.call('POST', `/api/orders/${a.orderId}/confirm`, { paymentKey: 'trial', amount: 0 }, { Authorization: 'Bearer ' + a.accessToken })).status, 200);
  const r2 = await t.call('POST', `/api/orders/${b.orderId}/confirm`, { paymentKey: 'trial', amount: 0 }, { Authorization: 'Bearer ' + b.accessToken });
  assert.equal(r2.status, 400); assert.equal((await r2.json()).code, 'COUPON_INVALID');
  assert.equal(t.calls.dispatch.length, 1);
});

test('체험단 코드 + 함께 고른 상품: 체험 한 권만 무료, 나머지는 정가로 토스 결제', async () => {
  const t = setup();
  const { codes } = await issueTrialCodes(t.store, 1, ENV.SITE_URL);
  const q = await (await t.call('POST', '/api/quote', { productId: 'newyear', email: 'trial@example.com', coupon: codes[0].code, extras: ['health'] })).json();
  assert.equal(q.base, 59600); assert.equal(q.amount, 29800);
});

test('체험단 코드는 모두 30개까지, 한 번에 10개까지', async () => {
  const t = setup();
  for (let i = 0; i < 3; i++) await issueTrialCodes(t.store, 10, ENV.SITE_URL);
  await assert.rejects(issueTrialCodes(t.store, 1, ENV.SITE_URL), e => e.code === 'TRIAL_LIMIT');
  await assert.rejects(issueTrialCodes(memoryStore(), 11, ENV.SITE_URL), e => e.code === 'BAD_COUNT');
});

test('후기: 리포트를 받은 뒤에만, 사장님이 싣기 전엔 안 보이고, 체험단 후기엔 무료 제공 표시', async () => {
  const t = setup();
  const { codes } = await issueTrialCodes(t.store, 1, ENV.SITE_URL);
  const { b } = await t.order({ coupon: codes[0].code });
  const auth = { Authorization: 'Bearer ' + b.accessToken };
  await t.call('POST', `/api/orders/${b.orderId}/confirm`, { paymentKey: 'trial', amount: 0 }, auth);
  const review = { stars: 5, text: '좋은 달이 언제인지 알게 되어 계획 세우기 좋았어요.', nick: '김**', agree: true };
  assert.equal((await t.call('POST', `/api/orders/${b.orderId}/review`, review, auth)).status, 409, '받기 전에는 후기를 못 쓴다');
  const pdf = new Uint8Array([37, 80, 68, 70, 1, 2, 3]);
  assert.equal((await t.call('POST', `/api/internal/orders/${b.orderId}/result`, pdf, { 'x-worker-secret': 'worker-secret' })).status, 200);
  assert.equal((await t.call('POST', `/api/orders/${b.orderId}/review`, { ...review, agree: false }, auth)).status, 400);
  assert.equal((await t.call('POST', `/api/orders/${b.orderId}/review`, { ...review, text: '짧음' }, auth)).status, 400);
  assert.equal((await t.call('POST', `/api/orders/${b.orderId}/review`, review, auth)).status, 200);
  assert.equal((await t.call('POST', `/api/orders/${b.orderId}/review`, review)).status, 403, '다른 사람은 이 주문에 후기를 못 쓴다');
  let pub = await (await t.call('GET', '/api/reviews?product=lifetime')).json();
  assert.equal(pub.count, 0, '사장님이 싣기 전에는 안 보인다');
  await moderateReview(t.store, b.orderId, 'approve');
  pub = await (await t.call('GET', '/api/reviews?product=lifetime')).json();
  assert.equal(pub.count, 1); assert.equal(pub.trialCount, 1); assert.equal(pub.avg, 5);
  assert.deepEqual(Object.keys(pub.reviews[0]).sort(), ['date', 'nick', 'productId', 'stars', 'text', 'trial']);
  assert.equal(pub.reviews[0].trial, true);
  assert.equal(pub.reviews[0].text, review.text, '후기 글은 고치지 않는다');
  assert.equal((await t.call('POST', `/api/orders/${b.orderId}/review`, review, auth)).status, 409, '실린 뒤에는 바꾸지 않는다');
  await moderateReview(t.store, b.orderId, 'hide');
  assert.equal((await (await t.call('GET', '/api/reviews')).json()).count, 0);
});
