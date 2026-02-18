/**
 * Gemini API Service
 *
 * Alternative chat backend using Google's Gemini models.
 * Cheaper than Claude for simple queries.
 *
 * Uses the REST API directly (no SDK dependency needed).
 */

const GEMINI_BASE_URL = 'https://generativelanguage.googleapis.com/v1beta/models';

/**
 * Send a message to Gemini with PRIME context.
 *
 * @param {string} userMessage - The user's chat message
 * @param {string} systemContext - System prompt with PRIME context
 * @param {string} [model] - Gemini model ID (default: gemini-2.5-flash)
 * @returns {object} { text, model, inputTokens, outputTokens }
 */
async function chat(userMessage, systemContext, model = 'gemini-2.5-flash') {
  const apiKey = process.env.GEMINI_API_KEY;
  if (!apiKey) {
    throw new Error('GEMINI_API_KEY not configured');
  }

  const url = `${GEMINI_BASE_URL}/${model}:generateContent?key=${apiKey}`;

  const requestBody = {
    system_instruction: {
      parts: [{ text: systemContext }],
    },
    contents: [
      {
        role: 'user',
        parts: [{ text: userMessage }],
      },
    ],
    generationConfig: {
      maxOutputTokens: 2048,
      temperature: 0.7,
    },
  };

  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(requestBody),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Gemini API error (${response.status}): ${errorText}`);
  }

  const data = await response.json();

  // Extract response text
  const text = data.candidates?.[0]?.content?.parts?.[0]?.text || 'No response generated.';
  const usage = data.usageMetadata || {};

  return {
    text,
    model,
    inputTokens: usage.promptTokenCount || 0,
    outputTokens: usage.candidatesTokenCount || 0,
  };
}

/**
 * Send a message to Gemini with conversation history.
 *
 * @param {Array} messages - Array of { role: 'user'|'model', content: string }
 * @param {string} systemContext - System prompt
 * @param {string} [model] - Gemini model ID
 * @returns {object} { text, model, inputTokens, outputTokens }
 */
async function chatWithHistory(messages, systemContext, model = 'gemini-2.5-flash') {
  const apiKey = process.env.GEMINI_API_KEY;
  if (!apiKey) {
    throw new Error('GEMINI_API_KEY not configured');
  }

  const url = `${GEMINI_BASE_URL}/${model}:generateContent?key=${apiKey}`;

  // Convert messages to Gemini format
  const contents = messages.map(m => ({
    role: m.role === 'assistant' ? 'model' : m.role,
    parts: [{ text: m.content }],
  }));

  const requestBody = {
    system_instruction: {
      parts: [{ text: systemContext }],
    },
    contents,
    generationConfig: {
      maxOutputTokens: 2048,
      temperature: 0.7,
    },
  };

  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(requestBody),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Gemini API error (${response.status}): ${errorText}`);
  }

  const data = await response.json();

  const text = data.candidates?.[0]?.content?.parts?.[0]?.text || 'No response generated.';
  const usage = data.usageMetadata || {};

  return {
    text,
    model,
    inputTokens: usage.promptTokenCount || 0,
    outputTokens: usage.candidatesTokenCount || 0,
  };
}

module.exports = {
  chat,
  chatWithHistory,
};
