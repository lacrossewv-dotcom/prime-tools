/**
 * PRIME Markdown Parser
 *
 * Parses PRIME ecosystem markdown files into structured JSON.
 * Handles:
 * - Inbox messages (canonical header format)
 * - Session registry entries
 * - Operations deadlines
 */

/**
 * Parse a PRIME inbox file into individual messages.
 *
 * Canonical format:
 * ## YYYY-MM-DD | From: [Session] | To: [Target] | Priority: [Level] | Status: [State]
 *
 * @param {string} content - Raw markdown content of an inbox file
 * @returns {Array} Array of parsed message objects
 */
function parseInboxMessages(content) {
  const messages = [];
  const lines = content.split('\n');

  let currentMessage = null;
  let bodyLines = [];

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];

    // Check if this line is a canonical message header
    const headerMatch = line.match(
      /^## (\d{4}-\d{2}-\d{2}) \| From: (.+?) \| (?:To: (.+?) \| )?Priority: (Normal|High|Urgent) \| Status: (NEW|ACKNOWLEDGED|CLOSED(?:\s.*)?)/
    );

    if (headerMatch) {
      // Save previous message if exists
      if (currentMessage) {
        currentMessage.body = bodyLines.join('\n').trim();
        messages.push(currentMessage);
      }

      // Start new message
      currentMessage = {
        date: headerMatch[1],
        from: headerMatch[2].trim(),
        to: headerMatch[3] ? headerMatch[3].trim() : 'Unknown',
        priority: headerMatch[4],
        status: headerMatch[5].startsWith('CLOSED') ? 'CLOSED' : headerMatch[5],
        statusDetail: headerMatch[5],
        rawHeader: line,
      };
      bodyLines = [];
    } else if (line.trim() === '---') {
      // Message separator — save current message
      if (currentMessage) {
        currentMessage.body = bodyLines.join('\n').trim();
        messages.push(currentMessage);
        currentMessage = null;
        bodyLines = [];
      }
    } else if (currentMessage) {
      bodyLines.push(line);
    }
  }

  // Don't forget the last message
  if (currentMessage) {
    currentMessage.body = bodyLines.join('\n').trim();
    messages.push(currentMessage);
  }

  return messages;
}

/**
 * Count messages by status in an inbox.
 *
 * @param {Array} messages - Parsed messages from parseInboxMessages
 * @returns {object} { total, new, acknowledged, closed }
 */
function countByStatus(messages) {
  return {
    total: messages.length,
    new: messages.filter(m => m.status === 'NEW').length,
    acknowledged: messages.filter(m => m.status === 'ACKNOWLEDGED').length,
    closed: messages.filter(m => m.status === 'CLOSED').length,
  };
}

/**
 * Parse SESSION_REGISTRY.md into structured session data.
 *
 * Extracts session blocks with metadata like name, directory,
 * purpose, parent, status, deadlines.
 *
 * @param {string} content - Raw markdown of SESSION_REGISTRY.md
 * @returns {Array} Array of session objects
 */
function parseSessionRegistry(content) {
  const sessions = [];
  const lines = content.split('\n');

  let currentSession = null;
  let currentSection = null;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];

    // H2 headers indicate session blocks
    // Format: ## SESSION: Name (Subtitle) or ## N. Name
    const sessionMatch = line.match(/^## (?:SESSION:\s*)?(\d+\.\s+)?(.+)/);
    if (sessionMatch && !line.includes('How To Use')) {
      const name = (sessionMatch[2] || sessionMatch[1] || '').trim();
      if (currentSession) {
        sessions.push(currentSession);
      }
      currentSession = {
        name: name,
        directory: null,
        purpose: null,
        parent: null,
        type: null,
        status: null,
        deadlines: [],
        raw: [],
      };
      currentSection = null;
      continue;
    }

    // H3 headers indicate sections within a session
    const sectionMatch = line.match(/^### (.+)/);
    if (sectionMatch && currentSession) {
      currentSection = sectionMatch[1].trim().toLowerCase();
      continue;
    }

    // Parse key-value pairs within session blocks
    if (currentSession) {
      currentSession.raw.push(line);

      // Look for common fields — matches both:
      // **Key:** value  AND  - **Key:** value
      const kvMatch = line.match(/^[-*]?\s*\*\*(.+?):?\*\*:?\s+(.+)/);
      if (kvMatch) {
        const key = kvMatch[1].toLowerCase().trim();
        const value = kvMatch[2].trim();

        if (key.includes('working dir') || key.includes('directory') || key.includes('path')) {
          currentSession.directory = value.replace(/`/g, '');
        } else if (key.includes('purpose') || key.includes('role') || key.includes('function')) {
          currentSession.purpose = value;
        } else if (key.includes('parent') || key.includes('orchestrator')) {
          currentSession.parent = value;
        } else if (key.includes('type') || key.includes('session type')) {
          currentSession.type = value;
        } else if (key.includes('status') || key.includes('state')) {
          currentSession.status = value;
        } else if (key.includes('deadline') || key.includes('due')) {
          currentSession.deadlines.push(value);
        }
      }

      // Check table rows for metadata
      const tableMatch = line.match(/^\|\s*(.+?)\s*\|\s*(.+?)\s*\|/);
      if (tableMatch) {
        const key = tableMatch[1].toLowerCase().replace(/\*\*/g, '').trim();
        const value = tableMatch[2].replace(/\*\*/g, '').trim();

        if (key.includes('directory') || key.includes('path')) {
          currentSession.directory = value.replace(/`/g, '');
        } else if (key.includes('purpose') || key.includes('role')) {
          currentSession.purpose = value;
        } else if (key.includes('parent')) {
          currentSession.parent = value;
        } else if (key.includes('type')) {
          currentSession.type = value;
        } else if (key.includes('status')) {
          currentSession.status = value;
        }
      }
    }
  }

  // Don't forget the last session
  if (currentSession) {
    sessions.push(currentSession);
  }

  return sessions;
}

/**
 * Extract deadlines from PRIME_OPERATIONS.md.
 *
 * Looks for date patterns and deadline-related keywords.
 *
 * @param {string} content - Raw markdown of PRIME_OPERATIONS.md
 * @returns {Array} Array of { date, description, session }
 */
function parseDeadlines(content) {
  const deadlines = [];
  const lines = content.split('\n');

  for (const line of lines) {
    // Match lines with dates and deadline keywords
    const dateMatch = line.match(/(Feb(?:ruary)?\s+\d{1,2}|Mar(?:ch)?\s+\d{1,2}|\d{4}-\d{2}-\d{2})/i);
    if (dateMatch && /deadline|due|submit|exam|brief|present/i.test(line)) {
      deadlines.push({
        date: dateMatch[1],
        description: line.replace(/^[\s\-\*\|]+/, '').trim(),
        raw: line.trim(),
      });
    }
  }

  return deadlines;
}

/**
 * Format a new message in PRIME canonical format.
 *
 * @param {object} params - { from, to, priority, subject, body }
 * @returns {string} Formatted markdown message
 */
function formatMessage({ from, to, priority = 'Normal', subject, body }) {
  const date = new Date().toISOString().split('T')[0]; // YYYY-MM-DD

  let message = `## ${date} | From: ${from} | To: ${to} | Priority: ${priority} | Status: NEW\n\n`;

  if (subject) {
    message += `### ${subject}\n\n`;
  }

  message += body;

  return message;
}

module.exports = {
  parseInboxMessages,
  countByStatus,
  parseSessionRegistry,
  parseDeadlines,
  formatMessage,
};
