/**
 * ProcessPulse Chart.js Visualizations
 */

let slaChartInstance = null;
let deptChartInstance = null;
let bottleneckChartInstance = null;

export function renderSlaChart(canvasId, slaData) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;

  if (slaChartInstance) {
    slaChartInstance.destroy();
  }

  slaChartInstance = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['Within Target SLA', 'SLA Breached'],
      datasets: [{
        data: [slaData.within_sla_count, slaData.breached_sla_count],
        backgroundColor: ['#10b981', '#f43f5e'],
        borderColor: '#1e293b',
        borderWidth: 3,
        hoverOffset: 6
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'bottom',
          labels: { color: '#94a3b8', font: { size: 12, family: 'Inter' } }
        }
      },
      cutout: '72%'
    }
  });
}

export function renderDeptChart(canvasId, deptMetrics) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;

  if (deptChartInstance) {
    deptChartInstance.destroy();
  }

  const labels = deptMetrics.map(d => d.department_name);
  const durations = deptMetrics.map(d => d.median_handling_hours);
  const breachRates = deptMetrics.map(d => d.sla_breach_rate_percent);

  deptChartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [
        {
          label: 'Median Handling Time (Hours)',
          data: durations,
          backgroundColor: '#38bdf8',
          borderRadius: 6,
          yAxisID: 'y'
        },
        {
          label: 'SLA Breach Rate (%)',
          data: breachRates,
          backgroundColor: '#f59e0b',
          borderRadius: 6,
          yAxisID: 'y1'
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: {
          ticks: { color: '#94a3b8' },
          grid: { color: '#1e293b' }
        },
        y: {
          type: 'linear',
          position: 'left',
          ticks: { color: '#94a3b8' },
          grid: { color: '#1e293b' },
          title: { display: true, text: 'Hours', color: '#94a3b8' }
        },
        y1: {
          type: 'linear',
          position: 'right',
          ticks: { color: '#f59e0b' },
          grid: { drawOnChartArea: false },
          title: { display: true, text: 'Breach %', color: '#f59e0b' }
        }
      },
      plugins: {
        legend: {
          labels: { color: '#94a3b8', font: { size: 12, family: 'Inter' } }
        }
      }
    }
  });
}

export function renderBottleneckChart(canvasId, bottlenecks) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;

  if (bottleneckChartInstance) {
    bottleneckChartInstance.destroy();
  }

  const labels = bottlenecks.map(b => b.stage_name);
  const bsiScores = bottlenecks.map(b => b.bottleneck_severity_index);
  const costs = bottlenecks.map(b => b.financial_cost_of_delay_usd);

  bottleneckChartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [
        {
          label: 'Bottleneck Severity Index (BSI)',
          data: bsiScores,
          backgroundColor: bsiScores.map(score => score >= 0.28 ? '#f43f5e' : '#86bc25'),
          borderRadius: 6
        }
      ]
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: {
          ticks: { color: '#94a3b8' },
          grid: { color: '#1e293b' },
          title: { display: true, text: 'BSI Score (Higher = Critical Drag)', color: '#94a3b8' }
        },
        y: {
          ticks: { color: '#f1f5f9', font: { size: 11 } },
          grid: { color: '#1e293b' }
        }
      },
      plugins: {
        legend: { display: false }
      }
    }
  });
}
