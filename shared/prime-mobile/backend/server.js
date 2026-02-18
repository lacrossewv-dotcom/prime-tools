/**
 * PRIME Mobile API — Express Server
 *
 * Backend for PRIME Mobile app. Provides:
 * - Google OAuth authentication (single-user: stephen@bender23.com)
 * - PRIME session dashboard data from Google Drive
 * - Inbox read/write for 12 session inboxes
 * - Claude and Gemini chat with PRIME context injection
 * - Drive file browser for PRIME folder
 *
 * Deployment: Google Cloud Run
 */

require('dotenv').config();

const express = require('express');
const cors = require('cors');
const path = require('path');
const rateLimit = require('express-rate-limit');

// Route modules
const authRoutes = require('./routes/auth');
const sessionRoutes = require('./routes/sessions');
const inboxRoutes = require('./routes/inbox');
const chatRoutes = require('./routes/chat');
const fileRoutes = require('./routes/files');

// Middleware
const { authenticateJWT } = require('./middleware/auth');

const app = express();
const PORT = process.env.PORT || 8080;

// --- Global Middleware ---

// CORS — allow mobile app origins
app.use(cors({
  origin: [
    'http://localhost:3000',
    'http://localhost:8080',
    'https://prime-mobile-769012743541.us-west1.run.app',
  ],
  credentials: true,
}));

// Parse JSON bodies
app.use(express.json({ limit: '1mb' }));

// Rate limiting — 60 requests per minute per IP
const limiter = rateLimit({
  windowMs: 60 * 1000,
  max: 60,
  standardHeaders: true,
  legacyHeaders: false,
  message: { error: 'Too many requests. Limit: 60/minute.' },
});
app.use('/api/', limiter);

// --- Health Check (no auth) ---
app.get('/api/health', (req, res) => {
  res.json({
    status: 'ok',
    service: 'prime-mobile-api',
    version: '1.0.0',
    timestamp: new Date().toISOString(),
  });
});

// --- Auth Routes (no JWT required) ---
app.use('/api/auth', authRoutes);

// --- Protected Routes (JWT required) ---
app.use('/api/sessions', authenticateJWT, sessionRoutes);
app.use('/api/inbox', authenticateJWT, inboxRoutes);
app.use('/api/chat', authenticateJWT, chatRoutes);
app.use('/api/files', authenticateJWT, fileRoutes);

// --- Serve PWA Static Files ---
// In production, serve the PWA from the backend (same Cloud Run service)
const pwaPath = path.join(__dirname, '..', 'mobile-pwa');
app.use(express.static(pwaPath));

// SPA fallback — serve index.html for non-API routes
app.get('*', (req, res, next) => {
  if (req.path.startsWith('/api/')) return next();
  res.sendFile(path.join(pwaPath, 'index.html'));
});

// --- Error Handler ---
app.use((err, req, res, next) => {
  console.error(`[ERROR] ${err.message}`);
  console.error(err.stack);
  res.status(err.status || 500).json({
    error: err.message || 'Internal server error',
  });
});

// --- Start Server ---
app.listen(PORT, () => {
  console.log(`PRIME Mobile API running on port ${PORT}`);
  console.log(`Environment: ${process.env.NODE_ENV || 'development'}`);
});

module.exports = app;
