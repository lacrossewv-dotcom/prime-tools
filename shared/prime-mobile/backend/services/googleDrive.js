/**
 * Google Drive Service
 *
 * Handles all Google Drive API operations for PRIME Mobile.
 * Uses OAuth refresh token for stephen@bender23.com to access Drive.
 *
 * Key operations:
 * - Read PRIME inbox files (TO_*.md)
 * - Write new messages to inbox files (append)
 * - List files in PRIME directory
 * - Read any file by ID
 */

const { google } = require('googleapis');

// PRIME folder structure on Google Drive
const PRIME_ROOT = '00_CLAUDE_PRIME';
const MESSAGES_DIR = `${PRIME_ROOT}/messages`;

// Session inbox file mapping
const SESSION_INBOXES = {
  athena: 'TO_ATHENA.md',
  '8901': 'TO_8901.md',
  '8902': 'TO_8902.md',
  jado: 'TO_JADO.md',
  coi_research: 'TO_COI_RESEARCH.md',
  atlas: 'TO_ATLAS.md',
  google: 'TO_GOOGLE_WORKSPACE.md',
  sketchi: 'TO_SKETCHI.md',
  semper: 'TO_SEMPER.md',
  fsmao: 'TO_FSMAO.md',
  index: 'TO_INDEX.md',
  historian: 'TO_HISTORIAN.md',
};

// Known PRIME files for quick access
const KNOWN_FILES = {
  session_registry: `${PRIME_ROOT}/registry/SESSION_REGISTRY.md`,
  operations: `${PRIME_ROOT}/operations/PRIME_OPERATIONS.md`,
  governance: `${PRIME_ROOT}/governance/PRIME_GOVERNANCE.md`,
  message_standard: `${PRIME_ROOT}/governance/MESSAGE_STANDARD.md`,
  lifecycle_rules: `${PRIME_ROOT}/governance/LIFECYCLE_RULES.md`,
  cross_session: `${PRIME_ROOT}/knowledge/CROSS_SESSION.md`,
  lessons_learned: `${PRIME_ROOT}/knowledge/LESSONS_LEARNED.md`,
};

let driveClient = null;
let docsClient = null;

/**
 * Initialize the Google Drive client using OAuth2 refresh token.
 */
function getOAuth2Client() {
  const oauth2Client = new google.auth.OAuth2(
    process.env.GOOGLE_CLIENT_ID,
    process.env.GOOGLE_CLIENT_SECRET
  );

  oauth2Client.setCredentials({
    refresh_token: process.env.GOOGLE_REFRESH_TOKEN,
  });

  return oauth2Client;
}

/**
 * Get the Drive client (lazy initialization).
 */
function getDrive() {
  if (!driveClient) {
    const auth = getOAuth2Client();
    driveClient = google.drive({ version: 'v3', auth });
  }
  return driveClient;
}

/**
 * Get the Docs client (lazy initialization).
 */
function getDocs() {
  if (!docsClient) {
    const auth = getOAuth2Client();
    docsClient = google.docs({ version: 'v1', auth });
  }
  return docsClient;
}

/**
 * Search for a file by name in Google Drive.
 *
 * @param {string} fileName - Name of the file to find
 * @param {string} [parentName] - Optional parent folder name
 * @returns {object|null} File metadata { id, name, mimeType, modifiedTime }
 */
async function findFileByName(fileName, parentName) {
  const drive = getDrive();

  let query = `name = '${fileName}' and trashed = false`;

  if (parentName) {
    // First find the parent folder
    const parentResult = await drive.files.list({
      q: `name = '${parentName}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false`,
      fields: 'files(id, name)',
      pageSize: 5,
    });

    if (parentResult.data.files && parentResult.data.files.length > 0) {
      query += ` and '${parentResult.data.files[0].id}' in parents`;
    }
  }

  const result = await drive.files.list({
    q: query,
    fields: 'files(id, name, mimeType, modifiedTime, size)',
    pageSize: 10,
  });

  if (result.data.files && result.data.files.length > 0) {
    return result.data.files[0];
  }

  return null;
}

/**
 * Read a Google Doc's content as plain text.
 *
 * PRIME stores .md files as Google Docs on Drive.
 * This reads the Doc and returns its text content.
 *
 * @param {string} fileId - Google Drive file ID
 * @returns {string} Plain text content
 */
async function readGoogleDoc(fileId) {
  const drive = getDrive();

  // Export Google Doc as plain text
  const response = await drive.files.export({
    fileId: fileId,
    mimeType: 'text/plain',
  });

  return response.data;
}

/**
 * Read a file's content from Google Drive.
 * Handles both Google Docs and regular files.
 *
 * @param {string} fileId - Google Drive file ID
 * @param {string} mimeType - File's MIME type
 * @returns {string} File content as text
 */
async function readFileContent(fileId, mimeType) {
  const drive = getDrive();

  if (mimeType === 'application/vnd.google-apps.document') {
    return readGoogleDoc(fileId);
  }

  // For regular files, download content
  const response = await drive.files.get({
    fileId: fileId,
    alt: 'media',
  });

  return response.data;
}

/**
 * Append text to a Google Doc (for writing inbox messages).
 *
 * @param {string} fileId - Google Drive file ID of the target Doc
 * @param {string} text - Markdown text to append
 */
async function appendToGoogleDoc(fileId, text) {
  const docs = getDocs();

  // Get current doc to find the end index
  const doc = await docs.documents.get({ documentId: fileId });
  const endIndex = doc.data.body.content[doc.data.body.content.length - 1].endIndex;

  // Insert at the end of the document
  await docs.documents.batchUpdate({
    documentId: fileId,
    requestBody: {
      requests: [
        {
          insertText: {
            location: { index: endIndex - 1 },
            text: '\n\n---\n\n' + text,
          },
        },
      ],
    },
  });
}

/**
 * List files in a Google Drive folder.
 *
 * @param {string} folderId - Folder ID (or 'root' for root)
 * @returns {Array} Array of { id, name, mimeType, modifiedTime, size }
 */
async function listFolder(folderId) {
  const drive = getDrive();

  const result = await drive.files.list({
    q: `'${folderId}' in parents and trashed = false`,
    fields: 'files(id, name, mimeType, modifiedTime, size)',
    orderBy: 'name',
    pageSize: 100,
  });

  return result.data.files || [];
}

/**
 * Find and read a PRIME inbox file.
 *
 * @param {string} sessionKey - Session key (e.g., 'athena', 'google', '8901')
 * @returns {string} Inbox file content
 */
async function readInbox(sessionKey) {
  const fileName = SESSION_INBOXES[sessionKey];
  if (!fileName) {
    throw new Error(`Unknown session: ${sessionKey}`);
  }

  const file = await findFileByName(fileName, 'messages');
  if (!file) {
    throw new Error(`Inbox file not found: ${fileName}`);
  }

  return {
    content: await readFileContent(file.id, file.mimeType),
    fileId: file.id,
    modifiedTime: file.modifiedTime,
  };
}

/**
 * Write a new message to a PRIME inbox file.
 *
 * @param {string} sessionKey - Target session key
 * @param {string} messageText - Formatted markdown message (with canonical header)
 */
async function writeToInbox(sessionKey, messageText) {
  const fileName = SESSION_INBOXES[sessionKey];
  if (!fileName) {
    throw new Error(`Unknown session: ${sessionKey}`);
  }

  const file = await findFileByName(fileName, 'messages');
  if (!file) {
    throw new Error(`Inbox file not found: ${fileName}`);
  }

  await appendToGoogleDoc(file.id, messageText);
}

/**
 * Read the SESSION_REGISTRY.md file.
 *
 * @returns {string} Full content of SESSION_REGISTRY.md
 */
async function readSessionRegistry() {
  const file = await findFileByName('SESSION_REGISTRY.md', 'registry');
  if (!file) {
    throw new Error('SESSION_REGISTRY.md not found');
  }

  return readFileContent(file.id, file.mimeType);
}

/**
 * Read PRIME_OPERATIONS.md for deadlines and active threads.
 *
 * @returns {string} Full content of PRIME_OPERATIONS.md
 */
async function readOperations() {
  const file = await findFileByName('PRIME_OPERATIONS.md', 'operations');
  if (!file) {
    throw new Error('PRIME_OPERATIONS.md not found');
  }

  return readFileContent(file.id, file.mimeType);
}

/**
 * Find the PRIME root folder on Drive.
 *
 * @returns {object} Folder metadata { id, name }
 */
async function findPrimeFolder() {
  const drive = getDrive();

  const result = await drive.files.list({
    q: `name = '${PRIME_ROOT}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false`,
    fields: 'files(id, name)',
    pageSize: 5,
  });

  if (result.data.files && result.data.files.length > 0) {
    return result.data.files[0];
  }

  throw new Error(`PRIME root folder not found: ${PRIME_ROOT}`);
}

module.exports = {
  SESSION_INBOXES,
  KNOWN_FILES,
  findFileByName,
  readGoogleDoc,
  readFileContent,
  appendToGoogleDoc,
  listFolder,
  readInbox,
  writeToInbox,
  readSessionRegistry,
  readOperations,
  findPrimeFolder,
};
