// 사이트 추가 기능 1단계 (2026-10-27 사장님 선택): 목차 펼쳐보기, 리포트 미리보기, 신년 이벤트 남은 날짜와 첫 화면 팝업,
// 무료 결과 공유 이미지. build_site.py 가 EXTRA_DATA 와 함께 사이트 코드 안에 넣는다.

// 18. 목차 펼쳐보기: 실제 리포트 목차(saju/report 의 SECTIONS)를 처음 5장만 보여 주고 나머지는 버튼으로 편다.
function tocBlock(p){
 const toc=EXTRA_DATA.toc[p.id]||[];if(!toc.length)return '';
 const card=(c,n)=>`<article class="chapter${n>=5?' toc-more':''}"${n>=5?' hidden':''}><span>${String(c[0]).padStart(2,'0')}</span><h3>${esc(c[1])}</h3>${c[2]?`<p>${esc(c[2])}</p>`:''}</article>`;
 return `<section class="chapters"><span class="eyebrow">CONTENTS</span><h2 class="serif">리포트의 목차</h2>${toc.map(card).join('')}${toc.length>5?`<button type="button" class="toc-toggle" data-toc-toggle>목차 전체 보기 (${toc.length}장)</button>`:''}</section>`;
}

// 2. 리포트 미리보기: 가상의 인물로 만든 실제 리포트에서 뽑은 쪽을 옆으로 넘겨 본다. 누르면 크게 본다.
function previewBlock(p){
 const pages=EXTRA_DATA.preview[p.id]||[];if(!pages.length)return '';
 return `<section class="report-preview"><span class="eyebrow">PREVIEW</span><h2 class="serif">리포트 미리보기</h2><p class="pv-lead">옆으로 넘겨 보세요. 누르면 크게 볼 수 있어요.</p><div class="pv-rail">${pages.map((src,n)=>`<button type="button" class="pv-page" data-pv="${esc(src)}" aria-label="미리보기 ${n+1}쪽 크게 보기"><img src="${esc(src)}" alt="리포트 미리보기 ${n+1}쪽" loading="lazy" decoding="async"></button>`).join('')}</div><p class="pv-note">가상의 인물로 만든 실제 리포트 페이지예요.</p></section>`;
}

// 17. 신년운세 이벤트: 기간 안에만 남은 날짜를 보여 주고, 기간이 끝나면 저절로 사라진다.
function eventDays(now=new Date()){
 const ev=EXTRA_DATA.event;if(!ev||!ev.start||!ev.end)return null;
 const kst=new Date(now.getTime()+9*3600e3).toISOString().slice(0,10);
 if(kst<ev.start||kst>ev.end)return null;
 return Math.round((Date.parse(ev.end)-Date.parse(kst))/864e5);
}
function eventBadge(){const d=eventDays();return d===null?'':`<span class="event-dday">${esc(EXTRA_DATA.event.label)} ${d?'D-'+d:'오늘 마감'}</span>`}

// 첫 화면 팝업 (사장님 2026-10-27): 처음 들어오면 한 번, 신년운세 이벤트 남은 날짜를 띄운다.
// 첫 구매 묶음 할인(2개 이상 10%)은 2단계 할인 장치가 들어가면 EXTRA_DATA.bundle 을 켜서 같이 보여 준다.
function entryPopup(){
 const d=eventDays();if(d===null)return;
 const today=new Date(Date.now()+9*3600e3).toISOString().slice(0,10);
 try{if(sessionStorage.getItem('unmyeong.entry')||localStorage.getItem('unmyeong.entryHide')===today)return;sessionStorage.setItem('unmyeong.entry','1')}catch{}
 const p=pById('newyear');
 const m=modal(`<div class="entry-pop"><span class="entry-tag">EVENT</span><h2>2027 신년운세</h2><p class="entry-dday">이벤트 마감까지 <b>${d?'D-'+d:'오늘 마감'}</b></p><p>내 사주로 보는 2027년 열두 달의 흐름을<br>한 권의 리포트로 받아 보세요.</p>${EXTRA_DATA.bundle?'<p class="entry-bundle">첫 구매라면, 2개 이상 함께 사면<br><b>전부 10% 할인</b>해 드려요.</p>':''}<a class="primary entry-go" href="#${link(p)}">신년운세 보러 가기</a><button type="button" class="entry-hide" data-entry-hide>오늘 하루 보지 않기</button></div>`,'entry-modal','이벤트 안내');
 m.style.setProperty('--entry-bg',"url('assets/geumwol/newyear-cover.webp')");
 m.querySelector('.entry-go').onclick=()=>closeModal();
 m.querySelector('[data-entry-hide]').onclick=()=>{try{localStorage.setItem('unmyeong.entryHide',today)}catch{}closeModal()};
}

// 11. 무료 결과 공유 이미지: 좋은 운 3개만 담은 세로 그림(1080×1920)을 손님 폰에서 만든다. 이름·생일·시간은 넣지 않는다.
async function tasterShareImage(r){
 const W=1080,H=1920,c=document.createElement('canvas');c.width=W;c.height=H;const g=c.getContext('2d');
 const font=(w,px)=>`${w} ${px}px "Pretendard Variable",Pretendard,sans-serif`;
 await document.fonts?.ready;
 const bg=g.createLinearGradient(0,0,0,H);bg.addColorStop(0,'#1b150c');bg.addColorStop(1,'#050505');g.fillStyle=bg;g.fillRect(0,0,W,H);
 g.strokeStyle='#d8bb78';g.lineWidth=3;g.strokeRect(60,60,W-120,H-120);g.strokeStyle='#d8bb7855';g.lineWidth=1.5;g.strokeRect(78,78,W-156,H-156);
 g.textAlign='center';g.fillStyle='#d8bb78';g.font=font(700,40);g.fillText('운명서재 무료 사주 분석',W/2,230);
 const day=r.pillars?.[1]?.ko;g.fillStyle='#fff';g.font=font(800,92);g.fillText(day?`나는 ${day}일주`:'나의 좋은 운',W/2,400);
 g.fillStyle='#f0c75e';g.font=font(700,54);g.fillText('좋은 운 TOP 3',W/2,560);
 r.good.slice(0,3).forEach((a,n)=>{const y=700+n*300;
  g.fillStyle='#ffffff10';g.strokeStyle='#d8bb7866';g.lineWidth=2;g.beginPath();g.roundRect?.(140,y-110,W-280,220,28);g.fill();g.stroke();
  g.fillStyle='#d8bb78';g.font=font(700,40);g.fillText(`${n+1}위`,W/2,y-30);g.fillStyle='#fff';g.font=font(800,60);g.fillText(a.title,W/2,y+55)});
 g.fillStyle='#e5e5e5';g.font=font(600,44);g.fillText('나의 좋은 운도 무료로 확인해 보세요',W/2,1640);
 g.fillStyle='#d8bb78';g.font=font(800,52);g.fillText('unmyeong-saju.com',W/2,1730);
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
 if(t.matches('[data-toc-toggle]')){const sec=t.closest('.chapters'),open=t.dataset.open!=='1';sec.querySelectorAll('.toc-more').forEach(a=>a.hidden=!open);t.dataset.open=open?'1':'';t.textContent=open?'목차 접기':`목차 전체 보기 (${sec.querySelectorAll('.chapter').length}장)`;if(!open)sec.scrollIntoView({behavior:'smooth'})}
 if(t.matches('[data-pv]'))modal(`<img class="pv-big" src="${esc(t.dataset.pv)}" alt="리포트 미리보기 크게 보기">`,'pv-modal','리포트 미리보기');
 if(t.matches('[data-taster-share]')&&tasterState.result)shareTaster(tasterState.result,t);
});
