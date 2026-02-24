/**
 * Chat Routes
 *
 * POST /api/chat         — Chat with Claude (PRIME context injected)
 * POST /api/chat/gemini  — Chat with Gemini (cheaper alternative)
 */

const express = require('express');
const router = express.Router();
const claudeAPI = require('../services/claudeAPI');
const geminiAPI = require('../services/geminiAPI');
const drive = require('../services/googleDrive');
const parser = require('../services/primeParser');
const sheets = require('../services/sheetsService');

// Price table for cost estimation (per 1M tokens: [input, output])
const PRICE_TABLE = {
  'claude-opus-4-6': [15.00, 75.00],
  'claude-sonnet-4-6': [3.00, 15.00],
  'claude-sonnet-4-20250514': [3.00, 15.00],
  'claude-haiku-4-5-20251001': [0.80, 4.00],
  'gemini-2.5-flash': [0.30, 2.50],
  'gemini-2.0-flash': [0.10, 0.40],
  'gemini-2.5-pro': [1.25, 10.00],
  'gemini-3-flash-preview': [0.50, 3.00],
};

function estimateCost(model, inputTokens, outputTokens) {
  const prices = PRICE_TABLE[model] || [3.00, 15.00];
  return (inputTokens * prices[0] / 1_000_000) + (outputTokens * prices[1] / 1_000_000);
}

/**
 * Build PRIME context data for chat.
 *
 * Fetches session registry, operations, and inbox counts
 * to give the AI full awareness of the PRIME ecosystem state.
 *
 * @param {string} scope - 'all' or a specific session key
 * @returns {object} Context data for system prompt building
 */
async function buildContext(scope = 'all') {
  // Fetch core PRIME data in parallel
  const [registryContent, operationsContent] = await Promise.all([
    drive.readSessionRegistry().catch(() => ''),
    drive.readOperations().catch(() => ''),
  ]);

  const sessions = parser.parseSessionRegistry(registryContent);
  const deadlines = parser.parseDeadlines(operationsContent);

  // Get inbox counts for all sessions
  const sessionKeys = Object.keys(drive.SESSION_INBOXES);
  const inboxPromises = sessionKeys.map(async (key) => {
    try {
      const { content } = await drive.readInbox(key);
      const messages = parser.parseInboxMessages(content);
      return { key, counts: parser.countByStatus(messages) };
    } catch {
      return { key, counts: { total: 0, new: 0, acknowledged: 0, closed: 0 } };
    }
  });

  const inboxResults = await Promise.all(inboxPromises);
  const inboxCounts = {};
  for (const { key, counts } of inboxResults) {
    inboxCounts[key] = counts;
  }

  // If scoped to a specific session, try to read its detailed context
  let sessionDetail = null;
  if (scope !== 'all' && drive.SESSION_INBOXES[scope]) {
    try {
      const { content } = await drive.readInbox(scope);
      // Get the latest messages as context
      const messages = parser.parseInboxMessages(content);
      const recentNew = messages.filter(m => m.status === 'NEW').slice(-5);
      sessionDetail = recentNew.map(m =>
        `[${m.date}] From: ${m.from} | Priority: ${m.priority}\n${m.body.substring(0, 500)}`
      ).join('\n\n---\n\n');
    } catch {
      // Proceed without session detail
    }
  }

  return {
    sessions,
    inboxCounts,
    deadlines,
    scope,
    sessionDetail,
  };
}

/**
 * POST /api/chat
 *
 * Chat with Claude with PRIME context injection.
 *
 * Body: {
 *   message: "User's message",
 *   scope: "all" | sessionKey (optional, default: "all"),
 *   model: "claude-sonnet-4-20250514" (optional),
 *   history: [ { role, content }, ... ] (optional conversation history)
 * }
 */
router.post('/', async (req, res) => {
  try {
    const { message, scope = 'all', model, history } = req.body;

    if (!message) {
      return res.status(400).json({ error: 'Message is required' });
    }

    // Build PRIME context
    const contextData = await buildContext(scope);

    let result;
    if (history && history.length > 0) {
      // Multi-turn conversation
      const messages = [
        ...history,
        { role: 'user', content: message },
      ];
      result = await claudeAPI.chatWithHistory(messages, contextData, model);
    } else {
      // Single-turn
      result = await claudeAPI.chat(message, contextData, model);
    }

    res.json({
      response: result.text,
      model: result.model,
      usage: {
        inputTokens: result.inputTokens,
        outputTokens: result.outputTokens,
      },
      provider: 'claude',
      timestamp: new Date().toISOString(),
    });

    // Fire-and-forget: log usage to Sheet
    sheets.appendUsageEntry({
      provider: 'claude',
      model: result.model,
      task: 'chat',
      inputTokens: result.inputTokens,
      outputTokens: result.outputTokens,
      cost: estimateCost(result.model, result.inputTokens, result.outputTokens),
      source: 'prime-mobile-chat',
    }).catch(err => console.error('[USAGE LOG] Claude chat:', err.message));
  } catch (err) {
    console.error('[CHAT/CLAUDE] Error:', err.message);
    res.status(500).json({ error: `Chat failed: ${err.message}` });
  }
});

/**
 * POST /api/chat/gemini
 *
 * Chat with Gemini (cheaper alternative).
 *
 * Body: same as /api/chat
 */
router.post('/gemini', async (req, res) => {
  try {
    const { message, scope = 'all', model = 'gemini-2.5-flash', history } = req.body;

    if (!message) {
      return res.status(400).json({ error: 'Message is required' });
    }

    // Build PRIME context (reuse same builder)
    const contextData = await buildContext(scope);
    const systemContext = claudeAPI.buildSystemPrompt(contextData);

    let result;
    if (history && history.length > 0) {
      const messages = [
        ...history,
        { role: 'user', content: message },
      ];
      result = await geminiAPI.chatWithHistory(messages, systemContext, model);
    } else {
      result = await geminiAPI.chat(message, systemContext, model);
    }

    res.json({
      response: result.text,
      model: result.model,
      usage: {
        inputTokens: result.inputTokens,
        outputTokens: result.outputTokens,
      },
      provider: 'gemini',
      timestamp: new Date().toISOString(),
    });

    // Fire-and-forget: log usage to Sheet
    sheets.appendUsageEntry({
      provider: 'gemini',
      model: result.model,
      task: 'chat',
      inputTokens: result.inputTokens,
      outputTokens: result.outputTokens,
      cost: estimateCost(result.model, result.inputTokens, result.outputTokens),
      source: 'prime-mobile-chat',
    }).catch(err => console.error('[USAGE LOG] Gemini chat:', err.message));
  } catch (err) {
    console.error('[CHAT/GEMINI] Error:', err.message);
    res.status(500).json({ error: `Chat failed: ${err.message}` });
  }
});

module.exports = router;
