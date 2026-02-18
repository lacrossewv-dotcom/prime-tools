/**
 * Inbox Module — Message list and compose
 */

const inbox = (() => {
  let allMessages = [];
  let expandedId = null;

  /**
   * Load unified inbox.
   */
  async function load() {
    const container = document.getElementById('inbox-messages');
    container.innerHTML = '<div class="loading">Loading messages...</div>';

    try {
      const data = await api.getUnifiedInbox();
      allMessages = data.messages;
      render(allMessages);
    } catch (err) {
      container.innerHTML = `<div class="error-text">Failed to load: ${err.message}</div>`;
    }
  }

  /**
   * Load messages for a specific session.
   */
  async function loadSession(sessionKey) {
    const container = document.getElementById('inbox-messages');
    container.innerHTML = '<div class="loading">Loading messages...</div>';

    try {
      const data = await api.getSessionInbox(sessionKey);
      allMessages = data.messages;
      render(allMessages);
    } catch (err) {
      container.innerHTML = `<div class="error-text">Failed to load: ${err.message}</div>`;
    }
  }

  /**
   * Filter messages by status.
   */
  function filter(value) {
    if (value === 'active') {
      render(allMessages.filter(m => m.status !== 'CLOSED'));
    } else if (value === 'all') {
      render(allMessages);
    } else {
      render(allMessages.filter(m => m.status === value));
    }
  }

  /**
   * Render message list.
   */
  function render(messages) {
    const container = document.getElementById('inbox-messages');

    if (messages.length === 0) {
      container.innerHTML = '<div class="loading">No messages</div>';
      return;
    }

    container.innerHTML = messages.map((msg, i) => {
      const statusBadge = msg.status === 'NEW'
        ? '<span class="badge badge-new">NEW</span>'
        : msg.status === 'ACKNOWLEDGED'
          ? '<span class="badge badge-normal">ACK</span>'
          : '<span class="badge" style="background:#555;color:#999;">CLOSED</span>';

      const priorityBadge = msg.priority === 'High'
        ? '<span class="badge badge-high">HIGH</span>'
        : msg.priority === 'Urgent'
          ? '<span class="badge badge-urgent">URGENT</span>'
          : '';

      const preview = (msg.body || '').substring(0, 100).replace(/[#*|]/g, '').trim();
      const isExpanded = expandedId === i;

      return `
        <div class="message-card" onclick="inbox.toggle(${i})">
          <div class="message-card-header">
            <span class="message-card-from">${msg.from}</span>
            <span class="message-card-date">${msg.date}</span>
          </div>
          <div class="message-card-to">
            To: ${msg.to} ${statusBadge} ${priorityBadge}
          </div>
          ${!isExpanded
            ? `<div class="message-card-preview">${preview}</div>`
            : `<div class="message-detail">${escapeHtml(msg.body || 'No content')}</div>`
          }
        </div>
      `;
    }).join('');
  }

  /**
   * Toggle message expansion.
   */
  function toggle(index) {
    expandedId = expandedId === index ? null : index;
    const currentFilter = document.getElementById('inbox-filter').value;
    filter(currentFilter);
  }

  /**
   * Show compose modal.
   */
  function showCompose() {
    document.getElementById('modal-compose').style.display = 'flex';
  }

  /**
   * Hide compose modal.
   */
  function hideCompose() {
    document.getElementById('modal-compose').style.display = 'none';
  }

  /**
   * Send a new message.
   */
  async function sendMessage() {
    const to = document.getElementById('compose-to').value;
    const priority = document.getElementById('compose-priority').value;
    const subject = document.getElementById('compose-subject').value;
    const body = document.getElementById('compose-body').value;

    if (!body.trim()) {
      alert('Message body is required');
      return;
    }

    try {
      await api.sendMessage(to, {
        from: 'Steve (Mobile)',
        priority,
        subject,
        body,
      });

      // Clear form and close modal
      document.getElementById('compose-subject').value = '';
      document.getElementById('compose-body').value = '';
      hideCompose();

      // Reload inbox
      load();
      alert('Message sent!');
    } catch (err) {
      alert(`Failed to send: ${err.message}`);
    }
  }

  /**
   * Escape HTML for safe rendering.
   */
  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  return {
    load,
    loadSession,
    filter,
    toggle,
    showCompose,
    hideCompose,
    sendMessage,
  };
})();
