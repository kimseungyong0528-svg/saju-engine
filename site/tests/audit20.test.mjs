// 자청 수제자 20명 점검 반영(사장님 2026-11-06 저녁): 고친 것이 되돌아가지 않게 지킨다.
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { situText } from '../public/assets/free/taster.mjs';

const html = readFileSync(new URL('../public/index.html', import.meta.url), 'utf8');
const T = JSON.parse(readFileSync(new URL('../public/assets/free/texts.json', import.meta.url), 'utf8'));
const toc = JSON.parse(readFileSync(new URL('../public/assets/free/toc-pages.json', import.meta.url), 'utf8'));

test('과장·보장 문구가 없다(1-3)', () => {
  const all = JSON.stringify(T);
  for (const bad of ['몇 배', '비교할 수 없이', '윗자리에 오르는 사주입니다', '인정은 받지 못하고', '타고난 몸이 큰 재산', '돈을 타고난 사주입니다', '먼저 연락합니다.']) assert.ok(!all.includes(bad), bad);
});

test('손님 상황에 따라 문장을 바꾼다(1-2): 결혼한 분, 사업하는 분, 건강운', () => {
  const ans = s => ({ status: s });
  const t1 = '나와 맞는 사람을 고르는 눈이 꼭 필요합니다.';
  assert.ok(situText('REASONS.im_palace_rough', t1, ans('결혼한 사이예요'), T, 'intimate').includes('이미 함께하는 사이라면'));
  assert.equal(situText('REASONS.im_palace_rough', t1, ans('연애 중이에요'), T, 'intimate'), t1);
  const money = T.REVEAL.MARKS.money.meaning;
  assert.ok(situText('MARKS.money.meaning', money, { occupation: '사업을 운영하고 있어요' }, T, 'wealth').includes('매출과 거래'));
  assert.ok(situText('MARKS.ny_bad.meaning', T.REVEAL.MARKS.ny_bad.meaning, {}, T, 'health').includes('몸에 티가'));
  assert.ok(!situText('MARKS.spouse_f.meaning', T.REVEAL.MARKS.spouse_f.meaning, { relationship: '결혼했어요' }, T, 'lifetime').includes('진지하게 오래 만날 사람'));
});

test('무료로 여는 좋은 칸은 상품 주제 표시가 붙은 가장 가까운 칸(1-1)', () => {
  assert.ok(html.includes('function rvFirstGood(m)') && /function rvOpen\(m\)\{[^}]*g=rvFirstGood\(m\)/.test(html));
  assert.ok(html.includes('m&&rvFirstGood(m)'), '남은 날 상자도 같은 칸');
});

test('결제 버튼은 점수 대신 잠긴 때의 개수, 점수 설명은 둘로 나눈다(1-4)', () => {
  assert.ok(!html.includes('점의 이유와 ${w} 보기'));
  assert.ok(html.includes('${w} ${n}번, 언제인지 전부 보기'));
  assert.ok(!html.includes('전체 점수 ${pt.score}점은 이 운의 사주 근거를'));
});

test('무료 사주 시간 모름은 여섯 글자, 이어보기는 방금 정보로(1-5, 1-6)', () => {
  assert.ok(html.includes('태어난 해·달·날을 여섯 글자로 바꿨어요'));
  assert.ok(html.includes('방금 넣은 생일 그대로, 확인만 하고 바로'));
  assert.ok(html.includes('d.self={...tp}'));
});

test('선물: 메시지 글자 수, 실리는 쪽 예시, 받는 분 기준 문구(3단계)', () => {
  for (const s of ['data-gift-count', 'assets/gift-page-sample.jpg', "' 님께 선물하기'", '주문하는 분 이메일', '함께 고르는 리포트도 받는 분']) assert.ok(html.includes(s), s);
});

test('FAQ·신뢰: 무료 앱과 차이, 상호, 계산 근거 창(4단계)', () => {
  for (const s of ['무료 사주 앱과 뭐가 다른가요?', '상호: 김승용 (운명서재)', 'const TRUST_HTML=', '출생 정보는 리포트를 보낸 즉시 지워요.']) assert.ok(html.includes(s), s);
  assert.ok(!html.includes('어떤 자료로 어떻게 계산했는지 모두 공개합니다.'));
});

test('목차 설명은 실제 리포트 쪽 제목, 질문은 누르는 칸(5단계)', () => {
  assert.ok(html.includes('toc-pages.json') && html.includes('rvTocPages(p,t[0])'));
  for (const k of ['lifetime', 'romance', 'newyear', 'wealth', 'career', 'business', 'health', 'intimate', 'reunion', 'reunion-solo']) assert.ok(Object.keys(toc[k] || {}).length >= 10, k);
  assert.ok(html.includes('data-sv-chip') && html.includes("'결혼을 고민하는 중이에요'") && html.includes("'퇴사를 고민해요'"));
  assert.ok(!/choice\('(status|experience|duration|occupation|stage|priority|rhythm|focus)','[^']+',\[[^\]]*\],true\)/.test(html), '질문은 모두 답하지 않아도 넘어갈 수 있다');
});
