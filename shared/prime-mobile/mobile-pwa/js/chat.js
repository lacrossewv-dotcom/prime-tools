/**
 * Chat Module — Claude/Gemini conversation with PRIME context
 */

const chat = (() => {
  let history = [];

  /**
   * Send a message.
   */
  async function send() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();

    if (!message) return;

    // Clear input
    input.value = '';
    input.style.height = 'auto';

    // Add user message to UI
    addBubble('user', message);

    // Get selected scope and provider
    const scope = document.getElementById('chat-scope').value;
    const provider = document.getElementById('chat-provider').value;

    // Show typing indicator
    const typingId = addBubble('assistant', 'Thinking...');

    try {
      const chatFn = provider === 'gemini' ? api.chatGemini : api.chatClaude;

      const data = await chatFn({
        message,
        scope,
        history: history.slice(-10), // Last 10 messages for context
      });

      // Update typing indicator with response
      updateBubble(typingId, data.response, provider, data.usage);

      // Add to conversation history
      history.push({ role: 'user', content: message });
      history.push({ role: 'assistant', content: data.response });

    } catch (err) {
      updateBubble(typingId, `Error: ${err.message}`, 'error');
    }

    // Scroll to bottom
    scrollToBottom();
  }

  /**
   * Handle keyboard events (Enter to send, Shift+Enter for newline).
   */
  function handleKey(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      send();
    }

    // Auto-resize textarea
    const textarea = event.target;
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
  }

  /**
   * Add a chat bubble to the UI.
   * Returns an ID for updating the bubble later.
   */
  function addBubble(role, text) {
    const container = document.getElementById('chat-messages');

    // Remove welcome message if present
    const welcome = container.querySelector('.chat-welcome');
    if (welcome) welcome.remove();

    const id = 'bubble-' + Date.now();
    const bubble = document.createElement('div');
    bubble.id = id;
    bubble.className = `chat-bubble ${role}`;
    bubble.textContent = text;

    container.appendChild(bubble);
    scrollToBottom();

    return id;
  }

  /**
   * Update an existing bubble's content.
   */
  function updateBubble(id, text, provider, usage) {
    const bubble = document.getElementById(id);
    if (!bubble) return;

    bubble.textContent = text;

    // Add provider tag
    if (provider && provider !== 'error') {
      const tag = document.createElement('div');
      tag.className = 'provider-tag';
      let tagText = provider;
      if (usage) {
        tagText += ` | ${usage.inputTokens + usage.outputTokens} tokens`;
      }
      tag.textContent = tagText;
      bubble.appendChild(tag);
    }
  }

  /**
   * Scroll chat to bottom.
   */
  function scrollToBottom() {
    const container = document.getElementById('chat-messages');
    container.scrollTop = container.scrollHeight;
  }

  /**
   * Clear chat history.
   */
  function clear() {
    history = [];
    const container = document.getElementById('chat-messages');
    container.innerHTML = `
      <div class="chat-welcome">
        <p>Chat with Claude or Gemini with full PRIME context.</p>
        <p class="hint">Select scope above to focus on a specific session.</p>
      </div>
    `;
  }

  return {
    send,
    handleKey,
    clear,
  };
})();
