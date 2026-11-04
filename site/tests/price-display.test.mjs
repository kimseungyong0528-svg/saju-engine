// 가격 표시(P-12·P-16·P-VC-1, 11-05 법무 판정): 판 적 없는 '정가'·상품 할인율을 손님 화면에 보이지 않는다.
// 결제 화면 맨 위 가격은 서버가 묶음 할인을 확인하기 전까지 판매가 그대로다.
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const html = readFileSync(new URL('../public/index.html', import.meta.url), 'utf8');

test('가격표·결제 상자에 정가 취소선과 상품 할인율이 없다', () => {
  for (const bad of ['money(p.original)', 'money(x.original)', 'discountPercent(p)}%', '>정가<', '상품 할인 <em', 'data-co-pct']) {
    assert.ok(!html.includes(bad), bad);
  }
});

test('맨 위 상품 가격은 서버가 할인을 확인했을 때만 바뀐다', () => {
  const fn = html.slice(html.indexOf('function coMainPrice'), html.indexOf('function bindDiscounts'));
  assert.match(fn, /q\?\.discount/);
  assert.doesNotMatch(fn, /original/);
});
