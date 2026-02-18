/**
 * Sessions Routes
 *
 * GET /api/sessions — List all 13 PRIME sessions with status and inbox counts
 * GET /api/sessions/:id — Detailed info for a specific session
 */

const express = require('express');
const router = express.Router();
const drive = require('../services/googleDrive');
const parser = require('../services/primeParser');

/**
 * GET /api/sessions
 *
 * Returns all sessions with:
 * - Name, purpose, parent, type
 * - Inbox message counts (new/acknowledged/closed)
 * - Upcoming deadlines
 */
router.get('/', async (req, res) => {
  try {
    // Fetch session registry and operations in parallel
    const [registryContent, operationsContent] = await Promise.all([
      drive.readSessionRegistry(),
      drive.readOperations().catch(() => ''),
    ]);

    // Parse session data
    const sessions = parser.parseSessionRegistry(registryContent);
    const deadlines = parser.parseDeadlines(operationsContent);

    // Fetch inbox counts for all sessions in parallel
    const sessionKeys = Object.keys(drive.SESSION_INBOXES);
    const inboxPromises = sessionKeys.map(async (key) => {
      try {
        const { content } = await drive.readInbox(key);
        const messages = parser.parseInboxMessages(content);
        return { key, counts: parser.countByStatus(messages) };
      } catch (err) {
        // If inbox file not found, return zero counts
        return { key, counts: { total: 0, new: 0, acknowledged: 0, closed: 0 } };
      }
    });

    const inboxResults = await Promise.all(inboxPromises);
    const inboxCounts = {};
    for (const { key, counts } of inboxResults) {
      inboxCounts[key] = counts;
    }

    // Combine data
    const enrichedSessions = sessions.map(session => {
      // Match session to inbox key
      const matchKey = sessionKeys.find(k =>
        k === session.name?.toLowerCase() ||
        session.name?.toLowerCase().includes(k)
      );

      return {
        ...session,
        inboxCounts: inboxCounts[matchKey] || { total: 0, new: 0, acknowledged: 0, closed: 0 },
        raw: undefined, // Don't send raw lines to mobile
      };
    });

    res.json({
      sessions: enrichedSessions,
      deadlines,
      totalSessions: sessions.length,
      totalUnread: Object.values(inboxCounts).reduce((sum, c) => sum + c.new, 0),
      timestamp: new Date().toISOString(),
    });
  } catch (err) {
    console.error('[SESSIONS] Error:', err.message);
    res.status(500).json({ error: `Failed to load sessions: ${err.message}` });
  }
});

/**
 * GET /api/sessions/:id
 *
 * Returns detailed info for a specific session including
 * its full inbox content and recent messages.
 */
router.get('/:id', async (req, res) => {
  try {
    const sessionKey = req.params.id.toLowerCase();

    if (!drive.SESSION_INBOXES[sessionKey]) {
      return res.status(404).json({ error: `Unknown session: ${sessionKey}` });
    }

    // Fetch inbox content
    const { content, modifiedTime } = await drive.readInbox(sessionKey);
    const messages = parser.parseInboxMessages(content);
    const counts = parser.countByStatus(messages);

    // Return newest messages first
    messages.reverse();

    res.json({
      session: sessionKey,
      inboxCounts: counts,
      messages: messages.slice(0, 20), // Last 20 messages
      lastModified: modifiedTime,
      timestamp: new Date().toISOString(),
    });
  } catch (err) {
    console.error(`[SESSIONS] Error for ${req.params.id}:`, err.message);
    res.status(500).json({ error: `Failed to load session: ${err.message}` });
  }
});

module.exports = router;
