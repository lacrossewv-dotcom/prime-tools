/**
 * Dashboard Module — Session overview, status, and quick actions
 */

const dashboard = (() => {
  let sessionsData = null;

  /**
   * Quick action templates — pre-formatted messages to send to sessions.
   */
  const QUICK_ACTIONS = [
    {
      id: 'check-in',
      label: '📋 Check In',
      priority: 'Normal',
      subject: 'Status Check-In',
      body: 'Requesting current status update. Please respond with:\n- What you\'re currently working on\n- Any blockers or issues\n- Estimated completion for active tasks',
    },
    {
      id: 'request-status',
      label: '📊 Request Status',
      priority: 'Normal',
      subject: 'Status Report Request',
      body: 'Please provide a brief status report including:\n- Active tasks and progress\n- Pending items\n- Any cross-session dependencies',
    },
    {
      id: 'complete-task',
      label: '✅ Complete Task',
      priority: 'Normal',
      subject: 'Task Completion Directive',
      body: 'Please finalize and close out your current active task(s). Mark all completed items as CLOSED in your inbox and update any relevant documentation.',
    },
    {
      id: 'urgent-respond',
      label: '🚨 Urgent: Respond Now',
      priority: 'Urgent',
      subject: 'URGENT — Immediate Response Required',
      body: 'This is an urgent request. Please prioritize responding to all NEW messages in your inbox immediately. Acknowledge receipt of this message.',
    },
    {
      id: 'sync-prime',
      label: '🔄 Sync with PRIME',
      priority: 'Normal',
      subject: 'PRIME Sync Request',
      body: 'Please check your PRIME inbox for any unread messages, process them, and update your session status. Report back when sync is complete.',
    },
    {
      id: 'close-stale',
      label: '🧹 Close Stale Messages',
      priority: 'Normal',
      subject: 'Inbox Cleanup Directive',
      body: 'Please review all ACKNOWLEDGED messages in your inbox. Close any that are resolved or no longer actionable. Report the count of messages closed.',
    },
  ];

  /**
   * Load dashboard data from API.
   */
  async function load() {
    const grid = document.getElementById('sessions-grid');
    grid.innerHTML = '<div class="loading">Loading sessions...</div>';

    try {
      const data = await api.getSessions();
      sessionsData = data;
      render(data);
    } catch (err) {
      grid.innerHTML = `<div class="error-text">Failed to load: ${err.message}</div>`;
    }
  }

  /**
   * Render the dashboard with session data.
   */
  function render(data) {
    const { sessions, deadlines, totalUnread } = data;

    // Update unread badge
    document.getElementById('total-unread').textContent = totalUnread;
    updateNavBadge(totalUnread);

    // Render deadlines
    if (deadlines && deadlines.length > 0) {
      const banner = document.getElementById('deadlines-banner');
      const list = document.getElementById('deadlines-list');
      banner.style.display = 'block';
      list.innerHTML = deadlines.map(d =>
        `<div class="deadline-item">${d.date} — ${d.description}</div>`
      ).join('');
    }

    // Render session cards
    const grid = document.getElementById('sessions-grid');
    grid.innerHTML = sessions.map(session => {
      const counts = session.inboxCounts || { new: 0, acknowledged: 0, total: 0 };
      const hasUnread = counts.new > 0;
      const hasDeadline = session.deadlines && session.deadlines.length > 0;
      const inboxKey = findInboxKey(session.name);

      let cardClass = 'session-card';
      if (hasUnread) cardClass += ' has-unread';
      if (hasDeadline) cardClass += ' has-deadline';

      return `
        <div class="${cardClass}">
          <div class="session-card-header" onclick="dashboard.openSession('${session.name}')">
            <span class="session-card-name">${session.name}</span>
            ${session.parent ? `<span class="session-card-parent">${session.parent}</span>` : ''}
          </div>
          ${session.purpose ? `<div class="session-card-purpose" onclick="dashboard.openSession('${session.name}')">${truncate(session.purpose, 80)}</div>` : ''}
          <div class="session-card-footer">
            <div class="session-card-stats" onclick="dashboard.openSession('${session.name}')">
              ${counts.new > 0 ? `<span class="badge badge-new">${counts.new} new</span>` : ''}
              ${counts.acknowledged > 0 ? `<span class="badge badge-normal">${counts.acknowledged} ack</span>` : ''}
              ${hasDeadline ? `<span class="badge badge-high">deadline</span>` : ''}
            </div>
            ${inboxKey ? `<button class="btn-action" onclick="event.stopPropagation(); dashboard.showActions('${inboxKey}', '${session.name}')" title="Quick Actions">&#9889;</button>` : ''}
          </div>
        </div>
      `;
    }).join('');
  }

  /**
   * Find the inbox key for a session name.
   */
  function findInboxKey(name) {
    const map = {
      athena: 'Athena', '8901': '8901', '8902': '8902',
      jado: 'JADO', atlas: 'Atlas', google: 'Google',
      sketchi: 'Sketchi', semper: 'Semper', fsmao: 'FSMAO',
      index: 'Index', historian: 'Historian', prime: 'PRIME',
      coi: '8902', theory: '8901',
    };
    const lowerName = name.toLowerCase();
    return Object.keys(map).find(k => lowerName.includes(k)) || null;
  }

  /**
   * Show quick actions modal for a session.
   */
  function showActions(sessionKey, sessionName) {
    const modal = document.getElementById('modal-actions');
    const title = document.getElementById('actions-session-name');
    const list = document.getElementById('actions-list');

    title.textContent = sessionName;

    list.innerHTML = QUICK_ACTIONS.map(action => `
      <button class="action-item ${action.priority === 'Urgent' ? 'action-urgent' : ''}"
              onclick="dashboard.executeAction('${sessionKey}', '${action.id}')">
        <span class="action-label">${action.label}</span>
        <span class="action-desc">${action.subject}</span>
      </button>
    `).join('');

    modal.style.display = 'flex';
  }

  /**
   * Hide the quick actions modal.
   */
  function hideActions() {
    document.getElementById('modal-actions').style.display = 'none';
  }

  /**
   * Execute a quick action — send a pre-formatted message to the session.
   */
  async function executeAction(sessionKey, actionId) {
    const action = QUICK_ACTIONS.find(a => a.id === actionId);
    if (!action) return;

    // Show sending state
    const list = document.getElementById('actions-list');
    list.innerHTML = `<div class="action-sending">Sending "${action.subject}"...</div>`;

    try {
      await api.sendMessage(sessionKey, {
        from: 'Steve (PRIME Mobile)',
        to: sessionKey,
        priority: action.priority,
        subject: action.subject,
        body: action.body,
      });

      // Show success briefly
      list.innerHTML = `<div class="action-success">&#10003; Sent to ${sessionKey}</div>`;
      setTimeout(() => {
        hideActions();
        load(); // Refresh dashboard to update counts
      }, 1200);

    } catch (err) {
      list.innerHTML = `<div class="action-error">Failed: ${err.message}</div>`;
      setTimeout(hideActions, 2500);
    }
  }

  /**
   * Open a specific session's inbox.
   */
  function openSession(name) {
    const key = findInboxKey(name);
    if (key) {
      navigate('inbox');
      inbox.loadSession(key);
    }
  }

  /**
   * Update the navigation badge with unread count.
   */
  function updateNavBadge(count) {
    const badge = document.getElementById('nav-inbox-badge');
    if (count > 0) {
      badge.textContent = count;
      badge.style.display = 'block';
    } else {
      badge.style.display = 'none';
    }
  }

  /**
   * Truncate text to a max length.
   */
  function truncate(text, maxLen) {
    if (!text) return '';
    return text.length > maxLen ? text.substring(0, maxLen) + '...' : text;
  }

  return {
    load,
    render,
    openSession,
    showActions,
    hideActions,
    executeAction,
  };
})();
