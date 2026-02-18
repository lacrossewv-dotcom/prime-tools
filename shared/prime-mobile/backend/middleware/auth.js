/**
 * JWT Authentication Middleware
 *
 * Verifies Bearer token on protected routes.
 * Single-user system: only stephen@bender23.com is allowed.
 */

const jwt = require('jsonwebtoken');

const JWT_SECRET = process.env.JWT_SECRET || 'dev-secret-change-in-production';
const ALLOWED_EMAIL = process.env.ALLOWED_EMAIL || 'stephen@bender23.com';

/**
 * Verify JWT from Authorization header.
 * Attaches decoded user info to req.user.
 */
function authenticateJWT(req, res, next) {
  const authHeader = req.headers.authorization;

  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ error: 'Missing or invalid Authorization header' });
  }

  const token = authHeader.split(' ')[1];

  try {
    const decoded = jwt.verify(token, JWT_SECRET);

    // Single-user security: only allow the configured email
    if (decoded.email !== ALLOWED_EMAIL) {
      console.warn(`[AUTH] Rejected login from: ${decoded.email}`);
      return res.status(403).json({ error: 'Unauthorized user' });
    }

    req.user = decoded;
    next();
  } catch (err) {
    if (err.name === 'TokenExpiredError') {
      return res.status(401).json({ error: 'Token expired. Please re-authenticate.' });
    }
    return res.status(401).json({ error: 'Invalid token' });
  }
}

/**
 * Generate a JWT for an authenticated user.
 *
 * @param {object} userInfo - { email, name, picture }
 * @returns {string} signed JWT (24-hour expiry)
 */
function generateToken(userInfo) {
  return jwt.sign(
    {
      email: userInfo.email,
      name: userInfo.name,
      picture: userInfo.picture,
    },
    JWT_SECRET,
    { expiresIn: '24h' }
  );
}

module.exports = { authenticateJWT, generateToken };
