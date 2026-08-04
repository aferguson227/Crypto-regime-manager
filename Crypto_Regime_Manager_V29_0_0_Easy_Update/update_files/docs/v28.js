(() => {
 const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c]));
 const fmt=(n,d=0)=>Number.isFinite(Number(n))?Number(n).toLocaleString(undefined,{maximumFractionDigits:d}):'—';
 function standardiseNav(){
   document.querySelectorAll('.nav,.v23-primary-nav,.v24-primary-nav').forEach(nav=>{
     const links=[...nav.querySelectorAll('a')]; if(!links.length)return;
     const order=['Dashboard','Cockpit','Research','Discovery','Validation','Queue','Data','More'];
     const map=new Map(links.map(a=>[a.textContent.trim().replace('Research Queue','Queue'),a]));
     order.forEach(label=>{const a=map.get(label);if(a)nav.appendChild(a)});
   });
 }
 async function enhanceDashboard(){
   if(!document.getElementById('portfolio'))return;
   try{
     const r=await fetch('decision_intelligence_v28.json?t='+Date.now(),{cache:'no-store'}); if(!r.ok)return;
     const d=await r.json(), best=d.best_setup, p=d.pipeline||{};
     const portfolio=document.getElementById('portfolio'); if(!portfolio)return;
     const h=portfolio.querySelector('h2'); const sub=h?.nextElementSibling;
     if(h)h.textContent=best?'Best setup: '+best.symbol:'No eligible setup';
     if(sub)sub.textContent=best?`${best.recommended_bot||'Configured bot'} · unified score ${fmt(best.decision_score,0)}/100`:'All production entries are blocked.';
     const card=document.createElement('section');card.className='v28-sync-card';
     card.innerHTML=`<h3>Unified decision engine</h3><div class="muted">Production, discovery, validation and research priorities are synchronised after every cloud refresh.</div><div class="v28-sync-grid"><div class="v28-sync-item"><span>Production ranked</span><strong>${fmt(p.production_assets)}</strong></div><div class="v28-sync-item"><span>Eligible now</span><strong>${fmt(p.eligible_production)}</strong></div><div class="v28-sync-item"><span>Discovery candidates</span><strong>${fmt(p.discovery_candidates)}</strong></div><div class="v28-sync-item"><span>Validation candidates</span><strong>${fmt(p.validation_candidates)}</strong></div></div><div class="v28-policy"><strong class="v28-proof">Evidence loop active.</strong> Discovery can prioritise research, but only independently validated and manually approved strategies can enter production ranking.</div>`;
     portfolio.insertAdjacentElement('afterend',card);
   }catch(_e){}
 }
 function badgeSpacing(){const b=document.getElementById('v25-cloud-badge');if(!b)return;b.parentElement?.classList.add('v27-reserved-after-badge');}
 window.addEventListener('load',()=>{standardiseNav();badgeSpacing();enhanceDashboard();setTimeout(()=>{standardiseNav();badgeSpacing()},400)});
})();
