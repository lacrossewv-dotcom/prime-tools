/**
 * Files Routes
 *
 * GET /api/files           — List PRIME root folder contents
 * GET /api/files/:folderId — List folder contents
 * GET /api/files/read/:fileId — Read a file's content
 * GET /api/files/known/:key — Quick access to known PRIME files
 */

const express = require('express');
const router = express.Router();
const drive = require('../services/googleDrive');

/**
 * GET /api/files
 *
 * List the PRIME root folder contents.
 */
router.get('/', async (req, res) => {
  try {
    const primeFolder = await drive.findPrimeFolder();
    const files = await drive.listFolder(primeFolder.id);

    res.json({
      folder: {
        id: primeFolder.id,
        name: primeFolder.name,
      },
      files: files.map(f => ({
        id: f.id,
        name: f.name,
        type: f.mimeType === 'application/vnd.google-apps.folder' ? 'folder' : 'file',
        mimeType: f.mimeType,
        modifiedTime: f.modifiedTime,
        size: f.size,
      })),
      timestamp: new Date().toISOString(),
    });
  } catch (err) {
    console.error('[FILES] Error listing PRIME folder:', err.message);
    res.status(500).json({ error: `Failed to list files: ${err.message}` });
  }
});

/**
 * GET /api/files/folder/:folderId
 *
 * List contents of a specific folder.
 */
router.get('/folder/:folderId', async (req, res) => {
  try {
    const files = await drive.listFolder(req.params.folderId);

    res.json({
      folderId: req.params.folderId,
      files: files.map(f => ({
        id: f.id,
        name: f.name,
        type: f.mimeType === 'application/vnd.google-apps.folder' ? 'folder' : 'file',
        mimeType: f.mimeType,
        modifiedTime: f.modifiedTime,
        size: f.size,
      })),
      timestamp: new Date().toISOString(),
    });
  } catch (err) {
    console.error(`[FILES] Error listing folder ${req.params.folderId}:`, err.message);
    res.status(500).json({ error: `Failed to list folder: ${err.message}` });
  }
});

/**
 * GET /api/files/read/:fileId
 *
 * Read a file's content (Google Doc or regular file).
 */
router.get('/read/:fileId', async (req, res) => {
  try {
    const drive2 = require('../services/googleDrive');
    const { google } = require('googleapis');

    // First get file metadata to determine type
    const auth = new google.auth.OAuth2(
      process.env.GOOGLE_CLIENT_ID,
      process.env.GOOGLE_CLIENT_SECRET
    );
    auth.setCredentials({ refresh_token: process.env.GOOGLE_REFRESH_TOKEN });
    const driveApi = google.drive({ version: 'v3', auth });

    const fileMeta = await driveApi.files.get({
      fileId: req.params.fileId,
      fields: 'id, name, mimeType, modifiedTime, size',
    });

    const content = await drive2.readFileContent(
      req.params.fileId,
      fileMeta.data.mimeType
    );

    res.json({
      file: {
        id: fileMeta.data.id,
        name: fileMeta.data.name,
        mimeType: fileMeta.data.mimeType,
        modifiedTime: fileMeta.data.modifiedTime,
        size: fileMeta.data.size,
      },
      content: typeof content === 'string' ? content : JSON.stringify(content),
      timestamp: new Date().toISOString(),
    });
  } catch (err) {
    console.error(`[FILES] Error reading file ${req.params.fileId}:`, err.message);
    res.status(500).json({ error: `Failed to read file: ${err.message}` });
  }
});

/**
 * GET /api/files/known/:key
 *
 * Quick access to known PRIME files by shortcut key.
 * Keys: session_registry, operations, governance, message_standard,
 *        lifecycle_rules, cross_session, lessons_learned
 */
router.get('/known/:key', async (req, res) => {
  try {
    const key = req.params.key;
    const knownPath = drive.KNOWN_FILES[key];

    if (!knownPath) {
      return res.status(404).json({
        error: `Unknown file key: ${key}`,
        validKeys: Object.keys(drive.KNOWN_FILES),
      });
    }

    // Parse the path to get folder and file name
    const parts = knownPath.split('/');
    const fileName = parts[parts.length - 1];
    const parentFolder = parts[parts.length - 2];

    const file = await drive.findFileByName(fileName, parentFolder);
    if (!file) {
      return res.status(404).json({ error: `File not found: ${fileName}` });
    }

    const content = await drive.readFileContent(file.id, file.mimeType);

    res.json({
      key,
      file: {
        id: file.id,
        name: file.name,
        mimeType: file.mimeType,
        modifiedTime: file.modifiedTime,
      },
      content: typeof content === 'string' ? content : JSON.stringify(content),
      timestamp: new Date().toISOString(),
    });
  } catch (err) {
    console.error(`[FILES] Error reading known file ${req.params.key}:`, err.message);
    res.status(500).json({ error: `Failed to read file: ${err.message}` });
  }
});

module.exports = router;
