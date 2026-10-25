// Aegis Browser - New Tab Page Logic (100% Offline & Private)

const ENGINES = {
  duckduckgo: { name: 'DuckDuckGo', prefix: ':d', url: 'https://duckduckgo.com/?q=' },
  brave: { name: 'Brave Search', prefix: ':b', url: 'https://search.brave.com/search?q=' },
  wikipedia: { name: 'Wikipedia', prefix: ':w', url: 'https://wikipedia.org/w/index.php?search=' },
  google: { name: 'Google', prefix: ':g', url: 'https://www.google.com/search?q=' }
};

const DEFAULT_SHORTCUTS = [
  { title: 'DuckDuckGo', url: 'https://duckduckgo.com', icon: '🦆' },
  { title: 'GitHub', url: 'https://github.com', icon: '🐙' },
  { title: 'Wikipedia', url: 'https://wikipedia.org', icon: '📚' },
  { title: 'Reddit', url: 'https://reddit.com', icon: '🤖' },
  { title: 'HackerNews', url: 'https://news.ycombinator.com', icon: '⚡' }
];

document.addEventListener('DOMContentLoaded', () => {
  initSearch();
  initShieldsStats();
  initShortcuts();
  initSettings();
});

// 1. Buscador Inteligente y Atajos
function initSearch() {
  const form = document.getElementById('search-form');
  const input = document.getElementById('search-input');
  const engineBtn = document.getElementById('engine-selector');

  let currentEngine = localStorage.getItem('aegis_search_engine') || 'duckduckgo';
  updateEngineUI(currentEngine);

  engineBtn.addEventListener('click', () => {
    const keys = Object.keys(ENGINES);
    const nextIdx = (keys.indexOf(currentEngine) + 1) % keys.length;
    currentEngine = keys[nextIdx];
    localStorage.setItem('aegis_search_engine', currentEngine);
    updateEngineUI(currentEngine);
  });

  form.addEventListener('submit', (e) => {
    e.preventDefault();
    const query = input.value.trim();
    if (!query) return;

    // Navegación directa a URL
    if (/^(https?:\/\/|[a-zA-Z0-9-]+\.[a-zA-Z]{2,})/.test(query)) {
      const url = query.startsWith('http') ? query : `https://${query}`;
      window.location.href = url;
      return;
    }

    // Prefijos rápidos (:d, :b, :w, :g)
    for (const [key, engine] of Object.entries(ENGINES)) {
      if (query.startsWith(engine.prefix + ' ')) {
        const cleanQuery = query.substring(engine.prefix.length + 1).trim();
        window.location.href = engine.url + encodeURIComponent(cleanQuery);
        return;
      }
    }

    // Búsqueda con motor predeterminado
    window.location.href = ENGINES[currentEngine].url + encodeURIComponent(query);
  });

  function updateEngineUI(engineKey) {
    const engine = ENGINES[engineKey] || ENGINES.duckduckgo;
    engineBtn.textContent = `${engine.name} (${engine.prefix})`;
    input.placeholder = `Buscar con ${engine.name} o escribir URL...`;
  }
}

// 2. Contador de Aegis Shields
function initShieldsStats() {
  const trackerEl = document.getElementById('trackers-count');
  let blockedCount = parseInt(localStorage.getItem('aegis_blocked_count') || '142', 10);

  // Simular incremento de estadísticas en sesión local
  trackerEl.textContent = blockedCount.toLocaleString();

  // Escuchar eventos de Chromium WebChannel si están presentes
  if (window.chrome && window.chrome.aegisShields) {
    window.chrome.aegisShields.onBlockedStatsUpdated = (stats) => {
      trackerEl.textContent = stats.totalBlocked.toLocaleString();
    };
  }
}

// 3. Cuadrícula de Accesos Directos
function initShortcuts() {
  const grid = document.getElementById('shortcuts-grid');
  let shortcuts = JSON.parse(localStorage.getItem('aegis_shortcuts') || 'null') || DEFAULT_SHORTCUTS;

  renderShortcuts();

  function renderShortcuts() {
    grid.innerHTML = '';
    shortcuts.forEach((s) => {
      const card = document.createElement('a');
      card.className = 'shortcut-card';
      card.href = s.url;
      card.innerHTML = `
        <div class="shortcut-icon">${s.icon || '🌐'}</div>
        <div class="shortcut-title">${s.title}</div>
      `;
      grid.appendChild(card);
    });
  }
}

// 4. Modal de Configuración y Preferencias
function initSettings() {
  const modal = document.getElementById('settings-modal');
  const openBtn = document.getElementById('open-settings');
  const closeBtn = document.getElementById('close-settings');
  const verticalTabsToggle = document.getElementById('vertical-tabs-toggle');
  const themeToggle = document.getElementById('theme-toggle');

  // Cargar estado de pestañas verticales
  const isVertical = localStorage.getItem('aegis_vertical_tabs') === 'true';
  verticalTabsToggle.checked = isVertical;

  verticalTabsToggle.addEventListener('change', (e) => {
    localStorage.setItem('aegis_vertical_tabs', e.target.checked);
    // Notificar al navegador si tiene la API nativa de Aegis
    if (window.chrome && window.chrome.aegisPrefs) {
      window.chrome.aegisPrefs.setBoolean('aegis.tabs.vertical_enabled', e.target.checked);
    }
  });

  // Tema
  let currentTheme = localStorage.getItem('aegis_theme') || 'auto';
  applyTheme(currentTheme);

  themeToggle.addEventListener('click', () => {
    currentTheme = currentTheme === 'dark' ? 'light' : 'dark';
    localStorage.setItem('aegis_theme', currentTheme);
    applyTheme(currentTheme);
  });

  function applyTheme(theme) {
    document.documentElement.className = `theme-${theme}`;
  }

  openBtn.addEventListener('click', () => modal.classList.add('active'));
  closeBtn.addEventListener('click', () => modal.classList.remove('active'));
  modal.addEventListener('click', (e) => {
    if (e.target === modal) modal.classList.remove('active');
  });
}
