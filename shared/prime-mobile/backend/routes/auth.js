/**
 * Auth Routes
 *
 * POST /api/auth/google — Exchange Google OAuth token for JWT
 *
 * Flow:
 * 1. Mobile app gets Google ID token via Google Sign-In
 * 2. Sends ID token to this endpoint
 * 3. We verify it with Google, check email is allowed
 * 4. Return a JWT for subsequent API calls
 */

const express = require('express');
const router = express.Router();
const { generateToken } = require('../middleware/auth');

const ALLOWED_EMAIL = process.env.ALLOWED_EMAIL || 'stephen@bender23.com';

// Web Application OAuth client ID (for PRIME Mobile PWA)
const WEB_CLIENT_ID = process.env.GOOGLE_WEB_CLIENT_ID || process.env.GOOGLE_CLIENT_ID;
const WEB_CLIENT_SECRET = process.env.GOOGLE_WEB_CLIENT_SECRET || process.env.GOOGLE_CLIENT_SECRET;

/**
 * POST /api/auth/google
 *
 * Body: { idToken: "google-id-token-from-sign-in" }
 * Returns: { token: "jwt-token", user: { email, name, picture } }
 */
router.post('/google', async (req, res) => {
  try {
    const { idToken } = req.body;

    if (!idToken) {
      return res.status(400).json({ error: 'Missing idToken in request body' });
    }

    // Verify Google ID token
    const { OAuth2Client } = require('google-auth-library');
    const client = new OAuth2Client(WEB_CLIENT_ID);

    const ticket = await client.verifyIdToken({
      idToken: idToken,
      audience: WEB_CLIENT_ID,
    });

    const payload = ticket.getPayload();

    // Single-user security check
    if (payload.email !== ALLOWED_EMAIL) {
      console.warn(`[AUTH] Rejected login attempt from: ${payload.email}`);
      return res.status(403).json({ error: 'Unauthorized. This app is restricted.' });
    }

    // Generate JWT
    const userInfo = {
      email: payload.email,
      name: payload.name || 'Steve',
      picture: payload.picture || null,
    };

    const token = generateToken(userInfo);

    res.json({
      token,
      user: userInfo,
      expiresIn: '24h',
    });
  } catch (err) {
    console.error('[AUTH] Google verification failed:', err.message);
    res.status(401).json({ error: 'Invalid Google token' });
  }
});

/**
 * POST /api/auth/google/callback
 *
 * Exchange OAuth authorization code for user info + JWT.
 * This is the server-side code exchange for the redirect-based OAuth flow.
 *
 * Body: { code: "auth-code-from-google", redirectUri: "https://..." }
 * Returns: { token: "jwt-token", user: { email, name, picture } }
 */
router.post('/google/callback', async (req, res) => {
  try {
    const { code, redirectUri } = req.body;

    if (!code) {
      return res.status(400).json({ error: 'Missing authorization code' });
    }

    // Exchange auth code for tokens using Google's token endpoint
    const tokenResponse = await fetch('https://oauth2.googleapis.com/token', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({
        code,
        client_id: WEB_CLIENT_ID,
        client_secret: WEB_CLIENT_SECRET,
        redirect_uri: redirectUri,
        grant_type: 'authorization_code',
      }),
    });

    const tokenData = await tokenResponse.json();

    if (!tokenResponse.ok) {
      console.error('[AUTH] Token exchange failed:', tokenData);
      return res.status(401).json({ error: tokenData.error_description || 'Token exchange failed' });
    }

    // Verify the ID token we received
    const { OAuth2Client } = require('google-auth-library');
    const client = new OAuth2Client(WEB_CLIENT_ID);

    const ticket = await client.verifyIdToken({
      idToken: tokenData.id_token,
      audience: WEB_CLIENT_ID,
    });

    const payload = ticket.getPayload();

    // Single-user security check
    if (payload.email !== ALLOWED_EMAIL) {
      console.warn(`[AUTH] Rejected login attempt from: ${payload.email}`);
      return res.status(403).json({ error: 'Unauthorized. This app is restricted to stephen@bender23.com.' });
    }

    // Generate JWT for our app
    const userInfo = {
      email: payload.email,
      name: payload.name || 'Steve',
      picture: payload.picture || null,
    };

    const token = generateToken(userInfo);

    console.log(`[AUTH] Successful OAuth login for ${payload.email}`);

    res.json({
      token,
      user: userInfo,
      expiresIn: '24h',
    });
  } catch (err) {
    console.error('[AUTH] OAuth callback failed:', err.message);
    res.status(401).json({ error: 'Authentication failed: ' + err.message });
  }
});

/**
 * POST /api/auth/dev
 *
 * Development-only: bypass Google OAuth for local testing.
 * Only available when NODE_ENV !== 'production'.
 */
router.post('/dev', (req, res) => {
  if (process.env.NODE_ENV === 'production') {
    return res.status(404).json({ error: 'Not found' });
  }

  const token = generateToken({
    email: ALLOWED_EMAIL,
    name: 'Steve (dev)',
    picture: null,
  });

  res.json({
    token,
    user: { email: ALLOWED_EMAIL, name: 'Steve (dev)' },
    expiresIn: '24h',
    warning: 'Development auth — not for production use',
  });
});

module.exports = router;
