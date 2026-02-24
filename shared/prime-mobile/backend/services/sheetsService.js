/**
 * Google Sheets Service — Usage Dashboard Data
 *
 * Reads _USAGE and _USAGE_DAILY tabs from the PRIME Data Catalog sheet.
 * Reuses the same OAuth pattern as googleDrive.js.
 */

const { google } = require('googleapis');

const SPREADSHEET_ID = '1Vijb9kxxRUUaKJ9ZUD6CR6RyB0uFSG-t_ZxNC1F5rmc';
const USAGE_TAB = '_USAGE';
const DAILY_TAB = '_USAGE_DAILY';

let sheetsClient = null;

/**
 * Get OAuth2 client (same pattern as googleDrive.js).
 */
function getOAuth2Client() {
  const oauth2Client = new google.auth.OAuth2(
    process.env.GOOGLE_CLIENT_ID,
    process.env.GOOGLE_CLIENT_SECRET
  );

  oauth2Client.setCredentials({
    refresh_token: process.env.GOOGLE_REFRESH_TOKEN,
  });

  return oauth2Client;
}

/**
 * Get Sheets client (lazy initialization).
 */
function getSheets() {
  if (!sheetsClient) {
    sheetsClient = google.sheets({ version: 'v4', auth: getOAuth2Client() });
  }
  return sheetsClient;
}

/**
 * Read daily rollup data for the dashboard chart.
 *
 * @param {number} days - Number of days to return (default 30)
 * @returns {Array<Object>} Array of { date, provider, model, inputTokens, outputTokens, cost, callCount }
 */
async function readUsageDailyRollups(days = 30) {
  const sheets = getSheets();

  const result = await sheets.spreadsheets.values.get({
    spreadsheetId: SPREADSHEET_ID,
    range: `${DAILY_TAB}!A:G`,
  });

  const rows = result.data.values || [];
  if (rows.length <= 1) return []; // header only

  // Parse rows (skip header), sorted by date desc in the sheet
  const cutoff = new Date();
  cutoff.setDate(cutoff.getDate() - days);
  const cutoffStr = cutoff.toISOString().slice(0, 10);

  const data = [];
  for (const row of rows.slice(1)) {
    if (row.length < 7) continue;
    const date = row[0];
    if (date < cutoffStr) continue;

    data.push({
      date,
      provider: row[1],
      model: row[2],
      inputTokens: parseInt(row[3]) || 0,
      outputTokens: parseInt(row[4]) || 0,
      cost: parseFloat(row[5]) || 0,
      callCount: parseInt(row[6]) || 0,
    });
  }

  return data;
}

/**
 * Read recent individual usage entries.
 *
 * @param {number} limit - Max number of entries (default 100)
 * @returns {Array<Object>} Recent entries, newest first
 */
async function readUsageRecent(limit = 100) {
  const sheets = getSheets();

  const result = await sheets.spreadsheets.values.get({
    spreadsheetId: SPREADSHEET_ID,
    range: `${USAGE_TAB}!A:I`,
  });

  const rows = result.data.values || [];
  if (rows.length <= 1) return [];

  // Parse all rows (skip header), return newest first
  const data = rows.slice(1).map(row => ({
    timestamp: row[0] || '',
    provider: row[1] || '',
    model: row[2] || '',
    task: row[3] || '',
    inputTokens: parseInt(row[4]) || 0,
    outputTokens: parseInt(row[5]) || 0,
    cost: parseFloat(row[6]) || 0,
    session: row[7] || 'unknown',
    source: row[8] || 'cli',
  }));

  // Sort newest first, then limit
  data.sort((a, b) => b.timestamp.localeCompare(a.timestamp));
  return data.slice(0, limit);
}

/**
 * Append a single usage entry to the _USAGE sheet.
 * Used by chat routes to log PRIME Mobile chat usage.
 *
 * @param {Object} entry - { provider, model, task, inputTokens, outputTokens, cost, session, source }
 */
async function appendUsageEntry(entry) {
  const sheets = getSheets();

  const row = [
    new Date().toISOString(),
    entry.provider || '',
    entry.model || '',
    entry.task || 'chat',
    entry.inputTokens || 0,
    entry.outputTokens || 0,
    entry.cost || 0,
    entry.session || 'prime-mobile',
    entry.source || 'prime-mobile-chat',
  ];

  await sheets.spreadsheets.values.append({
    spreadsheetId: SPREADSHEET_ID,
    range: `${USAGE_TAB}!A:I`,
    valueInputOption: 'RAW',
    insertDataOption: 'INSERT_ROWS',
    requestBody: { values: [row] },
  });
}

module.exports = {
  readUsageDailyRollups,
  readUsageRecent,
  appendUsageEntry,
  SPREADSHEET_ID,
};
