// 결제 전 이야기 화면 (2026-10-28 사장님: 상품을 누르고 결제까지 가는 길을 이야기로, 내 사주를 맛보기로 열어 결제로 잇는다).
// 정보 입력이 끝나면 금월선녀가 다섯 장면으로 내 사주를 보여 준다:
//   1 내 사주 펼치기 → 2 "이거 맞죠?" → 3 내 점수 → 4 앞으로 12년(신년운세는 2027년 열두 달) 지도 → 5 리포트 1장 미리 보기 → 리포트 안내 → 결제.
// 여는 것: 성격, 타고난 구조, 점수, 기회의 해·조심할 해(연도까지). 가리는 것: 몇 월인지, 무엇을·어떻게 하는지.
// 계산은 무료 맛보기와 같은 계산기(assets/free)가 브라우저에서 한다(AI 호출 없음). 결제 리포트도 같은 계산(saju/reveal.py)을 받아 이어 쓴다.
// build_site.py 가 사이트 코드 안에 그대로 넣는다.
const REVEAL_STEP={id:'reveal',type:'reveal'};
// 상품마다 '…리포트 살펴보기' 장면 자리에 이 화면을 넣는다(없으면 리포트 안내 바로 앞).
for(const [id,f] of Object.entries(FLOWS)){
 if(id==='compatibility')continue;
 const si=f.findIndex(s=>s.type==='sales');if(si<0)continue;
 if(f[si-1]?.id==='ready')f.splice(si-1,1,REVEAL_STEP);else f.splice(si,0,REVEAL_STEP);
}
let revealLib=null,revealState={key:'',scene:0,confirm:{},view:null};
async function revealLoad(){const lib=await tasterLoad();if(!revealLib)revealLib=await import('./assets/free/reveal.mjs');return {...lib,rv:revealLib}}
const REVEAL_SCENES=5;
function revealStartYear(){return Math.max(2027,new Date(Date.now()+9*3600e3).getUTCFullYear())}
// 재회사주 24개월 지도의 첫 달(한국 날짜로 15일까지면 이번 달, 16일부터 다음 달). saju/reveal.py start_month 와 같다.
function revealStartMonth(rv){const t=new Date(Date.now()+9*3600e3);return rv.startMonth(t.getUTCFullYear(),t.getUTCMonth()+1,t.getUTCDate())}
// 재회사주: 손님이 화면에서 본 첫 달을 주문에 함께 보내, 리포트가 정확히 같은 24개월을 쓰게 한다(제1조항, 사장님 2026-10-30).
function revealShownStart(p,d,rv){const sm=revealStartMonth(rv);if(p.id==='reunion'){d.answers=d.answers||{};d.answers.revealStart=`${sm[0]}-${String(sm[1]).padStart(2,'0')}`;try{save()}catch{}}return sm}
// 이야기 화면이 보여 준 사주의 열쇠: 내 정보(두 사람 상품은 상대방 정보까지)가 바뀌면 이야기를 처음부터 다시 보여 준다(제1조항).
function revealKey(p,d){return p.id+'|'+JSON.stringify(d.self)+(['intimate','reunion'].includes(p.id)?'|'+JSON.stringify(d.partner||{}):'')}
function revealCompute(p,d,lib){
 const {eng,tst,data,texts,rv}=lib,v=d.self,date=validateBirthDate(v);
 const fp=eng.chartFromPerson(data,v,v.calendar==='lunar'?date.solarDate:v.birth);
 const r=tst.reading(fp,v,texts),R=texts.REVEAL;
 const area=p.id==='lifetime'?null:tst.areaView(fp,v,texts,p.id),parts=p.id==='lifetime'?null:tst.areaParts(fp,v,texts,p.id);
 return {name:r.name,r,R,area,parts,map:rv.luckMap(fp,v.sex,p.id,texts,revealStartYear(),revealShownStart(p,d,rv)),fill:tst.fill,A:texts.AREAS,pair:revealPair(p,d,lib,fp),boundary:rv.boundaryLines(data,v,v.calendar==='lunar'?date.solarDate:v.birth),note:id=>tst.situationNote(id,d.answers,texts)};
}
// 깊은 궁합·재회사주: 그 사람 사주와 함께 본 '두 사람 궁합 점수'(saju/pair.py pair_score 와 같은 계산, 리포트에 같은 점수가 나온다).
function revealPair(p,d,lib,fp){
 if(!['intimate','reunion'].includes(p.id)||!d.partner||!personValid(d.partner))return null;
 const {eng,data,rv}=lib,o=d.partner,od=validateBirthDate(o);
 return {...rv.pairScore(fp,eng.chartFromPerson(data,o,o.calendar==='lunar'?od.solarDate:o.birth)),name:(o.name||'').trim()||'그 사람'};
}
function revealSpeech(p,text){return `<div class="rv-guide"><img src="${esc(MEDIA[p.id+'.cover'].image)}" alt="금월선녀" decoding="async"><div><strong>금월선녀</strong><p>${esc(text)}</p></div></div>`}
function revealLocks(items){return `<div class="rv-locks">${items.map(t=>`<div>${icon('lock')}<span>${esc(t)}</span><i>리포트에서 공개</i></div>`).join('')}</div>`}
// 1. 내 사주 펼치기: 사주팔자 네 기둥, 나를 뜻하는 글자, 타고난 큰 방향, 다섯 기운
// 타고난 큰 방향(격국) 설명은 돈·일과 이어지는 말이라, 돈·일·평생을 보는 상품에서만 보여 준다(손님 테스트: 건강운인데 '월급처럼 들어오는 돈').
function rvScene0(p,v){const c=v.r.chart,me=c.items[0],gy=['lifetime','wealth','career','business'].includes(p.id)?c.items[4]:null;
 return `${revealSpeech(p,`${v.name} 님이 태어난 순간의 여덟 글자를 펼쳤어요. 성격도, 돈도, 사람도 이 여덟 글자에서 읽고, 해마다 바깥에서 들어오는 운이 이 여덟 글자와 어떻게 만나는지도 함께 볼게요.`)}
 <span class="eyebrow">STEP 1 · ${typeof isGift==='function'&&isGift(p.id)?esc(v.name)+' 님':'내'} 사주 펼치기</span><h1>${esc(v.name)} 님의 사주팔자</h1>
 <div class="taster-chart">${c.columns.map(x=>`<div class="tc-col${x.me?' me':''}"><small>${x.label}</small><b>${x.hanja?esc(x.hanja[0]):'?'}</b><b>${x.hanja?esc(x.hanja[1]):'?'}</b><span>${x.ko?esc(x.ko):'모름'}</span>${x.me?'<em>나</em>':''}</div>`).join('')}</div>
 ${v.boundary.length?`<div class="rv-card rv-boundary">${v.boundary.map(l=>`<p>${esc(l)}</p>`).join('')}</div>`:''}
 <div class="rv-card"><strong>${esc(me.head)}</strong><p>${esc(me.text)}</p></div>
 ${gy?`<div class="rv-card"><strong>${esc(gy.head)}</strong><p>${esc(gy.text)}</p></div>`:''}
 <div class="rv-card"><strong>다섯 기운의 비율</strong><div class="tb-bars">${c.elements.map(e=>`<div class="tb-bar ${e.status}"><span>${esc(e.word)}</span><i><b style="width:${Math.min(100,e.pct*2)}%"></b></i><em>${e.pct}%</em></div>`).join('')}</div></div>`}
// 2. "이거 맞죠?": 가장 센 기운, 가장 모자란 기운, 나를 받쳐 주는 힘으로 본 모습 세 가지
function rvConfirmItems(v){const c=v.r.chart;return [c.items[1],c.items[2],{head:c.items[3].head,text:c.items[3].text.replace(/^.*?점수입니다\.\s*/,'')}]}
function rvScene1(p,v){const items=rvConfirmItems(v),ans=revealState.confirm,done=items.every((_,n)=>ans[n]),yes=items.filter((_,n)=>ans[n]==='yes').length;
 return `${revealSpeech(p,`제가 사주로 본 ${v.name} 님은 이런 사람이에요. 맞는지 하나씩 눌러 주세요.`)}
 <span class="eyebrow">STEP 2 · 이거 맞죠?</span><h1>${esc(v.name)} 님,<br>이거 맞죠?</h1>
 ${items.map((it,n)=>`<div class="rv-card rv-confirm"><small>${esc(it.head)}</small><p>${esc(it.text)}</p><div class="rv-yesno" role="group"><button type="button" data-confirm="${n}" data-v="yes" class="${ans[n]==='yes'?'on':''}">맞아요</button><button type="button" data-confirm="${n}" data-v="no" class="${ans[n]==='no'?'on':''}">아니에요</button></div>${ans[n]==='no'?`<p class="rv-no">그렇게 느끼실 수 있어요. 사주는 타고난 바탕이라, 자라온 환경과 지금까지의 노력에 따라 다르게 드러나기도 해요. 리포트에서 이 부분이 ${esc(v.name)} 님에게 어떻게 드러나는지 더 자세히 풀어 드릴게요.</p>`:''}</div>`).join('')}
 <p class="rv-skip-note">눌러 보지 않아도 아래 버튼으로 다음 이야기로 넘어갈 수 있어요.</p>
 ${done?`<p class="rv-result">${esc(v.fill(yes>=2?v.R.CONFIRM_MANY:v.R.CONFIRM_FEW,{name:v.name,n:String(yes)}))}</p>`:''}`}
// 3. 내 점수: 이 상품의 운 점수와 근거(맛보기와 같은 글) + 다른 운 점수까지 모두 공개
// 막대 색과 이름은 아래 카드·무료 풀이와 같게: 무료 풀이 '좋은 운 TOP3'는 초록, '조심할 운 TOP3'는 빨강, 나머지는 보통(제1조항).
function rvBars(v,skip){const side=id=>v.r.good.some(a=>a.id===id)?'good':v.r.bad.some(a=>a.id===id)?'bad':'mid';return `<div class="rv-bars">${Object.entries(v.r.scores).filter(([id])=>id!==skip).sort((a,b)=>b[1]-a[1]).map(([id,s])=>{const k=side(id);return `<div class="rv-bar ${k}"><span>${esc(v.A[id]?.title||v.R.AREA_WORD[id])}</span><i><b style="width:${s}%"></b></i><em>${s}점</em></div>`}).join('')}</div>`}
function rvScene2(p,v){const s=SALES[p.id];
 if(!v.area){const all=[...v.r.good.map(a=>[a,1]),...v.r.bad.map(a=>[a,-1])];
  return `${revealSpeech(p,`${v.name} 님 사주로 여덟 가지 운의 점수를 모두 계산했어요. 높은 운은 크게 받고, 낮은 운은 미리 대비하면 돼요.`)}
  <span class="eyebrow">STEP 3 · ${typeof isGift==='function'&&isGift(p.id)?esc(v.name)+' 님':'내'} 점수</span><h1>${esc(v.name)} 님의<br>여덟 가지 운 점수</h1>${rvBars(v)}
  ${all.map(([a,sg])=>`<div class="rv-card ${sg>0?'good':'bad'}"><small>${sg>0?'가장 좋은 운':'가장 조심할 운'} · ${esc(a.title)} ${a.score}점</small><p>${esc(a.text)}${v.note(a.id)?' '+esc(v.note(a.id)):''}</p><p class="rv-hook">${esc(v.fill(sg>0?v.R.SCORE_GOOD:v.R.SCORE_BAD,{name:v.name,area:v.R.AREA_WORD[a.id]}))}</p></div>`).slice(0,4).join('')}
  ${revealLocks(s?.locks||[])}`}
 const pt=v.parts,word=v.R.AREA_WORD[p.id];
 const M=v.R.MARKS,month=v.map.unit==='month',when=ls=>ls.map(l=>month?l:l+'년').join(' · '),vals={name:v.name,weak:v.map.weak};
 // 좋은 점·조심할 점 모두 같은 크기의 큰 점수로 보여 준다(사장님 2026-10-28).
 const big=(kind,sc,sub)=>`<div class="rv-score ${kind}"><small class="rv-score-label">${esc(word)}의 ${kind==='good'?'좋은 점':'조심할 점'}</small><strong>${sc}<small>점</small></strong>${sub?`<span>${esc(sub)}</span>`:''}<i><b style="width:${sc}%"></b></i></div>`;
 // 근거가 한쪽에만 있으면 다른 쪽은 지도에서 그 쪽 해(달)를 꺼내 짚는다.
 // 점수: 앞으로 12년(12달) 가운데 그런 해(달)가 몇 번인지로 매긴다(saju/reveal.py side_score 와 같은 식).
 const N=v.map.cells.length,spanW=N===24?'24개월':month?'열두 달':'12년';
 const sideScore=(d,kind)=>{const n=new Set(Object.values(d).flat()).size;return kind==='good'?Math.min(95,50+Math.round(50*n/N)):Math.max(5,50-Math.round(50*n/N))};
 const yearsPart=(d,kind)=>{const n=new Set(Object.values(d).flat()).size,sc=sideScore(d,kind);
  // 'N번'이라고 했으면 N개를 모두 적는다(표시마다 한 줄). 뜻 풀이는 첫 표시 하나만.
  const ents=Object.entries(d);if(!ents.length)return '';const [k0]=ents[0];
  return big(kind,sc,`앞으로 ${spanW} 중 ${kind==='good'?'운이 들어오는':'조심할'} ${month?'달':'해'} ${n}번`)+`<div class="rv-card ${kind}">${ents.map(([key,ls])=>`<p>${esc(when(ls))}은 ${esc(v.fill(M[key].line,vals))}입니다.</p>`).join('')}<p>${esc(v.fill(M[k0].meaning,vals))}</p><p class="rv-hook">${esc(M[k0].hook)}</p></div>`};
 const reasonPart=(x,kind)=>big(kind,x.score,kind==='good'?(x.score>=60?'좋은 운':'좋은 편인 운'):'조심할 운')+`<div class="rv-card ${kind}"><p>${esc(x.text)}</p><p class="rv-hook">${esc(v.fill(kind==='good'?v.R.SCORE_GOOD:v.R.SCORE_BAD,{name:v.name,area:word}))}</p></div>`;
 const goodPart=pt.good?reasonPart(pt.good,'good'):yearsPart(v.map.good,'good');
 const badPart=pt.bad?reasonPart(pt.bad,'bad'):yearsPart(v.map.bad,'bad');
 // 점수가 높은 쪽이 위, 낮은 쪽이 아래(사장님 2026-10-28). 같으면 전체 점수로 정한다.
 const gs=pt.good?pt.good.score:sideScore(v.map.good,'good'),bs=pt.bad?pt.bad.score:sideScore(v.map.bad,'bad');
 const good=gs!==bs?gs>bs:pt.score>=50;
 // 제목·말풍선은 무료 풀이에서 이 운을 좋은 운/조심할 운 어느 쪽으로 보여 줬는지(areaView sign)를 따른다(제1조항: 모순 금지).
 const tone=v.area.sign>0,unitW=month?'달':'해';
 const speech=tone?(pt.good?`${word}부터 볼게요. 점수가 좋은 편이에요. 때를 알고 움직이면 더 크게 받을 수 있어요.`:`${word}부터 볼게요. 좋은 운이 들어오는 ${unitW}가 정해져 있어요. 그때를 알면 놓치지 않고 받을 수 있어요.`)
  :(good?`${word}부터 볼게요. 좋은 점과 조심할 점이 함께 있어요.`:`${word}부터 볼게요. 조심할 점이 있는 운이에요. 언제 조심하면 되는지 알면 충분히 넘길 수 있어요.`);
 const pairCard=v.pair?(()=>{const q=v.pair,ew=e=>({목:'나무',화:'불',토:'흙',금:'쇠',수:'물'})[e]+'('+e+')';
  const palace={조화:'두 사람의 배우자 자리(태어난 날의 지지)가 서로 손을 잡는 사이입니다. 함께 있을수록 마음이 편해집니다.',긴장:'두 사람의 배우자 자리(태어난 날의 지지)가 서로 부딪히는 사이입니다. 가까워질수록 작은 일로 다투기 쉬워, 다투는 때와 푸는 법을 알아 두면 좋습니다.',복합:'두 사람의 배우자 자리(태어난 날의 지지)에 손잡는 면과 부딪히는 면이 함께 있습니다.',중립:'두 사람의 배우자 자리(태어난 날의 지지)는 크게 끌리지도 부딪히지도 않는 담담한 사이입니다.'}[q.palace];
  const fill=[...q.fill.map(e=>`${q.name} 님은 ${v.name} 님에게 모자란 ${ew(e)} 기운을 채워 줍니다.`),...q.give.map(e=>`${v.name} 님은 ${q.name} 님에게 모자란 ${ew(e)} 기운을 채워 줍니다.`)].join(' ');
  return big(q.score>=60?'good':'bad',q.score,`${v.name} 님과 ${q.name} 님 사주를 함께 본 점수`).replace(`${esc(word)}의 ${q.score>=60?'좋은 점':'조심할 점'}`,'두 사람 궁합 점수')+`<div class="rv-card ${q.score>=60?'good':'bad'}"><p>${esc(palace)}${fill?' '+esc(fill):''}</p><p class="rv-hook">두 사람이 언제 가까워지고 언제 부딪히는지는 리포트에 달 이름까지 담았습니다.</p></div>`})():'';
 const head=tone?(pt.good?'좋은 운을 타고났습니다':`들어오는 ${unitW}가 있습니다`):'미리 알면 대비할 수 있습니다';
 return `${revealSpeech(p,speech)}
 <span class="eyebrow">STEP 3 · ${typeof isGift==='function'&&isGift(p.id)?esc(v.name)+' 님':'내'} 점수</span><h1>${esc(v.name)} 님의 ${esc(word)},<br>${head}</h1>
 <p class="rv-score-help">점수는 100점에 가까울수록 좋아요. 좋은 점 점수는 높을수록 크게 받는 운이고, 조심할 점 점수는 낮을수록 더 챙겨야 하는 부분이에요.${pt.score!=null?` 무료 풀이에서 본 ${esc(word)} 점수 ${pt.score}점은 좋은 근거와 조심할 근거를 모두 합해 매긴 점수이고, 여기서는 둘을 나눠 따로 매겼어요.`:''}</p>
 ${pairCard}
 ${good?`${goodPart}<p class="rv-bridge bad">다만, 조심할 점도 함께 있습니다.</p>${badPart}`:`${badPart}<p class="rv-bridge good">그리고, 좋은 점도 분명히 있습니다.</p>${goodPart}`}
 ${revealLocks(s?.locks||[])}`}
// 4. 지도: 기회의 해·조심할 해는 연도까지 공개, 몇 월인지와 무엇을 해야 하는지는 잠금
function rvScene3(p,v){const m=v.map,M=v.R.MARKS,month=m.unit==='month',unit=month?'달':'해',re=p.id==='reunion';
 const vals={name:v.name,weak:m.weak};
 const when=labels=>labels.map(l=>month?l:l+'년').join(' · ');
 const card=(key,labels,kind)=>`<div class="rv-card rv-mark ${kind}"><div class="rv-mark-head"><span class="rv-tag ${kind}">${esc(M[key].tag)}</span><b>${esc(when(labels))}</b></div><p class="rv-mark-line">${esc(v.fill(M[key].line,vals))}</p><p>${esc(v.fill(M[key].meaning,vals))}</p><p class="rv-hook">${esc(M[key].hook)}</p></div>`;
 const goods=Object.entries(m.good),bads=Object.entries(m.bad);
 const first=goods.length===1?M[goods[0][0]].tag:'';
 return `${revealSpeech(p,`이제 가장 중요한 이야기예요. ${v.name} 님에게 운이 들어오는 ${month?'달과':'해와'} 조심해야 할 ${month?'달은':'해는'} 사주에 이미 정해져 있어요.`)}
 <span class="eyebrow">STEP 4 · ${re?'앞으로 24개월':month?'2027년 열두 달':'앞으로 12년'}</span><h1>${re?`${esc(v.name)} 님의 앞으로 24개월,<br>다시 이어지기 좋은 달`:month?`${esc(v.name)} 님의<br>2027년 열두 달`:first?`${esc(v.name)} 님의 앞으로 12년,<br>'${esc(first)}' 표시가 붙은 해`:`앞으로 12년,<br>기회의 해와 조심할 해`}</h1>
 <div class="rv-grid">${m.cells.map(c=>{const ym=re&&c.label.match(/^(\d{4})년 (\d+)월$/);return `<div class="rv-cell${c.good.length?' good':''}${c.bad.length?' bad':''}"><b>${esc(ym?ym[2]+'월':c.label)}</b><small>${esc(ym?ym[1]+' '+c.ko:c.ko)}</small>${[...c.good.map(x=>`<span class="g">${esc(M[x].tag)}</span>`),...c.bad.map(x=>`<span class="r">${esc(M[x].tag)}</span>`)].join('')}</div>`}).join('')}</div>
 <div class="rv-legend"><span class="g">${re?'좋은 달':month?'돕는 달':'좋은 해'}</span><span class="r">조심할 ${unit}</span>${month?'<span>달은 절기 기준(매달 4~8일 무렵 시작)</span>':''}</div>
 ${goods.map(([k,l])=>card(k,l,'good')).join('')}${bads.map(([k,l])=>card(k,l,'bad')).join('')}
 ${revealLocks(re?['가장 좋은 달의 며칠 무렵, 어떤 상황에 연락하면 좋은지','문자·전화·SNS 가운데 나에게 맞는 연락 수단과 첫마디','엇갈리는 달에 피할 말과 다시 연락해도 되는 달']:month?['좋은 달에 시작해야 할 일과 그 방법','조심할 달에 미뤄야 할 일과 막는 방법','열두 달 각각의 돈·일·사람·건강 흐름']:['이 해의 몇 월에 들어오는지','그 해에 해야 할 일과 하지 말아야 할 일','조심할 해를 막는 구체적인 방법'])}`}
// 5. 리포트 1장 미리 보기: 실제 리포트 목차. 1장은 지금까지 본 내 사주로 열고, 2장부터는 제목만 보이고 내용은 가린다.
function rvScene4(p,v){const toc=EXTRA_DATA.toc[p.id]||[],c=v.r.chart,rest=Math.max(0,toc.length-1);
 return `${revealSpeech(p,`여기까지가 제가 미리 보여 드릴 수 있는 내용이에요. 몇 월에, 무엇을, 어떻게 해야 하는지는 ${v.name} 님 리포트에 모두 적어 드릴게요.`)}
 <span class="eyebrow">STEP 5 · 리포트 미리 보기</span><h1>${esc(v.name)} 님만의<br>한 권이 준비됐어요</h1>
 <div class="tp-page rv-page"><div class="tp-frame"><div class="tp-head">${esc(EXTRA_DATA.header?.[p.id]||'')}</div>
 ${toc[0]?`<div class="rv-ch open"><span class="tp-no">${esc(String(toc[0][0]))}</span><div><b>${esc(toc[0][1])}</b><p>${esc(c.items[0].text)}</p>${c.items[4]?`<p>${esc(c.items[4].text)}</p>`:''}<p>${esc(c.items[3].text.replace(/^.*?점수입니다\.\s*/,''))}</p></div></div>`:''}
 ${toc.slice(1).map(t=>`<div class="rv-ch"><span class="tp-no">${esc(String(t[0]))}</span><div><b>${esc(t[1])}</b><p class="rv-blur" aria-hidden="true">${esc(t[2]||`${v.name} 님 사주로 풀어 드리는 이 장의 내용`)}</p></div>${icon('lock')}</div>`).join('')}
 </div></div>
 <p class="rv-close">목차 2번부터 ${toc.length}번까지 ${esc(v.name)} 님의 ${v.map.unit==='month'?'달마다':'해마다'} 할 일과 방법이 들어 있습니다.<br>결제하면 PDF로 써서 이메일로 보내드려요.</p>
 <div class="rv-price"><span>${typeof isGift==='function'&&isGift(p.id)?esc(v.name)+' 님의':'나의'} ${esc(p.short)} 전체 풀이</span><s>${money(p.original)}</s><em>${discountPercent(p)}%</em><strong>${money(p.price)}</strong></div>
 ${typeof savedCoupon==='function'&&savedCoupon()?'<p class="rv-price-note">재구매 할인 10%는 결제 화면에서 더 깎여요.</p>':''}`}
const RV_CTA=['계속 듣기','다음 이야기 듣기','내 운이 들어오는 해 보기','리포트 미리 보기',''];
window.addEventListener('popstate',e=>{if(!document.querySelector('.reveal-flow')||!revealState.view)return;const n=e.state&&typeof e.state.rvScene==='number'?e.state.rvScene:0;if(n!==revealState.scene){revealState.scene=n;revealRepaint&&revealRepaint();window.scrollTo({top:0,behavior:'instant'})}});
let revealRepaint=null;
function revealPage(p,i){
 const d=draft(p.id);
 if(!personValid(d.self)){go(pathFor(p,FLOWS[p.id].findIndex(s=>s.type==='info')));return}
 const key=revealKey(p,d);
 // 새로고침해도 보던 장면에서 이어 본다(장면마다 남긴 브라우저 기록을 다시 읽는다, 손님 테스트 2차)
 if(revealState.key!==key){const h=history.state&&typeof history.state.rvScene==='number'?history.state.rvScene:0;revealState={key,scene:Math.min(Math.max(h,0),REVEAL_SCENES-1),confirm:{},view:null}}
 const paint=()=>{
  const v=revealState.view,n=revealState.scene,rest=Math.max(0,(EXTRA_DATA.toc[p.id]||[]).length-1);
  const body=[rvScene0,rvScene1,rvScene2,rvScene3,rvScene4][n](p,v);
  const cta=n===REVEAL_SCENES-1?`전체 풀이 받기 · ${money(p.price)}`:n===2&&p.id==='newyear'?'내 운이 들어오는 달 보기':RV_CTA[n];
  app.innerHTML=`<div class="shell flow reveal-flow" style="--accent:${p.color}">${progress(p,i)}<div class="rv-dots" aria-label="${n+1} / ${REVEAL_SCENES}">${Array.from({length:REVEAL_SCENES},(_,k)=>`<i class="${k<=n?'on':''}"></i>`).join('')}</div><main id="main"><div class="flow-content rv-body"><button type="button" class="rv-edit" data-rv-edit>입력한 정보 고치기</button>${n===0&&typeof savedCoupon==='function'&&savedCoupon()?'<button type="button" class="rv-edit" data-rv-skip>이야기 건너뛰기</button>':''}${body}</div></main>${bottom(p,i,cta)}</div>`;
  document.activeElement?.blur?.();
  const next=document.querySelector('[data-next]'),back=document.querySelector('.back-square');
  // 장면마다 브라우저 기록을 하나씩 남겨, 휴대폰 '뒤로'를 누르면 한 장면씩 돌아간다(질문 화면까지 한꺼번에 가지 않게).
  next.onclick=()=>{if(n<REVEAL_SCENES-1){revealState.scene++;try{history.pushState({rvScene:revealState.scene},'')}catch{}paint();window.scrollTo({top:0,behavior:'instant'})}else advance(p,i)};
  back.onclick=e=>{if(n>0){e.preventDefault();if(history.state&&history.state.rvScene===n)history.back();else{revealState.scene--;paint();window.scrollTo({top:0,behavior:'instant'})}}};
  const skip=document.querySelector('[data-rv-skip]');if(skip)skip.onclick=()=>advance(p,i);
  const edit=document.querySelector('[data-rv-edit]');if(edit)edit.onclick=()=>go(pathFor(p,FLOWS[p.id].findIndex(s=>s.type==='info')));
  document.querySelectorAll('[data-confirm]').forEach(b=>b.onclick=()=>{revealState.confirm[b.dataset.confirm]=b.dataset.v;const y=window.scrollY;paint();window.scrollTo({top:y,behavior:'instant'})});
 };
 revealRepaint=paint;
 if(revealState.view)return paint();
 app.innerHTML=`<div class="shell flow reveal-flow" style="--accent:${p.color}">${progress(p,i)}<main id="main"><div class="flow-content rv-body rv-loading">${revealSpeech(p,`${d.self.name} 님의 사주를 펼치고 있어요.`)}</div></main></div>`;
 revealLoad().then(lib=>{if(revealState.key!==key)return;revealState.view=revealCompute(p,d,lib);paint()})
  .catch(err=>{console.error(err);toast('사주를 계산하지 못했어요. 리포트 안내로 넘어갈게요.');advance(p,i)});
}
