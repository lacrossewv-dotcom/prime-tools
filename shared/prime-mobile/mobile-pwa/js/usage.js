/**
 * Usage Module — API usage dashboard
 *
 * Shows cost tracking, token consumption, and provider breakdown
 * using Chart.js for visualization.
 */

const usage = (() => {
  let dailyChart = null;
  let providerChart = null;

  // Provider colors for charts (matches dark theme accents)
  const PROVIDER_COLORS = {
    gemini: '#4dabf7',
    claude: '#e91e8c',
    groq: '#00cc66',
    chroma: '#ffc107',
    openai: '#ff6b35',
    jules: '#9b59b6',
  };

  /**
   * Load the usage dashboard data.
   */
  async function load() {
    try {
      // Fetch totals and summary in parallel
      const [totalsRes, summaryRes, recentRes] = await Promise.all([
        api.get('/api/usage/totals'),
        api.get('/api/usage/summary?days=30'),
        api.get('/api/usage/recent?limit=50'),
      ]);

      renderCards(totalsRes);
      renderDailyChart(summaryRes.data);
      renderProviderChart(totalsRes.byProvider);
      renderRecentTable(recentRes.data);
    } catch (err) {
      console.error('[USAGE] Load error:', err);
      document.getElementById('usage-content').innerHTML =
        '<div class="loading">Failed to load usage data. Sync logs first.</div>';
    }
  }

  /**
   * Render the 3 header cards.
   */
  function renderCards(totals) {
    document.getElementById('usage-cost-mtd').textContent =
      '$' + (totals.totalCost || 0).toFixed(2);
    document.getElementById('usage-tokens-mtd').textContent =
      formatTokens(totals.totalTokens || 0);
    document.getElementById('usage-providers').textContent =
      totals.activeProviders || 0;
  }

  /**
   * Format large token numbers (e.g., 1.2M, 450K).
   */
  function formatTokens(n) {
    if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + 'M';
    if (n >= 1_000) return (n / 1_000).toFixed(1) + 'K';
    return n.toString();
  }

  /**
   * Render the daily cost stacked bar chart.
   */
  function renderDailyChart(data) {
    const canvas = document.getElementById('usage-daily-chart');
    if (!canvas) return;

    // Group by date, then by provider
    const byDate = {};
    const providers = new Set();
    for (const entry of data) {
      if (!byDate[entry.date]) byDate[entry.date] = {};
      byDate[entry.date][entry.provider] = (byDate[entry.date][entry.provider] || 0) + entry.cost;
      providers.add(entry.provider);
    }

    const dates = Object.keys(byDate).sort();
    const datasets = [];
    for (const provider of providers) {
      datasets.push({
        label: provider,
        data: dates.map(d => byDate[d][provider] || 0),
        backgroundColor: PROVIDER_COLORS[provider] || '#888',
      });
    }

    if (dailyChart) dailyChart.destroy();
    dailyChart = new Chart(canvas, {
      type: 'bar',
      data: {
        labels: dates.map(d => d.slice(5)), // MM-DD
        datasets,
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            labels: { color: '#e0e0e0', font: { size: 11 } },
          },
          tooltip: {
            callbacks: {
              label: ctx => `${ctx.dataset.label}: $${ctx.parsed.y.toFixed(4)}`,
            },
          },
        },
        scales: {
          x: {
            stacked: true,
            ticks: { color: '#8892a0', font: { size: 10 } },
            grid: { color: '#2a2a4a' },
          },
          y: {
            stacked: true,
            ticks: {
              color: '#8892a0',
              font: { size: 10 },
              callback: v => '$' + v.toFixed(2),
            },
            grid: { color: '#2a2a4a' },
          },
        },
      },
    });
  }

  /**
   * Render the provider breakdown doughnut chart.
   */
  function renderProviderChart(byProvider) {
    const canvas = document.getElementById('usage-provider-chart');
    if (!canvas || !byProvider) return;

    const providers = Object.keys(byProvider);
    const costs = providers.map(p => byProvider[p].cost);
    const colors = providers.map(p => PROVIDER_COLORS[p] || '#888');

    if (providerChart) providerChart.destroy();
    providerChart = new Chart(canvas, {
      type: 'doughnut',
      data: {
        labels: providers,
        datasets: [{
          data: costs,
          backgroundColor: colors,
          borderWidth: 0,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'bottom',
            labels: { color: '#e0e0e0', font: { size: 11 }, padding: 12 },
          },
          tooltip: {
            callbacks: {
              label: ctx => {
                const total = costs.reduce((a, b) => a + b, 0);
                const pct = total > 0 ? ((ctx.parsed / total) * 100).toFixed(1) : 0;
                return `${ctx.label}: $${ctx.parsed.toFixed(4)} (${pct}%)`;
              },
            },
          },
        },
      },
    });
  }

  /**
   * Render the recent API calls table.
   */
  function renderRecentTable(data) {
    const tbody = document.getElementById('usage-recent-body');
    if (!tbody) return;

    if (!data || data.length === 0) {
      tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;color:var(--text-muted)">No usage data yet</td></tr>';
      return;
    }

    tbody.innerHTML = data.map(entry => {
      const time = entry.timestamp ? new Date(entry.timestamp).toLocaleString('en-US', {
        month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
      }) : '-';
      const providerClass = `provider-${entry.provider}`;
      const tokens = formatTokens(entry.inputTokens + entry.outputTokens);
      const cost = entry.cost > 0 ? '$' + entry.cost.toFixed(4) : 'free';

      return `<tr>
        <td>${time}</td>
        <td><span class="usage-provider-tag ${providerClass}">${entry.provider}</span></td>
        <td class="td-truncate">${entry.model}</td>
        <td>${entry.task}</td>
        <td>${tokens}</td>
        <td>${cost}</td>
      </tr>`;
    }).join('');
  }

  return { load };
})();
