(() => {
  const dense = document.body?.dataset?.v27Dense === 'true';
  const moveBadgeInline = () => {
    if (!dense) return;
    const badge = document.getElementById('v25-cloud-badge');
    if (!badge || badge.dataset.v27Placed) return;
    const context = document.querySelector('.v24-context-nav,.v23-context-nav');
    const primary = document.querySelector('.v24-primary-nav,.v23-primary-nav');
    const anchor = context || primary;
    if (anchor) anchor.insertAdjacentElement('afterend', badge);
    badge.dataset.v27Placed='true';
  };
  const observer = new MutationObserver(moveBadgeInline);
  observer.observe(document.documentElement,{childList:true,subtree:true});
  window.addEventListener('load',()=>{moveBadgeInline();setTimeout(moveBadgeInline,250)});
})();
