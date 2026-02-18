/**
 * Files Module — Drive file browser
 */

const files = (() => {
  let breadcrumbs = [{ name: 'PRIME', id: null }];

  /**
   * Load the PRIME root folder.
   */
  async function load() {
    const list = document.getElementById('file-list');
    list.innerHTML = '<div class="loading">Loading files...</div>';

    try {
      const data = await api.listFiles();
      breadcrumbs = [{ name: data.folder.name, id: data.folder.id }];
      renderBreadcrumbs();
      renderFiles(data.files);
    } catch (err) {
      list.innerHTML = `<div class="error-text">Failed to load: ${err.message}</div>`;
    }
  }

  /**
   * Open a folder.
   */
  async function openFolder(folderId, folderName) {
    const list = document.getElementById('file-list');
    list.innerHTML = '<div class="loading">Loading...</div>';

    // Hide file viewer if open
    closeViewer();

    try {
      const data = await api.listFolder(folderId);
      breadcrumbs.push({ name: folderName, id: folderId });
      renderBreadcrumbs();
      renderFiles(data.files);
    } catch (err) {
      list.innerHTML = `<div class="error-text">Failed to load: ${err.message}</div>`;
    }
  }

  /**
   * Open a file for reading.
   */
  async function openFile(fileId, fileName) {
    const viewer = document.getElementById('file-viewer');
    const viewerName = document.getElementById('file-viewer-name');
    const viewerContent = document.getElementById('file-viewer-content');

    viewer.style.display = 'block';
    viewerName.textContent = fileName;
    viewerContent.textContent = 'Loading...';

    try {
      const data = await api.readFile(fileId);
      viewerContent.textContent = data.content;
    } catch (err) {
      viewerContent.textContent = `Error: ${err.message}`;
    }
  }

  /**
   * Close the file viewer.
   */
  function closeViewer() {
    document.getElementById('file-viewer').style.display = 'none';
  }

  /**
   * Navigate to the PRIME root.
   */
  function goHome() {
    closeViewer();
    breadcrumbs = [];
    load();
  }

  /**
   * Navigate to a breadcrumb position.
   */
  function navigateTo(index) {
    closeViewer();
    if (index === 0) {
      breadcrumbs = breadcrumbs.slice(0, 1);
      load();
      return;
    }

    const target = breadcrumbs[index];
    breadcrumbs = breadcrumbs.slice(0, index + 1);
    renderBreadcrumbs();

    // Reload the target folder
    const list = document.getElementById('file-list');
    list.innerHTML = '<div class="loading">Loading...</div>';

    api.listFolder(target.id).then(data => {
      renderFiles(data.files);
    }).catch(err => {
      list.innerHTML = `<div class="error-text">${err.message}</div>`;
    });
  }

  /**
   * Render breadcrumbs navigation.
   */
  function renderBreadcrumbs() {
    const nav = document.getElementById('file-breadcrumbs');
    nav.innerHTML = breadcrumbs.map((b, i) => {
      if (i === breadcrumbs.length - 1) {
        return `<span>${b.name}</span>`;
      }
      return `<span onclick="files.navigateTo(${i})">${b.name}</span> / `;
    }).join('');
  }

  /**
   * Render file list.
   */
  function renderFiles(fileList) {
    const container = document.getElementById('file-list');

    if (!fileList || fileList.length === 0) {
      container.innerHTML = '<div class="loading">Empty folder</div>';
      return;
    }

    // Sort: folders first, then files
    const sorted = [...fileList].sort((a, b) => {
      if (a.type === 'folder' && b.type !== 'folder') return -1;
      if (a.type !== 'folder' && b.type === 'folder') return 1;
      return a.name.localeCompare(b.name);
    });

    container.innerHTML = sorted.map(f => {
      const icon = f.type === 'folder' ? '&#128193;' : '&#128196;';
      const clickAction = f.type === 'folder'
        ? `files.openFolder('${f.id}', '${escapeAttr(f.name)}')`
        : `files.openFile('${f.id}', '${escapeAttr(f.name)}')`;
      const meta = f.modifiedTime
        ? new Date(f.modifiedTime).toLocaleDateString()
        : '';

      return `
        <div class="file-item" onclick="${clickAction}">
          <span class="file-icon">${icon}</span>
          <div class="file-info">
            <div class="file-name">${f.name}</div>
            <div class="file-meta">${meta}${f.size ? ' | ' + formatSize(f.size) : ''}</div>
          </div>
        </div>
      `;
    }).join('');
  }

  /**
   * Format file size.
   */
  function formatSize(bytes) {
    if (!bytes) return '';
    const kb = bytes / 1024;
    if (kb < 1024) return Math.round(kb) + ' KB';
    return (kb / 1024).toFixed(1) + ' MB';
  }

  /**
   * Escape HTML attribute value.
   */
  function escapeAttr(str) {
    return str.replace(/'/g, "\\'").replace(/"/g, '&quot;');
  }

  return {
    load,
    openFolder,
    openFile,
    closeViewer,
    goHome,
    navigateTo,
  };
})();
