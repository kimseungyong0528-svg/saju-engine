// 가격 표시: 정가(55,000원 등)와 상품 할인율은 보이지 않는다(사장님 2026-11-06: 그 값에 판 적이 없다. 11-05 "빼지 마"를 바꿈).
// 법무 PR143 조건 중 묶음 안내·지어낸 후기 삭제는 그대로 지킨다.
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const html = readFileSync(new URL('../public/index.html', import.meta.url), 'utf8');

test('묶음 10% 목록 위에는 늘 "처음 구매하실 때" 조건 안내가 있다 (법무 PR143 조건 ①)', () => {
  const at = html.indexOf('function bundleBlock'), block = html.slice(at, html.indexOf('\n}\n', at));
  assert.ok(block.includes('처음 구매하실 때'), '조건 안내가 bundleBlock에 있어야 함');
});

test('지어낸 후기·거짓 체험 할인 코드가 없다 (법무 PR143 조건 ②)', () => {
  for (const bad of ['DEMO_REVIEWS', 'reviewRail', 'function offer(', 'UNMYEONG5000', '★★★★★']) assert.ok(!html.includes(bad), bad);
});

test('맨 위 가격은 서버가 확인한 첫 구매 묶음 할인일 때만 깎인 값을 보인다 (P-VC-1)', () => {
  const fn = html.slice(html.indexOf('function coMainPrice'), html.indexOf('function coMainPrice') + 600);
  assert.ok(fn.includes("q?.discount?.kind==='bundle'"), '서버 견적의 묶음 할인 확인이 있어야 함');
  assert.ok(!/const on=\(d\.extras\|\|\[\]\)\.length>0&&!d\.coupon/.test(fn), '이메일 확인 전 조건 없이 깎던 옛 조건이 남아 있으면 안 됨');
});

test('판 적 없는 정가·상품 할인율을 보이지 않는다 (사장님 2026-11-06)', () => {
  for (const fn of ['function priceLabel', 'function priceBox', 'function quoteBox']) {
    const body = html.slice(html.indexOf(fn), html.indexOf(fn) + 2500);
    assert.ok(!body.includes('p.original') && !body.includes('>정가<') && !body.includes('상품 할인'), fn);
  }
  assert.ok(!html.includes('<s>${money(p.original)}</s>'), '결제 화면 맨 위 정가');
});
