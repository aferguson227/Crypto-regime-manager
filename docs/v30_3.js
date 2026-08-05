(() => {
  const VERSION = 'V30.3.0';
  const fixes = new Map([
    ['·','·'],['Â',''],['←','←'],['→','→'],['—','—'],['…','…'],['`r`n','']
  ]);
  function cleanText(root=document.body){
    const w=document.createTreeWalker(root,NodeFilter.SHOW_TEXT); let n;
    while((n=w.nextNode())){
      let v=n.nodeValue;
      fixes.forEach((to,from)=>{v=v.split(from).join(to)});
      if(v!==n.nodeValue)n.nodeValue=v;
    }
  }
  function version(){
    document.querySelectorAll('.version,.version-badge,.v22-version,[data-version]').forEach(el=>{
      if(/^V(?:15(?:\.3)?|2[7-9](?:\.0\.0)?|30\.[0-2]\.0)$/i.test(el.textContent.trim())) el.textContent=VERSION;
    });
  }
  function labelPage(){
    if(/backtest_lab\.html$/i.test(location.pathname)) document.body.dataset.page='backtest-lab';
  }
  document.addEventListener('DOMContentLoaded',()=>{labelPage();cleanText();version();});
  const observer=new MutationObserver(()=>{cleanText();version()});
  window.addEventListener('load',()=>observer.observe(document.body,{subtree:true,childList:true}));
})();
