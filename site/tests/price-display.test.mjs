// 가격 표시: 정가·할인율 표시는 대표님 결정(11-05 "정가 할인율은 빼지 마")으로 그대로 둔다.
// 법무 PR143 조건 중 묶음 안내·지어낸 후기 삭제는 그대로 지킨다.
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const html = readFileSync(new URL('../public/index.html', import.meta.url), 'utf8');

test('묶음 10% 목록 위에는 늘 "처음 구매하실 때" 조건 안내가 있다 (법무 PR143 조건 ①)', () => {
  const block = html.slice(html.indexOf('function bundleBlock'), html.indexOf('function bundleBlock') + 4000);
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
