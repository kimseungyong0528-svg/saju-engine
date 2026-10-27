// 할인 장치 (2026-10-27 사장님 결정). 할인은 모두 10%이고, 한 주문에는 하나만 들어간다(더하지 않음).
// 1) 첫 구매 묶음 할인: 처음 사는 이메일이 상품 2개 이상을 함께 사면 전부 10%.
// 2) 할인 코드: 리포트 끝·메일로 받은 재구매 코드, 친구 초대 보상 코드. 한 번 쓰면 끝.
// 3) 친구 초대: 초대 링크(?ref=)로 들어온 친구 10%. 친구가 결제하면 초대한 사람에게 10% 코드를 보낸다.
// 금액은 항상 서버가 계산한다. 화면에서 보낸 금액·할인값은 믿지 않는다.
import { createHash, createHmac, randomBytes } from 'node:crypto';
import { PRODUCTS, intakePayload, evaluateIntake } from './intake.mjs';

export const PERCENT = 10;
export const COUPON_DAYS = 30;
// 묶음에 함께 담을 수 있는 상품. 재회·깊은궁합은 상대방 정보가 필요해서, 주 주문에 상대방 정보가 있을 때만 접수 검사를 통과한다.
export const BUNDLE_PRODUCTS = ['newyear', 'romance', 'intimate', 'reunion', 'wealth', 'career', 'business', 'health', 'lifetime'];
const LABELS = { bundle: '첫 구매 묶음 할인', rebuy: '재구매 할인', 'referral-reward': '친구 초대 보상 할인', referral: '친구 초대 할인' };

export const emailHash = email => createHash('sha256').update('unmyeong:' + String(email || '').trim().toLowerCase()).digest('hex');
const CODE_CHARS = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
export const newCode = (prefix = 'UNM') => prefix + '-' + Array.from(randomBytes(6), b => CODE_CHARS[b % CODE_CHARS.length]).join('');
const normCode = c => String(c || '').trim().toUpperCase().replace(/[^A-Z0-9-]/g, '').slice(0, 20);
export const discounted = base => Math.round(base * (100 - PERCENT) / 100);

export function kstDate(iso) {
  const d = new Date(new Date(iso).getTime() + 9 * 3600e3);
  return `${d.getUTCFullYear()}년 ${d.getUTCMonth() + 1}월 ${d.getUTCDate()}일`;
}

// 함께 사는 상품: 중복·주 상품·묶음 불가 상품을 빼고, 같은 출생 정보와 그 상품 질문의 답으로 접수가 되는 것만 남긴다.
export function bundleItems(body) {
  const main = String(body?.productId || '');
  const want = [...new Set(Array.isArray(body?.extras) ? body.extras.map(String) : [])]
    .filter(id => id !== main && BUNDLE_PRODUCTS.includes(id)).slice(0, BUNDLE_PRODUCTS.length);
  return want.filter(id => evaluateIntake(intakePayload(id, extraBody(body, id))).inputAccepted);
}

// 함께 사는 상품의 접수 내용: 출생 정보는 주 상품과 같고, 그 상품의 질문 답(extraAnswers)만 따로 받는다.
export function extraBody(body, id) {
  const ans = body?.extraAnswers && typeof body.extraAnswers === 'object' ? body.extraAnswers[id] : null;
  return { ...body, productId: id, answers: ans && typeof ans === 'object' ? ans : {}, question: '' };
}

async function validCoupon(store, code, now) {
  if (!code) return null;
  const c = await store.get(`coupons/${code}`);
  if (!c || c.usedAt || new Date(c.expiresAt) < now) return null;
  return c;
}

// 가격 계산. 화면의 '상품 금액 안내'와 실제 주문 금액이 같은 함수에서 나온다.
export async function quote(store, body, now = new Date()) {
  const main = PRODUCTS.find(p => p.id === String(body?.productId || ''));
  if (!main) return null;
  const extras = bundleItems(body);
  const items = [main, ...extras.map(id => PRODUCTS.find(p => p.id === id))].map(p => ({ id: p.id, name: p.name, price: p.price }));
  const base = items.reduce((a, p) => a + p.price, 0);
  const hash = body?.email ? emailHash(body.email) : null;
  const buyer = hash ? Boolean(await store.get(`buyers/${hash}`)) : null;
  const code = normCode(body?.coupon), refCode = normCode(body?.ref);
  const coupon = await validCoupon(store, code, now);
  const ref = refCode ? await store.get(`refs/${refCode}`) : null;
  let discount = null;
  if (coupon) discount = { kind: coupon.kind, code };
  else if (extras.length && hash && !buyer) discount = { kind: 'bundle' };
  else if (ref && hash && ref.ownerHash !== hash) discount = { kind: 'referral', code: refCode };
  if (discount) discount = { ...discount, label: LABELS[discount.kind] || '할인', percent: PERCENT, amount: base - discounted(base) };
  const notes = [];
  if (code && !coupon) notes.push('COUPON_INVALID');
  if (extras.length && buyer && !coupon) notes.push('BUNDLE_FIRST_ONLY');
  if (extras.length && !hash) notes.push('EMAIL_FOR_DISCOUNT');
  return { items, extras, base, discount, amount: discount ? base - discount.amount : base, firstPurchase: hash ? !buyer : null, notes };
}

// 결제가 확인된 뒤: 코드 사용 처리, 첫 구매 기록, 친구 초대 보상 코드 발급.
export async function afterPaid(store, services, order, now = new Date()) {
  const hash = emailHash(order.email);
  if (!(await store.get(`buyers/${hash}`))) await store.set(`buyers/${hash}`, { firstPaidAt: now.toISOString() });
  const d = order.discount;
  if (d?.code && d.kind !== 'referral') {
    const c = await store.get(`coupons/${d.code}`);
    if (c && !c.usedAt) await store.set(`coupons/${d.code}`, { ...c, usedAt: now.toISOString(), usedBy: order.id });
  }
  if (d?.kind === 'referral') {
    const ref = await store.get(`refs/${d.code}`);
    if (ref?.email && ref.ownerHash !== hash) {
      const coupon = await issueCoupon(store, 'referral-reward', now);
      await store.set(`refs/${d.code}`, { ...ref, rewards: (ref.rewards || 0) + 1 });
      if (!(await store.get(`unsub/${ref.ownerHash}`))) await services.sendCoupon?.(ref.email, coupon, 'referral-reward', { ref: d.code }).catch(() => {});
    }
  }
}

export async function issueCoupon(store, kind, now = new Date()) {
  const code = newCode();
  const coupon = { code, kind, percent: PERCENT, createdAt: now.toISOString(), expiresAt: new Date(now.getTime() + COUPON_DAYS * 864e5).toISOString() };
  await store.set(`coupons/${code}`, coupon);
  return coupon;
}

// 리포트 끝에 넣는 재구매 코드. 주문마다 한 번만 만든다.
export async function rebuyFor(store, order, site, now = new Date()) {
  let c = order.rebuyCode ? await store.get(`coupons/${order.rebuyCode}`) : null;
  if (!c) {
    c = await issueCoupon(store, 'rebuy', now);
    order.rebuyCode = c.code;
    await store.set(`orders/${order.id}`, order);
  }
  return { code: c.code, until: kstDate(c.expiresAt), url: `${String(site || 'https://unmyeong-saju.com').replace(/\/$/, '')}/?coupon=${c.code}` };
}

// 묶음으로 함께 만든 책은 본 주문의 코드를 같이 쓴다(한 번 결제에 코드 하나).
export async function rebuyForJob(store, order, site, now = new Date()) {
  const main = order.parentId ? await store.get(`orders/${order.parentId}`) : order;
  return main ? rebuyFor(store, main, site, now) : null;
}

// 재구매 안내 메일: 결과를 보낸 지 3일 뒤, 광고 메일에 동의한 손님에게 한 번만. 이미 코드를 썼거나 수신 거부했으면 보내지 않는다.
export const REMIND_DAYS = 3;
export async function remindRebuy(store, services, now = new Date()) {
  let sent = 0;
  for (const key of await store.list('orders/')) {
    const o = await store.get(key);
    if (!o || o.parentId || !o.marketing || o.rebuyMailedAt || !o.emailedAt || !o.rebuyCode) continue;
    if ((now - new Date(o.emailedAt)) / 864e5 < REMIND_DAYS) continue;
    o.rebuyMailedAt = now.toISOString();
    await store.set(key, o);
    const c = await store.get(`coupons/${o.rebuyCode}`);
    if (!c || c.usedAt || new Date(c.expiresAt) < now || await store.get(`unsub/${emailHash(o.email)}`)) continue;
    const ref = await referralFor(store, o).catch(() => null);
    await services.sendCoupon?.(o.email, c, 'rebuy', { name: o.mailName, ref }).then(() => { sent += 1; }).catch(e => console.error('remind', e?.message));
  }
  return sent;
}

// 친구 초대 링크: 광고 메일에 동의한 손님에게만 만든다(보상 코드를 메일로 보내야 하므로).
export async function referralFor(store, order) {
  if (!order.marketing) return null;
  const hash = emailHash(order.email);
  const mine = await store.get(`refowner/${hash}`);
  if (mine) return mine.code;
  const code = newCode('FR');
  await store.set(`refs/${code}`, { ownerHash: hash, email: order.email, createdAt: new Date().toISOString() });
  await store.set(`refowner/${hash}`, { code });
  return code;
}

// 수신 거부 링크(광고 메일 끝). 비밀값으로 서명해서 남의 이메일을 대신 거부할 수 없게 한다.
export const unsubToken = (hash, secret) => createHmac('sha256', String(secret || '')).update(hash).digest('hex').slice(0, 32);
export const unsubUrl = (email, site, secret) => {
  const h = emailHash(email);
  return `${String(site || 'https://unmyeong-saju.com').replace(/\/$/, '')}/api/unsubscribe?h=${h}&t=${unsubToken(h, secret)}`;
};
