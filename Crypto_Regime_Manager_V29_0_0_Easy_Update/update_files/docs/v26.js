(() => {
  const CHECK_MS = 5 * 60 * 1000;
  let knownSnapshot = null;
  const getJson = async p => {
    const r = await fetch(`${p}?t=${Date.now()}`, {cache:'no-store'});
    if (!r.ok) throw new Error(`${p} HTTP ${r.status}`);
    return r.json();
  };
  const parseDate = value => {
    if (!value) return null;
    const d = new Date(value);
    return Number.isNaN(d.getTime()) ? null : d;
  };
  const zoneName = date => {
    if (!date) return '';
    const parts = new Intl.DateTimeFormat(undefined,{timeZoneName:'short'}).formatToParts(date);
    return parts.find(x=>x.type==='timeZoneName')?.value || '';
  };
  const formatLocal = (value, withDate=true) => {
    const d=parseDate(value); if(!d) return '—';
    const opts=withDate ? {day:'numeric',month:'short',year:'numeric',hour:'2-digit',minute:'2-digit'} : {hour:'2-digit',minute:'2-digit'};
    return `${new Intl.DateTimeFormat(undefined,opts).format(d)} ${zoneName(d)}`.trim();
  };
  const relative = value => {
    const d=parseDate(value); if(!d) return 'No completed run';
    const sec=Math.round((d-Date.now())/1000), abs=Math.abs(sec);
    const unit=abs<90?'second':abs<5400?'minute':abs<129600?'hour':'day';
    const div=unit==='second'?1:unit==='minute'?60:unit==='hour'?3600:86400;
    return new Intl.RelativeTimeFormat(undefined,{numeric:'auto'}).format(Math.round(sec/div),unit);
  };
  const freshness = value => {
    const d=parseDate(value); if(!d) return 'unknown';
    const hours=(Date.now()-d)/36e5;
    return hours<=5?'fresh':hours<=9?'stale':'critical';
  };
  window.V26Time={parseDate,formatLocal,relative,freshness,zoneName};
  document.querySelectorAll('[data-utc-time]').forEach(el=>el.textContent=formatLocal(el.dataset.utcTime));
  async function checkCloud(reloadOnChange=false) {
    try {
      const [cloud, strategies] = await Promise.all([getJson('cloud_status.json'), getJson('strategies.json')]);
      const snapshot = strategies.generated_at || cloud.latest_strategy_snapshot;
      const state = String(cloud.state || 'unknown').toLowerCase();
      const ageState=freshness(cloud.completed_at);
      document.documentElement.dataset.cloudState = state;
      document.documentElement.dataset.cloudFreshness = ageState;
      let badge = document.getElementById('v25-cloud-badge');
      if (!badge) {
        badge = document.createElement('a'); badge.id='v25-cloud-badge'; badge.href='cloud.html'; badge.className='v25-cloud-badge'; document.body.appendChild(badge);
      }
      badge.textContent = state === 'healthy' ? `● Cloud healthy · ${relative(cloud.completed_at)}` : state === 'running' ? '● Cloud refresh running' : state.includes('await') ? '● Cloud setup pending' : '● Cloud refresh review';
      badge.title = cloud.completed_at ? `Last cloud run: ${formatLocal(cloud.completed_at)}` : 'Open cloud status';
      if (reloadOnChange && knownSnapshot && snapshot && snapshot !== knownSnapshot) location.reload();
      knownSnapshot = snapshot || knownSnapshot;
    } catch (_) { /* published dashboard remains usable offline */ }
  }
  document.addEventListener('visibilitychange',()=>{if(!document.hidden)checkCloud(true)});
  window.addEventListener('focus',()=>checkCloud(true));
  window.addEventListener('load',()=>{checkCloud(false);setInterval(()=>checkCloud(true),CHECK_MS)});
})();
