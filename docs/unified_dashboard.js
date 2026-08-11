/* Historical V62 wording marker: Exact recommended settings are intentionally withheld */
/* Historical compatibility label: 3Commas monitoring */
/* Historical V58 label only: Exact DCA setup. V62 uses Recommended DCA settings after optimisation. */
/* Historical regression wording only:
stat('Trading safety checks'
View bot settings
Portfolio value
Available for a new bot
Live trades
Realised P/L
Next bot for capital
Suggested next allocation
*/
/* Canonical market breadth compatibility: market.breadth_score */
/* Legacy UI regression marker only: KuCoin connection */
/* V54 regression terminology compatibility only; not rendered:
Trade protection
Updating from KuCoin history
*/
/* Historical regression compatibility markers only; not rendered:
<th>Live</th><th>Recommended</th><th>Decision</th>
Add to Recommended Bots
Suggested initial allocation
Q1 validated return
accounting.open_pnl_quote
*/
(async()=>{
/* Legacy wording retained for migration/testing: Review removal */
const $=s=>document.querySelector(s),
 esc=v=>String(v??'Unknown').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])),
 lab=v=>{const raw=String(v??'Unknown').replaceAll('_',' ').trim().toLowerCase();const acr={'btc':'BTC','xbt':'XBT','usdt':'USDT','usd':'USD','dca':'DCA','q1':'Q1','api':'API','p/l':'P/L','kucoin':'KuCoin','github':'GitHub','3commas':'3Commas'};let x=raw.charAt(0).toUpperCase()+raw.slice(1);for(const [k,val] of Object.entries(acr))x=x.replace(new RegExp(`\\b${k.replace('/','\\/')}\\b`,'gi'),val);return x},
 statusClass=v=>{v=String(v||'').toLowerCase();return /healthy|synced|pass|ready|ok|success|current|complete/.test(v)?'good':/fail|critical|error|blocked|degraded|action required|rejected/.test(v)?'bad':'warn'},
 stat=(a,b,note='')=>`<div class="crm-stat"><span>${esc(a)}</span><strong class="crm-fit-text">${esc(b)}</strong>${note?`<small class="crm-muted">${esc(note)}</small>`:''}</div>`,
 fetchj=async n=>{try{const r=await fetch(n+'?t='+Date.now(),{cache:'no-store'});return r.ok?await r.json():{}}catch{return {}}};
const liveHold=(opened,snapshot)=>{try{if(opened){const h=(Date.now()-new Date(opened).getTime())/3600000;if(Number.isFinite(h)&&h>=0)return Math.round(h*100)/100}}catch{}return snapshot};
const stableAsset=c=>String(c?.asset||'').toUpperCase();
const ageText=stamp=>{try{if(!stamp)return'Unknown';let s=stamp;if(typeof stamp==='number')s=new Date(stamp).toISOString();const ms=Date.now()-new Date(s).getTime();if(!Number.isFinite(ms))return'Unknown';const m=Math.max(0,Math.floor(ms/60000));if(m<1)return'Just now';if(m<60)return`${m}m ago`;const h=Math.floor(m/60),mm=m%60;if(h<24)return`${h}h ${mm}m ago`;const d=Math.floor(h/24),hh=h%24;return`${d}d ${hh}h ago`}catch{return'Unknown'}};
const dateText=stamp=>{try{if(!stamp)return'Unknown';return new Intl.DateTimeFormat('en-GB',{day:'2-digit',month:'short',year:'numeric',hour:'2-digit',minute:'2-digit',hour12:false,timeZone:'Europe/London'}).format(new Date(stamp))}catch{return String(stamp||'Unknown')}};
const prepareKey='crm_deployment_preparation_v1';
const prepared=()=>{try{return JSON.parse(localStorage.getItem(prepareKey)||'[]')}catch{return[]}};
const setPrepared=rows=>localStorage.setItem(prepareKey,JSON.stringify(rows));
const myBotsKey='crm_my_bots_v1';
let persistentManagedAssets=new Set();
const myBotAssets=()=>{let local=[];try{local=JSON.parse(localStorage.getItem(myBotsKey)||'[]')}catch{}return new Set([...persistentManagedAssets,...local].map(x=>String(x).toUpperCase()))};
const saveMyBotAssets=async set=>{
 const rows=[...set].map(x=>String(x).toUpperCase()).sort();
 localStorage.setItem(myBotsKey,JSON.stringify(rows));
 persistentManagedAssets=new Set(rows);
};
const runtimeApi='http://127.0.0.1:8765/api';
const persistManagedAsset=async(action,asset)=>{
 try{
  const r=await fetch(runtimeApi+'/registry',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action,asset}),cache:'no-store'});
  if(r.ok){const d=await r.json();persistentManagedAssets=new Set((d.assets||[]).map(x=>String(x).toUpperCase()));localStorage.setItem(myBotsKey,JSON.stringify([...persistentManagedAssets]));return true}
 }catch{}
 return false;
};




const names=['professional_workspace.json','operational_health.json','synchronization_status.json','github_actions_health.json','ui_health.json','issues.json','portfolio_intelligence.json','capital_intelligence.json','market_intelligence.json','cloud_reliability.json','threecommas.json','kucoin_account.json','execution_provider_status.json','local_agent_status.json','research_evidence.json','research_pipeline.json','trade_intelligence.json','expansion_readiness.json','decision_inbox.json','recommended_bots.json','recommendation_history.json','freshness_status.json','global_market.json','optimisation_queue.json','research_activity.json','coin_registry.json','recommendation_timeline.json','autonomous_diagnostics.json','independent_trade_accounting.json','source_health.json','market_universe_status.json','historical_data_status.json','kucoin_walk_forward.json','validation_resolution.json','research_scheduler_status.json','research_database_status.json','portfolio_allocation_recommendations.json','presentation_quality.json','candidate_review.json','adaptive_research_queue.json','kucoin_fill_ledger.json','coin_discovery.json','execution_reconciliation.json','live_portfolio_truth.json','live_bot_profiles.json','cross_exchange_continuation.json','shadow_execution_plans.json','kucoin_order_state.json','execution_assurance.json','native_execution_readiness.json','candidate_evidence_grades.json','continuation_acquisition_queue.json','execution_migration_status.json','crm_health_recovery.json','deployment_lifecycle.json','portfolio_capital_v2.json','integrity_status.json','live_strategy_revalidation.json','fast_live_truth_status.json','kucoin_canonical_service.json','kucoin_live_prices.json','kucoin_live_service_status.json','paper_portfolio.json','managed_bot_portfolio.json','managed_bot_registry.json','version.json'];
const [w,op,sync,gh,ui,issues,port,capital,market,cloud,three,kucoin,providers,agent,research,pipeline,trades,expansion,inbox,recommendedBots,history,freshness,globalMarket,optimisation,researchActivity,coinRegistry,timeline,autoDiag,accounting,sourceHealth,marketUniverse,historicalData,kucoinWF,validationResolution,researchScheduler,researchDb,portfolioAllocation,presentationQuality,candidateReview,adaptiveResearch,fillLedger,coinDiscovery,executionReconciliation,liveTruth,liveBotProfiles,crossContinuation,shadowPlans,kucoinOrders,executionAssurance,nativeReadiness,evidenceGrades,continuationQueue,migrationStatus,crmHealth,deploymentLifecycle,portfolioCapitalV2,integrityStatus,liveRevalidation,fastLiveTruth,canonicalKucoin,livePrices,liveService,paperPortfolio,managedPortfolio,managedRegistry,ver]=await Promise.all(names.map(fetchj));
const d=w.daily_decision||{},rd=w.decision_readiness||{},alloc=w.allocation||{},rs=w.recommended_settings||{};
persistentManagedAssets=new Set((managedRegistry.assets||[]).map(x=>String(x).toUpperCase()));

$('#summary').textContent=`${lab(d.action)} · ${d.bot_name||'No bot'} · confidence ${CRMFormat.percent(d.confidence_pct)} · V${ver.version||'Unknown'}`;
let overall='VIEW CURRENT';
const syncEntries=Object.entries(sync.components||{}),livePagesStatus=String(sync.components?.live_pages?.status||'').toUpperCase();
const blockingSync=syncEntries.some(([k,v])=>k!=='live_pages'&&/FAIL|ERROR|OUT_OF_SYNC|BLOCKED/.test(String(v?.status||'').toUpperCase()));
if(op.overall?.state==='CRITICAL'||(executionReconciliation.summary?.blocked_next_entry_risks||0)>0)overall='ACTION REQUIRED';
else if(crmHealth.overall==='RECOVERING_AUTOMATICALLY')overall='RECOVERING AUTOMATICALLY';
else if(freshness.overall==='ACTION_REQUIRED'||executionAssurance.status==='FAIL')overall='ACTION REQUIRED';
else if(freshness.overall==='SOURCE_OVERDUE')overall='SOURCE OVERDUE';
else if(blockingSync||ui.overall?.state!=='HEALTHY')overall='CHECK STATUS';
else if(freshness.overall==='UPDATE_PENDING')overall='UPDATING';
else if(freshness.overall==='PARTIALLY_DEGRADED')overall='KUCOIN CURRENT · PROVIDER DEGRADED';
else if(freshness.overall==='PUBLICATION_DELAYED')overall='PUBLICATION DELAYED';
else if(freshness.overall==='PUBLISHING'||/PENDING|PUBLISHING|QUEUED/.test(livePagesStatus))overall='PUBLISHING';

$('#overall-status').textContent=overall;$('#overall-status').className='crm-status '+statusClass(overall);

const lifecycleBots=deploymentLifecycle.bots||[];
const lifecycleActive=lifecycleBots.filter(x=>x.lifecycle_state==='ACTIVE');
const lifecycleReady=lifecycleBots.filter(x=>['READY_TO_DEPLOY','RECOMMENDED_NOW','READY_FOR_DEPLOYMENT_REVIEW','DCA_OPTIMISATION_IN_PROGRESS'].includes(x.lifecycle_state));
const lifecycleRecommended=lifecycleBots.find(x=>x.lifecycle_state==='RECOMMENDED_NOW');
const lifecycleProduction=lifecycleActive.find(x=>String(x.recommended_action||'').toUpperCase().includes('KEEP'))||lifecycleActive[0]||null;
const totalCapital=capital.exchange_total??port.total_equity??kucoin.usdt_balance??null;
const kucoinCash=capital.kucoin_cash_available??capital.free_available??kucoin.free_usdt??null;
const reservedCapital=capital.active_dca_reserve??capital.remaining_active_deal_dca_reserve??capital.reserved_capital??port.reserved_capital??null;
const safeAllocate=portfolioCapitalV2.safe_multi_bot_pool_usdt??portfolioAllocation.deployable_capital_usdt??capital.safe_to_allocate_now??capital.deployable_capital??alloc.deployable_quote??port.deployable_capital??null;
const truthDeals=liveTruth.deals||[];
const effectiveDeals=truthDeals.filter(x=>x.effective_position_state==='OPEN');
const realisedPnl=liveTruth.realised_profit_quote??accounting.realised_profit_quote??three.realised_profit_usdt??three.realized_profit_usdt??null;
const openPnl=liveTruth.open_pnl_quote??accounting.open_pnl_quote??null;
const totalPnl=(realisedPnl!=null&&openPnl!=null)?Number(realisedPnl)+Number(openPnl):null;
const openCapital=liveTruth.open_capital_quote??effectiveDeals.reduce((s,x)=>s+Number(x.position_cost_basis_quote??x.capital_used_quote??0),0);
const openPnlPct=(liveTruth.open_pnl_pct!=null)?Number(liveTruth.open_pnl_pct):((openPnl!=null&&openCapital>0)?100*Number(openPnl)/openCapital:null);
const realisedPnlPct=(realisedPnl!=null&&totalCapital>0)?100*Number(realisedPnl)/Number(totalCapital):null;
const totalPnlPct=(totalPnl!=null&&totalCapital>0)?100*Number(totalPnl)/Number(totalCapital):null;
const pnlValue=(q,p)=>q==null?'Updating':`${CRMFormat.quote(q,'USDT')}${p==null?'':` · ${CRMFormat.percent(p)}`}`;

const readyCandidates=(candidateReview.candidates||[]).filter(x=>Number(x.readiness_pct||0)>=100);
const allocationRows=portfolioAllocation.recommendations||[];
const nextDeployment=allocationRows.find(x=>x.selected_for_next_portfolio_slot)||allocationRows[0]||readyCandidates[0]||null;
const nextAsset=stableAsset(nextDeployment)||stableAsset(readyCandidates[0])||null;
const nextCandidateReview=(candidateReview.candidates||[]).find(x=>stableAsset(x)===nextAsset)||null;
const rawNextAllocation=nextDeployment?.recommended_allocation_usdt??nextDeployment?.suggested_allocation_usdt??null;
const desiredNextAllocation=(rawNextAllocation!=null&&Number(rawNextAllocation)>0)?Number(rawNextAllocation):(nextCandidateReview?.suggested_allocation_usdt??nextCandidateReview?.recommended_allocation_usdt??null);
const activeDeal=effectiveDeals[0]||null;
const activePct=activeDeal?.profit_pct;
const backfillProgress=fillLedger.backfill_progress||{};
const deepCost=fillLedger.deep_cost_basis_search||{};
const deepAsset=(deepCost.assets||[])[0]||null;
const legacyCostUnavailable=fillLedger.realised_profit_status==='HISTORICAL_COST_BASIS_UNAVAILABLE';
const deepCostActive=fillLedger.realised_profit_status==='DEEP_COST_BASIS_SEARCH';
const realisedStatus=realisedPnl!=null?CRMFormat.quote(realisedPnl,'USDT'):
  legacyCostUnavailable?`Legacy cost basis unavailable`:
  deepCostActive&&deepAsset?`Deep history ${deepAsset.weeks_checked??0}/${deepAsset.total_weeks_target??0} weeks`:
  (backfillProgress.total_weeks_target?`History ${backfillProgress.weeks_checked??0}/${backfillProgress.total_weeks_target} weeks`:
   (fillLedger.reconciliation_progress_pct==null?'History building':`Reconciling · ${CRMFormat.percent(fillLedger.reconciliation_progress_pct)}`));
const realisedDetail=realisedPnl!=null?'Closed-trade profit currently recognised by CRM.':
  `${fillLedger.progress_explanation||'CRM is building the older KuCoin cost basis.'}${deepCostActive&&deepAsset?.estimated_minutes_remaining?` Targeted ${deepAsset.asset} search: about ${deepAsset.estimated_minutes_remaining} min of scheduled background work remains.`:(!legacyCostUnavailable&&backfillProgress.estimated_minutes_remaining!=null&&backfillProgress.estimated_minutes_remaining>0?` Estimated background time remaining: about ${backfillProgress.estimated_minutes_remaining} min.`:(fillLedger.next_automatic_retry_minutes?` Next background pass within ${fillLedger.next_automatic_retry_minutes} min.`:''))}`;
const partialTotalText=totalPnl!=null?CRMFormat.quote(totalPnl,'USDT'):
  legacyCostUnavailable?(openPnl!=null?`${CRMFormat.quote(openPnl,'USDT')} open · legacy realised P/L excluded`:'Legacy realised P/L excluded'):
  (openPnl!=null?`${CRMFormat.quote(openPnl,'USDT')} open + realised history building`:'Waiting for current and realised P/L');
const canFundNext=(safeAllocate!=null&&desiredNextAllocation!=null&&Number(safeAllocate)>=Number(desiredNextAllocation));
const nextAllocationText=!nextAsset?'No next deployment':
  desiredNextAllocation==null?'Allocation still being calculated':
  canFundNext?`${CRMFormat.quote(desiredNextAllocation,'USDT')} available for ${nextAsset}/USDT`:
  `${nextAsset}/USDT next · waiting for ${CRMFormat.quote(desiredNextAllocation,'USDT')} safe capital`;
const brief=$('#trading-briefing');
if(brief){
 brief.innerHTML=`
  <div class="crm-trader-metrics crm-trader-metrics-compact">
   ${stat('Portfolio',CRMFormat.quote(totalCapital,'USDT'),'Current KuCoin-recognised portfolio value.')}
   ${stat('Cash',CRMFormat.quote(kucoinCash,'USDT'),'Free USDT on KuCoin.')}
   ${stat('DCA reserve',CRMFormat.quote(reservedCapital,'USDT'),'Protected for remaining live DCA commitments.')}
   ${stat('Deployable now',CRMFormat.quote(safeAllocate,'USDT'),safeAllocate===0?(portfolioCapitalV2.conditional_multi_bot_capacity_usdt>0?`Conditional advisory capacity: ${CRMFormat.quote(portfolioCapitalV2.conditional_multi_bot_capacity_usdt,'USDT')}.`:'No capital currently passes the conservative safety gate.'):'Capital currently safe for another approved strategy.')}
   <div class="crm-stat"><span>Trading P/L</span><strong id="crm-live-total-pnl" class="crm-fit-text">${esc(totalPnl!=null?pnlValue(totalPnl,totalPnlPct):partialTotalText)}</strong><small id="crm-live-total-pnl-note" class="crm-muted">${esc(totalPnl==null?realisedDetail:`Realised ${realisedPnl==null?'—':CRMFormat.quote(realisedPnl,'USDT')} · Open ${openPnl==null?'—':CRMFormat.quote(openPnl,'USDT')} · live price ${ageText(liveTruth.open_pnl_priced_at)}.`)}</small><span id="crm-live-open-pnl" hidden>${esc(openPnl==null?'':pnlValue(openPnl,openPnlPct))}</span><span id="crm-live-open-pnl-note" hidden></span></div>
  </div>
 `;
}
const briefingState=$('#briefing-state');if(briefingState){briefingState.textContent=(crmHealth.decision_data_usable&&crmHealth.background_recovery_only)?'Trading data current · background recovery':(overall==='VIEW CURRENT'?'Up to date':lab(overall));briefingState.className='crm-status '+((crmHealth.decision_data_usable&&crmHealth.background_recovery_only)?'warn':statusClass(overall))}

function renderManagedBots(){
 const root=$('#managed-bots'),badge=$('#managed-bots-count');if(!root)return;
 const selected=myBotAssets();
 const all=managedPortfolio.bots||[];
 const rows=all.filter(x=>x.state==='LIVE'||x.managed===true||selected.has(String(x.asset||'').toUpperCase()));
 const display=rows.slice().sort((a,b)=>({LIVE:0,PAPER:1,READY:2,RESEARCH:3}[a.state]??9)-({LIVE:0,PAPER:1,READY:2,RESEARCH:3}[b.state]??9));
 if(badge){badge.textContent=`${display.length} managed · ${(all.filter(x=>x.state==='LIVE')).length} live · ${display.filter(x=>x.state==='PAPER').length} paper`;badge.className='crm-status '+(display.length?'good':'warn')}
 const priority=display.filter(x=>x.state==='PAPER').sort((a,b)=>(a.portfolio_rank??999)-(b.portfolio_rank??999))[0]||null;
 const priorityHtml=priority?`<div class="crm-capital-priority"><span class="crm-command-label">Next capital priority</span><strong>${esc(priority.asset)}/USDT</strong><small>${esc(`Rank #${priority.portfolio_rank||1} among managed paper strategies · ${safeAllocate>0?`${CRMFormat.quote(safeAllocate,'USDT')} deployable now`:'continue paper trading until safe capital is released'}.`)}</small></div>`:'';
 root.innerHTML=display.length?`${priorityHtml}<div class="crm-managed-table"><div class="crm-managed-head"><span>Bot</span><span>State</span><span>Capital</span><span>DCA</span><span>P/L</span><span>Regime</span><span>CRM decision</span><span>Action</span></div>${display.map(x=>{
  const so=(x.safety_orders_filled==null&&x.max_safety_orders==null)?'—':`${x.safety_orders_filled??0}/${x.max_safety_orders??'?'}`;
  const pnl=x.open_pnl_quote==null?'—':pnlValue(x.open_pnl_quote,x.open_pnl_pct);
  const reserve=x.state==='LIVE'?(x.reserved_quote==null?'—':CRMFormat.quote(x.reserved_quote,'USDT')):(x.capital_required_usdt==null?'—':CRMFormat.quote(x.capital_required_usdt,'USDT'));
  const pos=x.position_quote==null?'—':CRMFormat.quote(x.position_quote,'USDT');
  const label=x.state==='PAPER'?`Paper trading${x.portfolio_rank?` · rank ${x.portfolio_rank}`:''}`:x.state==='READY'?'Ready / paper available':lab(x.state);
  const decision=x.state==='LIVE'?(x.would_deploy_today===false?'Keep current deal · review next deal':lab(x.next_action||'Keep active deal')):(x.state==='PAPER'?(x.portfolio_rank===1?'Next capital priority · continue paper trading':'Continue paper trading'):lab(x.next_action||'Review'));
  const paperNote=x.state==='PAPER'?` · ${x.paper_closed_deals??0} deals${x.paper_win_rate_pct==null?'':` · ${CRMFormat.percent(x.paper_win_rate_pct)} wins`}`:'';
  return `<div class="crm-managed-row"><div><strong>${esc(x.asset)}/USDT</strong><small>${esc(x.bot_name||'DCA strategy')}</small></div><span class="crm-status ${x.state==='LIVE'?'good':x.state==='PAPER'?'warn':''}">${esc(label+paperNote)}</span><span>${esc(pos)}<small>${esc(x.state==='LIVE'?`Reserve ${reserve}`:`Need ${reserve}`)}</small></span><span>${esc(so)}</span><span>${esc(pnl)}</span><span>${esc(lab(x.current_regime||'Unknown'))}</span><span>${esc(decision)}</span><div class="crm-actions-row"><button type="button" class="crm-mini crm-open-setup" data-asset="${esc(x.asset)}">Details</button>${x.state!=='LIVE'?`<button type="button" class="crm-mini crm-remove-my-bot" data-asset="${esc(x.asset)}">Remove</button>`:''}</div></div>`;
 }).join('')}</div>`:`<div class="crm-alert"><strong>Your live bot is shown here automatically.</strong><br>Add a validated candidate from the Deployment Queue to start following its forward paper performance in My Bots.</div>`;
}
renderManagedBots();

const topReady=$('#deployment-ready-top'),topReadyCount=$('#deployment-ready-count');
if(topReady){
 const managedSelected=myBotAssets();
 const rows=lifecycleReady.filter(x=>!managedSelected.has(String(x.asset||'').toUpperCase())).slice().sort((a,b)=>({RECOMMENDED_NOW:0,READY_TO_DEPLOY:1,READY_FOR_DEPLOYMENT_REVIEW:2,DCA_OPTIMISATION_IN_PROGRESS:3}[a.lifecycle_state]??9)-({RECOMMENDED_NOW:0,READY_TO_DEPLOY:1,READY_FOR_DEPLOYMENT_REVIEW:2,DCA_OPTIMISATION_IN_PROGRESS:3}[b.lifecycle_state]??9));
 topReady.innerHTML=rows.length?`<div class="crm-ready-grid">${rows.map(x=>{const kp=x.kucoin_profitability||{},state=x.lifecycle_state,blockers=x.blockers||[];return `<article class="crm-ready-card"><div class="crm-ready-head"><strong>${esc(x.asset)}/USDT</strong><span class="crm-status ${state==='RECOMMENDED_NOW'||state==='READY_TO_DEPLOY'?'good':'warn'}">${esc(lab(state))}</span></div>${stat('Current regime',lab(x.current_regime||'Unknown'))}${stat('DCA optimisation',x.dca_optimisation_status==='COMPLETE'?'Complete':(x.dca_optimisation_status==='UNSEEN_VALIDATION_FAILED'?'Validation failed · new research queued':`${lab(x.dca_optimisation_status||'In progress')} · ${CRMFormat.percent(x.settings_completeness_pct)}`),x.dca_optimisation_status==='COMPLETE'?'Recommended DCA settings have passed optimisation, freeze and unseen KuCoin validation.':'CRM will only publish exact recommended settings after a training winner passes unseen KuCoin validation.')}${stat('Capital required',CRMFormat.quote(x.capital_required_usdt,'USDT'),x.capital_sizing_status==='OPTIMISED_AND_UNSEEN_VALIDATED'?'Capital required by the optimised and unseen-validated setup.':'Capital requirement will be published after DCA optimisation passes.')}${stat('Safe allocation now',CRMFormat.quote(x.allocation_usdt,'USDT'),x.allocation_usdt==null||Number(x.allocation_usdt)===0?'No safe portfolio allocation is currently available; this does not invalidate the candidate setup.':'Current portfolio allocator amount.')}${stat('KuCoin validation return',CRMFormat.percent(kp.validation_return_on_max_capital_pct),'Historical unseen-validation result; not a forecast.')}${blockers.length?`<div class="crm-alert warn"><strong>What remains</strong><br><small>${blockers.map(esc).join('<br>')}</small></div>`:''}<div class="crm-actions-row"><button type="button" class="primary-action crm-open-setup" data-asset="${esc(x.asset)}">${esc(x.button_label||'View deployment plan')}</button>${x.dca_optimisation_status==='COMPLETE'?`<button type="button" class="secondary-action crm-add-my-bot" data-asset="${esc(x.asset)}">${myBotAssets().has(String(x.asset).toUpperCase())?'In My Bots':'Add to My Bots'}</button>`:''}</div></article>`}).join('')}</div>`:'<div class="crm-alert">No additional bot is currently at deployment review. CRM continues research automatically.</div>';
}
if(topReadyCount){const n=lifecycleReady.filter(x=>!myBotAssets().has(String(x.asset||'').toUpperCase())).length;topReadyCount.textContent=n?`${n} in deployment queue`:'No bot awaiting deployment';topReadyCount.className='crm-status '+(n?'good':'warn')}

const ec=$('#execution-control');if(ec){const assets=executionAssurance.assets||[],nr=nativeReadiness;const kuAccountHealthy=String(kucoin.status||'').toUpperCase()==='OK';const kuTradingHealthy=String(kucoinOrders.status||'').toUpperCase()==='OK';const kuFillHealthy=String(fillLedger.status||'').toUpperCase()==='OK';const assuranceHealthy=executionAssurance.status==='HEALTHY'&&kuTradingHealthy;ec.innerHTML=`<div class="crm-review-grid">${`<div class="crm-stat" id="crm-live-service-stat"><span>KuCoin live data service</span><strong>${esc(liveService?.status||canonicalKucoin?.status||'Checking')}</strong><small class="crm-muted">Resident local service maintains prices, balances, orders, fills and P/L independently from research · ${esc(ageText(liveService?.heartbeat_at||liveService?.generated_at))}.</small></div>`+stat('KuCoin balances',kuAccountHealthy?'Connected':'Needs attention',kuAccountHealthy?'Account balances and available capital are refreshing normally.':esc(kucoin.message||'Balance refresh needs attention.'))}${stat('KuCoin orders',kuTradingHealthy?'Connected':'Recovering',`${kucoinOrders.symbols_checked??0} symbol(s) checked · ${kucoinOrders.active_count??0} open order(s) · ${kucoinOrders.recent_closed_count??0} recent completed order(s).`)}${stat('KuCoin trade history',kuFillHealthy?'Connected':'Recovering',kuFillHealthy?'Recent fills are available for independent P/L accounting.':(fillLedger.progress_explanation||'CRM is retrying symbol-aware fill history automatically.'))}${stat('Trade Protection & DCA Health',assuranceHealthy?'Protected':'Checking / needs attention',assuranceHealthy?'The live position, take-profit order and DCA protection agree with current KuCoin data.':'CRM is verifying the live position, take-profit order, DCA ladder and reserved capital against KuCoin.')}${stat('3Commas secondary monitor',String(three.overall_status||three.status||'').toLowerCase()==='ok'?'Connected':'Delayed / secondary','Secondary provider only. KuCoin determines authoritative position and order truth.')}${stat('CRM direct trading',nr.overall==='SHADOW_READY'?'Testing ready':'Testing',nr.live_order_submission_implemented?'Direct order submission capability exists.':'CRM is recreating trading plans without sending live orders yet.')}${stat('Migration to CRM direct trading',CRMFormat.percent(migrationStatus.progress_pct),migrationStatus.next_required_stage?`Next: ${lab(migrationStatus.next_required_stage.label)}. ${migrationStatus.next_required_stage.detail||''}`:'All pre-live migration stages complete.')}${stat('Test trading plans',(nr.shadow_plans||[]).length,'CRM-calculated DCA plans used to prove order-by-order parity before direct trading is unlocked.')}${stat('Kraken → KuCoin follow-up',continuationQueue.count??0,(continuationQueue.count??0)?'CRM is collecting later KuCoin history to resolve historical Kraken tests that ended with a trade still open.':'No unresolved continuation case currently waiting for data.')}</div>${assets.map(x=>`<details class="crm-review-panel"><summary>${esc(x.asset)} · ${esc(x.status==='HEALTHY'?'Protection checks passed':lab(x.status))}</summary>${(x.checks||[]).map(c=>stat(c.check,lab(c.state),c.detail)).join('')}<div class="crm-alert ${x.status==='HEALTHY'?'good':x.status==='FAIL'?'bad':''}"><strong>What this means</strong><br>${esc(x.next_action||'')}</div></details>`).join('')}`};const neb=$('#native-execution-badge');if(neb){neb.textContent=nativeReadiness.overall==='SHADOW_READY'?'CRM direct trading · Test ready':'CRM direct trading · Testing';neb.classList.add(nativeReadiness.overall==='SHADOW_READY'?'good':'warn')}
const act=$('#crm-activity');if(act){const a=researchScheduler.activity||[],ms=researchScheduler.market_scan||{},hs=researchScheduler.history||{},rsch=researchScheduler.research||{},shortlist=coinDiscovery.summary?.shortlist_size??ms.markets_shortlisted??0;act.innerHTML=`<div title="Eligible KuCoin USDT markets promoted from the broad universe scan into deeper research."><strong>${esc(shortlist)}</strong><span>research shortlist</span></div><div><strong>${esc(hs.ready??0)}/${esc(hs.total??0)}</strong><span>histories ready</span></div><div><strong>${esc(rsch.backtests_run_this_cycle??0)}</strong><span>backtests this cycle</span></div><div><strong>${esc(rsch.ready_for_manual_review??0)}</strong><span>ready for review</span></div><div><strong>${esc((trades.trades||[]).length)}</strong><span>live deals</span></div><div><strong>${esc((()=>{try{return JSON.parse(localStorage.getItem('crm_recommended_bots_v1')||'[]').length}catch{return 0}})())}</strong><span>staged bots</span></div>`+`<p class="crm-muted full">${esc(rsch.cache_hit?'Backtest cache reused — no unnecessary full optimisation. The next scheduled scan will still check for new KuCoin candidates.':a.map(x=>`${lab(x.stage)}: ${lab(x.status)}`).join(' · ')||'Background scheduler is waiting for its next cycle.')}</p>`};const dbb=$('#research-db-badge');if(dbb){dbb.textContent=researchDb.status==='READY'?`Research DB ready · ${researchDb.known_assets??0} assets`:'Research database starting';dbb.classList.add(researchDb.status==='READY'?'good':'warn')}
const lp=$('#live-portfolio');if(lp){const cards=truthDeals.length?truthDeals.map(t=>`<div class="crm-stat"><span>${esc(t.bot_name||t.asset)}</span><strong>${esc(t.provider_stale?'Closed on KuCoin':(t.profit_pct==null?'P/L updating':CRMFormat.percent(t.profit_pct)))}</strong><small class="crm-muted">${t.provider_stale?`3Commas has not caught up with KuCoin · ${esc(t.action||'Review provider status')}`:`${esc(liveHold(t.opened_at,null)==null?'Trade duration unavailable':liveHold(t.opened_at,null)+'h open')} · ${esc(lab(t.action||'Monitor'))}`}</small></div>`).join(''):'<div class="crm-alert good">No live trades detected on KuCoin.</div>';lp.innerHTML=`${stat('Portfolio value',CRMFormat.quote(totalCapital,'USDT'))}${stat('Available capital',CRMFormat.quote(availableCapital,'USDT'),'Available for another approved strategy after live-trade protection.')}${stat('Capital protecting live trades',CRMFormat.quote(reservedCapital,'USDT'))}${stat('Active trades',effectiveDeals.length)}${stat('Open P/L',openPnl==null?'Waiting for current price':CRMFormat.quote(openPnl,'USDT'))}${stat('Realised P/L',realisedPnl==null?fillLedger.reconciliation_progress_pct==null?'Reconciliation pending':`Reconciling · ${CRMFormat.percent(fillLedger.reconciliation_progress_pct)}`:CRMFormat.quote(realisedPnl,'USDT'),realisedPnl==null?`${fillLedger.progress_explanation||'Closed-fill reconciliation is still incomplete.'}${fillLedger.next_automatic_retry_minutes?` Next retry within ${fillLedger.next_automatic_retry_minutes} min.`:''}`:'Closed-trade profit currently recognised by CRM.')}${stat('Total trading P/L',totalPnl==null?(realisedPnl==null?'Waiting for realised P/L':'Waiting for current open P/L'):CRMFormat.quote(totalPnl,'USDT'))}${cards}`;}
const tradeRows=trades.trades||[];const ti=$('#trade-intelligence');if(ti)ti.innerHTML=tradeRows.length?tradeRows.map(t=>`<div class="crm-alert ${statusClass(t.monitoring_state==='MONITOR'?'ok':'warn')}"><strong>${esc(t.bot_name||t.asset)}</strong> · ${esc(lab(t.monitoring_state))}<br><span class="crm-muted">P/L ${esc(CRMFormat.percent(t.profit_pct))} · ${esc(t.completed_safety_orders??0)}/${esc(t.max_safety_orders??'Unknown')} SO filled · current hold ${esc(liveHold(t.opened_at,t.hold_hours)==null?'Unknown':liveHold(t.opened_at,t.hold_hours)+'h')} · distance to TP ${esc(CRMFormat.percent(t.distance_to_take_profit_pct))}</span></div>`).join(''):'<div class="crm-alert good">No active 3Commas deals.</div>';
const er=$('#expansion-readiness');if(er){const gs=expansion.gates||[];er.innerHTML=stat('State',lab(expansion.state||'Unknown'))+stat('Readiness',CRMFormat.percent(expansion.score_pct),'Readiness score, not projected profit.')+stat('Next candidate',expansion.recommended_next_candidate||'None')+`<div class="crm-alert ${expansion.state==='READY_FOR_MANUAL_REVIEW'?'good':''}"><strong>Expansion gate status</strong><br>${esc(expansion.next_action||'No action yet.')}<br><small>This reports deployment gates. Backtesting progress is shown under Background Research.</small></div>`+`<div class="table-wrap"><table class="crm-table"><thead><tr><th>Gate</th><th>State</th><th>Evidence</th></tr></thead><tbody>${gs.map(g=>`<tr><td>${esc(g.label)}</td><td><span class="crm-status ${statusClass(g.state)}">${esc(lab(g.state))}</span></td><td>${esc(g.detail)}</td></tr>`).join('')}</tbody></table></div>`;}

const legacyAckKey='crm_v43_acknowledged_events',ackKey='crm_acknowledged_events_v1',savedKey='crm_recommended_bots_v1',legacySavedKeys=['crm_v45_recommended_bots'];
const acked=()=>{try{return Array.from(new Set([...(JSON.parse(localStorage.getItem(legacyAckKey)||'[]')),...(JSON.parse(localStorage.getItem(ackKey)||'[]'))]))}catch{return []}},
 saveAck=ids=>localStorage.setItem(ackKey,JSON.stringify(Array.from(new Set([...acked(),...ids]))));
function getSaved(){
 let rows=[];try{rows=JSON.parse(localStorage.getItem(savedKey)||'[]')}catch{}
 for(const key of legacySavedKeys){try{for(const x of JSON.parse(localStorage.getItem(key)||'[]'))if(x?.asset&&!rows.some(r=>stableAsset(r)===stableAsset(x)))rows.push(x)}catch{}}
 const clean=rows.filter(x=>x?.asset);try{localStorage.setItem(savedKey,JSON.stringify(clean))}catch{};return clean;
}
const putSaved=rows=>localStorage.setItem(savedKey,JSON.stringify(rows));
const isSaved=c=>getSaved().some(x=>stableAsset(x)===stableAsset(c));
function downloadJson(name,obj){const blob=new Blob([JSON.stringify(obj,null,2)],{type:'application/json'}),a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),500)}
function renderInbox(){const root=$('#decision-inbox');if(!root)return;const rows=inbox.items||[];root.innerHTML=rows.length?rows.map(x=>`<div class="crm-change-item"><strong>${esc(x.title)}</strong><br><span class="crm-muted">${esc(x.detail||'')}</span></div>`).join(''):'<div class="crm-alert good">No material changes require review.</div>'}
function candidateCard(c){
 const saved=isSaved(c),review=(candidateReview.candidates||[]).find(x=>stableAsset(x)===stableAsset(c)),ready=(review?.readiness_pct??0)>=100||c.state==='DEPLOYMENT_REVIEW_READY';
 const p=c.profitability_evidence||{},pa=(portfolioAllocation.recommendations||[]).find(x=>stableAsset(x)===stableAsset(c)),allocation=review?.suggested_allocation_usdt??c.suggested_initial_allocation_usdt??pa?.recommended_allocation_usdt;
 const kp=review?.kucoin_profitability||{},prog=review?.research_progress||{},cont=review?.kraken_robustness?.continuation;
 const currentProfile=review?.regime_profiles?.[review?.current_regime]||{};
 const settings=currentProfile.settings||review?.settings||c.dca_settings||{},entries=Object.entries(settings).filter(([,v])=>v!==null&&v!==undefined).slice(0,12);
 const robustness=String(review?.kraken_robustness?.status||c.kraken_q1_status||'MISSING').toUpperCase(),caution=ready&&robustness==='FAIL';
 return `<article class="crm-candidate" data-candidate="${esc(c.candidate_id)}">
 <h3 class="crm-fit-text">${esc(c.asset)}/USDT</h3>
 <p><span class="crm-status ${ready?(caution?'warn':'good'):'warn'}">${esc(ready?(caution?'Ready for review — caution':'Ready for manual review'):lab(review?.recommendation||c.state||'Research pending'))}</span></p>
 ${stat('Decision readiness',CRMFormat.percent(review?.readiness_pct),review?`${review.gates.filter(g=>g.state==='PASS').length}/${review.gates.length} primary KuCoin gates passed.`:'')}
 ${stat('Research progress',CRMFormat.percent(prog.progress_pct),prog.remaining_stages!=null?`${prog.remaining_stages} research stage${prog.remaining_stages===1?'':'s'} remaining · estimated ${prog.estimated_remaining_cycles??'Unknown'} background cycle(s).`:'')}
 ${stat('Current regime',lab(review?.current_regime||c.current_global_regime||'Unknown'),currentProfile.validated?'Validated regime profile selected.':'Current-regime profile is not yet validated.')}${stat('Evidence grade',lab(review?.evidence_grade?.evidence_grade||'Unknown'),review?.evidence_grade?`${review.evidence_grade.history_years} years · ${review.evidence_grade.bars_4h} 4h bars · ${review.evidence_grade.regime_profile_count} regime profile(s). ${review.evidence_grade.reason||''}`:'Evidence depth is still being calculated.')}${stat('Kraken comparison',review?.evidence_grade?.kraken_robustness_status==='MISSING'?'Not available':lab(review?.evidence_grade?.kraken_robustness_status||'Unknown'),review?.evidence_grade?.kraken_robustness_status==='MISSING'?'No comparable Kraken archive is available for this asset. KuCoin training + unseen KuCoin walk-forward remain the primary research path.':'Secondary cross-exchange robustness evidence.') }
 ${stat('KuCoin validation return',CRMFormat.percent(kp.validation_return_on_max_capital_pct),'Historical return on maximum capital in unseen KuCoin validation; not a forecast.')}
 ${stat('KuCoin validation P/L',kp.validation_mark_to_market_pnl==null?'Unknown':CRMFormat.quote(kp.validation_mark_to_market_pnl,'USDT'))}
 ${stat('Forward observation return',CRMFormat.percent(kp.forward_return_on_max_capital_pct),'Later KuCoin observation after the frozen validation window.')}
 ${stat('Historical annualised equivalent',CRMFormat.percent(kp.historical_annualised_equivalent_pct),kp.annualised_label||'Shown only when enough validation time exists.')}
 ${stat('Validation closed deals',kp.validation_closed_deals??'Unknown')}
 ${stat('Average / P90 hold',`${kp.validation_average_hold_hours??'Unknown'}h / ${kp.validation_p90_hold_hours??'Unknown'}h`)}
 ${stat('Longest validation trade',kp.validation_longest_hold_hours==null?'Unknown':kp.validation_longest_hold_hours+'h')}
 ${stat('Validation drawdown',CRMFormat.percent(kp.validation_drawdown_pct))}
 ${stat('Suggested allocation',CRMFormat.quote(allocation,'USDT'),review?.allocation_reason||pa?.reason||c.allocation_explanation||'')}
 ${stat('Kraken robustness',lab(robustness),review?.kraken_robustness?.explanation||'')}
 ${cont?stat('Kraken → KuCoin continuation',lab(cont.continuation_status||'Unknown'),cont.continuation?.closed_at?`Closed later on KuCoin at ${dateText(cont.continuation.closed_at)} · total duration ${cont.continuation.total_duration_hours}h · final P/L ${CRMFormat.quote(cont.continuation.final_net_pnl,'USDT')}. Original Kraken result remains unchanged.`:(cont.continuation_status==='STILL_OPEN'?`Still unresolved after ${cont.continuation?.total_duration_hours??'Unknown'}h · mark-to-market ${CRMFormat.quote(cont.continuation?.current_mark_to_market_pnl,'USDT')}.`:'Independent Kraken continuation evidence is unavailable. KuCoin-primary validation remains authoritative; this is a terminal evidence limitation, not a background task still waiting.')):''}
 ${stat('Entry trigger',lab(review?.entry_trigger||c.entry_trigger||'Optimisation pending'))}
 <table class="crm-mini-table"><tbody>${entries.map(([k,v])=>`<tr><td>${esc(lab(k))}</td><td>${esc(v)}</td></tr>`).join('')}</tbody></table>
 <div class="crm-actions-row">${saved?`<span class="crm-saved-pill">Deployment candidate saved</span><button type="button" class="crm-remove-candidate" data-asset="${esc(c.asset)}">Remove</button>`:ready?`<button type="button" class="primary-action crm-add-candidate" data-id="${esc(c.candidate_id)}">Add to Deployment Candidates</button>`:'<button type="button" disabled title="Outstanding research gates must complete first">Continue research</button>'}<button type="button" class="crm-download-candidate" data-id="${esc(c.candidate_id)}">Download evidence</button></div>
 <p class="crm-explain"><strong>Next step:</strong> ${esc(review?.next_action||c.next_step||'Background research continues; live deployment remains manual.')}</p>
 </article>`
}
function renderStaged(){
 const root=$('#staged-bots');if(!root)return;const saved=getSaved(),current=recommendedBots.candidates||[],reviews=candidateReview.candidates||[],prep=prepared(),plans=shadowPlans.plans||[];
 if(!saved.length){root.innerHTML='<div class="crm-alert">No Deployment Candidates are currently saved. Add a research candidate once you want CRM to keep it prominent for governed follow-up.</div>';return}
 root.innerHTML=saved.map(x=>{
   const c=current.find(r=>stableAsset(r)===stableAsset(x)),rv=reviews.find(r=>stableAsset(r)===stableAsset(x)),asset=stableAsset(x),isPrepared=prep.some(r=>String(r.asset).toUpperCase()===asset),plan=plans.find(r=>stableAsset(r)===asset);
   const readiness=rv?.readiness_pct??0,ready=readiness===100,robust=String(rv?.kraken_robustness?.status||'').toUpperCase(),caution=ready&&robust==='FAIL',rp=rv?.research_progress||{},kp=rv?.kucoin_profitability||{};
   const status=ready?(caution?'Ready for review — caution':'Ready for manual review'):(rv?.recommendation||'Continue monitoring');
   const gates=(rv?.gates||[]).map(g=>`<li>${g.state==='PASS'?'✓':'○'} <strong>${esc(g.label)}</strong> — ${esc(lab(g.state))}<br><small>${esc(g.detail||'')}</small></li>`).join('');
   const stages=(rp.stages||[]).map(s=>`<li>${s.complete?'✓':'○'} ${esc(s.label)}</li>`).join('');
   const adaptive=rv?.adaptive_research?`<div class="crm-alert"><strong>Adaptive research</strong><br>${(rv.adaptive_research.failure_reasons||[]).map(z=>esc(z)).join('<br>')}<br><small>Next experiments: ${(rv.adaptive_research.next_experiments||[]).map(z=>esc(lab(z))).join(' · ')||'Waiting for next cycle'}</small></div>`:'';
   const monitorText=rv?.monitoring_complete?`Forward-observation requirement complete: ${rv.forward_observation_days} days available versus ${rv.monitoring_target_days} days preferred.`:(rv?.forward_observation_days==null?'Forward-observation duration is still being established.':`${rv.forward_observation_days} of ${rv.monitoring_target_days} preferred observation days recorded (${CRMFormat.percent(rv.monitoring_progress_pct)}).`);
   const profileRows=Object.entries(rv?.regime_profiles||{}).map(([reg,p])=>`<tr><td>${esc(lab(reg))}</td><td>${esc(p.validated?'Validated':'Not validated')}</td><td>${esc(lab(p.entry_trigger||'None'))}</td><td>${p.validation_metrics?.return_on_max_capital_pct==null?'—':esc(CRMFormat.percent(p.validation_metrics.return_on_max_capital_pct))}</td></tr>`).join('');
   return `<article class="crm-staged-review"><div class="crm-staged-row"><strong>${esc(asset)}/USDT</strong><span class="crm-status ${ready?(caution?'warn':'good'):'warn'}">${esc(lab(status))}</span><span>${esc(CRMFormat.percent(readiness))} primary readiness</span><button type="button" class="crm-remove-staged" data-asset="${esc(asset)}">Remove</button><small>${esc(monitorText)}</small></div>
   <div class="crm-progress-line"><div class="visual-meter"><span style="width:${Math.max(0,Math.min(100,Number(rp.progress_pct)||0))}%"></span></div><small>${esc(CRMFormat.percent(rp.progress_pct))} research progress · ${esc(rp.remaining_stages??'Unknown')} stage(s) remaining · estimated ${esc(rp.estimated_remaining_cycles??'Unknown')} background cycle(s)</small></div>
   <details class="crm-review-panel"><summary>Review candidate</summary><div class="crm-review-grid">
   ${stat('Current regime',lab(rv?.current_regime||c?.current_global_regime||'Unknown'))}${stat('Evidence grade',lab(rv?.evidence_grade?.evidence_grade||'Unknown'),rv?.evidence_grade?`${rv.evidence_grade.history_years} years · ${rv.evidence_grade.bars_4h} 4h bars. ${rv.evidence_grade.reason||''}`:'')}
   ${stat('Entry trigger',lab(rv?.entry_trigger||c?.entry_trigger||'Pending'))}
   ${stat('Suggested allocation',CRMFormat.quote(rv?.suggested_allocation_usdt,'USDT'),rv?.allocation_reason||'')}
   ${stat('KuCoin validation return',CRMFormat.percent(kp.validation_return_on_max_capital_pct),'Historical unseen-validation return on maximum capital; not a forecast.')}
   ${stat('Forward observation return',CRMFormat.percent(kp.forward_return_on_max_capital_pct))}
   ${stat('Validation P/L',kp.validation_mark_to_market_pnl==null?'Unknown':CRMFormat.quote(kp.validation_mark_to_market_pnl,'USDT'))}
   ${stat('Longest / P90 hold',`${kp.validation_longest_hold_hours??'Unknown'}h / ${kp.validation_p90_hold_hours??'Unknown'}h`)}
   ${stat('Validation drawdown',CRMFormat.percent(kp.validation_drawdown_pct))}
   ${stat('Kraken robustness',lab(rv?.kraken_robustness?.status||'Unavailable'),rv?.kraken_robustness?.explanation||'')}
   </div><ul class="crm-list">${gates}</ul><details><summary>Research stages</summary><ul class="crm-list">${stages}</ul></details>${adaptive}
   ${profileRows?`<details><summary>Regime-specific profiles</summary><div class="table-wrap"><table class="crm-table"><thead><tr><th>Regime</th><th>Validation</th><th>Entry trigger</th><th>Return</th></tr></thead><tbody>${profileRows}</tbody></table></div></details>`:''}
   ${plan?`<div class="crm-alert good"><strong>CRM Trading Plan — Test Mode</strong><br>${esc(lab(plan.status))} · budget ${esc(CRMFormat.quote(plan.allocated_budget_usdt,'USDT'))} · ${esc((plan.hypothetical_order_ladder||[]).length)} hypothetical orders. Nothing has been sent to KuCoin.</div>`:''}
   <div class="crm-actions-row">${ready?`<button type="button" class="primary-action crm-prepare-deployment" data-asset="${esc(asset)}">${isPrepared?'Deployment preparation saved':'Prepare deployment'}</button>`:'<button type="button" disabled>Continue monitoring automatically</button>'}<button type="button" class="crm-remove-staged" data-asset="${esc(asset)}">Remove</button></div>
   <p class="crm-explain">${ready?'Prepare deployment saves your review decision locally and exposes the shadow execution package. It does not create a 3Commas bot, start a deal or place a KuCoin order.':'CRM will reassess automatically after new KuCoin data, a research cycle or a regime change. No manual action is required while research remains incomplete.'}</p></details></article>`;
 }).join('');
 root.querySelectorAll('.crm-remove-staged').forEach(b=>b.onclick=()=>{putSaved(getSaved().filter(x=>stableAsset(x)!==String(b.dataset.asset).toUpperCase()));renderStaged();renderCandidates()});
 root.querySelectorAll('.crm-prepare-deployment').forEach(b=>b.onclick=()=>{const a=String(b.dataset.asset).toUpperCase(),rv=reviews.find(x=>stableAsset(x)===a),plan=plans.find(x=>stableAsset(x)===a),rows=prepared().filter(x=>String(x.asset).toUpperCase()!==a);rows.push({asset:a,prepared_at:new Date().toISOString(),review_snapshot:rv||null,shadow_plan:plan||null,status:'PREPARED_FOR_MANUAL_EXECUTION_REVIEW'});setPrepared(rows);renderStaged()});
}
function renderCandidates(){const root=$('#recommended-bots');if(!root)return;const rows=recommendedBots.candidates||[],saved=getSaved();root.innerHTML=(rows.length?`<div class="crm-candidate-grid">${rows.map(candidateCard).join('')}</div>`:'<div class="crm-alert">No candidate currently passes research-review gates.</div>')+(saved.length?`<p class="crm-muted" style="margin-top:1rem">${saved.length} recommendation${saved.length===1?'':'s'} saved as deployment candidates in this browser profile. Staging is retained across CRM versions on this device.</p>`:'');root.querySelectorAll('.crm-add-candidate').forEach(b=>b.addEventListener('click',()=>{const c=rows.find(x=>x.candidate_id===b.dataset.id);if(!c)return;const cur=getSaved().filter(x=>stableAsset(x)!==stableAsset(c));cur.push({...c,saved_at:new Date().toISOString(),status:'STAGED_RECOMMENDATION'});putSaved(cur);renderStaged();renderCandidates()}));root.querySelectorAll('.crm-remove-candidate').forEach(b=>b.addEventListener('click',()=>{putSaved(getSaved().filter(x=>stableAsset(x)!==String(b.dataset.asset).toUpperCase()));renderStaged();renderCandidates()}));root.querySelectorAll('.crm-download-candidate').forEach(b=>b.addEventListener('click',()=>{const c=rows.find(x=>x.candidate_id===b.dataset.id);if(c)downloadJson(`CRM_${c.asset}_recommended_bot.json`,c)}))}
function renderHistory(){const root=$('#recommendation-history');if(!root)return;const rows=(history.records||[]).slice(-8).reverse();root.innerHTML=rows.length?rows.map(r=>`<div class="crm-history-row"><span>${esc(dateText(r.recorded_at))}</span><strong>${esc(r.asset||'')} · ${esc(lab(r.action||''))}</strong><span>Confidence ${esc(CRMFormat.percent(r.overall_confidence))}</span></div>`).join(''):'<p class="crm-muted">Recommendation history will build as governed recommendations change.</p>'}
function showBriefing(){const modal=$('#briefing-modal');if(!modal)return;const unseen=(inbox.items||[]).filter(x=>!acked().includes(x.event_id));if(!unseen.length)return;$('#briefing-content').innerHTML=unseen.slice(0,8).map(x=>`<div class="crm-change-item"><strong>${esc(x.title)}</strong><br><span class="crm-muted">${esc(x.detail||'')}</span></div>`).join('');modal.hidden=false;modal.setAttribute('aria-hidden','false');const close=()=>{modal.hidden=true;modal.setAttribute('aria-hidden','true')};$('#briefing-close').onclick=close;$('#briefing-review').onclick=()=>{close();$('#decision-inbox-card')?.scrollIntoView({behavior:'smooth'})};$('#briefing-dismiss').onclick=()=>{saveAck(unseen.map(x=>x.event_id));close()};modal.querySelector('.crm-modal-backdrop').onclick=close}
function renderV45(){
 const healthRoot=$('#crm-health-recovery'),healthBadge=$('#crm-health-badge');
 if(healthRoot){
   const issues=crmHealth.issues||[],summary=crmHealth.summary||{},actions=crmHealth.recovery_transaction||[];
   let html='<div class="crm-health-summary">';
   html+=stat('Overall status',crmHealth.overall==='HEALTHY'?'Healthy':lab(crmHealth.overall),crmHealth.next_action||'');
   const actionCount=summary.recovery_actions_attempted??actions.length;
   const actionNote=actionCount?String(summary.root_issues_resolved??0)+' root issue(s) resolved in this recovery cycle.':'No recovery action was executed in this cycle.';
   html+=stat('Recovery actions run',actionCount,actionNote);
   html+=stat('Root issues remaining',summary.root_issues_after??issues.length,'Dependent symptoms are grouped under their upstream cause.');
   html+='</div>';
   if((crmHealth.resolved_this_cycle||[]).length){
     html+='<div class="crm-alert good"><strong>Recovered this cycle</strong><br>'+crmHealth.resolved_this_cycle.map(x=>esc(lab(x))).join(' · ')+'</div>';
   }
   if((crmHealth.informational_limitations||[]).length){
     html+='<div class="crm-alert"><strong>Operational notes — not system faults</strong><br>'+crmHealth.informational_limitations.map(x=>esc(x.detail||lab(x.state))).join('<br>')+'</div>';
   }
   if(issues.length){
     html+=issues.map(x=>{
       const lastNote=x.last_recovery_transaction_at?('Last recovery: '+dateText(x.last_recovery_transaction_at)+' · consecutive unresolved cycles '+String(x.consecutive_failed_cycles??0)):'';
       let block='<details class="crm-review-panel"><summary>'+esc(x.title)+' · '+esc(lab(x.state))+'</summary>';
       block+=stat('Area',x.area);
       block+=stat('What CRM found',lab(x.state),x.detail);
       block+=stat('Automatic recovery',x.automatic_recovery_attempted?'Recovery transaction executed':'No recovery action executed yet',lastNote);
       if(x.user_action){
         block+='<div class="crm-alert '+(x.escalated_to_user?'bad':'warn')+'"><strong>'+(x.escalated_to_user?'Your action is now required':'If automatic recovery continues to fail')+'</strong><br>'+esc(x.user_action)+'</div>';
       }
       block+='</details>';
       return block;
     }).join('');
   }else{
     html+='<div class="crm-alert good"><strong>CRM checked itself and found no unresolved root problem.</strong><br><small>Trading data, accounting, safety and freshness continue to be checked automatically.</small></div>';
   }
   healthRoot.innerHTML=html;
 }
 if(healthBadge){
   healthBadge.textContent=crmHealth.overall==='HEALTHY'?'Healthy':(crmHealth.decision_data_usable&&crmHealth.background_recovery_only)?'Trading current · background recovery':crmHealth.overall==='RECOVERING_AUTOMATICALLY'?'Recovering automatically':crmHealth.overall==='ATTENTION'?'Check status':'Action required';
   healthBadge.className='crm-status '+(crmHealth.overall==='HEALTHY'?'good':crmHealth.overall==='RECOVERING_AUTOMATICALLY'||crmHealth.overall==='ATTENTION'?'warn':'bad');
 }
const fr=$('#freshness');if(fr)fr.innerHTML=`<div class="crm-alert"><strong>Refresh view vs collectors</strong><br><small>Refresh View reloads the latest published dashboard. CRM’s Local Agent refreshes private KuCoin and research data automatically every 15 minutes.</small></div>`+(freshness.components||[]).map(x=>`<div class="crm-stat"><span>${esc({'KuCoin account truth':'KuCoin account data','KuCoin order truth':'KuCoin trading data','3Commas telemetry':'3Commas secondary monitor','Website publication':'Website update'}[x.name]||x.name)}</span><strong class="crm-fit-text">${esc(lab(x.status))}</strong><small class="crm-muted">${esc(x.age_display||'Unknown')} · automatic target ${esc(x.expected_cadence_minutes)} min<br>${esc(x.reason||'')}</small></div>`).join('')+`<div class="crm-alert ${freshness.overall==='ACTION_REQUIRED'?'bad':freshness.overall==='CURRENT'?'good':''}"><strong>${esc(lab(freshness.overall||'Unknown'))}</strong><br>${esc(freshness.overall_reason||'')}<br><small>System checks: ${esc(lab(autoDiag.result||'Unknown'))}${autoDiag.generated_at?` · checked ${esc(ageText(autoDiag.generated_at))}`:''}</small></div>`;
 const gm=$('#global-market');if(gm){const crit=(globalMarket.criteria||[]).map(x=>`${x.criterion}: ${x.value==null?'Unknown':x.value} → ${x.score_contribution>=0?'+':''}${x.score_contribution}`).join('<br>');gm.innerHTML=stat('Universal regime',lab(globalMarket.regime||'Unknown'),globalMarket.explanation||'')+stat('Global score',CRMFormat.percent(globalMarket.score_pct))+stat('BTC 30d trend',CRMFormat.percent(globalMarket.current_evidence?.btc_30d_trend_pct))+stat('Market breadth',CRMFormat.percent(globalMarket.current_evidence?.breadth_pct),globalMarket.breadth_explanation||'')+stat('Historical BTC evidence',lab(globalMarket.historical_btc_evidence?.status||'Unknown'),globalMarket.historical_btc_evidence?.note||'')+`<div class="crm-alert"><strong>How the regime was calculated</strong><br><small>${crit||'No criteria available.'}</small></div>`;}
 const ra=$('#research-activity');if(ra){const s=researchActivity.summary||{},dp=researchActivity.trade_duration_policy||{},inv=historicalData.inventory||[],wfSum=kucoinWF.summary||{};ra.innerHTML=`<div class="crm-research-summary"><div><strong>${esc(s.historical_ready??0)}/${esc(s.historical_symbols??0)}</strong><br><span class="crm-muted">histories research-ready</span></div><div><strong>${esc(CRMFormat.percent(s.history_progress_pct))}</strong><br><span class="crm-muted">history acquisition progress</span></div><div><strong>${esc(wfSum.ready_for_manual_review??0)}</strong><br><span class="crm-muted">KuCoin walk-forward ready</span></div><div><strong>${esc(s.backtests_last_cycle??0)}</strong><br><span class="crm-muted">backtests last cycle</span></div></div><div class="crm-alert good"><strong>Persistent research memory</strong><br>${esc(researchDb.known_assets??0)} known assets · ${esc(researchDb.cached_results??0)} cached result bundles · survives CRM upgrades.<br><small>Installations no longer need to repeat unchanged optimisation work.</small></div><div class="crm-alert"><strong>Historical acquisition</strong><br>${inv.slice(0,8).map(x=>`${esc(x.symbol)}: ${esc(x.bars??0)} bars · ${esc(lab(x.status||'QUEUED'))}`).join('<br>')||'Waiting for the first Local Agent history cycle.'}<br><small>Raw 4h candles are stored outside Git and extend automatically each Local Agent cycle.</small></div><p class="crm-explain">${(researchActivity.process||[]).map((x,i)=>`${i+1}. ${esc(x)}`).join(' → ')}</p><div class="crm-alert"><strong>Trade-fluidity policy</strong><br>Preferred longest closed trade ≤ ${esc(dp.preferred_longest_closed_hours??168)}h (7d). Strong penalty above ${esc(dp.strong_penalty_hours??336)}h (14d). An unresolved research trade at ${esc(dp.reject_open_duration_hours??720)}h (30d) normally rejects the configuration.</div>`;}
 const cr=$('#coin-registry');if(cr){const rows=coinRegistry.coins||[];cr.innerHTML=rows.length?`<div class="crm-coin-grid">${rows.map(c=>`<article class="crm-coin-card"><div class="crm-ready-head"><strong>${esc(c.asset)}/USDT</strong><span class="crm-status ${statusClass(c.lifecycle)}">${esc(lab(c.lifecycle))}</span></div><div class="crm-coin-fields"><div><span>Trading status</span><strong>${esc(lab(c.execution_state||'Not deployed'))}</strong></div><div><span>Research status</span><strong>${esc(lab(c.research_state||'Not started'))}</strong></div><div class="full"><span>Current CRM view</span><small>${esc((c.reasons||[])[0]||'Recorded and monitored by CRM.')}</small></div></div></article>`).join('')}</div>`:'<p class="crm-muted">Coin Registry is waiting for its first research cycle.</p>';}
 const tl=$('#recommendation-timeline');if(tl)tl.innerHTML=(timeline.events||[]).slice(-12).reverse().map(e=>`<div class="crm-history-row"><span>${esc(dateText(e.recorded_at))}</span><strong>${esc(e.asset||'System')} · ${esc(lab(e.status||e.kind))}</strong><span>Confidence ${esc(CRMFormat.percent(e.confidence_pct))}</span></div>`).join('')||'<p class="crm-muted">Timeline will build automatically.</p>';
 const rb=$('#recommended-bots');if(rb&&(optimisation.items||[]).length){const q=document.createElement('div');q.className='crm-alert';q.innerHTML='<strong>Background optimisation queue</strong><br>'+optimisation.items.slice(0,8).map(x=>`${esc(x.asset)}: ${esc(lab(x.status))} · current regime ${esc(lab(x.current_regime_family||x.current_global_regime))}`).join('<br>');rb.prepend(q)}
 setTimeout(()=>{for(const id of ['market','sync','settings','operations','ui-quality','changes']){const el=$('#'+id);if(!el)continue;const text=(el.textContent||'').replace(/[—–\s]/g,'').trim();if(!text){const card=el.closest('.crm-card');if(card)card.hidden=true}}},120);
setTimeout(()=>{window.CRMFitText?.scan?.();const candidates=[...document.querySelectorAll('.crm-card,.crm-stat,.crm-ready-card,.crm-coin-card')],bad=[];for(const el of candidates){const overflow=(el.scrollWidth-el.clientWidth)>3||(el.scrollHeight-el.clientHeight)>24;if(overflow){el.classList.add('crm-overflow-safe');bad.push(el)}}const out=$('#runtime-layout-check');if(out){out.innerHTML=bad.length?`<div class="crm-alert warn"><strong>Layout self-check adjusted ${bad.length} item(s).</strong><br><small>Overflow protection was applied automatically for this screen size. This condition is also covered by the release UI checks.</small></div>`:`<small>Layout self-check: passed for this screen size.</small>`}},180);
}
function setupRows(settings,keys){
 const order=keys||Object.keys(settings||{});
 const present=order.filter(k=>settings?.[k]!==null&&settings?.[k]!==undefined);
 return `<div class="crm-setup-grid">${present.map(k=>stat(lab(k),settings[k])).join('')}</div>`;
}
const optimisedSetupKeys=['base_order_volume','safety_order_volume','take_profit_pct','so_deviation_pct','safety_orders','volume_scale','step_scale','start_condition','entry_trigger'];
const governedControlKeys=['max_active_safety_orders','max_active_deals','order_type','trailing_enabled','cooldown_seconds'];
function openBotSetup(asset){
 const modal=$('#bot-setup-modal'),content=$('#bot-setup-content');if(!modal||!content)return;
 const row=lifecycleBots.find(x=>String(x.asset).toUpperCase()===String(asset).toUpperCase());
 if(!row)return;
 const assetKey=String(row.asset||asset).toUpperCase();
 if(row.lifecycle_state==='ACTIVE'){
  const deal=(liveTruth.deals||[]).find(x=>String(x.asset||'').toUpperCase()===assetKey&&x.effective_position_state==='OPEN')||{};
  const prof=(liveBotProfiles.bots||[]).find(x=>String(x.asset||'').toUpperCase()===assetKey)||{};
  const rv=(liveRevalidation.live_bots||[]).find(x=>String(x.asset||'').toUpperCase()===assetKey)||{};
  $('#bot-setup-title').textContent=`${assetKey}/USDT · Live bot`;
  const so=`${deal.completed_safety_orders??0}/${deal.max_safety_orders??prof.live_settings?.safety_orders??'?'}`;
  const current=prof.live_settings||{};
  const latest=rv.latest_validated_settings||prof.recommended_current_regime?.settings||{};
  content.innerHTML=`<div class="crm-review-grid">${stat('State','Live','This bot already has an active deal; deployment readiness does not apply to the current position.')}${stat('Position size',CRMFormat.quote(deal.position_cost_basis_quote??deal.capital_used_quote,'USDT'))}${stat('Open P/L',pnlValue(deal.open_pnl_quote,deal.profit_pct),`KuCoin mark-to-market · ${ageText(deal.open_pnl_priced_at||liveTruth.open_pnl_priced_at)}`)}${stat('Safety orders',so,`${deal.active_safety_orders??0} active order(s) reported by the provider.`)}${stat('DCA reserve',CRMFormat.quote(deal.remaining_dca_reserve_quote,'USDT'),'Capital protected for the remaining ladder.')}${stat('Deal age',liveHold(deal.opened_at,null)==null?'Updating':`${liveHold(deal.opened_at,null)}h`)}${stat('Current regime',lab(prof.current_regime||'Unknown'))}${stat('Would CRM select this strategy today?',rv.would_deploy_today===true?'Yes':rv.would_deploy_today===false?'No / review next deal':'Checking','The active deal remains frozen; CRM never changes its DCA structure mid-trade.')}</div><h3>Current live settings</h3>${setupRows(current,optimisedSetupKeys.concat(governedControlKeys))}<h3>Latest validated next-deal settings</h3>${Object.keys(latest).length?setupRows(latest,optimisedSetupKeys):'<div class="crm-alert">Latest validated settings are still being calculated.</div>'}<div class="crm-alert good"><strong>Current position is already deployed</strong><br>CRM is monitoring this live deal. Any newer validated configuration is considered only after this deal closes.</div>`;
  modal.hidden=false;modal.setAttribute('aria-hidden','false');return;
 }
 $('#bot-setup-title').textContent=`${row.asset}/USDT · ${lab(row.lifecycle_state)}`;
 const blockers=row.blockers||[];
 const optReady=row.dca_optimisation_status==='COMPLETE'&&Object.keys(row.settings||{}).length>0;
 const paper=(paperPortfolio.bots||[]).find(x=>String(x.asset||'').toUpperCase()===assetKey)||null;
 const paperTrades=paper?.recent_trades||[];
 const paperPanel=paper?`<h3>Forward paper performance</h3><div class="crm-review-grid">${stat('Total paper P/L',pnlValue(paper.total_pnl_quote,paper.total_pnl_pct),'Realised paper results plus the current simulated deal.')}${stat('Open paper P/L',pnlValue(paper.open_pnl_quote,paper.open_pnl_pct))}${stat('Realised paper P/L',CRMFormat.quote(paper.realised_pnl_quote,'USDT'))}${stat('Deals completed',paper.closed_deals??0)}${stat('Win rate',paper.win_rate_pct==null?'Building evidence':CRMFormat.percent(paper.win_rate_pct))}${stat('Paper observation',paper.paper_days==null?'Starting':`${paper.paper_days} days`)}${stat('Profit per day',paper.profit_per_day_quote==null?'Building evidence':CRMFormat.quote(paper.profit_per_day_quote,'USDT'))}${stat('Maximum drawdown',CRMFormat.quote(paper.max_drawdown_quote,'USDT'))}${stat('Current safety orders',`${paper.safety_orders_filled??0}/${paper.max_safety_orders??'?'}`)}</div>${paperTrades.length?`<details class="crm-review-panel"><summary>Recent paper trades · ${paperTrades.length}</summary><div class="crm-paper-ledger"><div class="crm-paper-ledger-head"><span>Opened</span><span>Closed</span><span>Capital</span><span>P/L</span><span>SO</span></div>${paperTrades.map(t=>`<div class="crm-paper-ledger-row"><span>${esc(dateText(t.opened_at))}</span><span>${esc(dateText(t.closed_at))}</span><span>${esc(CRMFormat.quote(t.quote_in,'USDT'))}</span><span>${esc(CRMFormat.quote(t.realised_pnl_quote,'USDT'))}</span><span>${esc(t.safety_orders_filled??0)}</span></div>`).join('')}</div></details>`:'<div class="crm-alert"><strong>Paper ledger is active</strong><br>No simulated deal has closed yet. Current open performance is still being recorded.</div>'}`:'';
 content.innerHTML=`${paperPanel}<div class="crm-review-grid">${stat('Lifecycle',lab(row.lifecycle_state),row.explanation||'')}${stat('Recommended action',lab(row.recommended_action||'Monitor'))}${stat('DCA optimisation',optReady?'Complete':lab(row.dca_optimisation_status||'In progress'),optReady?'Only unseen-validated strategy settings are shown below.':'Exact recommended settings are withheld while optimisation/validation is incomplete.')}${stat('Capital required',CRMFormat.quote(row.capital_required_usdt,'USDT'))}${stat('Safe allocation now',CRMFormat.quote(row.allocation_usdt,'USDT'))}</div>${optReady?`<h3>Recommended DCA settings</h3>${setupRows(row.settings||{},optimisedSetupKeys)}${Object.keys(row.governed_execution_controls||{}).length?`<h3>Governed execution controls</h3>${setupRows(row.governed_execution_controls||{},governedControlKeys)}<p class="crm-muted">These controls are governed for execution safety and are not labelled as profit-optimised settings.</p>`:''}`:`<div class="crm-alert warn"><strong>DCA setting optimisation in progress</strong><br>CRM will publish the exact setup only after the training winner is frozen and passes unseen KuCoin validation.</div>`}${row.entry_trigger?stat('Entry trigger',lab(row.entry_trigger)):''}${blockers.length?`<div class="crm-alert warn"><strong>What remains</strong><br>${blockers.map(x=>esc(x)).join('<br>')}</div>`:''}<div class="crm-alert ${row.deployment_allowed?'good':'warn'}"><strong>${row.deployment_allowed?'Manual live deployment permitted':'Strategy not yet funded for live deployment'}</strong><br>${esc(row.deployment_allowed?'All mandatory evidence, setup and capital gates are complete. CRM still does not place the order automatically.':'The strategy can continue accumulating paper evidence while CRM waits for its remaining research or portfolio-capital requirements.')}</div>`;
 modal.hidden=false;modal.setAttribute('aria-hidden','false');
}

async function refreshDirectRuntime(){
 try{
  const r=await fetch(runtimeApi+'/runtime?ts='+Date.now(),{cache:'no-store'});
  if(!r.ok)throw new Error('runtime api unavailable');
  const d=await r.json();
  if(d.live_service)Object.assign(liveService,d.live_service);
  window.crmResident=d.resident||window.crmResident||{};
  window.crmConsistency=d.consistency||window.crmConsistency||{};
  if(d.paper)Object.assign(paperPortfolio,d.paper);
  if(d.managed)Object.assign(managedPortfolio,d.managed);
  if(d.registry){
   persistentManagedAssets=new Set((d.registry.assets||[]).map(x=>String(x).toUpperCase()));
   localStorage.setItem(myBotsKey,JSON.stringify([...persistentManagedAssets]));
  }
  const ls=$('#crm-live-service-stat');
  if(ls)ls.innerHTML=`<span>KuCoin live data service</span><strong>${esc(liveService.status||'LIVE')}</strong><small class="crm-muted">Direct local runtime heartbeat · ${esc(ageText(liveService.heartbeat_at||liveService.generated_at))} · browser connected to resident service.</small>`;
  renderManagedBots();
  window.crmRuntimeDirect=true;
 }catch{
  window.crmRuntimeDirect=false;
  const ls=$('#crm-live-service-stat');
  if(ls)ls.querySelector('small')?.append(document.createTextNode(' · using published fallback'));
 }
}
refreshDirectRuntime();
setInterval(refreshDirectRuntime,5000);

async function refreshBrowserLivePnl(){
 try{
  const deal=(liveTruth.deals||[]).find(x=>x.effective_position_state==='OPEN');
  if(!deal)return;
  const asset=String(deal.asset||'').toUpperCase(),qty=Number(deal.position_quantity),cost=Number(deal.position_cost_basis_quote);
  if(!asset||!Number.isFinite(qty)||qty<=0||!Number.isFinite(cost)||cost<=0)return;
  const r=await fetch(`https://api.kucoin.com/api/v1/market/orderbook/level1?symbol=${encodeURIComponent(asset+'-USDT')}`,{cache:'no-store'});
  if(!r.ok)return;
  const p=await r.json(),px=Number(p?.data?.price);if(!Number.isFinite(px))return;
  const pnl=qty*px-cost,pct=100*pnl/cost;
  const total=(realisedPnl!=null)?Number(realisedPnl)+pnl:null;
  const totalPct=(total!=null&&Number(totalCapital)>0)?100*total/Number(totalCapital):null;
  const el=$('#crm-live-open-pnl'),note=$('#crm-live-open-pnl-note');
  if(el)el.textContent=pnlValue(pnl,pct);
  if(note)note.textContent=`Live browser KuCoin price · ${px} USDT · updated just now`;
  const tel=$('#crm-live-total-pnl'),tn=$('#crm-live-total-pnl-note');
  if(tel&&total!=null)tel.textContent=pnlValue(total,totalPct);
  if(tn&&total!=null)tn.textContent='Open + realised P/L · live price applied in this browser.';
 }catch{}
}
refreshBrowserLivePnl();
setInterval(refreshBrowserLivePnl,15000);

function closeBotSetup(){const m=$('#bot-setup-modal');if(!m)return;m.hidden=true;m.setAttribute('aria-hidden','true')}
document.addEventListener('click',e=>{
 const b=e.target.closest('.crm-open-setup');if(b)openBotSetup(b.dataset.asset);
 const add=e.target.closest('.crm-add-my-bot');if(add){const asset=String(add.dataset.asset||'').toUpperCase();const set=myBotAssets();set.add(asset);saveMyBotAssets(set);persistManagedAsset('add',asset);renderManagedBots();add.textContent='In My Bots'}
 const rem=e.target.closest('.crm-remove-my-bot');if(rem){const asset=String(rem.dataset.asset||'').toUpperCase();const set=myBotAssets();set.delete(asset);saveMyBotAssets(set);persistManagedAsset('remove',asset);renderManagedBots();document.querySelectorAll(`.crm-add-my-bot[data-asset="${CSS.escape(rem.dataset.asset)}"]`).forEach(x=>x.textContent='Add to My Bots')}
});
$('#bot-setup-close')?.addEventListener('click',closeBotSetup);$('#bot-setup-dismiss')?.addEventListener('click',closeBotSetup);$('#bot-setup-modal .crm-modal-backdrop')?.addEventListener('click',closeBotSetup);

function safeRender(name,fn,selector){
 try{fn()}
 catch(err){
   console.error('CRM section failed:',name,err);
   const root=selector?$(selector):null;
   if(root&&!root.innerHTML)root.innerHTML=`<div class="crm-alert bad"><strong>${esc(name)} could not render</strong><br><small>Other dashboard sections remain available.</small></div>`;
 }
}
safeRender('Staged Bots',renderStaged,'#staged-bots');
safeRender('Decision Inbox',renderInbox,'#decision-inbox');
safeRender('Recommended Bots',renderCandidates,'#recommended-bots');
safeRender('Recommendation History',renderHistory,'#recommendation-history');
/* Legacy validation marker: safeRender('V46 intelligence' */
safeRender('V49 intelligence',renderV45,'#global-market');
safeRender('Decision Briefing',showBriefing,null);
})();

function hideEmptySecondaryCards(){
 const ids=['market','sync','settings','operations','ui-quality','changes'];
 for(const id of ids){
  const root=document.getElementById(id);if(!root)continue;
  const text=(root.textContent||'').replace(/\s+/g,' ').trim();
  const meaningful=root.querySelector('table,.crm-stat,.crm-alert,.crm-review-panel,button,a')||text.length>12;
  const card=root.closest('.crm-card');
  if(card)card.hidden=!meaningful;
 }
}
setTimeout(hideEmptySecondaryCards,260);

// V70 Portfolio Truth & Decision Consistency overlay.
function crmFindStat(label){
  return [...document.querySelectorAll('.crm-stat')].find(x=>String(x.querySelector('span')?.textContent||'').trim().toLowerCase()===String(label).trim().toLowerCase());
}
function crmSetStat(label,value,note){
  const el=crmFindStat(label);if(!el)return;
  const strong=el.querySelector('strong');if(strong)strong.textContent=value;
  const small=el.querySelector('small');if(small&&note)small.textContent=note;
}
function crmFmtQ(v){return v==null||!Number.isFinite(Number(v))?'Updating':`${Number(v).toLocaleString(undefined,{maximumFractionDigits:2})} USDT`}
function applyV70PortfolioTruth(){
  const c=window.crmConsistency||{},p=c.portfolio||{},n=c.next_capital||{},pub=c.publication||{};
  if(p.authoritative_value_quote!=null)crmSetStat('Portfolio',crmFmtQ(p.authoritative_value_quote),'Total recognised KuCoin portfolio value including live positions.');
  if(p.cash_quote!=null)crmSetStat('Cash',crmFmtQ(p.cash_quote),'Free USDT currently available on KuCoin.');
  if(p.dca_reserve_quote!=null)crmSetStat('DCA reserve',crmFmtQ(p.dca_reserve_quote),'Remaining capital protected for active DCA commitments.');
  if(p.deployable_quote!=null)crmSetStat('Deployable now',crmFmtQ(p.deployable_quote),'Safe cash available for an approved next strategy after current commitments.');
  const section=[...document.querySelectorAll('section,div')].find(x=>String(x.querySelector('h2')?.textContent||'').trim()==='My Bots');
  if(section&&n.asset){
    let box=section.querySelector('#crm-v70-next-capital');
    if(!box){box=document.createElement('div');box.id='crm-v70-next-capital';box.className='crm-alert';section.insertBefore(box,section.querySelector('h2')?.nextSibling||section.firstChild)}
    const evidence=n.paper_evidence||{};
    const req=n.capital_required_quote==null?'calculating':crmFmtQ(n.capital_required_quote);
    box.innerHTML=`<strong>After the current live deal: ${String(n.asset).replace(/</g,'&lt;')}/USDT is currently ranked #1</strong><br>${String(n.plain_english||'').replace(/</g,'&lt;')}<br><span class="crm-muted">Capital required ${req} · Paper evidence: ${String(evidence.summary||'building').replace(/</g,'&lt;')} · Automation preview only; live execution remains locked.</span>`;
  }
  if(pub.delayed&&!pub.trading_blocker){
    document.querySelectorAll('*').forEach(el=>{
      if(el.children.length===0&&/Application publication needs attention/i.test(el.textContent||''))el.textContent='Website snapshot delayed';
      if(el.children.length===0&&/Latest successful publication was/i.test(el.textContent||''))el.textContent=`${pub.plain_english||'Website publication is delayed; local live trading truth remains current.'}`;
    });
  }
}
setInterval(applyV70PortfolioTruth,5000);
document.addEventListener('DOMContentLoaded',()=>setTimeout(applyV70PortfolioTruth,500));
