(()=>{
'use strict';
const VERSION='31.2.1';
const NAV=[
 ['index.html','Dashboard'],['cockpit.html','Cockpit'],['research.html','Research'],
 ['discovery.html','Discovery'],['research_hub.html','Research Hub'],
 ['research_intelligence.html','Intelligence'],['validation.html','Validation'],
 ['research_queue.html','Research Queue'],['data.html','Data'],['more.html','More']
];
const TOOLS=[['explainability.html','Why this decision'],['timeline.html','Timeline'],['integrity.html','Data integrity']];
const BAD=[['Â·','·'],['â†’','→'],['â†','←'],['â€”','—'],['â€“','–'],['â—','●'],['â˜°','☰'],['Ã‚',''],['Â',''],['`r`n','']];
function clean(root=document.body){const w=document.createTreeWalker(root,NodeFilter.SHOW_TEXT);let n;while(n=w.nextNode()){let v=n.nodeValue;for(const [a,b] of BAD)v=v.split(a).join(b);if(v!==n.nodeValue)n.nodeValue=v}}
function current(){return (location.pathname.split('/').pop()||'index.html').toLowerCase()}
function link(h,l){const a=document.createElement('a');a.href=h;a.textContent=l;if(current()===h)a.className='active';return a}
function rebuildNav(){
 const first=document.querySelector('.v20-nav,.v24-primary-nav,nav.nav');
 if(first){first.className='crm-main-nav';first.replaceChildren(...NAV.map(x=>link(...x)))}
 document.querySelectorAll('.v20-nav,.v24-primary-nav,nav.nav').forEach((n,i)=>{if(i>0)n.remove()});
 const tools=document.querySelector('.v20-tools,.v24-tools');
 if(tools){tools.className='crm-tool-nav';tools.replaceChildren(...TOOLS.map(x=>link(...x)))}
 document.querySelectorAll('.v20-tools,.v24-tools').forEach((n,i)=>{if(i>0)n.remove()});
}
function versions(){document.querySelectorAll('.version,.v22-version,[id="version"]').forEach(e=>e.textContent='V'+VERSION);document.title=document.title.replace(/V\d+(?:\.\d+)*/g,'V'+VERSION)}
window.crmFetchJson=async function(name,options={}){
 const stamp=Date.now();
 const cleanName=String(name).replace(/^\.\//,'').split('?')[0];
 const urls=[
  './'+cleanName+'?v=31.2.1&t='+stamp,
  '/Crypto-regime-manager/'+cleanName+'?v=31.2.1&t='+(stamp+1),
  'https://raw.githubusercontent.com/aferguson227/Crypto-regime-manager/main/docs/'+cleanName+'?t='+(stamp+2)
 ];
 const errors=[];
 for(let i=0;i<urls.length;i++){
  try{
   const r=await fetch(urls[i],{...options,cache:'no-store',headers:{...(options.headers||{}),'Accept':'application/json'}});
   const text=await r.text();
   if(!r.ok)throw new Error(`HTTP ${r.status}`);
   if(!text.trim())throw new Error('empty response');
   return JSON.parse(text);
  }catch(e){errors.push(`attempt ${i+1}: ${e.message}`);if(i<urls.length-1)await new Promise(ok=>setTimeout(ok,350*(i+1)))}
 }
 throw new Error(`${cleanName} could not be loaded. ${errors.join(' | ')}`);
};
function fixFloating(){document.querySelectorAll('a[href="index.html"],button').forEach(e=>{if(/dashboard/i.test(e.textContent||'')&&getComputedStyle(e).position==='fixed')e.classList.add('crm-floating-dashboard')})}
function boot(){clean();rebuildNav();versions();fixFloating();setTimeout(()=>{clean();rebuildNav();versions();fixFloating()},600)}
document.readyState==='loading'?document.addEventListener('DOMContentLoaded',boot):boot();
})();
