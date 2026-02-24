/**
 * Usage Routes — API usage dashboard data
 *
 * GET /api/usage/summary  — Daily rollups for chart (last 30 days)
 * GET /api/usage/recent   — Last 100 individual API calls
 * GET /api/usage/totals   — Current month totals by provider
 */

const express = require('express');
const router = express.Router();
const sheets = require('../services/sheetsService');

/**
 * GET /api/usage/summary
 *
 * Returns daily rollups for the dashboard chart.
 * Query params: ?days=30 (default)
 */
router.get('/summary', async (req, res) => {
  try {
    const days = parseInt(req.query.days) || 30;
    const data = await sheets.readUsageDailyRollups(days);
    res.json({ data, days });
  } catch (err) {
    console.error('[USAGE/SUMMARY] Error:', err.message);
    res.status(500).json({ error: `Failed to load usage summary: ${err.message}` });
  }
});

/**
 * GET /api/usage/recent
 *
 * Returns the most recent individual API calls.
 * Query params: ?limit=100 (default)
 */
router.get('/recent', async (req, res) => {
  try {
    const limit = Math.min(parseInt(req.query.limit) || 100, 500);
    const data = await sheets.readUsageRecent(limit);
    res.json({ data, limit });
  } catch (err) {
    console.error('[USAGE/RECENT] Error:', err.message);
    res.status(500).json({ error: `Failed to load recent usage: ${err.message}` });
  }
});

/**
 * GET /api/usage/totals
 *
 * Returns current month totals grouped by provider (for header cards).
 */
router.get('/totals', async (req, res) => {
  try {
    // Get this month's daily rollups
    const now = new Date();
    const monthStart = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-01`;
    const data = await sheets.readUsageDailyRollups(now.getDate());

    // Filter to current month and aggregate by provider
    const totals = {};
    let totalCost = 0;
    let totalTokens = 0;
    const providers = new Set();

    for (const entry of data) {
      if (entry.date < monthStart) continue;

      const p = entry.provider;
      providers.add(p);

      if (!totals[p]) {
        totals[p] = { inputTokens: 0, outputTokens: 0, cost: 0, callCount: 0 };
      }
      totals[p].inputTokens += entry.inputTokens;
      totals[p].outputTokens += entry.outputTokens;
      totals[p].cost += entry.cost;
      totals[p].callCount += entry.callCount;
      totalCost += entry.cost;
      totalTokens += entry.inputTokens + entry.outputTokens;
    }

    res.json({
      month: monthStart.slice(0, 7),
      totalCost: Math.round(totalCost * 100) / 100,
      totalTokens,
      activeProviders: providers.size,
      byProvider: totals,
    });
  } catch (err) {
    console.error('[USAGE/TOTALS] Error:', err.message);
    res.status(500).json({ error: `Failed to load usage totals: ${err.message}` });
  }
});

module.exports = router;
