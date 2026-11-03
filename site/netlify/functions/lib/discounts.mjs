// 할인 장치 (2026-10-27 사장님 결정). 할인은 모두 10%이고, 한 주문에는 하나만 들어간다(더하지 않음).
// 1) 첫 구매 묶음 할인: 처음 사는 이메일이 상품 2개 이상을 함께 사면 전부 10%.
// 2) 재구매 할인: 리포트 끝의 링크(?coupon=)로 들어온 손님. 기한·횟수 제한 없음(2026-10-27 사장님). 할인 코드 칸·친구 초대·할인 메일은 없다.
// 금액은 항상 서버가 계산한다. 화면에서 보낸 금액·할인값은 믿지 않는다.
import { createHash, randomBytes } from 'node:crypto';
import { PRODUCTS, intakePayload, evaluateIntake } from './intake.mjs';

export const PERCENT = 10;
// 묶음에 함께 담을 수 있는 상품. 재회·깊은궁합은 상대방 정보가 필요해서, 주 주문에 상대방 정보가 있을 때만 접수 검사를 통과한다.
export const BUNDLE_PRODUCTS = ['newyear', 'romance', 'intimate', 'reunion', 'wealth', 'career', 'business', 'health', 'lifetime'];
const LABELS = { bundle: '첫 구매 묶음 할인', rebuy: '재구매 할인' };

export const emailHash = email => createHash('sha256').update('unmyeong:' + String(email || '').trim().toLowerCase()).digest('hex');
const CODE_CHARS = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
export const newCode = (prefix = 'UNM') => prefix + '-' + Array.from(randomBytes(6), b => CODE_CHARS[b % CODE_CHARS.length]).join('');
const normCode = c => String(c || '').trim().toUpperCase().replace(/[^A-Z0-9-]/g, '').slice(0, 20);
export const discounted = base => Math.round(base * (100 - PERCENT) / 100);

// 함께 사는 상품: 중복·주 상품·묶음 불가 상품을 뺀, 손님이 체크한 상품 전부.
export function bundleWanted(body) {
  const main = String(body?.productId || '');
  return [...new Set(Array.isArray(body?.extras) ? body.extras.map(String) : [])]
    .filter(id => id !== main && BUNDLE_PRODUCTS.includes(id)).slice(0, BUNDLE_PRODUCTS.length);
}
// 체크한 상품 가운데 그 상품 질문의 답(재회·깊은궁합은 상대방 정보)이 아직 없어 접수가 안 되는 것.
export const bundleIncomplete = body => bundleWanted(body).filter(id => !evaluateIntake(intakePayload(id, extraBody(body, id))).inputAccepted);
// 접수가 되는 것만(예전 이름).
export const bundleItems = body => { const bad = new Set(bundleIncomplete(body)); return bundleWanted(body).filter(id => !bad.has(id)); };

// 함께 사는 상품의 접수 내용: 출생 정보는 주 상품과 같고, 그 상품의 질문 답(extraAnswers)만 따로 받는다.
export function extraBody(body, id) {
  const ans = body?.extraAnswers && typeof body.extraAnswers === 'object' ? body.extraAnswers[id] : null;
  // 선물 주문 표시는 함께 사는 책에도 그대로(받는 분이 읽는 책이다)
  const gift = body?.answers?.revealGift === '1' ? { revealGift: '1' } : {};
  return { ...body, productId: id, answers: { ...(ans && typeof ans === 'object' ? ans : {}), ...gift }, question: '' };
}

async function validCoupon(store, code) {
  if (!code) return null;
  const c = await store.get(`coupons/${code}`);
  return c || null;
}

// 가격 계산. 화면의 '상품 금액 안내'와 실제 주문 금액이 같은 함수에서 나온다.
export async function quote(store, body, now = new Date()) {
  const main = PRODUCTS.find(p => p.id === String(body?.productId || ''));
  if (!main) return null;
  // 체크하면 금액에 바로 담는다(2026-10-28 손님 테스트: "체크했는데 금액이 안 바뀐다"). 답이 비어 있는 상품은 incomplete 로 알려 주고,
  // 주문(createOrder)은 그 답을 채우기 전에는 받지 않는다(말없이 빠지지 않게).
  const extras = bundleWanted(body), incomplete = bundleIncomplete(body);
  const items = [main, ...extras.map(id => PRODUCTS.find(p => p.id === id))].map(p => ({ id: p.id, name: p.name, price: p.price }));
  const base = items.reduce((a, p) => a + p.price, 0);
  const hash = body?.email ? emailHash(body.email) : null;
  const buyer = hash ? Boolean(await store.get(`buyers/${hash}`)) : null;
  const code = normCode(body?.coupon);
  const coupon = await validCoupon(store, code);
  let discount = null;
  if (coupon) discount = { kind: coupon.kind, code };
  else if (extras.length && hash && !buyer) discount = { kind: 'bundle' };
  if (discount) discount = { ...discount, label: LABELS[discount.kind] || '할인', percent: PERCENT, amount: base - discounted(base) };
  const notes = [];
  if (code && !coupon) notes.push('COUPON_INVALID');
  if (extras.length && buyer && !coupon) notes.push('BUNDLE_FIRST_ONLY');
  if (extras.length && !hash) notes.push('EMAIL_FOR_DISCOUNT');
  if (incomplete.length) notes.push('EXTRA_ANSWERS');
  return { items, extras, incomplete, base, discount, amount: discount ? base - discount.amount : base, firstPurchase: hash ? !buyer : null, notes };
}

// 결제가 확인된 뒤: 첫 구매 기록, 재구매 링크로 산 횟수 기록(링크는 계속 쓸 수 있다).
export async function afterPaid(store, order, now = new Date()) {
  const hash = emailHash(order.email);
  if (!(await store.get(`buyers/${hash}`))) await store.set(`buyers/${hash}`, { firstPaidAt: now.toISOString() });
  const d = order.discount;
  if (d?.code) {
    const c = await store.get(`coupons/${d.code}`);
    if (c) await store.set(`coupons/${d.code}`, { ...c, uses: (c.uses || 0) + 1, lastUsedAt: now.toISOString() });
  }
  // 들어온 곳별 결제 수(달마다, 한국 시간). 스튜디오 '손님이 온 곳'에 보인다. 묶음은 결제 한 번으로 센다.
  const month = new Date(now.getTime() + 9 * 3600_000).toISOString().slice(0, 7);
  const key = `stats/sources/${month}`, src = order.source || 'direct';
  const stats = (await store.get(key)) || {};
  const row = stats[src] || { orders: 0, amount: 0 };
  stats[src] = { orders: row.orders + 1, amount: row.amount + (order.amount || 0) };
  await store.set(key, stats);
}

export async function issueCoupon(store, kind, now = new Date()) {
  const code = newCode();
  const coupon = { code, kind, percent: PERCENT, createdAt: now.toISOString() };
  await store.set(`coupons/${code}`, coupon);
  return coupon;
}

// 리포트 끝에 넣는 재구매 할인 링크. 주문마다 하나 만든다. 할인 코드 칸이 없어서 이 링크로 들어와야만 할인된다.
export async function rebuyFor(store, order, site, now = new Date()) {
  let c = order.rebuyCode ? await store.get(`coupons/${order.rebuyCode}`) : null;
  if (!c) {
    c = await issueCoupon(store, 'rebuy', now);
    order.rebuyCode = c.code;
    await store.set(`orders/${order.id}`, order);
  }
  return { code: c.code, url: `${String(site || 'https://unmyeong-saju.com').replace(/\/$/, '')}/?coupon=${c.code}` };
}

// 묶음으로 함께 만든 책은 본 주문의 코드를 같이 쓴다(한 번 결제에 코드 하나).
export async function rebuyForJob(store, order, site, now = new Date()) {
  const main = order.parentId ? await store.get(`orders/${order.parentId}`) : order;
  return main ? rebuyFor(store, main, site, now) : null;
}
