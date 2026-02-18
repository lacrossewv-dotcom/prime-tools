/**
 * Auth Module — Google Sign-In and token management
 */

const auth = (() => {
  // Web Application OAuth client ID (created for PRIME Mobile PWA)
  const GOOGLE_CLIENT_ID = '269058620781-dieg1td2o867fbh68ccsrmckvje7n9rk.apps.googleusercontent.com';

  /**
   * Start Google OAuth login flow.
   * For PWA, we use the redirect-based OAuth flow.
   */
  async function login() {
    // For development on localhost, show dev login option
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
      return devLogin();
    }

    // Redirect to Google OAuth consent screen
    const redirectUri = encodeURIComponent(window.location.origin + '/auth/callback');
    const scope = encodeURIComponent('openid email profile');
    const authUrl = `https://accounts.google.com/o/oauth2/v2/auth?` +
      `client_id=${GOOGLE_CLIENT_ID}&redirect_uri=${redirectUri}&response_type=code&scope=${scope}&access_type=offline&prompt=consent`;

    window.location.href = authUrl;
  }

  /**
   * Handle OAuth callback — exchange auth code for JWT via backend.
   * Called from the /auth/callback page.
   */
  async function handleCallback() {
    const params = new URLSearchParams(window.location.search);
    const code = params.get('code');
    const error = params.get('error');

    if (error) {
      alert(`Google login failed: ${error}`);
      window.location.href = '/';
      return;
    }

    if (!code) {
      window.location.href = '/';
      return;
    }

    try {
      // Exchange the authorization code for a JWT via our backend
      const response = await fetch(api.getBaseUrl() + '/api/auth/google/callback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          code,
          redirectUri: window.location.origin + '/auth/callback',
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Authentication failed');
      }

      // Store the JWT and redirect to dashboard
      api.setToken(data.token);
      window.location.href = '/';
    } catch (err) {
      alert(`Login failed: ${err.message}`);
      window.location.href = '/';
    }
  }

  /**
   * Development login — bypasses Google OAuth.
   */
  async function devLogin() {
    try {
      const data = await api.authDev();
      api.setToken(data.token);
      onLoginSuccess(data.user);
    } catch (err) {
      alert(`Login failed: ${err.message}`);
    }
  }

  /**
   * Handle successful login.
   */
  function onLoginSuccess(user) {
    console.log(`[AUTH] Logged in as ${user.email}`);
    document.getElementById('bottom-nav').style.display = 'flex';
    navigate('dashboard');
    dashboard.load();
  }

  /**
   * Logout — clear token and return to login screen.
   */
  function logout() {
    api.setToken(null);
    document.getElementById('bottom-nav').style.display = 'none';
    navigate('login');
  }

  /**
   * Check if user is already authenticated.
   */
  function isLoggedIn() {
    return !!api.getToken();
  }

  /**
   * Show dev login button (for non-production environments).
   */
  function showDevButton() {
    const btn = document.getElementById('btn-dev-login');
    if (btn) btn.style.display = 'block';
  }

  return {
    login,
    devLogin,
    handleCallback,
    onLoginSuccess,
    logout,
    isLoggedIn,
    showDevButton,
  };
})();
