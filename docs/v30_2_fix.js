(() => {
  const VERSION = 'V30.2.0';
  const replaceText = (root, from, to) => {
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    let n; while ((n = walker.nextNode())) if (n.nodeValue && n.nodeValue.trim() === from) n.nodeValue = n.nodeValue.replace(from,to);
  };
  document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.version, .version-badge, [data-version]').forEach(el => {
      if (/^V(?:15\.3|30\.1\.0)$/i.test(el.textContent.trim())) el.textContent = VERSION;
    });
    replaceText(document.body, 'Data age', 'Candle data age');
    document.querySelectorAll('*').forEach(el => {
      if (el.childElementCount===0 && el.textContent.trim()==='Candle data age') {
        el.title='Age of the latest completed market candle used by the strategy-health calculation; this is not the cloud heartbeat age.';
      }
    });
  });
})();
