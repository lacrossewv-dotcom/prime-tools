/**
 * Claude API Service
 *
 * Wraps Anthropic's Claude API with PRIME context injection.
 * When a user chats from the mobile app, this service:
 * 1. Builds a system prompt from PRIME session data
 * 2. Sends the user's message to Claude
 * 3. Returns the streamed response
 */

const Anthropic = require('@anthropic-ai/sdk');

let client = null;

/**
 * Get the Anthropic client (lazy initialization).
 */
function getClient() {
  if (!client) {
    client = new Anthropic({
      apiKey: process.env.CLAUDE_API_KEY,
    });
  }
  return client;
}

/**
 * Build a PRIME context system prompt.
 *
 * Constructs a system prompt that gives Claude awareness of:
 * - All 13 sessions and their roles
 * - Current inbox status (unread counts)
 * - Recent deadlines
 * - The user's selected context scope
 *
 * @param {object} contextData - {
 *   sessions: Array of session summaries,
 *   inboxCounts: { sessionKey: { new, acknowledged, closed } },
 *   deadlines: Array of upcoming deadlines,
 *   scope: 'all' | sessionKey (which session to focus on),
 *   sessionDetail: string (specific session's CLAUDE.md content, if scoped)
 * }
 * @returns {string} System prompt
 */
function buildSystemPrompt(contextData) {
  const { sessions, inboxCounts, deadlines, scope, sessionDetail } = contextData;

  let prompt = `You are Steve's PRIME Mobile assistant. Steve manages 13 AI sessions (the PRIME ecosystem) that coordinate through Google Drive inbox files. You have full awareness of the system state.\n\n`;

  // Session overview
  prompt += `## Active Sessions\n`;
  if (sessions && sessions.length > 0) {
    for (const s of sessions) {
      const counts = inboxCounts?.[s.name?.toLowerCase()] || {};
      const unread = counts.new || 0;
      prompt += `- **${s.name}**: ${s.purpose || 'No description'}`;
      if (s.parent) prompt += ` (under ${s.parent})`;
      if (unread > 0) prompt += ` [${unread} unread]`;
      prompt += `\n`;
    }
  }

  // Deadlines
  if (deadlines && deadlines.length > 0) {
    prompt += `\n## Upcoming Deadlines\n`;
    for (const d of deadlines) {
      prompt += `- ${d.date}: ${d.description}\n`;
    }
  }

  // Scoped session detail
  if (scope !== 'all' && sessionDetail) {
    prompt += `\n## Focused Session: ${scope}\n`;
    prompt += `The user is focused on the ${scope} session. Here is its full configuration:\n\n`;
    prompt += sessionDetail.substring(0, 4000); // Limit to 4K chars to save tokens
  }

  prompt += `\n## Your Role\n`;
  prompt += `- Answer questions about the PRIME ecosystem\n`;
  prompt += `- Help Steve manage sessions, route messages, check status\n`;
  prompt += `- Provide concise, actionable responses\n`;
  prompt += `- When Steve asks to send a message, format it in PRIME canonical format\n`;
  prompt += `- Be aware this is a mobile interface — keep responses brief\n`;

  return prompt;
}

/**
 * Send a message to Claude with PRIME context.
 *
 * @param {string} userMessage - The user's chat message
 * @param {object} contextData - PRIME context (see buildSystemPrompt)
 * @param {string} [model] - Claude model to use (default: claude-sonnet-4-20250514)
 * @returns {string} Claude's response text
 */
async function chat(userMessage, contextData, model = 'claude-sonnet-4-20250514') {
  const anthropic = getClient();
  const systemPrompt = buildSystemPrompt(contextData);

  const response = await anthropic.messages.create({
    model: model,
    max_tokens: 2048,
    system: systemPrompt,
    messages: [
      { role: 'user', content: userMessage },
    ],
  });

  // Extract text from response
  const textBlock = response.content.find(block => block.type === 'text');
  return {
    text: textBlock ? textBlock.text : 'No response generated.',
    model: response.model,
    inputTokens: response.usage?.input_tokens || 0,
    outputTokens: response.usage?.output_tokens || 0,
  };
}

/**
 * Send a message to Claude with conversation history.
 *
 * @param {Array} messages - Array of { role: 'user'|'assistant', content: string }
 * @param {object} contextData - PRIME context
 * @param {string} [model] - Claude model
 * @returns {object} { text, model, inputTokens, outputTokens }
 */
async function chatWithHistory(messages, contextData, model = 'claude-sonnet-4-20250514') {
  const anthropic = getClient();
  const systemPrompt = buildSystemPrompt(contextData);

  const response = await anthropic.messages.create({
    model: model,
    max_tokens: 2048,
    system: systemPrompt,
    messages: messages,
  });

  const textBlock = response.content.find(block => block.type === 'text');
  return {
    text: textBlock ? textBlock.text : 'No response generated.',
    model: response.model,
    inputTokens: response.usage?.input_tokens || 0,
    outputTokens: response.usage?.output_tokens || 0,
  };
}

module.exports = {
  buildSystemPrompt,
  chat,
  chatWithHistory,
};
