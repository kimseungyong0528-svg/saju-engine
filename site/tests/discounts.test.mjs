// 할인 시험(2026-10-27 사장님 결정): 첫 구매 묶음 10%, 재구매 코드 10%, 할인은 하나만. 할인 코드 칸·친구 초대·할인 메일은 없다.
import test from 'node:test';
import assert from 'node:assert/strict';
import { makeApi, memoryStore } from '../netlify/functions/lib/api.mjs';

const ENV = { TOSS_CLIENT_KEY: 'live_ck', TOSS_SECRET_KEY: 'live_sk', GH_DISPATCH_TOKEN: 'gh', WORKER_SECRET: 'worker-secret', RESEND_API_KEY: 're', SITE_URL: 'https://unmyeong-saju.com' };
const place = { status: 'known', countryCode: 'KR', countryName: '대한민국', regionChoice: '1100000000', regionCode: '1100000000', districtCode: '1111000000', city: '종로구', inputMode: 'list', referenceEra: 'unknown' };
const self = { name: '김테스트', sex: 'female', birth: '1995-03-12', calendar: 'solar', timeAccuracy: 'exact', time: '06:30', birthPlace: place };
const W = { wealth: { occupation: '직장에 다니고 있어요' } };
const draft = { self, answers: { occupation: '직장에 다니고 있어요' }, question: '', email: 'a@example.com' };

function setup() {
  const store = memoryStore();
  const calls = { dispatch: [], email: [] };
  const services = {
    tossConfirm: async () => ({ ok: true }),
    startWorker: async id => { calls.dispatch.push(id); },
    sendEmail: async o => { calls.email.push(o.id); },
  };
  const api = makeApi({ store, services, env: ENV });
  const call = (method, path, body, headers = {}) => api(new Request('https://x.test' + path, {
    method, headers: { 'Content-Type': 'application/json', ...headers }, body: body ? JSON.stringify(body) : undefined,
  }));
  const buy = async extra => {
    const b = await (await call('POST', '/api/orders', { ...draft, productId: 'lifetime', ...extra }, { 'Idempotency-Key': 'k-' + Math.random().toString(36).slice(2) })).json();
    if (b.orderId) await call('POST', `/api/orders/${b.orderId}/confirm`, { paymentKey: 'pk', amount: b.amount }, { Authorization: 'Bearer ' + b.accessToken });
    return b;
  };
  const job = async id => (await call('GET', `/api/internal/orders/${id}`, null, { 'x-worker-secret': 'worker-secret' })).json();
  return { store, calls, call, buy, job };
}

test('첫 구매 묶음: 2개 이상이면 전부 10%, 결제 뒤 책마다 따로 만든다', async () => {
  const t = setup();
  const q = await (await t.call('POST', '/api/quote', { ...draft, productId: 'lifetime', extras: ['wealth', 'lifetime', 'reunion', 'health'], extraAnswers: { wealth: { occupation: '직장에 다니고 있어요' } } })).json();
  assert.deepEqual(q.items.map(i => i.id), ['lifetime', 'wealth']);   // 주 상품·상대방 필요한 상품·질문 답이 없는 상품은 빠진다
  assert.equal(q.base, 49800 + 29800); assert.equal(q.discount.kind, 'bundle'); assert.equal(q.amount, Math.round(79600 * 0.9));
  const b = await t.buy({ extras: ['wealth'], extraAnswers: W, discount: 99999 });
  assert.equal(b.amount, 71640);
  const o = await t.store.get(`orders/${b.orderId}`);
  assert.equal(o.status, 'queued'); assert.equal(o.children.length, 1);
  const child = await t.store.get(`orders/${o.children[0]}`);
  assert.equal(child.productId, 'wealth'); assert.equal(child.amount, 0); assert.equal(child.parentId, o.id);
  assert.deepEqual(t.calls.dispatch, [o.id, child.id]);
  // 두 번째 구매부터는 묶음 할인 없음
  const q2 = await (await t.call('POST', '/api/quote', { ...draft, productId: 'lifetime', extras: ['wealth'], extraAnswers: W })).json();
  assert.equal(q2.discount, null); assert.equal(q2.amount, 79600); assert.ok(q2.notes.includes('BUNDLE_FIRST_ONLY'));
  // 한 개만 사면 묶음 할인 없음
  const t2 = setup();
  const q3 = await (await t2.call('POST', '/api/quote', { ...draft, productId: 'lifetime' })).json();
  assert.equal(q3.discount, null); assert.equal(q3.amount, 49800);
});

test('재구매 코드: 리포트에 실리고, 한 번 쓰면 끝, 묶음 책은 같은 코드', async () => {
  const t = setup();
  const b = await t.buy({ extras: ['wealth'], extraAnswers: W });
  const o = await t.store.get(`orders/${b.orderId}`);
  const j1 = await t.job(o.id), j2 = await t.job(o.children[0]);
  assert.match(j1.rebuy.code, /^UNM-[A-Z2-9]{6}$/); assert.equal(j2.rebuy.code, j1.rebuy.code);
  assert.equal(j1.rebuy.url, `https://unmyeong-saju.com/?coupon=${j1.rebuy.code}`); assert.match(j1.rebuy.until, /년 .*월 .*일$/);
  assert.equal((await t.job(o.id)).rebuy.code, j1.rebuy.code);   // 다시 물어도 같은 코드
  // 코드는 묶음보다 먼저, 금액은 10%
  const q = await (await t.call('POST', '/api/quote', { ...draft, productId: 'romance', coupon: j1.rebuy.code.toLowerCase() })).json();
  assert.equal(q.discount.kind, 'rebuy'); assert.equal(q.amount, Math.round(29800 * 0.9));
  const b2 = await t.buy({ coupon: j1.rebuy.code });
  assert.equal(b2.amount, Math.round(49800 * 0.9));
  const again = await (await t.call('POST', '/api/orders', { ...draft, productId: 'lifetime', coupon: j1.rebuy.code }, { 'Idempotency-Key': 'k-again-1' })).json();
  assert.equal(again.code, 'COUPON_INVALID');
});

test('친구 초대·할인 메일은 없다: 초대 링크(ref)는 할인되지 않고, 수신 거부 주소도 없다', async () => {
  const t = setup();
  const a = await t.buy({});
  assert.equal((await t.job(a.orderId)).rebuy.invite, undefined);
  const q = await (await t.call('POST', '/api/quote', { ...draft, email: 'friend@example.com', productId: 'lifetime', ref: 'FR-ABCDEF' })).json();
  assert.equal(q.discount, null);
  assert.equal((await t.call('GET', '/api/unsubscribe?h=x&t=y')).status, 404);
});

test('재회·깊은궁합 묶음: 상대방 정보가 있는 주문에서만 함께 담긴다', async () => {
  const t = setup();
  const partner = { ...self, name: '이상대', sex: 'male', birth: '1993-07-01' };
  const q = await (await t.call('POST', '/api/quote', { ...draft, productId: 'reunion', partner, answers: { breakup: '3개월 이내예요' },
    extras: ['intimate'], extraAnswers: { intimate: { status: '헤어진 사이예요', duration: '1~3년' } } })).json();
  assert.deepEqual(q.items.map(i => i.id).sort(), ['intimate', 'reunion']);
  assert.equal(q.discount.kind, 'bundle');
});
