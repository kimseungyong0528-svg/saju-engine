// 사이트 추가 기능 (2026-10-27 사장님 선택): 리포트 목차, 신년 이벤트 남은 날짜와 첫 화면 팝업, 할인.
// build_site.py 가 EXTRA_DATA 와 함께 사이트 코드 안에 넣는다.

// 18. 리포트 목차: 실제 리포트 목차(saju/report 의 SECTIONS)를 리포트 목차 쪽과 같은 모양(한지 바탕, 붉은 줄, 붉은 숫자)으로 다 펼쳐 보여 준다.
// 2026-10-27 사장님: 펼치기·닫기 없이 늘 펼쳐 두고, 실제 리포트 디자인으로.
const CHEVRON='<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m6 9 6 6 6-6"/></svg>';
function tocBlock(p){
 const toc=EXTRA_DATA.toc[p.id]||[];if(!toc.length)return '';
 const row=c=>`<li><span class="tp-no">${esc(String(c[0]))}</span><span class="tp-t"><b>${esc(c[1])}</b>${c[2]?`<small>${esc(c[2])}</small>`:''}</span></li>`;
 return `<section class="toc-x"><span class="x-eyebrow">CONTENTS</span><h2 class="x-title">리포트 목차</h2><p class="x-sub">실제 리포트의 목차 쪽 그대로예요. ${toc.length}개 장으로 되어 있어요.</p><div class="tp-page"><div class="tp-frame"><div class="tp-head">${esc(EXTRA_DATA.header?.[p.id]||'')}</div><h3 class="tp-h">목차</h3><ol class="tp-list">${toc.map(row).join('')}</ol></div></div></section>`;
}

// 17. 신년운세 이벤트: 기간 안에만 남은 날짜를 보여 주고, 기간이 끝나면 저절로 사라진다.
function eventDays(now=new Date()){
 const ev=EXTRA_DATA.event;if(!ev||!ev.start||!ev.end)return null;
 const kst=new Date(now.getTime()+9*3600e3).toISOString().slice(0,10);
 if(kst<ev.start||kst>ev.end)return null;
 return Math.round((Date.parse(ev.end)-Date.parse(kst))/864e5);
}
function eventBadge(){const d=eventDays();if(d===null)return '';const end=EXTRA_DATA.event.end.split('-');return d>30?`<span class="event-dday"><b>${Number(end[1])}월 ${Number(end[2])}일</b> 마감</span>`:`<span class="event-dday">${esc(EXTRA_DATA.event.label)} <b>${d?'D-'+d:'오늘 마감'}</b></span>`}

// 첫 화면 팝업 (사장님 2026-10-27): 처음 들어오면 한 번, 신년운세 이벤트 남은 날짜를 띄운다.
// 첫 구매 묶음 할인(2개 이상 10%)은 2단계 할인 장치가 들어가면 EXTRA_DATA.bundle 을 켜서 같이 보여 준다.
function entryPopup(){
 const d=eventDays();if(d===null)return;
 // 재구매 링크로 온 손님에게는 이벤트 팝업 대신 '재구매 할인 적용' 안내를 먼저 보여 준다.
 if(savedCoupon()){try{if(sessionStorage.getItem('unmyeong.rebuyNote'))return;sessionStorage.setItem('unmyeong.rebuyNote','1')}catch{}
  const tr=/^TRY-/.test(savedCoupon());couponCheck().then(ok=>{if(ok===true)toast(tr?'체험단 초대 링크예요. 고르신 리포트 한 권을 무료로 보내 드려요. 결제 화면에서 0원으로 보여요.':'재구매 할인 10%가 적용돼요. 어떤 리포트를 고르셔도 결제할 때 저절로 깎여요.');else if(ok===false&&tr)toast('이미 쓰인 체험단 링크예요. 보내 드린 분께 새 링크를 받아 주세요.');else if(ok===false)toast('재구매 할인 링크를 확인하지 못했어요. 리포트 안의 링크로 다시 들어와 주세요.')});return}
 const today=new Date(Date.now()+9*3600e3).toISOString().slice(0,10);
 try{if(sessionStorage.getItem('unmyeong.entry')||localStorage.getItem('unmyeong.entryHide')===today)return;sessionStorage.setItem('unmyeong.entry','1')}catch{}
 const p=pById('newyear');
 const m=modal(`<div class="entry-pop"><div class="entry-art"><img src="assets/geumwol/newyear-poster.webp" alt="금월선녀의 2027 신년운세" width="720" height="1018"><span class="entry-tag">한정 풀이</span></div><div class="entry-body"><p class="entry-lead">내 사주로 보는 2027년 열두 달의 흐름,<br><b>2월 28일까지만</b> 받을 수 있는 한정 풀이예요.</p><div class="entry-count"><span>한정 풀이 마감까지</span><b>${d?'D-'+d:'오늘 마감'}</b></div><a class="entry-go" href="${link(p)}">신년운세 보러 가기</a><button type="button" class="entry-hide" data-entry-hide>오늘 하루 보지 않기</button></div></div>`,'entry-modal','한정 풀이 안내');
 m.querySelector('.entry-go').onclick=()=>closeModal();
 m.querySelector('[data-entry-hide]').onclick=()=>{try{localStorage.setItem('unmyeong.entryHide',today)}catch{}closeModal()};
}

// 2단계 할인 (2026-10-27 사장님 결정). 할인은 모두 10%이고 한 주문에 하나만(더하지 않음). 금액은 서버(/api/quote)가 계산한다.
// 9·10. 첫 구매 묶음 할인: 처음 사는 분이 2개 이상 함께 사면 전부 10%.
// 12. 재구매 할인: 리포트 끝의 링크(?coupon=)로 들어왔을 때만 된다. 할인 코드 칸은 없다(2026-10-27 사장님).
const discounted=v=>Math.round(v*0.9);
// 묶음 목록과 금액 안내의 상품 순서(2026-10-27 사장님). 재회·깊은궁합은 상대방 정보가 필요하다(아래 bundleBlock).
const BUNDLE_IDS=['newyear','romance','intimate','reunion','wealth','career','business','health','lifetime'];
const PAIR_IDS=['intimate','reunion'];
const byOrder=(a,b)=>(BUNDLE_IDS.indexOf(a.id)+1||99)-(BUNDLE_IDS.indexOf(b.id)+1||99);
(()=>{try{const cp=new URLSearchParams(location.search).get('coupon');
 if(cp)localStorage.setItem('unmyeong.coupon',cp.slice(0,20).toUpperCase());}catch{}})();
function savedCoupon(){try{return localStorage.getItem('unmyeong.coupon')||''}catch{return ''}}
// '누구한테나 같은 말 하겠지' 반박 카드(자청 기획안 B-4, 2026-11-05): 예시 생일 두 개를 이 화면과 같은 계산기로 계산해 나란히 보여 준다. 손으로 쓴 숫자 없음(제1조항).
const RV_CMP=[{label:'예시 A',birth:'1994-04-11'},{label:'예시 B',birth:'1996-09-23'}];
function revealCompare(p,lib){try{const {eng,tst,data,texts,rv}=lib,R=texts.REVEAL;return RV_CMP.map(x=>{const person={name:x.label,sex:'female',calendar:'solar',birth:x.birth,timeAccuracy:'unknown',time:'',birthPlace:{status:'unknown'}};const fp=eng.chartFromPerson(data,person,x.birth),r=tst.reading(fp,person,texts);const m=rv.luckMap(fp,'female',p.id,texts,revealStartYear(),p.id==='reunion'?revealStartMonth(rv):null);const c=m.cells.find(c=>c.good.length);const word=p.id==='lifetime'?'가장 좋은 운':(R.AREA_WORD[p.id]||'운');const score=p.id==='lifetime'?r.good[0]?.title:r.scores[p.id];return {label:x.label,birth:x.birth,word,score,first:c?{label:c.label,tag:R.MARKS[c.good[0]]?.tag||''}:null,unit:m.unit}})}catch(e){return null}}
function revealCompareCard(v){const c=v.cmp;if(!c||c.length<2)return '';const yr=b=>b.slice(0,4)+'년 '+Number(b.slice(5,7))+'월 '+Number(b.slice(8,10))+'일생';
 return `<section class="rv-cmp" aria-label="생일이 다르면 답도 달라요"><h3>생일이 다르면, 답도 달라요</h3><p class="rv-cmp-lead">같은 계산기로 예시 생일 두 개를 계산해 봤어요. ${esc(v.name)} 님 결과도 ${esc(v.name)} 님 생일로만 나와요.</p><div class="rv-cmp-grid">${c.map(x=>`<div><b>${esc(x.label)}</b><small>${esc(yr(x.birth))}</small><p>${esc(x.word)} <strong>${typeof x.score==='number'?x.score+'점':esc(String(x.score||''))}</strong></p><p>첫 '${esc(x.first?.tag||'-')}' <strong>${esc(x.first?(x.unit==='month'?x.first.label:x.first.label+'년'):'-')}</strong></p></div>`).join('')}</div><p class="rv-cmp-note">예시 생일은 실존 인물이 아니에요. 태어난 시간은 모름으로 계산했어요.</p></section>`}
// 결제 전 화면 '계산 근거 자세히 보기'(자청 기획안 B-1): 홈의 계산 근거 칸으로 바로 내려간다.
document.addEventListener('click',e=>{if(e.target.closest('[data-goto-trust]'))try{sessionStorage.setItem('unmyeong.gotoTrust','1')}catch{}});
new MutationObserver(()=>{try{if(sessionStorage.getItem('unmyeong.gotoTrust')!=='1')return;const t=document.querySelector('#trust-title');if(!t)return;sessionStorage.removeItem('unmyeong.gotoTrust');setTimeout(()=>t.scrollIntoView({block:'start',behavior:'instant'}),60)}catch{}}).observe(document.documentElement,{childList:true,subtree:true});
// 지금까지 보낸 리포트 수(자청 기획안 E-4): 실제 발송 수만, 50권이 넘을 때만 보인다.
new MutationObserver(()=>document.querySelectorAll('[data-delivered]:not([data-filled])').forEach(el=>{el.dataset.filled='1';fetch('/api/stats/public').then(r=>r.ok?r.json():null).then(d=>{if(d&&d.delivered&&el.isConnected){el.textContent=`지금까지 ${d.delivered.toLocaleString('ko-KR')}권의 리포트를 보냈어요`;el.hidden=false}}).catch(()=>{})})).observe(document.documentElement,{childList:true,subtree:true});
// 실제 후기(2026-11-05 체험단): 사장님이 관리 사이트에서 '싣기'한 후기만 서버에서 받아 보여 준다. 없으면 칸을 숨긴다.
// 체험단 무료 코드로 받은 리포트의 후기는 '체험단 무료 제공'을 붙이고 아래에 뜻을 적는다(표시광고법 추천·보증 심사지침).
const reviewCache={};
function fillReviews(box){const pid=box.dataset.reviews;box.dataset.filled='1';
 (reviewCache[pid]||=fetch('/api/reviews?product='+encodeURIComponent(pid)).then(r=>r.ok?r.json():null).catch(()=>null)).then(d=>{if(!d||!d.count||!box.isConnected)return;
  box.innerHTML=`<h3>받아 보신 분들의 후기 <span class="rvw-avg">★ ${d.avg} · ${d.count}개</span></h3>${d.reviews.slice(0,5).map(r=>`<article class="rvw"><p class="rvw-stars" aria-label="별 ${r.stars}개">${'★'.repeat(r.stars)}${'☆'.repeat(5-r.stars)}${r.trial?'<em class="rvw-tag">체험단 무료 제공</em>':''}</p><p class="rvw-text">${esc(r.text)}</p><p class="rvw-who">${esc(r.nick)} · ${esc(r.date.replace(/-/g,'.'))}</p></article>`).join('')}${d.trialCount?'<p class="rvw-note">\'체험단 무료 제공\' 표시가 있는 후기는 운명서재가 리포트를 무료로 드리고 받은 후기예요. 글은 고치지 않고 그대로 실어요.</p>':'<p class="rvw-note">리포트를 받으신 분이 남긴 글을 고치지 않고 그대로 실어요.</p>'}`;box.hidden=false})}
new MutationObserver(()=>document.querySelectorAll('[data-reviews]:not([data-filled])').forEach(fillReviews)).observe(document.documentElement,{childList:true,subtree:true});
// 재구매 링크 확인(2026-11-05 자청 점검 F-6): 서버(/api/quote)가 쿠폰을 확인하기 전에는 '적용돼요'라고 말하지 않는다. 틀린 링크면 저장값을 지운다.
let couponValid=null;
function couponCheck(){const c=savedCoupon();if(!c){couponValid=false;return Promise.resolve(false)}return fetch('/api/quote',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({productId:'newyear',email:'',extras:[],coupon:c}),signal:AbortSignal.timeout(15000)}).then(r=>r.ok?r.json():null).then(q=>{couponValid=Boolean(q&&!q.notes?.includes('COUPON_INVALID'));if(q&&!couponValid){try{localStorage.removeItem('unmyeong.coupon')}catch{}}return couponValid}).catch(()=>{couponValid=null;return null})}
// 함께 받아 보기 순서 (2026-11-05): 같은 순서를 모두에게 보이지 않고, 이 손님에게 맞는 상품을 위로. 점수가 같으면 사장님 순서(CO_TOP).
// 고른 답 → 상품: 손님이 고른 보기 글자 그대로(예전 선택지 값)
const CO_HINT={'일과 직장':'career','돈과 재물':'wealth','연애와 결혼':'romance','건강':'health','한 해 전체':'lifetime','사업을 하고 있어요':'business','사업을 운영하고 있어요':'business','창업을 생각해요':'business','이직을 고민해요':'career','첫 취업을 준비해요':'career','헤어진 사이예요':'reunion','최근에 헤어졌어요':'reunion','아직 헤어지지 않았어요':'intimate','연애 중이에요':'intimate','결혼했어요':'intimate','결혼한 사이예요':'newyear'};
function tasterPicks(){try{const v=JSON.parse(localStorage.getItem('unmyeong.tasterPicks')||'null');if(v&&Date.now()-(v.at||0)<30*864e5)return {good:v.good||[],bad:v.bad||[]}}catch{}return {good:[],bad:[]}}
// 방금 고른 상품의 '다음 질문'(2026-11-05 자청 점검 N-11): 가치 사다리. 손님이 고른 답(CO_HINT)과 상대 정보보다는 아래 점수.
const CO_NEXT={career:['wealth','business','newyear'],business:['wealth','newyear','career'],wealth:['business','newyear','career'],health:['newyear','lifetime','wealth'],lifetime:['newyear','romance','wealth'],romance:['intimate','newyear','reunion'],reunion:['intimate','romance','newyear'],intimate:['reunion','newyear','romance'],newyear:['romance','wealth','career']};
const CO_WHY={'career>wealth':'옮길 해와 돈 들어오는 해 같이','business>wealth':'키울 해와 돈 들어오는 해 같이','wealth>business':'돈 들어오는 해에 벌일 일도','health>newyear':'쉬어야 할 때를 2027년 달마다','lifetime>newyear':'평생 흐름 중 2027년을 달마다','romance>intimate':'만나는 사람과 궁합도','reunion>intimate':'넣은 생일 그대로, 두 사람 궁합','intimate>reunion':'다시 가까워지는 달도 같이','newyear>romance':'2027년 연애운 자세히','reunion-solo>romance':'그 사람 정보 없이 내 연애 패턴'};
function coSolo(p,d){return p.id==='reunion'&&Boolean(d.partner&&d.partner.birthUnknown)}
function coOrder(p,d,others){
 const ans=new Set([...Object.values(d.answers||{}),...Object.values(d.extraAnswers||{}).flatMap(a=>Object.values(a||{}))].filter(Boolean).map(String));
 const tp=tasterPicks(),gift=typeof isGift==='function'&&isGift(p.id),married=['결혼했어요','결혼한 사이예요'].some(x=>ans.has(x)),hasPartner=Boolean(d.partner&&personValid(d.partner));
 const nx=coSolo(p,d)?['romance','newyear','wealth']:(CO_NEXT[p.id]||[]);const sc=x=>{let s=0;const ni=nx.indexOf(x.id);if(ni>=0)s+=40-ni*10;if(coSolo(p,d)&&x.id==='romance')s+=80;if(hasPartner&&PAIR_IDS.includes(x.id))s+=100;for(const [k,v] of Object.entries(CO_HINT))if(v===x.id&&ans.has(k))s+=60;const gi=tp.good.indexOf(x.id);if(gi>=0)s+=45-gi*5;const bi=tp.bad.indexOf(x.id);if(bi>=0)s+=30-bi*5;if(married&&['romance','reunion'].includes(x.id))s-=200;if(gift&&['romance','reunion'].includes(x.id))s-=50;return s};
 return [...others].sort((x,y)=>sc(y)-sc(x)||((CO_TOP.indexOf(x.id)+1||99)-(CO_TOP.indexOf(y.id)+1||99)));
}
// 이메일은 이 기기에만 기억해 두고 다음 결제 때 다시 채운다(서버로 따로 보내지 않음).
function savedEmail(){try{return localStorage.getItem('unmyeong.email')||''}catch{return ''}}
function rememberEmail(v){try{localStorage.setItem('unmyeong.email',String(v).slice(0,120))}catch{}}
function bundleBlock(p,d){
 if(!EXTRA_DATA.bundle)return '';
 const pair=FLOWS[p.id].some(st=>st.who==='partner');
 const others=BUNDLE_IDS.filter(id=>id!==p.id).map(id=>PRODUCTS.find(x=>x.id===id)).filter(Boolean),on=new Set(d.extras||[]);
 const ea=d.extraAnswers||(d.extraAnswers={});
 const qs=x=>FLOWS[x.id].filter(st=>st.type==='choice').map(st=>{
  // 같은 질문(같은 이름)에 이미 답했으면 그 답을 미리 채운다(다시 묻지 않게)
  const mine=d.answers?.[st.id]||Object.values(ea).map(a=>a?.[st.id]).find(Boolean);if(!ea[x.id]?.[st.id]&&mine&&st.options.includes(mine))(ea[x.id]||(ea[x.id]={}))[st.id]=mine;
  const cur=ea[x.id]?.[st.id]||'';
  return `<label class="bundle-ask"><span>${esc(st.title)}</span><select data-extra-q="${x.id}" data-step="${st.id}"><option value="">선택해주세요</option>${st.options.map(o=>`<option${o===cur?' selected':''}>${esc(o)}</option>`).join('')}</select></label>`}).join('');
 // 재회·깊은궁합은 상대방 정보가 필요하다. 주 주문에서 상대방 정보를 받지 않았으면, 둘 중 하나를 고를 때 바로 아래에 상대방 입력칸을 펼친다(2026-10-27 사장님).
 const lastPair=[...others].reverse().find(x=>PAIR_IDS.includes(x.id))?.id;
 const partnerForm=`<form class="bundle-partner" data-bundle-partner novalidate><p class="bundle-partner-title">상대방 정보</p><p class="bundle-partner-sub">재회사주·깊은 궁합은 상대방의 출생 정보로 두 사람을 함께 봐요. 둘 다 고르면 같은 상대방으로 봐요.</p>${personFields('bundle-partner',d.partner||{}).replace('나의 이야기 준비하기','상대방 정보 준비하기')}</form>`;
 // 재구매 링크로 온 손님: 재구매 할인 10%가 붙고 묶음 할인과는 겹치지 않는다(한 주문에 할인 하나). 첫 구매 상자 대신 한 줄로 알려 준다.
 if(d.coupon||savedCoupon())return couponValid===true?`<p class="bundle-rebuy">재구매 할인 10%가 이 주문에 적용돼요. 할인은 한 주문에 하나만 들어가요.</p>`:`<p class="bundle-rebuy">재구매 할인 링크를 확인하고 있어요. 확인되면 결제 금액에서 10%가 깎여요.</p>`;
 // 목록은 접어 두고(결제 화면이 길어지지 않게), 이미 고른 상품이 있으면 펼친다.
 return `<section class="bundle-x"><details class="bundle-more"${on.size?' open':''}><summary><span class="x-eyebrow">FIRST ORDER</span><span class="x-title">함께 사면 전부 <em>10%</em> 할인</span><span class="x-sub">처음 구매하시는 분이 2개 이상 함께 사면 전부 10% 할인돼요. 리포트는 한 권씩 따로 보내드려요.</span><b class="bundle-open">여기를 눌러서 할인 받기</b></summary><div class="bundle-list">${others.map(x=>{const q=qs(x);return `<div class="bundle-row"><label class="bundle-item"><input type="checkbox" name="extra" value="${x.id}"${on.has(x.id)?' checked':''}><span class="bundle-name">${esc(x.name.replace(/^금월선녀의\s*/,''))}</span><span class="bundle-price"><s>${money(x.price)}</s><span><em>10%</em> ${money(discounted(x.price))}</span></span></label>${q?`<div class="bundle-q">${q}</div>`:''}</div>${!pair&&x.id===lastPair?partnerForm:''}`}).join('')}</div></details></section>`;
}
const QUOTE_NOTES={EXTRA_ANSWERS:'함께 살 리포트의 질문과 상대방 정보를 채워야 결제할 수 있어요.',BUNDLE_FIRST_ONLY:'묶음 할인은 첫 구매 때만 돼요. 이 이메일로 구매하신 적이 있어요.',EMAIL_FOR_DISCOUNT:'이메일을 넣으면 첫 구매인지 확인해서 묶음 할인을 적용해 드려요.'};
function quoteBox(p,q){
 if(!q)return priceBox(p,0);
 // 내가 고른 상품이 맨 위, 함께 산 상품은 그 아래(사이트 순서)
 const all=q.items.map(it=>PRODUCTS.find(x=>x.id===it.id)||{...it,original:it.price}),items=[all[0],...all.slice(1).sort(byOrder)],orig=items.reduce((a,x)=>a+x.original,0);
 const list=items.length>1?`<div class="qb-items">${items.map(x=>`<div><span>${esc(x.name.replace(/^금월선녀의\s*/,''))}</span><span>${x.original>x.price?`<s>${money(x.original)}</s> `:''}${money(x.price)}</span></div>`).join('')}</div>`:'';
 // 금액은 단계를 나눠 보인다: ① 정가 ② 상품 할인 ③ 첫 구매 묶음 할인 → 최종 금액(2026-10-30 사장님).
 // 이메일을 넣기 전에도 묶음 할인 금액을 보여 주고, '이메일 확인 뒤 적용'으로 표시한다(실제 금액은 서버가 확인한 뒤에만 깎인다).
 const wait=!q.discount&&items.length>1&&(q.notes||[]).includes('EMAIL_FOR_DISCOUNT'),cut=q.base-discounted(q.base);
 const dc=q.discount?`<div class="qb-disc"><span><i class="qb-no">③</i>${esc(q.discount.label)} <em>${q.discount.percent}%</em></span><strong>−${money(q.discount.amount)}</strong></div>`
  :wait?`<div class="qb-disc wait"><span><i class="qb-no">③</i>첫 구매 묶음 할인 <em>10%</em><small>이메일 확인 뒤 적용</small></span><strong>−${money(cut)}</strong></div>`:'';
 // 같은 안내를 두 번 쓰지 않고(손님 테스트 2차), 질문이 비어 있는 상품 이름을 짚는다.
 const gap=(q.incomplete||[]).map(id=>PRODUCTS.find(x=>x.id===id)?.short||'').filter(Boolean);
 const notes=[...new Set([...(q.notes||[]),...(q.missing?['EXTRA_ANSWERS']:[])])].filter(n=>QUOTE_NOTES[n]).map(n=>`<p class="qb-note">${n==='EXTRA_ANSWERS'&&gap.length?`${esc(gap.join(', '))}의 질문${gap.some(x=>/재회|궁합/.test(x))?'(재회사주·깊은 궁합은 상대방 정보)':''}을 채워야 결제할 수 있어요.`:QUOTE_NOTES[n]}</p>`).join('');
 return `<div class="price-box">${list}<div><span><i class="qb-no">①</i>정가</span><s>${money(orig)}</s></div><div><span><i class="qb-no">②</i>상품 할인</span><strong>−${money(orig-q.base)}</strong></div>${dc}<div class="price-total"><span>최종 금액</span>${q.discount?`<span class="qb-final"><s>${money(q.base)}</s><strong>${money(q.amount)}</strong></span>`:wait?`<span class="qb-final"><strong>${money(q.amount)}</strong><small>첫 구매라면 <b>${money(q.base-cut)}</b></small></span>`:`<strong>${money(q.amount)}</strong>`}</div></div>${notes}`;
}
// 결제가 '함께 살 리포트의 질문이 비어 있음'으로 막히면, 접힌 목록을 펼치고 비어 있는 칸으로 데려간다.
function showBundleGap(){
 const det=document.querySelector('.bundle-more');if(det)det.open=true;
 const rows=[...document.querySelectorAll('.bundle-row')].filter(r=>r.querySelector('input[name=extra]:checked'));
 const el=rows.map(r=>r.querySelector('select[data-extra-q]:not([data-ok])')).find(x=>x&&!x.value)||document.querySelector('[data-bundle-partner] input:invalid, [data-bundle-partner] select:invalid')||rows[0];
 if(el){el.scrollIntoView({block:'center',behavior:'smooth'});try{el.focus({preventScroll:true})}catch{}}
 // 비어 있는 칸은 빨갛게, 안내 글에는 그 상품 이름을 넣는다(손님 테스트 3차: 어느 상품의 무엇이 빠졌는지 몰랐다)
 const gap=rows.filter(r=>[...r.querySelectorAll('select[data-extra-q]:not([data-ok])')].some(x=>!x.value));
 gap.forEach(r=>r.querySelectorAll('select[data-extra-q]').forEach(x=>{if(!x.value)x.classList.add('qb-missing')}));
 const pf=document.querySelector('[data-bundle-partner]');if(pf&&pf.querySelector('input:invalid, select:invalid'))pf.querySelectorAll('input:invalid, select:invalid').forEach(x=>x.classList.add('qb-missing'));
 const names=gap.map(r=>(r.querySelector('.bundle-name')?.textContent||'').trim()).filter(Boolean);
 return names.length?`${names.join(', ')}의 질문을 골라 주세요. 사지 않으려면 그 상품의 체크를 풀어 주세요.`:'';
}
document.addEventListener('change',e=>{if(e.target.classList&&e.target.classList.contains('qb-missing')&&e.target.value)e.target.classList.remove('qb-missing');
 // 빈 칸을 채우면 결제 버튼 아래 '질문을 골라 주세요' 안내를 지운다(손님 테스트 4차: 채운 뒤에도 남았다)
 if(e.target.closest&&(e.target.closest('.bundle-row')||e.target.closest('[data-bundle-partner]'))&&!document.querySelector('.qb-missing')){const n=document.querySelector('[data-checkout-error]');if(n&&/질문|상대방 정보/.test(n.textContent))n.textContent=''}});
let quoteSeq=0;
async function refreshQuote(p,d){
 const seq=++quoteSeq,box=document.querySelector('#checkout-price');if(!box)return;
 let q=null;try{const r=await fetch('/api/quote',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({...d,productId:p.id,email:d.email||'',extras:d.extras||[],coupon:d.coupon||''}),signal:AbortSignal.timeout(15000)});if(r.ok)q=await r.json()}catch{}
 if(seq!==quoteSeq||!box.isConnected)return;
 if(q&&d.coupon&&q.notes?.includes('COUPON_INVALID')){couponValid=false;toast('재구매 할인 링크를 확인하지 못했어요. 리포트 안의 링크로 다시 들어와 주세요.');d.coupon='';try{localStorage.removeItem('unmyeong.coupon')}catch{}save();document.querySelector('.bundle-rebuy')?.remove();return refreshQuote(p,d)}
 if(q&&d.coupon&&couponValid!==true){couponValid=true;const rb=document.querySelector('.bundle-rebuy');if(rb)rb.textContent='재구매 할인 10%가 이 주문에 적용돼요. 할인은 한 주문에 하나만 들어가요.'}
 if(q)q.missing=Boolean(q.incomplete?.length);
 // 이미 구매한 이메일이면 목록의 '10%' 가격을 지운다(손님 테스트 4차: 재구매 손님에게도 '10% 26,820원'이 보였다)
 document.querySelector('.bundle-x')?.classList.toggle('no-first',Boolean(q?.notes?.includes('BUNDLE_FIRST_ONLY')));
 box.innerHTML=quoteBox(p,q);
}
function bindDiscounts(p,d){
 const form=document.querySelector('#checkout-form');if(!form)return;
 // 묶음 할인은 이메일 칸 아래, 금액 안내 바로 위에서 고른다(2026-10-30 사장님). 상대방 정보 칸은 따로 된 form이라 화면을 그린 뒤 옮긴다.
 const ph=form.querySelector(':scope>h2.checkout-label');document.querySelectorAll('.bundle-x,.bundle-rebuy').forEach(b=>{if(ph)form.insertBefore(b,ph)});
 if(!d.coupon&&savedCoupon())d.coupon=savedCoupon();
 delete d.discount;
 // 상대방 입력칸은 체크한 재회사주·깊은 궁합 바로 밑에 연다(손님 테스트: 깊은 궁합을 골랐는데 재회사주 밑에 열림).
 const placePartner=()=>{const f=document.querySelector('[data-bundle-partner]'),b=[...document.querySelectorAll('.bundle-x input[name=extra]:checked')].find(x=>PAIR_IDS.includes(x.value));if(f&&b)b.closest('.bundle-row').after(f)};
 document.querySelectorAll('.bundle-x input[name=extra]').forEach(b=>b.onchange=()=>{if(b.checked)window.uTrack&&uTrack('add_extra',{product:p.id,extra:b.value});d.extras=[...document.querySelectorAll('.bundle-x input[name=extra]:checked')].map(x=>x.value);save();placePartner();refreshQuote(p,d)});
 placePartner();
 const pf=document.querySelector('[data-bundle-partner]');
 if(pf){let pt;bindPerson(pf,(v,valid)=>{d.partner=v;save();clearTimeout(pt);pt=setTimeout(()=>refreshQuote(p,d),400)})}
 document.querySelectorAll('[data-extra-q]').forEach(sel=>sel.onchange=()=>{const ea=d.extraAnswers||(d.extraAnswers={});(ea[sel.dataset.extraQ]||(ea[sel.dataset.extraQ]={}))[sel.dataset.step]=sel.value;save();refreshQuote(p,d)});
 let t,emSent=false;form.elements.email.addEventListener('input',()=>{clearTimeout(t);t=setTimeout(()=>refreshQuote(p,d),600);emailHintShow(form);const em=form.elements.email;if(!emSent&&em.validity.valid&&/@[^@]+\.[a-z]{2,}$/i.test(em.value)){emSent=true;window.uTrack&&uTrack('add_email',{product:p.id})}});
 form.elements.email.addEventListener('blur',()=>emailHintShow(form,true));
 emailHintShow(form);
 // 환불 안내·약관을 보고 돌아와도 동의 체크가 풀리지 않게(손님 테스트 2차)
 const CK='unmyeong.consent.'+p.id,boxes=['privacy','payment'].map(n=>form.elements[n]).filter(Boolean);
 try{if(sessionStorage.getItem(CK)==='1'&&boxes.length){boxes.forEach(b=>{b.checked=true});const all=document.querySelector('#all-consent');if(all)all.checked=true;boxes[0].dispatchEvent(new Event('input',{bubbles:true}))}}catch{}   // 결제 버튼은 'input'에서 다시 계산된다(손님 테스트 3차: 체크는 켜졌는데 버튼이 꺼져 있었음)
 form.addEventListener('change',()=>{try{sessionStorage.setItem(CK,boxes.length&&boxes.every(b=>b.checked)?'1':'0')}catch{}});
 // 결제 버튼이 왜 안 눌리는지 알려 준다(손님 테스트 4차: 동의를 안 하면 이유 없이 버튼이 안 눌렸다)
 const pay=form.querySelector('#pay');
 if(pay&&boxes.length){let why=form.querySelector('.pay-why');if(!why){why=document.createElement('p');why.className='pay-why';pay.after(why)}
  const upd=()=>{const em=form.elements.email;why.textContent=!(em&&em.value&&em.validity.valid)?'맨 위에 리포트 받을 이메일을 넣어 주세요.':boxes.every(b=>b.checked)?'':'위의 동의 두 곳에 체크하면 결제할 수 있어요.'};form.addEventListener('input',upd);form.addEventListener('change',upd);form.elements.email?.addEventListener('input',upd);upd()}
 // 이메일 오타 안내가 떠 있으면 결제 전에 한 번 멈춘다(손님 테스트 4차: 오타 추천이 떠 있어도 결제됐다). 그대로 쓰려면 한 번 더 누르면 된다.
 if(pay){let ok='';pay.addEventListener('click',e=>{const v=form.elements.email?.value||'',h=emailHint(v);if(h&&h.fix&&ok!==v){ok=v;e.preventDefault();e.stopImmediatePropagation();emailHintShow(form,true);
  const box=document.querySelector('.email-hint');if(box){box.scrollIntoView({block:'center',behavior:'smooth'});box.classList.add('qb-missing')}}},true)}
 refreshQuote(p,d);
}

// 이메일 오타 알려 주기(손님 테스트 2026-10-28): 결과가 남의 메일로 가지 않게, 흔한 오타와 끝(.com)을 빠뜨린 주소를 바로 짚는다.
const EMAIL_FIX={'gmial.com':'gmail.com','gamil.com':'gmail.com','gmai.com':'gmail.com','gmail.co':'gmail.com','gmail.con':'gmail.com','gmail.cm':'gmail.com','gmail.om':'gmail.com',
 'naver.co':'naver.com','naver.con':'naver.com','naver.cm':'naver.com','naver.om':'naver.com','nave.com':'naver.com','navr.com':'naver.com','naer.com':'naver.com',
 'daum.ne':'daum.net','daum.com':'daum.net','hanmail.com':'hanmail.net','hanmail.ne':'hanmail.net','kakao.co':'kakao.com','kakao.con':'kakao.com','nate.co':'nate.com','nate.con':'nate.com',
 'hanmial.net':'hanmail.net','hanmali.net':'hanmail.net','hamail.net':'hanmail.net','hanmil.net':'hanmail.net','hanmai.net':'hanmail.net','hnmail.net':'hanmail.net','hanmail.ent':'hanmail.net','hanmail.nte':'hanmail.net','hanmial.com':'hanmail.net',
 'daum.ent':'daum.net','daum.nte':'daum.net','duam.net':'daum.net','naver.ent':'naver.com','naver.net':'naver.com','gmail.net':'gmail.com','gmali.com':'gmail.com','gmil.com':'gmail.com','nate.ent':'nate.com'};
const EMAIL_BARE={naver:'naver.com',gmail:'gmail.com',daum:'daum.net',hanmail:'hanmail.net',kakao:'kakao.com',nate:'nate.com'};
function emailHint(v){const t=String(v||'').trim(),m=/^([^@\s]+)@([^@\s]+)$/.exec(t);if(!m)return t?{bad:true}:null;const dom=m[2].toLowerCase();
 if(EMAIL_FIX[dom])return {fix:m[1]+'@'+EMAIL_FIX[dom]};if(!dom.includes('.'))return EMAIL_BARE[dom]?{fix:m[1]+'@'+EMAIL_BARE[dom]}:{end:true};return null}
function emailHintShow(form,done){
 const input=form.elements.email;if(!input)return;let box=document.querySelector('.email-hint');
 let h=emailHint(input.value);
 // '@'가 빠진 주소는 다 쓰고 칸을 벗어났을 때 알려 준다(쓰는 중에는 띄우지 않는다). 안내가 없으면 결제 버튼이 왜 꺼졌는지 모른다(손님 테스트 3차).
 if(h&&h.bad&&!done&&!box)h=null;
 if(!h){box?.remove();input.setCustomValidity('');return}
 if(!box){box=document.createElement('p');box.className='email-hint';box.setAttribute('role','status');input.closest('label,div')?.after(box)||input.after(box)}
 // 같은 안내면 다시 그리지 않는다: '이 주소로 고치기'를 누를 때 칸을 벗어나며(blur) 버튼이 새로 그려지면 누른 것이 사라진다
 const key=JSON.stringify(h);if(box.dataset.key===key)return;box.dataset.key=key;
 if(h.fix){box.innerHTML=`혹시 <b>${esc(h.fix)}</b> 인가요? <button type="button" class="email-fix">이 주소로 고치기</button>`;box.querySelector('.email-fix').onclick=()=>{input.value=h.fix;input.dispatchEvent(new Event('input',{bubbles:true}))};input.setCustomValidity('')}
 else if(h.bad){box.textContent='이메일 주소가 맞는지 다시 봐 주세요. 가운데에 @가 들어가야 해요. 예: name@naver.com';input.setCustomValidity('')}
 else{box.textContent='이메일 주소 끝(.com, .net 같은 부분)까지 넣어 주세요. 예: name@naver.com';input.setCustomValidity('이메일 주소 끝까지 넣어 주세요.')}
}
