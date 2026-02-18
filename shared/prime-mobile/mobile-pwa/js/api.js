/**
 * API Client — Handles all backend communication
 */

const api = (() => {
  // Backend URL — auto-detect: same origin in production, localhost in dev
  let BASE_URL = localStorage.getItem('prime_api_url') ||
    (window.location.hostname.includes('run.app') ? '' : 'http://localhost:8080');
  let token = localStorage.getItem('prime_token') || null;

  /**
   * Set the API base URL.
   */
  function setBaseUrl(url) {
    BASE_URL = url.replace(/\/$/, '');
    localStorage.setItem('prime_api_url', BASE_URL);
  }

  /**
   * Set the JWT auth token.
   */
  function setToken(t) {
    token = t;
    if (t) {
      localStorage.setItem('prime_token', t);
    } else {
      localStorage.removeItem('prime_token');
    }
  }

  /**
   * Get the stored token.
   */
  function getToken() {
    return token;
  }

  /**
   * Make an authenticated API request.
   */
  async function request(endpoint, options = {}) {
    const url = `${BASE_URL}${endpoint}`;
    const headers = {
      'Content-Type': 'application/json',
      ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
      ...options.headers,
    };

    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (response.status === 401) {
      // Token expired — redirect to login
      setToken(null);
      navigate('login');
      throw new Error('Session expired. Please login again.');
    }

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || `API error: ${response.status}`);
    }

    return data;
  }

  // --- Convenience Methods ---

  function get(endpoint) {
    return request(endpoint, { method: 'GET' });
  }

  function post(endpoint, body) {
    return request(endpoint, {
      method: 'POST',
      body: JSON.stringify(body),
    });
  }

  // --- API Endpoints ---

  /**
   * Get the current base URL.
   */
  function getBaseUrl() {
    return BASE_URL;
  }

  return {
    setBaseUrl,
    getBaseUrl,
    setToken,
    getToken,

    // Health check
    health: () => get('/api/health'),

    // Auth
    authGoogle: (idToken) => post('/api/auth/google', { idToken }),
    authDev: () => post('/api/auth/dev', {}),

    // Sessions
    getSessions: () => get('/api/sessions'),
    getSession: (id) => get(`/api/sessions/${id}`),

    // Inbox
    getUnifiedInbox: (params = '') => get(`/api/inbox${params ? '?' + params : ''}`),
    getSessionInbox: (session) => get(`/api/inbox/${session}`),
    sendMessage: (session, data) => post(`/api/inbox/${session}`, data),

    // Chat
    chatClaude: (data) => post('/api/chat', data),
    chatGemini: (data) => post('/api/chat/gemini', data),

    // Files
    listFiles: () => get('/api/files'),
    listFolder: (folderId) => get(`/api/files/folder/${folderId}`),
    readFile: (fileId) => get(`/api/files/read/${fileId}`),
    readKnownFile: (key) => get(`/api/files/known/${key}`),
  };
})();
