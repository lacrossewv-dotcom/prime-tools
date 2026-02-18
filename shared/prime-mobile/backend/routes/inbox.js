/**
 * Inbox Routes
 *
 * GET  /api/inbox          — Unified inbox across all sessions
 * GET  /api/inbox/:session — Messages for a specific session
 * POST /api/inbox/:session — Send a new message to a session's inbox
 */

const express = require('express');
const router = express.Router();
const drive = require('../services/googleDrive');
const parser = require('../services/primeParser');

/**
 * GET /api/inbox
 *
 * Unified inbox view: all NEW and ACKNOWLEDGED messages across all sessions.
 * Sorted by date (newest first).
 */
router.get('/', async (req, res) => {
  try {
    const sessionKeys = Object.keys(drive.SESSION_INBOXES);
    const { status, priority } = req.query;

    // Fetch all inboxes in parallel
    const inboxPromises = sessionKeys.map(async (key) => {
      try {
        const { content } = await drive.readInbox(key);
        const messages = parser.parseInboxMessages(content);
        // Tag each message with its inbox
        return messages.map(m => ({ ...m, inbox: key }));
      } catch {
        return [];
      }
    });

    const allInboxes = await Promise.all(inboxPromises);
    let allMessages = allInboxes.flat();

    // Filter by status if requested
    if (status) {
      allMessages = allMessages.filter(m => m.status === status.toUpperCase());
    }

    // Filter by priority if requested
    if (priority) {
      allMessages = allMessages.filter(m => m.priority === priority);
    }

    // Sort by date (newest first), then by priority (Urgent > High > Normal)
    const priorityOrder = { Urgent: 0, High: 1, Normal: 2 };
    allMessages.sort((a, b) => {
      const dateCompare = b.date.localeCompare(a.date);
      if (dateCompare !== 0) return dateCompare;
      return (priorityOrder[a.priority] || 2) - (priorityOrder[b.priority] || 2);
    });

    // Summary counts
    const counts = {
      total: allMessages.length,
      new: allMessages.filter(m => m.status === 'NEW').length,
      acknowledged: allMessages.filter(m => m.status === 'ACKNOWLEDGED').length,
      closed: allMessages.filter(m => m.status === 'CLOSED').length,
    };

    // By default, only show active messages (NEW + ACKNOWLEDGED) unless status filter is set
    const displayMessages = status
      ? allMessages
      : allMessages.filter(m => m.status !== 'CLOSED');

    res.json({
      messages: displayMessages.slice(0, 50), // Limit to 50 most recent
      counts,
      timestamp: new Date().toISOString(),
    });
  } catch (err) {
    console.error('[INBOX] Error:', err.message);
    res.status(500).json({ error: `Failed to load inbox: ${err.message}` });
  }
});

/**
 * GET /api/inbox/:session
 *
 * Messages for a specific session inbox.
 */
router.get('/:session', async (req, res) => {
  try {
    const sessionKey = req.params.session.toLowerCase();

    if (!drive.SESSION_INBOXES[sessionKey]) {
      return res.status(404).json({
        error: `Unknown session: ${sessionKey}`,
        validSessions: Object.keys(drive.SESSION_INBOXES),
      });
    }

    const { content, modifiedTime } = await drive.readInbox(sessionKey);
    const messages = parser.parseInboxMessages(content);
    const counts = parser.countByStatus(messages);

    // Newest first
    messages.reverse();

    res.json({
      session: sessionKey,
      messages: messages.slice(0, 30),
      counts,
      lastModified: modifiedTime,
      timestamp: new Date().toISOString(),
    });
  } catch (err) {
    console.error(`[INBOX] Error for ${req.params.session}:`, err.message);
    res.status(500).json({ error: `Failed to load inbox: ${err.message}` });
  }
});

/**
 * POST /api/inbox/:session
 *
 * Send a new message to a session's inbox.
 *
 * Body: {
 *   from: "Steve" (or session name),
 *   priority: "Normal" | "High" | "Urgent",
 *   subject: "Message subject",
 *   body: "Message body in markdown"
 * }
 */
router.post('/:session', async (req, res) => {
  try {
    const sessionKey = req.params.session.toLowerCase();

    if (!drive.SESSION_INBOXES[sessionKey]) {
      return res.status(404).json({
        error: `Unknown session: ${sessionKey}`,
        validSessions: Object.keys(drive.SESSION_INBOXES),
      });
    }

    const { from, priority, subject, body } = req.body;

    if (!body) {
      return res.status(400).json({ error: 'Message body is required' });
    }

    // Determine the "To" field based on session key
    const sessionNames = {
      athena: 'Athena',
      '8901': '8901',
      '8902': '8902',
      jado: 'JADO',
      coi_research: 'COI Research',
      atlas: 'Atlas',
      google: 'Google',
      sketchi: 'Sketchi',
      semper: 'Semper',
      fsmao: 'FSMAO',
      index: 'Index',
      historian: 'Historian',
    };

    // Format the message in PRIME canonical format
    const messageText = parser.formatMessage({
      from: from || 'Steve (Mobile)',
      to: sessionNames[sessionKey] || sessionKey,
      priority: priority || 'Normal',
      subject,
      body,
    });

    // Append to the session's inbox file
    await drive.writeToInbox(sessionKey, messageText);

    res.json({
      success: true,
      message: `Message sent to ${sessionNames[sessionKey]} inbox`,
      timestamp: new Date().toISOString(),
    });
  } catch (err) {
    console.error(`[INBOX] Write error for ${req.params.session}:`, err.message);
    res.status(500).json({ error: `Failed to send message: ${err.message}` });
  }
});

module.exports = router;
