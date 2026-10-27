// 사이트 추가 기능 1단계 (2026-10-27 사장님 선택): 목차 펼쳐보기, 리포트 미리보기, 신년 이벤트 남은 날짜와 첫 화면 팝업,
// 무료 결과 공유 이미지. build_site.py 가 EXTRA_DATA 와 함께 사이트 코드 안에 넣는다.

// 18. 목차 펼쳐보기: 실제 리포트 목차(saju/report 의 SECTIONS)를 처음 5장만 보여 주고 나머지는 버튼으로 편다.
const CHEVRON='<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m6 9 6 6 6-6"/></svg>';
function tocBlock(p){
 const toc=EXTRA_DATA.toc[p.id]||[];if(!toc.length)return '';
 const row=(c,n)=>`<li${n>=5?' class="toc-more" hidden':''}><span class="toc-n">${String(c[0]).padStart(2,'0')}</span><div><b>${esc(c[1])}</b>${c[2]?`<small>${esc(c[2])}</small>`:''}</div></li>`;
 return `<section class="toc-x"><span class="x-eyebrow">CONTENTS</span><h2 class="x-title">리포트 목차</h2><p class="x-sub">실제 리포트에 들어가는 ${toc.length}개 장이에요.</p><ol class="toc-list">${toc.map(row).join('')}</ol>${toc.length>5?`<button type="button" class="x-more" data-toc-toggle><span>목차 전체 보기</span>${CHEVRON}</button>`:''}</section>`;
}

// 2. 리포트 미리보기: 가상의 인물로 만든 실제 리포트에서 뽑은 쪽을 옆으로 넘겨 본다. 누르면 크게 본다.
function previewBlock(p){
 const pages=EXTRA_DATA.preview[p.id]||[];if(!pages.length)return '';
 return `<section class="pv-x"><span class="x-eyebrow">PREVIEW</span><h2 class="x-title">리포트 미리보기</h2><p class="x-sub">가상의 인물로 만든 실제 리포트예요. 눌러서 크게 보세요.</p><div class="pv-rail" data-pv-rail>${pages.map(([src,cap],n)=>`<button type="button" class="pv-page" data-pv="${n}" data-pv-product="${p.id}" aria-label="${esc(cap)} 크게 보기"><img src="${esc(src)}" alt="리포트 미리보기: ${esc(cap)}" loading="lazy" decoding="async" width="720" height="1018"><span class="pv-cap">${esc(cap)}</span></button>`).join('')}</div><div class="pv-dots" aria-hidden="true">${pages.map((_,n)=>`<i${n?'':' class="on"'}></i>`).join('')}</div></section>`;
}
function previewModal(pid,n){
 const pages=EXTRA_DATA.preview[pid]||[];n=(n+pages.length)%pages.length;const [src,cap]=pages[n];
 const d=modal(`<figure class="pv-fig"><img class="pv-big" src="${esc(src)}" alt="리포트 미리보기: ${esc(cap)}"><figcaption><button type="button" class="pv-nav" data-pv-step="-1" aria-label="이전 쪽">‹</button><span>${esc(cap)} <em>${n+1} / ${pages.length}</em></span><button type="button" class="pv-nav" data-pv-step="1" aria-label="다음 쪽">›</button></figcaption></figure>`,'pv-modal','리포트 미리보기');
 d.querySelectorAll('[data-pv-step]').forEach(b=>b.onclick=()=>previewModal(pid,n+Number(b.dataset.pvStep)));
}

// 17. 신년운세 이벤트: 기간 안에만 남은 날짜를 보여 주고, 기간이 끝나면 저절로 사라진다.
function eventDays(now=new Date()){
 const ev=EXTRA_DATA.event;if(!ev||!ev.start||!ev.end)return null;
 const kst=new Date(now.getTime()+9*3600e3).toISOString().slice(0,10);
 if(kst<ev.start||kst>ev.end)return null;
 return Math.round((Date.parse(ev.end)-Date.parse(kst))/864e5);
}
function eventBadge(){const d=eventDays();return d===null?'':`<span class="event-dday">${esc(EXTRA_DATA.event.label)} <b>${d?'D-'+d:'오늘 마감'}</b></span>`}

// 첫 화면 팝업 (사장님 2026-10-27): 처음 들어오면 한 번, 신년운세 이벤트 남은 날짜를 띄운다.
// 첫 구매 묶음 할인(2개 이상 10%)은 2단계 할인 장치가 들어가면 EXTRA_DATA.bundle 을 켜서 같이 보여 준다.
function entryPopup(){
 const d=eventDays();if(d===null)return;
 const today=new Date(Date.now()+9*3600e3).toISOString().slice(0,10);
 try{if(sessionStorage.getItem('unmyeong.entry')||localStorage.getItem('unmyeong.entryHide')===today)return;sessionStorage.setItem('unmyeong.entry','1')}catch{}
 const p=pById('newyear');
 const m=modal(`<div class="entry-pop"><div class="entry-art"><img src="assets/geumwol/newyear-cover.webp" alt="" aria-hidden="true"><span class="entry-tag">EVENT</span></div><div class="entry-body"><p class="x-eyebrow">2027 NEW YEAR</p><h2 class="entry-title">2027 신년운세</h2><p class="entry-lead">내 사주로 보는 2027년 열두 달의 흐름을<br>한 권의 리포트로 받아 보세요.</p><div class="entry-count"><span>이벤트 마감까지</span><b>${d?'D-'+d:'오늘 마감'}</b></div>${EXTRA_DATA.bundle?'<div class="entry-bundle"><b>첫 구매 묶음 할인</b><span>처음 구매하시는 분이 2개 이상 함께 사면<br>전부 10% 할인해 드려요.</span></div>':''}<a class="x-cta entry-go" href="#${link(p)}">신년운세 보러 가기</a><button type="button" class="entry-hide" data-entry-hide>오늘 하루 보지 않기</button></div></div>`,'entry-modal','이벤트 안내');
 m.querySelector('.entry-go').onclick=()=>closeModal();
 m.querySelector('[data-entry-hide]').onclick=()=>{try{localStorage.setItem('unmyeong.entryHide',today)}catch{}closeModal()};
}

// 11. 무료 결과 공유 이미지: 좋은 운 3개만 담은 세로 그림(1080×1920)을 손님 폰에서 만든다. 이름·생일·시간은 넣지 않는다.
async function tasterShareImage(r){
 const W=1080,H=1920,c=document.createElement('canvas');c.width=W;c.height=H;const g=c.getContext('2d');
 const sans=(w,px)=>`${w} ${px}px "Pretendard Variable",Pretendard,sans-serif`,serif=px=>`700 ${px}px "Noto Serif KR","Noto Serif CJK KR",Georgia,serif`;
 try{await Promise.all([document.fonts.load(serif(80),'나의좋은운'),document.fonts.ready])}catch{}
 const GOLD='#d8bb78',GOLD2='#f0d896';
 const bg=g.createRadialGradient(W/2,560,80,W/2,900,1300);bg.addColorStop(0,'#2a2114');bg.addColorStop(.55,'#120f0a');bg.addColorStop(1,'#050505');g.fillStyle=bg;g.fillRect(0,0,W,H);
 // 두 겹 금색 테두리 + 모서리 장식
 g.strokeStyle=GOLD;g.lineWidth=2.5;g.strokeRect(54,54,W-108,H-108);g.strokeStyle=GOLD+'55';g.lineWidth=1.5;g.strokeRect(72,72,W-144,H-144);
 g.fillStyle=GOLD;for(const [x,y] of [[54,54],[W-54,54],[54,H-54],[W-54,H-54]]){g.save();g.translate(x,y);g.rotate(Math.PI/4);g.fillRect(-9,-9,18,18);g.restore()}
 const line=(y,w=180)=>{const lg=g.createLinearGradient(W/2-w,0,W/2+w,0);lg.addColorStop(0,GOLD+'00');lg.addColorStop(.5,GOLD);lg.addColorStop(1,GOLD+'00');g.fillStyle=lg;g.fillRect(W/2-w,y,w*2,2)};
 g.textAlign='center';g.textBaseline='alphabetic';
 g.fillStyle=GOLD;g.font=sans(600,34);g.letterSpacing='10px';g.fillText('運命書齋 · 운명서재',W/2,200);g.letterSpacing='0px';
 line(240);
 const day=r.pillars?.[1]?.ko,hanja=r.pillars?.[1]?.hanja;
 g.fillStyle='#ffffff';g.font=serif(96);g.fillText(day?`나는 ${day}일주`:'나의 좋은 운',W/2,390);
 if(hanja){g.fillStyle=GOLD+'cc';g.font=serif(46);g.fillText(hanja+'日柱',W/2,462)}
 g.fillStyle=GOLD2;g.font=sans(800,46);g.fillText('내 사주의 좋은 운 TOP 3',W/2,600);
 r.good.slice(0,3).forEach((a,n)=>{const y=660+n*270,x=150,w=W-300,h=220;
  const cg=g.createLinearGradient(0,y,0,y+h);cg.addColorStop(0,'#ffffff12');cg.addColorStop(1,'#ffffff05');g.fillStyle=cg;
  g.beginPath();g.roundRect?g.roundRect(x,y,w,h,30):g.rect(x,y,w,h);g.fill();g.strokeStyle=GOLD+'66';g.lineWidth=2;g.stroke();
  g.fillStyle=GOLD;g.beginPath();g.arc(x+110,y+h/2,52,0,Math.PI*2);g.fill();
  g.fillStyle='#1a140a';g.font=serif(52);g.fillText(String(n+1),x+110,y+h/2+18);
  g.textAlign='left';g.fillStyle='#ffffff';g.font=sans(800,62);g.fillText(a.title,x+200,y+h/2+40);
  g.fillStyle='#bdb5a6';g.font=sans(500,30);g.fillText(n?'좋은 운':'가장 강한 운',x+200,y+h/2-40);g.textAlign='center'});
 line(1520,240);
 g.fillStyle='#e9e2d4';g.font=sans(600,42);g.fillText('나의 좋은 운도 무료로 확인해 보세요',W/2,1620);
 g.fillStyle=GOLD2;g.font=sans(800,54);g.fillText('unmyeong-saju.com',W/2,1712);
 return await new Promise(res=>c.toBlob(res,'image/png'));
}
async function shareTaster(r,btn){
 btn.disabled=true;
 try{const blob=await tasterShareImage(r),file=new File([blob],'운명서재-나의-좋은운.png',{type:'image/png'});
  if(navigator.canShare?.({files:[file]})){try{await navigator.share({files:[file],text:'나의 좋은 운 TOP 3 · 운명서재 무료 사주 분석 https://unmyeong-saju.com/#/taster'})}catch(e){if(e.name!=='AbortError')throw e}}
  else{const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=file.name;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),5000);toast('그림을 내려받았어요. 카톡이나 인스타에 올려 보세요.')}}
 catch(e){console.error(e);toast('그림을 만들지 못했어요. 잠시 뒤 다시 눌러 주세요.')}
 finally{btn.disabled=false}
}

// 버튼들은 화면이 새로 그려져도 동작하도록 문서 전체에서 한 번만 받는다.
document.addEventListener('click',e=>{
 const t=e.target.closest('[data-toc-toggle],[data-pv],[data-taster-share]');if(!t)return;
 if(t.matches('[data-toc-toggle]')){const sec=t.closest('.toc-x'),open=t.dataset.open!=='1';sec.querySelectorAll('.toc-more').forEach(a=>a.hidden=!open);t.dataset.open=open?'1':'';t.querySelector('span').textContent=open?'목차 접기':'목차 전체 보기';if(!open)sec.scrollIntoView({behavior:'smooth'})}
 if(t.matches('[data-pv]'))previewModal(t.dataset.pvProduct,Number(t.dataset.pv));
 if(t.matches('[data-taster-share]')&&tasterState.result)shareTaster(tasterState.result,t);
});
// 미리보기를 옆으로 넘길 때 아래 점이 따라 움직인다.
document.addEventListener('scroll',e=>{const r=e.target;if(!r.matches?.('[data-pv-rail]'))return;const w=r.firstElementChild?.offsetWidth||1,n=Math.round(r.scrollLeft/(w+12));r.nextElementSibling?.querySelectorAll('i').forEach((d,k)=>d.classList.toggle('on',k===n))},true);

// 2단계 할인 (2026-10-27 사장님 결정). 할인은 모두 10%이고 한 주문에 하나만(더하지 않음). 금액은 서버(/api/quote)가 계산한다.
// 9·10. 첫 구매 묶음 할인: 처음 사는 분이 2개 이상 함께 사면 전부 10%.  12. 친구 초대(?ref=)  16. 재구매 코드(?coupon=)
const BUNDLE_IDS=['newyear','lifetime','romance','wealth','career','business','health'];
(()=>{try{const q=new URLSearchParams(location.search),ref=q.get('ref'),cp=q.get('coupon');
 if(ref)localStorage.setItem('unmyeong.ref',JSON.stringify({code:ref.slice(0,20),at:Date.now()}));
 if(cp)localStorage.setItem('unmyeong.coupon',cp.slice(0,20).toUpperCase());}catch{}})();
function savedRef(){try{const r=JSON.parse(localStorage.getItem('unmyeong.ref'));return r&&Date.now()-r.at<30*864e5?r.code:''}catch{return ''}}
function savedCoupon(){try{return localStorage.getItem('unmyeong.coupon')||''}catch{return ''}}
function bundleBlock(p,d){
 if(!EXTRA_DATA.bundle)return '';
 const others=BUNDLE_IDS.filter(id=>id!==p.id).map(id=>PRODUCTS.find(x=>x.id===id)).filter(Boolean),on=new Set(d.extras||[]);
 const ea=d.extraAnswers||(d.extraAnswers={});
 const qs=x=>FLOWS[x.id].filter(st=>st.type==='choice'&&st.required).map(st=>{
  const mine=d.answers?.[st.id];if(!ea[x.id]?.[st.id]&&mine&&st.options.includes(mine))(ea[x.id]||(ea[x.id]={}))[st.id]=mine;
  const cur=ea[x.id]?.[st.id]||'';
  return `<label class="bundle-ask"><span>${esc(st.title)}</span><select data-extra-q="${x.id}" data-step="${st.id}"><option value="">선택해주세요</option>${st.options.map(o=>`<option${o===cur?' selected':''}>${esc(o)}</option>`).join('')}</select></label>`}).join('');
 return `<section class="bundle-x"><span class="x-eyebrow">FIRST ORDER</span><h2 class="x-title">첫 구매 묶음 할인 <em>10%</em></h2><p class="x-sub">처음 구매하시는 분이 2개 이상 함께 사면 <b>전부 10% 할인</b>돼요. 같은 출생 정보로 리포트를 한 권씩 따로 보내드려요.</p><div class="bundle-list">${others.map(x=>{const q=qs(x);return `<div class="bundle-row"><label class="bundle-item"><input type="checkbox" name="extra" value="${x.id}"${on.has(x.id)?' checked':''}><span class="bundle-name">${esc(x.name.replace(/^금월선녀의\s*/,''))}</span><span class="bundle-price">${money(x.price)}</span></label>${q?`<div class="bundle-q">${q}</div>`:''}</div>`}).join('')}</div></section>`;
}
const QUOTE_NOTES={EXTRA_ANSWERS:'함께 살 리포트의 질문에 답해주시면 금액에 담겨요.',BUNDLE_FIRST_ONLY:'묶음 할인은 첫 구매 때만 돼요. 이 이메일로 구매하신 적이 있어요.',EMAIL_FOR_DISCOUNT:'이메일을 넣으면 첫 구매인지 확인해서 묶음 할인을 적용해 드려요.'};
function quoteBox(p,q){
 if(!q)return priceBox(p,0);
 const items=q.items.map(it=>PRODUCTS.find(x=>x.id===it.id)||{...it,original:it.price}),orig=items.reduce((a,x)=>a+x.original,0);
 const list=items.length>1?`<div class="qb-items">${items.map(x=>`<div><span>${esc(x.name.replace(/^금월선녀의\s*/,''))}</span><span>${money(x.price)}</span></div>`).join('')}</div>`:'';
 const dc=q.discount?`<div class="qb-disc"><span>${esc(q.discount.label)} <em>${q.discount.percent}%</em></span><strong>−${money(q.discount.amount)}</strong></div>`:'';
 const notes=[...(q.notes||[]),...(q.missing?['EXTRA_ANSWERS']:[])].filter(n=>QUOTE_NOTES[n]).map(n=>`<p class="qb-note">${QUOTE_NOTES[n]}</p>`).join('');
 return `<div class="price-box">${list}<div><span>정가</span><s>${money(orig)}</s></div><div><span>상품 할인</span><strong>−${money(orig-q.base)}</strong></div>${dc}<div class="price-total"><span>최종 금액</span><strong>${money(q.amount)}</strong></div></div>${notes}`;
}
let quoteSeq=0;
async function refreshQuote(p,d){
 const seq=++quoteSeq,box=document.querySelector('#checkout-price'),msg=document.querySelector('#coupon-message');if(!box)return;
 let q=null;try{const r=await fetch('/api/quote',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({...d,productId:p.id,email:d.email||'',extras:d.extras||[],coupon:d.coupon||'',ref:savedRef()}),signal:AbortSignal.timeout(15000)});if(r.ok)q=await r.json()}catch{}
 if(seq!==quoteSeq||!box.isConnected)return;
 if(q&&d.coupon&&q.notes?.includes('COUPON_INVALID')){if(msg){msg.textContent='사용할 수 없는 코드예요. 이미 썼거나 기한이 지났을 수 있어요.';msg.classList.add('error')}d.coupon='';try{localStorage.removeItem('unmyeong.coupon')}catch{}save();return refreshQuote(p,d)}
 if(q&&msg&&d.coupon&&q.discount?.code){msg.textContent=`${q.discount.label} ${q.discount.percent}%가 적용됐어요.`;msg.classList.remove('error')}
 if(q)q.missing=(d.extras||[]).some(id=>!q.items.some(i=>i.id===id));
 box.innerHTML=quoteBox(p,q);
}
function bindDiscounts(p,d){
 const form=document.querySelector('#checkout-form');if(!form)return;
 if(!d.coupon&&savedCoupon())d.coupon=savedCoupon();
 const coupon=form.elements.coupon;if(coupon&&d.coupon)coupon.value=d.coupon;
 delete d.discount;
 document.querySelectorAll('.bundle-x input[name=extra]').forEach(b=>b.onchange=()=>{d.extras=[...document.querySelectorAll('.bundle-x input[name=extra]:checked')].map(x=>x.value);save();refreshQuote(p,d)});
 document.querySelectorAll('[data-extra-q]').forEach(sel=>sel.onchange=()=>{const ea=d.extraAnswers||(d.extraAnswers={});(ea[sel.dataset.extraQ]||(ea[sel.dataset.extraQ]={}))[sel.dataset.step]=sel.value;save();refreshQuote(p,d)});
 const mk=form.elements.marketing;if(mk){mk.checked=d.marketing===true;mk.onchange=()=>{d.marketing=mk.checked;save()}}
 let t;form.elements.email.addEventListener('input',()=>{clearTimeout(t);t=setTimeout(()=>refreshQuote(p,d),600)});
 document.querySelector('#apply-coupon').onclick=()=>{d.coupon=coupon.value.trim().toUpperCase();save();refreshQuote(p,d)};
 refreshQuote(p,d);
}
