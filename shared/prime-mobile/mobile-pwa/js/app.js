/**
 * App Module — Navigation and initialization
 */

/**
 * Navigate to a screen.
 */
function navigate(screenName) {
  // Hide all screens
  document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));

  // Show target screen
  const target = document.getElementById(`screen-${screenName}`);
  if (target) {
    target.classList.add('active');
  }

  // Update nav buttons
  document.querySelectorAll('.nav-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.screen === screenName);
  });

  // Load data for the screen
  switch (screenName) {
    case 'dashboard':
      dashboard.load();
      break;
    case 'inbox':
      inbox.load();
      break;
    case 'files':
      files.load();
      break;
    // Chat doesn't auto-reload (preserves history)
  }
}

/**
 * Initialize the app on page load.
 */
function init() {
  console.log('[PRIME Mobile] Initializing...');

  // Check for API URL override in URL params
  const params = new URLSearchParams(window.location.search);
  if (params.has('api')) {
    api.setBaseUrl(params.get('api'));
    console.log(`[PRIME Mobile] API URL set to: ${params.get('api')}`);
  }

  // Show dev login button in non-production
  if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    auth.showDevButton();
  }

  // Check if already logged in
  if (auth.isLoggedIn()) {
    document.getElementById('bottom-nav').style.display = 'flex';
    navigate('dashboard');
  } else {
    navigate('login');
  }

  // Register service worker for PWA
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('sw.js')
      .then(() => console.log('[PWA] Service worker registered'))
      .catch(err => console.warn('[PWA] SW registration failed:', err));
  }
}

// Start the app
document.addEventListener('DOMContentLoaded', init);
