(()=>{const V='46.0.0';const pages=[['Dashboard','index.html'],['Bots','bots.html'],['Market','market.html'],['System','health.html'],['Engineering','engineering.html']];const path=(location.pathname.split('/').pop()||'index.html').toLowerCase();document.querySelectorAll('.workspace-nav,.v20-nav,.v20-tools').forEach(n=>n.remove());document.querySelectorAll('header nav').forEach(n=>{if(!n.classList.contains('crm-global-nav'))n.remove()});document.querySelectorAll('.crm-global-nav').forEach((n,i)=>{if(i)n.remove()});if(!document.querySelector('.crm-global-nav')){const nav=document.createElement('nav');nav.className='crm-global-nav';nav.setAttribute('aria-label','Primary');nav.innerHTML=`<a class="crm-brand crm-home-link" href="index.html">Crypto Regime Manager <small>V${V}</small></a><div class="crm-nav-links">${pages.map(([n,h])=>`<a href="${h}" ${path===h?'aria-current="page"':''}>${n}</a>`).join('')}</div>`;document.body.prepend(nav)}window.CRMFormat={number(v,d=2){if(v===null||v===undefined||v==='')return'Unknown';const n=Number(v);return Number.isFinite(n)?new Intl.NumberFormat('en-GB',{maximumFractionDigits:d}).format(n):'Unknown'},percent(v,d=1){const x=this.number(v,d);return x==='Unknown'?x:`${x}%`},asset(v,a,d=4){const x=this.number(v,d);return x==='Unknown'?x:`${x} ${a||''}`.trim()},quote(v,c='USDT',d=2){const x=this.number(v,d);return x==='Unknown'?x:`${x} ${c}`},money(v,c='USDT',d=2){return this.quote(v,c,d)},datetime(v){if(!v)return'Unknown';const d=new Date(v);return Number.isNaN(d.valueOf())?'Unknown':new Intl.DateTimeFormat('en-GB',{dateStyle:'medium',timeStyle:'short',timeZone:'Europe/London'}).format(d)+' UK'},ageMinutes(v){if(!v)return null;const d=new Date(v);if(Number.isNaN(d.valueOf()))return null;return Math.max(0,(Date.now()-d.valueOf())/60000)},minus(v){return String(v).replace(/^-/,'−')}};document.documentElement.dataset.crmVersion=V;if(!document.querySelector('script[src*="self-healing.js"]')){const x=document.createElement('script');x.src='self-healing.js?v=46.0.0';x.defer=true;document.head.append(x)}})();

/* V46 dashboard recovery: resize only designated values, never ordinary labels/notes. */
(()=>{
 const MIN=13;
 function fit(el){
   if(!el||!el.parentElement)return;
   el.style.fontSize='';
   let size=parseFloat(getComputedStyle(el).fontSize)||24;
   const available=Math.max(48,el.parentElement.clientWidth-12);
   el.style.whiteSpace='normal';el.style.wordBreak='normal';el.style.overflowWrap='normal';
   while(el.scrollWidth>available&&size>MIN){size-=1;el.style.fontSize=size+'px'}
 }
 function scan(){document.querySelectorAll('.crm-fit-text,.crm-big,.metric-value,.metric strong').forEach(fit)}
 document.addEventListener('DOMContentLoaded',()=>{scan();setTimeout(scan,150)});
 window.addEventListener('resize',()=>requestAnimationFrame(scan));
 if('ResizeObserver'in window){new ResizeObserver(()=>requestAnimationFrame(scan)).observe(document.documentElement)}
 window.CRMFitText={scan,fit};
})();
