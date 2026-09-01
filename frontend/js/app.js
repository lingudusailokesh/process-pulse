/**
 * ProcessPulse Main Application Coordinator (ES6+ Vanilla JavaScript)
 */

import { api } from './api.js';
import { renderSlaChart, renderDeptChart, renderBottleneckChart } from './charts.js';
import { renderProcessGraph, fitProcessGraph } from './processGraph.js';

// Application State
const state = {
  currentProcess: 'ONBOARD_V1',
  kpis: null,
  bottlenecks: [],
  departments: [],
  sla: null,
  dfg: null,
  variants: [],
  triageQueue: [],
  aiAdvisory: null,
  loading: false
};

// Initialize Application
document.addEventListener('DOMContentLoaded', async () => {
  setupNavigation();
  setupEventListeners();
  await loadDashboardData();

  window.addEventListener('resize', () => {
    fitProcessGraph();
  });
});

function setupNavigation() {
  const tabs = document.querySelectorAll('.nav-tab');
  tabs.forEach(tab => {
    tab.addEventListener('click', (e) => {
      e.preventDefault();
      tabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');

      const targetId = tab.getAttribute('data-target');
      document.querySelectorAll('.tab-content').forEach(section => {
        section.classList.add('hidden');
      });
      const targetSection = document.getElementById(targetId);
      if (targetSection) {
        targetSection.classList.remove('hidden');
        if (targetId === 'tab-process-mining') {
          setTimeout(() => fitProcessGraph(), 60);
        }
      }
    });
  });
}

function setupEventListeners() {
  const refreshBtn = document.getElementById('btn-refresh');
  if (refreshBtn) {
    refreshBtn.addEventListener('click', async () => {
      await loadDashboardData();
    });
  }

  const aiRefreshBtn = document.getElementById('btn-ai-refresh');
  if (aiRefreshBtn) {
    aiRefreshBtn.addEventListener('click', async () => {
      await loadAIAdvisory(true);
    });
  }

  const closeModalBtn = document.getElementById('btn-close-modal');
  if (closeModalBtn) {
    closeModalBtn.addEventListener('click', () => {
      document.getElementById('node-modal').classList.add('hidden');
    });
  }
}

async function loadDashboardData() {
  setLoadingState(true);
  try {
    // 1. Fetch Parallel Data
    const [kpis, bottlenecks, departments, sla, dfg, variants, triage] = await Promise.all([
      api.getOverviewKPIs(state.currentProcess),
      api.getBottlenecks(state.currentProcess),
      api.getDepartments(state.currentProcess),
      api.getSlaDistribution(state.currentProcess),
      api.getDFG(state.currentProcess),
      api.getVariants(state.currentProcess),
      api.getTriageQueue(state.currentProcess)
    ]);

    state.kpis = kpis;
    state.bottlenecks = bottlenecks;
    state.departments = departments;
    state.sla = sla;
    state.dfg = dfg;
    state.variants = variants.variants || [];
    state.triageQueue = triage || [];

    // 2. Render Components
    renderKpis(kpis);
    renderProcessGraph('cy-container', dfg, handleNodeClick);
    renderBottlenecksTable(bottlenecks);
    renderTriageQueueTable(state.triageQueue);
    renderVariantsList(state.variants);
    
    // 3. Render Charts
    renderSlaChart('sla-chart-canvas', sla);
    renderDeptChart('dept-chart-canvas', departments);
    renderBottleneckChart('bottleneck-chart-canvas', bottlenecks);

    // 4. Load AI Advisory in background
    loadAIAdvisory(false);

  } catch (error) {
    console.error('Failed to load dashboard telemetry:', error);
    showToast('Failed to connect to backend service. Ensure FastAPI server is running.', 'error');
  } finally {
    setLoadingState(false);
  }
}

function renderKpis(kpis) {
  if (!kpis) return;
  document.getElementById('kpi-total-cases').textContent = kpis.total_cases.toLocaleString();
  document.getElementById('kpi-median-time').textContent = `${kpis.median_cycle_time_hours}h`;
  document.getElementById('kpi-sla-rate').textContent = `${kpis.sla_compliance_rate_percent}%`;
  document.getElementById('kpi-rework-rate').textContent = `${kpis.rework_case_rate_percent}%`;
  document.getElementById('kpi-waste-cost').textContent = `$${kpis.total_financial_waste_usd.toLocaleString()}`;

  // Dynamic completed vs active subtext
  const casesSub = document.getElementById('kpi-cases-sub');
  if (casesSub && kpis.completed_cases !== undefined && kpis.active_cases !== undefined) {
    casesSub.textContent = `${kpis.completed_cases.toLocaleString()} Completed | ${kpis.active_cases.toLocaleString()} Active`;
  }

  // Target comparisons
  const diffHours = kpis.median_cycle_time_hours - kpis.sla_target_hours;
  const timeSub = document.getElementById('kpi-median-time-sub');
  if (timeSub) {
    timeSub.textContent = diffHours > 0 
      ? `+${diffHours.toFixed(1)}h over SLA target (${kpis.sla_target_hours}h)`
      : `Within SLA target (${kpis.sla_target_hours}h)`;
    timeSub.className = diffHours > 0 ? 'text-xs text-rose-400 mt-1' : 'text-xs text-emerald-400 mt-1';
  }

  const wasteSub = document.getElementById('kpi-waste-cost-sub');
  if (wasteSub && kpis.case_sla_breach_waste_usd !== undefined) {
    wasteSub.textContent = `Sum of Stage Delays | Breach Penalty: $${kpis.case_sla_breach_waste_usd.toLocaleString()}`;
  }
}

function renderBottlenecksTable(bottlenecks) {
  const tbody = document.getElementById('bottlenecks-table-body');
  if (!tbody) return;
  tbody.innerHTML = '';

  bottlenecks.forEach((b, idx) => {
    const tr = document.createElement('tr');
    tr.className = 'border-b border-slate-800 hover:bg-slate-800/40 transition-colors';

    const bsiBadge = b.is_critical_bottleneck
      ? `<span class="px-2.5 py-1 text-xs font-semibold rounded-full badge-risk-critical">CRITICAL (BSI: ${b.bottleneck_severity_index})</span>`
      : `<span class="px-2.5 py-1 text-xs font-semibold rounded-full badge-risk-low">MODERATE (BSI: ${b.bottleneck_severity_index})</span>`;

    tr.innerHTML = `
      <td class="py-3 px-4 text-sm font-medium text-slate-200">
        <span class="text-xs text-slate-500 mr-1.5 font-mono">#${idx + 1}</span> ${b.stage_name}
      </td>
      <td class="py-3 px-4 text-sm text-slate-400">${b.department_name}</td>
      <td class="py-3 px-4 text-sm font-semibold text-slate-200">${b.median_duration_hours} hrs</td>
      <td class="py-3 px-4 text-sm ${b.rework_rate_percent > 10 ? 'text-rose-400 font-semibold' : 'text-slate-400'}">${b.rework_rate_percent}%</td>
      <td class="py-3 px-4 text-sm">${bsiBadge}</td>
      <td class="py-3 px-4 text-sm font-semibold text-emerald-400 font-mono">$${b.financial_cost_of_delay_usd.toLocaleString()}</td>
    `;
    tbody.appendChild(tr);
  });
}

function renderTriageQueueTable(triageItems) {
  const badge = document.getElementById('triage-badge-count');
  if (badge) {
    badge.textContent = `${triageItems.length} Active In-Progress Cases Evaluated`;
  }

  const tbody = document.getElementById('triage-table-body');
  if (!tbody) return;
  tbody.innerHTML = '';

  if (triageItems.length === 0) {
    tbody.innerHTML = `<tr><td colspan="6" class="text-center py-6 text-slate-500">No active in-progress cases in system.</td></tr>`;
    return;
  }

  triageItems.forEach(item => {
    const tr = document.createElement('tr');
    tr.className = 'border-b border-slate-800 hover:bg-slate-800/40 transition-colors';

    let badgeClass = 'badge-risk-low';
    if (item.risk_level === 'CRITICAL') badgeClass = 'badge-risk-critical';
    else if (item.risk_level === 'HIGH') badgeClass = 'badge-risk-high';

    const probPct = Math.round(item.breach_probability * 100);

    tr.innerHTML = `
      <td class="py-3 px-4 text-xs font-mono text-cyan-400 font-semibold">${item.case_id}</td>
      <td class="py-3 px-4 text-sm text-slate-300 font-medium">${item.department_id}</td>
      <td class="py-3 px-4 text-sm text-slate-400">${item.current_stage}</td>
      <td class="py-3 px-4 text-sm text-slate-300 font-mono">${item.elapsed_hours}h</td>
      <td class="py-3 px-4">
        <div class="flex items-center gap-2">
          <div class="w-20 bg-slate-700 h-2 rounded-full overflow-hidden">
            <div class="h-full ${probPct > 60 ? 'bg-rose-500' : 'bg-amber-400'}" style="width: ${probPct}%"></div>
          </div>
          <span class="text-xs font-semibold ${probPct > 60 ? 'text-rose-400' : 'text-amber-400'} font-mono">${probPct}%</span>
        </div>
      </td>
      <td class="py-3 px-4">
        <span class="px-2 py-0.5 text-xs font-semibold rounded-md ${badgeClass}">${item.risk_level}</span>
      </td>
      <td class="py-3 px-4 text-xs text-slate-300">${item.suggested_action}</td>
    `;
    tbody.appendChild(tr);
  });
}

function renderVariantsList(variants) {
  const container = document.getElementById('variants-list-container');
  if (!container) return;
  container.innerHTML = '';

  variants.forEach((v, idx) => {
    const div = document.createElement('div');
    div.className = 'p-4 rounded-lg bg-slate-900/60 border border-slate-800 hover:border-slate-700 transition-all';

    const isHappy = v.is_happy_path;
    const badge = isHappy 
      ? `<span class="px-2.5 py-0.5 text-xs font-semibold rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">HAPPY PATH (${v.percentage}%)</span>`
      : `<span class="px-2.5 py-0.5 text-xs font-semibold rounded-full bg-rose-500/20 text-rose-400 border border-rose-500/30">DEVIATION / REWORK (${v.percentage}%)</span>`;

    const stepsHtml = v.path.map((p, i) => `
      <span class="inline-flex items-center text-xs font-medium ${p.includes('REJECTED') ? 'text-rose-400 font-bold' : 'text-slate-300'}">
        ${p}
        ${i < v.path.length - 1 ? '<svg class="w-3.5 h-3.5 mx-1 text-slate-600 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>' : ''}
      </span>
    `).join('');

    div.innerHTML = `
      <div class="flex items-center justify-between mb-2">
        <div class="flex items-center gap-2">
          <span class="text-sm font-semibold text-slate-200">Variant #${idx + 1} (${v.variant_id})</span>
          ${badge}
        </div>
        <div class="text-xs text-slate-400 font-mono">
          Avg Duration: <strong class="text-slate-200">${v.avg_duration_hours}h</strong> | SLA Breach: <strong class="text-rose-400">${v.sla_breach_rate_percent}%</strong>
        </div>
      </div>
      <p class="text-xs text-slate-400 mb-3">${v.description}</p>
      <div class="p-2.5 rounded bg-slate-950/80 border border-slate-800/80 flex flex-wrap items-center">
        ${stepsHtml}
      </div>
    `;
    container.appendChild(div);
  });
}

async function loadAIAdvisory(force = false) {
  const container = document.getElementById('ai-advisory-container');
  if (!container) return;

  if (state.aiAdvisory && !force) {
    renderAIAdvisory(state.aiAdvisory);
    return;
  }

  container.innerHTML = `
    <div class="p-8 text-center text-slate-400">
      <div class="inline-block animate-spin w-6 h-6 border-2 border-deloitte-green border-t-transparent rounded-full mb-3"></div>
      <p class="text-sm">Synthesizing grounded executive advisory from deterministic metrics...</p>
    </div>
  `;

  try {
    const advisory = await api.getAIAdvisory(state.currentProcess);
    state.aiAdvisory = advisory;
    renderAIAdvisory(advisory);
  } catch (err) {
    container.innerHTML = `<div class="p-4 text-xs text-rose-400 bg-rose-950/30 rounded border border-rose-900">Failed to generate AI brief: ${err.message}</div>`;
  }
}

function renderAIAdvisory(adv) {
  const container = document.getElementById('ai-advisory-container');
  if (!container || !adv) return;

  const recsHtml = adv.recommendations.map(r => `
    <div class="p-4 rounded-lg bg-slate-800/50 border border-slate-700 hover:border-deloitte-green/40 transition-all">
      <div class="flex items-center justify-between mb-1.5">
        <div class="flex items-center gap-2">
          <span class="px-2 py-0.5 text-xs font-bold rounded bg-cyan-950 text-cyan-400 border border-cyan-800">${r.category}</span>
          <h4 class="text-sm font-semibold text-slate-100">${r.title}</h4>
        </div>
        <span class="text-xs font-semibold px-2 py-0.5 rounded bg-amber-950 text-amber-300 border border-amber-800">${r.implementation_priority}</span>
      </div>
      <p class="text-xs text-slate-300 mb-2">${r.description}</p>
      <div class="flex items-center gap-4 text-xs text-slate-400 font-mono">
        <span>Target Stage: <strong class="text-slate-200">${r.target_stage}</strong></span>
        <span>Est. Cycle Time Cut: <strong class="text-emerald-400">-${r.expected_cycle_time_reduction_percent}%</strong></span>
        <span>Est. Annual ROI: <strong class="text-emerald-400">+$${r.estimated_annual_cost_savings_usd.toLocaleString()}</strong></span>
      </div>
    </div>
  `).join('');

  const rootCausesHtml = adv.root_causes.map(rc => `
    <li class="text-xs text-slate-300 mb-2 flex items-start gap-2">
      <span class="w-1.5 h-1.5 rounded-full bg-rose-500 mt-1.5 shrink-0"></span>
      <div>
        <strong class="text-slate-100">${rc.stage_name} (${rc.department}):</strong> ${rc.observed_metric} — <span class="text-slate-400">${rc.business_impact}</span>
      </div>
    </li>
  `).join('');

  container.innerHTML = `
    <div class="space-y-6">
      <div class="p-4 rounded-lg bg-slate-800/40 border border-slate-700">
        <div class="flex items-center justify-between mb-2">
          <h3 class="text-xs font-bold uppercase tracking-wider text-deloitte-green">Executive Health Score</h3>
          <span class="text-xs font-bold px-2.5 py-1 rounded bg-slate-900 text-deloitte-green border border-deloitte-green/30">${adv.overall_health_score}</span>
        </div>
        <p class="text-sm text-slate-200 leading-relaxed">${adv.executive_summary}</p>
      </div>

      <div>
        <h4 class="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3">Root Cause Diagnosis</h4>
        <ul class="space-y-1.5">${rootCausesHtml}</ul>
      </div>

      <div>
        <h4 class="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3">Prioritized Strategic Recommendations (ROI Roadmap)</h4>
        <div class="space-y-3">${recsHtml}</div>
      </div>
    </div>
  `;
}

function handleNodeClick(nodeData) {
  const modal = document.getElementById('node-modal');
  if (!modal || !nodeData) return;

  document.getElementById('modal-node-title').textContent = nodeData.label;
  document.getElementById('modal-node-dept').textContent = nodeData.department_id || 'Cross-Department';
  document.getElementById('modal-node-count').textContent = `${nodeData.unique_cases_count} Unique Cases (${nodeData.execution_count} Total Events)`;
  document.getElementById('modal-node-median').textContent = `${nodeData.median_duration_hours} hrs`;
  document.getElementById('modal-node-avg').textContent = `${nodeData.avg_duration_hours} hrs`;
  document.getElementById('modal-node-status').textContent = nodeData.is_bottleneck ? 'CRITICAL BOTTLENECK' : 'NOMINAL';
  document.getElementById('modal-node-status').className = nodeData.is_bottleneck 
    ? 'text-xs font-bold px-2 py-0.5 rounded badge-risk-critical' 
    : 'text-xs font-bold px-2 py-0.5 rounded badge-risk-low';

  modal.classList.remove('hidden');
}

function setLoadingState(isLoading) {
  state.loading = isLoading;
  const indicator = document.getElementById('loading-indicator');
  if (indicator) {
    if (isLoading) indicator.classList.remove('hidden');
    else indicator.classList.add('hidden');
  }
}

function showToast(msg, type = 'info') {
  console.log(`[Toast ${type}]:`, msg);
}
