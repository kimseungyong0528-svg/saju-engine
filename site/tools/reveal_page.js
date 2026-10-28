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
function revealCompute(p,d,lib){
 const {eng,tst,data,texts,rv}=lib,v=d.self,date=validateBirthDate(v);
 const fp=eng.chartFromPerson(data,v,v.calendar==='lunar'?date.solarDate:v.birth);
 const r=tst.reading(fp,v,texts),R=texts.REVEAL;
 const area=p.id==='lifetime'?null:tst.areaView(fp,v,texts,p.id),parts=p.id==='lifetime'?null:tst.areaParts(fp,v,texts,p.id);
 return {name:r.name,r,R,area,parts,map:rv.luckMap(fp,v.sex,p.id,texts,revealStartYear()),fill:tst.fill,approx:v.timeAccuracy==='approximate'};
}
function revealSpeech(p,text){return `<div class="rv-guide"><img src="${esc(MEDIA[p.id+'.cover'].image)}" alt="금월선녀" decoding="async"><div><strong>금월선녀</strong><p>${esc(text)}</p></div></div>`}
function revealLocks(items){return `<div class="rv-locks">${items.map(t=>`<div>${icon('lock')}<span>${esc(t)}</span><i>리포트에서 공개</i></div>`).join('')}</div>`}
// 1. 내 사주 펼치기: 사주팔자 네 기둥, 나를 뜻하는 글자, 타고난 큰 방향, 다섯 기운
function rvScene0(p,v){const c=v.r.chart,me=c.items[0],gy=c.items[4];
 return `${revealSpeech(p,`${v.name} 님이 태어난 순간의 여덟 글자를 펼쳤어요. 성격도, 돈도, 사람도, 운이 들어오는 해도 모두 이 여덟 글자 안에 있어요.`)}
 <span class="eyebrow">STEP 1 · 내 사주 펼치기</span><h1>${esc(v.name)} 님의 사주팔자</h1>
 <div class="taster-chart">${c.columns.map(x=>`<div class="tc-col${x.me?' me':''}"><small>${x.label}</small><b>${x.hanja?esc(x.hanja[0]):'?'}</b><b>${x.hanja?esc(x.hanja[1]):'?'}</b><span>${x.ko?esc(x.ko):'모름'}</span>${x.me?'<em>나</em>':''}</div>`).join('')}</div>
 ${v.approx?`<p class="rv-approx">시간을 대략으로 넣으셔서 태어난 시(時)는 비워 두고 풀었어요. 리포트는 넣어 주신 시간 범위로 시(時)까지 정해서 풀기 때문에, 이 화면과 조금 다를 수 있어요.</p>`:''}
 <div class="rv-card"><strong>${esc(me.head)}</strong><p>${esc(me.text)}</p></div>
 ${gy?`<div class="rv-card"><strong>${esc(gy.head)}</strong><p>${esc(gy.text)}</p></div>`:''}
 <div class="rv-card"><strong>다섯 기운의 비율</strong><div class="tb-bars">${c.elements.map(e=>`<div class="tb-bar ${e.status}"><span>${esc(e.word)}</span><i><b style="width:${Math.min(100,e.pct*2)}%"></b></i><em>${e.pct}%</em></div>`).join('')}</div></div>`}
// 2. "이거 맞죠?": 가장 센 기운, 가장 모자란 기운, 나를 받쳐 주는 힘으로 본 모습 세 가지
function rvConfirmItems(v){const c=v.r.chart;return [c.items[1],c.items[2],{head:c.items[3].head,text:c.items[3].text.replace(/^.*?점수입니다\.\s*/,'')}]}
function rvScene1(p,v){const items=rvConfirmItems(v),ans=revealState.confirm,done=items.every((_,n)=>ans[n]),yes=items.filter((_,n)=>ans[n]==='yes').length;
 return `${revealSpeech(p,`제가 사주로 본 ${v.name} 님은 이런 사람이에요. 맞는지 하나씩 눌러 주세요.`)}
 <span class="eyebrow">STEP 2 · 이거 맞죠?</span><h1>${esc(v.name)} 님,<br>이거 맞죠?</h1>
 ${items.map((it,n)=>`<div class="rv-card rv-confirm"><small>${esc(it.head)}</small><p>${esc(it.text)}</p><div class="rv-yesno" role="group"><button type="button" data-confirm="${n}" data-v="yes" class="${ans[n]==='yes'?'on':''}">맞아요</button><button type="button" data-confirm="${n}" data-v="no" class="${ans[n]==='no'?'on':''}">아니에요</button></div></div>`).join('')}
 ${done?`<p class="rv-result">${esc(v.fill(yes>=2?v.R.CONFIRM_MANY:v.R.CONFIRM_FEW,{name:v.name,n:String(yes)}))}</p>`:''}`}
// 3. 내 점수: 이 상품의 운 점수와 근거(맛보기와 같은 글) + 다른 운 점수까지 모두 공개
function rvScore(score){return score>=60?['good','좋은 운']:score>=45?['mid','보통인 운']:['bad','조심할 운']}
function rvBars(v,skip){return `<div class="rv-bars">${Object.entries(v.r.scores).filter(([id])=>id!==skip).sort((a,b)=>b[1]-a[1]).map(([id,s])=>{const [k]=rvScore(s);return `<div class="rv-bar ${k}"><span>${esc(v.R.AREA_WORD[id])}</span><i><b style="width:${s}%"></b></i><em>${s}점</em></div>`}).join('')}</div>`}
function rvScene2(p,v){const s=SALES[p.id];
 if(!v.area){const all=[...v.r.good.map(a=>[a,1]),...v.r.bad.map(a=>[a,-1])];
  return `${revealSpeech(p,`${v.name} 님 사주로 여덟 가지 운의 점수를 모두 계산했어요. 높은 운은 제대로 받아야 하고, 낮은 운은 지금 막아야 해요.`)}
  <span class="eyebrow">STEP 3 · 내 점수</span><h1>${esc(v.name)} 님의<br>여덟 가지 운 점수</h1>${rvBars(v)}
  ${all.map(([a,sg])=>`<div class="rv-card ${sg>0?'good':'bad'}"><small>${sg>0?'가장 좋은 운':'가장 조심할 운'} · ${esc(a.title)} ${a.score}점</small><p>${esc(a.text)}</p><p class="rv-hook">${esc(v.fill(sg>0?v.R.SCORE_GOOD:v.R.SCORE_BAD,{name:v.name,area:v.R.AREA_WORD[a.id]}))}</p></div>`).slice(0,4).join('')}
  ${revealLocks(s?.locks||[])}`}
 const pt=v.parts,word=v.R.AREA_WORD[p.id];
 const M=v.R.MARKS,month=v.map.unit==='month',when=ls=>ls.map(l=>month?l:l+'년').join(' · '),vals={name:v.name,weak:v.map.weak};
 // 좋은 점·조심할 점 모두 같은 크기의 큰 점수로 보여 준다(사장님 2026-10-28).
 const big=(kind,sc,sub)=>`<div class="rv-score ${kind}"><small class="rv-score-label">${esc(word)}의 ${kind==='good'?'좋은 점':'조심할 점'}</small><strong>${sc}<small>점</small></strong>${sub?`<span>${esc(sub)}</span>`:''}<i><b style="width:${sc}%"></b></i></div>`;
 // 근거가 한쪽에만 있으면 다른 쪽은 지도에서 그 쪽 해(달)를 꺼내 짚는다.
 // 점수: 앞으로 12년(12달) 가운데 그런 해(달)가 몇 번인지로 매긴다(saju/reveal.py side_score 와 같은 식).
 const sideScore=(d,kind)=>{const n=new Set(Object.values(d).flat()).size;return kind==='good'?Math.min(95,50+Math.round(50*n/12)):Math.max(5,50-Math.round(50*n/12))};
 const yearsPart=(d,kind)=>{const n=new Set(Object.values(d).flat()).size,sc=sideScore(d,kind);
  return Object.entries(d).slice(0,1).map(([key,ls])=>big(kind,sc,`앞으로 ${month?'열두 달':'12년'} 중 ${kind==='good'?'운이 들어오는':'조심할'} ${month?'달':'해'} ${n}번`)+`<div class="rv-card ${kind}"><p>${esc(when(ls))}은 ${esc(v.fill(M[key].line,vals))}입니다. ${esc(v.fill(M[key].meaning,vals))}</p><p class="rv-hook">${esc(M[key].hook)}</p></div>`).join('')};
 const reasonPart=(x,kind)=>big(kind,x.score,kind==='good'?(x.score>=60?'좋은 운':'좋은 편인 운'):'조심할 운')+`<div class="rv-card ${kind}"><p>${esc(x.text)}</p><p class="rv-hook">${esc(v.fill(kind==='good'?v.R.SCORE_GOOD:v.R.SCORE_BAD,{name:v.name,area:word}))}</p></div>`;
 const goodPart=pt.good?reasonPart(pt.good,'good'):yearsPart(v.map.good,'good');
 const badPart=pt.bad?reasonPart(pt.bad,'bad'):yearsPart(v.map.bad,'bad');
 // 점수가 높은 쪽이 위, 낮은 쪽이 아래(사장님 2026-10-28). 같으면 전체 점수로 정한다.
 const gs=pt.good?pt.good.score:sideScore(v.map.good,'good'),bs=pt.bad?pt.bad.score:sideScore(v.map.bad,'bad');
 const good=gs!==bs?gs>bs:pt.score>=50;
 // 제목·말풍선은 무료 풀이에서 이 운을 좋은 운/조심할 운 어느 쪽으로 보여 줬는지(areaView sign)를 따른다(제1조항: 모순 금지).
 const tone=v.area.sign>0,unitW=month?'달':'해';
 const speech=tone?(pt.good?`${word}부터 볼게요. 점수가 높아요. 그런데 높은 점수도 때를 모르면 절반밖에 받지 못해요.`:`${word}부터 볼게요. 좋은 운이 들어오는 ${unitW}가 정해져 있어요. 그런데 그때를 모르면 그냥 지나가요.`)
  :(good?`${word}부터 볼게요. 좋은 점도 있지만, 그냥 두면 안 되는 점이 함께 있어요.`:`${word}부터 볼게요. 솔직하게 말씀드릴게요. 이 점수는 그냥 두면 안 되는 점수예요.`);
 const head=tone?(pt.good?'타고난 그릇이 큽니다':`들어오는 ${unitW}를 잡아야 합니다`):'지금 막아야 합니다';
 return `${revealSpeech(p,speech)}
 <span class="eyebrow">STEP 3 · 내 점수</span><h1>${esc(v.name)} 님의 ${esc(word)},<br>${head}</h1>
 ${good?`${goodPart}<p class="rv-bridge bad">하지만, 아직 방심하면 안 됩니다.</p>${badPart}`:`${badPart}<p class="rv-bridge good">하지만, 아직 실망하기에는 이릅니다.</p>${goodPart}`}
 ${revealLocks(s?.locks||[])}`}
// 4. 지도: 기회의 해·조심할 해는 연도까지 공개, 몇 월인지와 무엇을 해야 하는지는 잠금
function rvScene3(p,v){const m=v.map,M=v.R.MARKS,month=m.unit==='month',unit=month?'달':'해';
 const vals={name:v.name,weak:m.weak};
 const when=labels=>labels.map(l=>month?l:l+'년').join(' · ');
 const card=(key,labels,kind)=>`<div class="rv-card rv-mark ${kind}"><div class="rv-mark-head"><span class="rv-tag ${kind}">${esc(M[key].tag)}</span><b>${esc(when(labels))}</b></div><p class="rv-mark-line">${esc(v.fill(M[key].line,vals))}</p><p>${esc(v.fill(M[key].meaning,vals))}</p><p class="rv-hook">${esc(M[key].hook)}</p></div>`;
 const goods=Object.entries(m.good),bads=Object.entries(m.bad);
 const first=goods.length===1?M[goods[0][0]].tag:'';
 return `${revealSpeech(p,`이제 가장 중요한 이야기예요. ${v.name} 님에게 운이 들어오는 ${month?'달과':'해와'} 조심해야 할 ${month?'달은':'해는'} 사주에 이미 정해져 있어요.`)}
 <span class="eyebrow">STEP 4 · ${month?'2027년 열두 달':'앞으로 12년'}</span><h1>${month?`${esc(v.name)} 님의<br>2027년 열두 달`:first?`${esc(v.name)} 님에게<br>${esc(first)}이 들어오는 해`:`앞으로 12년,<br>기회의 해와 조심할 해`}</h1>
 <div class="rv-grid">${m.cells.map(c=>`<div class="rv-cell${c.good.length?' good':''}${c.bad.length?' bad':''}"><b>${esc(c.label)}</b><small>${esc(c.ko)}</small>${[...c.good.map(x=>`<span class="g">${esc(M[x].tag)}</span>`),...c.bad.map(x=>`<span class="r">${esc(M[x].tag)}</span>`)].join('')}</div>`).join('')}</div>
 <div class="rv-legend"><span class="g">좋은 ${unit}</span><span class="r">조심할 ${unit}</span>${month?'<span>달은 절기 기준(매달 4~8일 무렵 시작)</span>':''}</div>
 ${goods.map(([k,l])=>card(k,l,'good')).join('')}${bads.map(([k,l])=>card(k,l,'bad')).join('')}
 ${revealLocks(month?['좋은 달에 시작해야 할 일과 그 방법','조심할 달에 미뤄야 할 일과 막는 방법','열두 달 각각의 돈·일·사람·건강 흐름']:['이 해의 몇 월에 들어오는지','그 해에 해야 할 일과 하지 말아야 할 일','조심할 해를 막는 구체적인 방법'])}`}
// 5. 리포트 1장 미리 보기: 실제 리포트 목차. 1장은 지금까지 본 내 사주로 열고, 2장부터는 제목만 보이고 내용은 가린다.
function rvScene4(p,v){const toc=EXTRA_DATA.toc[p.id]||[],c=v.r.chart,rest=Math.max(0,toc.length-1);
 return `${revealSpeech(p,`여기까지가 제가 미리 보여 드릴 수 있는 내용이에요. 몇 월에, 무엇을, 어떻게 해야 하는지는 ${v.name} 님 리포트에 모두 적어 드릴게요.`)}
 <span class="eyebrow">STEP 5 · 리포트 미리 보기</span><h1>${esc(v.name)} 님만의<br>한 권이 준비됐어요</h1>
 <div class="tp-page rv-page"><div class="tp-frame"><div class="tp-head">${esc(EXTRA_DATA.header?.[p.id]||'')}</div>
 ${toc[0]?`<div class="rv-ch open"><span class="tp-no">${esc(String(toc[0][0]))}</span><div><b>${esc(toc[0][1])}</b><p>${esc(c.items[0].text)}</p>${c.items[4]?`<p>${esc(c.items[4].text)}</p>`:''}<p>${esc(c.items[3].text.replace(/^.*?점수입니다\.\s*/,''))}</p></div></div>`:''}
 ${toc.slice(1).map(t=>`<div class="rv-ch"><span class="tp-no">${esc(String(t[0]))}</span><div><b>${esc(t[1])}</b><p class="rv-blur" aria-hidden="true">${esc(t[2]||'')} · ${esc(v.name)} 님의 시기와 방법</p></div>${icon('lock')}</div>`).join('')}
 </div></div>
 <p class="rv-close">${rest}개 장에 ${esc(v.name)} 님의 ${v.map.unit==='month'?'달마다':'해마다'} 할 일과 방법이 들어 있습니다.<br>결제하면 PDF로 써서 이메일로 보내드려요.</p>`}
const RV_CTA=['계속 듣기','다음 이야기 듣기','내 운이 들어오는 해 보기','리포트 미리 보기',''];
function revealPage(p,i){
 const d=draft(p.id);
 if(!personValid(d.self)){go(pathFor(p,FLOWS[p.id].findIndex(s=>s.type==='info')));return}
 const key=p.id+'|'+JSON.stringify(d.self);
 if(revealState.key!==key)revealState={key,scene:0,confirm:{},view:null};
 const paint=()=>{
  const v=revealState.view,n=revealState.scene,rest=Math.max(0,(EXTRA_DATA.toc[p.id]||[]).length-1);
  const body=[rvScene0,rvScene1,rvScene2,rvScene3,rvScene4][n](p,v);
  const cta=n===REVEAL_SCENES-1?`나머지 ${rest}장 받아 보기`:n===2&&p.id==='newyear'?'내 운이 들어오는 달 보기':RV_CTA[n];
  app.innerHTML=`<div class="shell flow reveal-flow" style="--accent:${p.color}">${progress(p,i)}<div class="rv-dots" aria-label="${n+1} / ${REVEAL_SCENES}">${Array.from({length:REVEAL_SCENES},(_,k)=>`<i class="${k<=n?'on':''}"></i>`).join('')}</div><main id="main"><div class="flow-content rv-body">${body}</div></main>${bottom(p,i,cta)}</div>`;
  document.activeElement?.blur?.();
  const next=document.querySelector('[data-next]'),back=document.querySelector('.back-square');
  if(n===1)next.disabled=!rvConfirmItems(v).every((_,k)=>revealState.confirm[k]);
  next.onclick=()=>{if(n<REVEAL_SCENES-1){revealState.scene++;paint();window.scrollTo({top:0,behavior:'instant'})}else advance(p,i)};
  back.onclick=e=>{if(n>0){e.preventDefault();revealState.scene--;paint();window.scrollTo({top:0,behavior:'instant'})}};
  document.querySelectorAll('[data-confirm]').forEach(b=>b.onclick=()=>{revealState.confirm[b.dataset.confirm]=b.dataset.v;const y=window.scrollY;paint();window.scrollTo({top:y,behavior:'instant'})});
 };
 if(revealState.view)return paint();
 app.innerHTML=`<div class="shell flow reveal-flow" style="--accent:${p.color}">${progress(p,i)}<main id="main"><div class="flow-content rv-body rv-loading">${revealSpeech(p,`${d.self.name} 님의 사주를 펼치고 있어요.`)}</div></main></div>`;
 revealLoad().then(lib=>{if(revealState.key!==key)return;revealState.view=revealCompute(p,d,lib);paint()})
  .catch(err=>{console.error(err);toast('사주를 계산하지 못했어요. 리포트 안내로 넘어갈게요.');advance(p,i)});
}
