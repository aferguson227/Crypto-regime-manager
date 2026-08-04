(() => {
  const CHECK_MS = 5 * 60 * 1000;
  let knownSnapshot = null;
  const getJson = async p => {
    const r = await fetch(`${p}?t=${Date.now()}`, {cache:'no-store'});
    if (!r.ok) throw new Error(`${p} HTTP ${r.status}`);
    return r.json();
  };
  async function checkCloud(reloadOnChange=false) {
    try {
      const [cloud, strategies] = await Promise.all([getJson('cloud_status.json'), getJson('strategies.json')]);
      const snapshot = strategies.generated_at || cloud.latest_strategy_snapshot;
      const state = String(cloud.state || 'unknown').toLowerCase();
      document.documentElement.dataset.cloudState = state;
      let badge = document.getElementById('v25-cloud-badge');
      if (!badge) {
        badge = document.createElement('a');
        badge.id = 'v25-cloud-badge';
        badge.href = 'cloud.html';
        badge.className = 'v25-cloud-badge';
        document.body.appendChild(badge);
      }
      badge.textContent = state === 'healthy' ? '● Cloud refresh healthy' : state === 'running' ? '● Cloud refresh running' : state.includes('await') ? '● Cloud setup pending' : '● Cloud refresh review';
      badge.title = cloud.completed_at ? `Last cloud run: ${cloud.completed_at}` : 'Open cloud status';
      if (reloadOnChange && knownSnapshot && snapshot && snapshot !== knownSnapshot) location.reload();
      knownSnapshot = snapshot || knownSnapshot;
    } catch (_) { /* dashboard data remains usable offline */ }
  }
  document.addEventListener('visibilitychange', () => { if (!document.hidden) checkCloud(true); });
  window.addEventListener('focus', () => checkCloud(true));
  window.addEventListener('load', () => { checkCloud(false); setInterval(() => checkCloud(true), CHECK_MS); });
})();
