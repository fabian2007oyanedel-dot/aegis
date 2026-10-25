// Aegis Browser - Production-Grade WebUI & Hub Controller (100x Features)

const ENGINES = {
  duckduckgo: { name: 'DuckDuckGo', prefix: ':d', url: 'https://duckduckgo.com/?q=' },
  brave: { name: 'Brave Search', prefix: ':b', url: 'https://search.brave.com/search?q=' },
  startpage: { name: 'Startpage', prefix: ':sp', url: 'https://www.startpage.com/sp/search?query=' },
  wikipedia: { name: 'Wikipedia', prefix: ':w', url: 'https://wikipedia.org/w/index.php?search=' },
  github: { name: 'GitHub', prefix: ':gh', url: 'https://github.com/search?q=' },
  youtube: { name: 'YouTube', prefix: ':yt', url: 'https://www.youtube.com/results?search_query=' },
  google: { name: 'Google', prefix: ':g', url: 'https://www.google.com/search?q=' }
};

const DEFAULT_SHORTCUTS = [
  { id: '1', title: 'DuckDuckGo', url: 'https://duckduckgo.com', icon: '🦆' },
  { id: '2', title: 'GitHub', url: 'https://github.com', icon: '🐙' },
  { id: '3', title: 'Wikipedia', url: 'https://wikipedia.org', icon: '📚' },
  { id: '4', title: 'Reddit', url: 'https://reddit.com', icon: '🤖' },
  { id: '5', title: 'YouTube', url: 'https://youtube.com', icon: '▶️' },
  { id: '6', title: 'Hacker News', url: 'https://news.ycombinator.com', icon: '⚡' }
];

const DEFAULT_HISTORY = [
  { title: 'Aegis Browser GitHub Repository', url: 'https://github.com/fabian2007oyanedel-dot/aegis', time: 'Hoy' },
  { title: 'adblock-rust Documentation', url: 'https://docs.rs/adblock', time: 'Hoy' },
  { title: 'Chromium Source Tree', url: 'https://source.chromium.org', time: 'Ayer' },
  { title: 'DuckDuckGo Privacy Protection', url: 'https://duckduckgo.com', time: 'Ayer' }
];

document.addEventListener('DOMContentLoaded', () => {
  initClock();
  initOmnibox();
  initShortcuts();
  initBookmarksBar();
  initScratchpad();
  initShieldsModal();
  initSettingsHub();
  initPasswordGenerator();
  initHistoryView();
  initThemeManager();
});

// 1. Reloj y Fecha en Vivo
function initClock() {
  const clockEl = document.getElementById('live-clock');
  const dateEl = document.getElementById('live-date');

  function update() {
    const now = new Date();
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    clockEl.textContent = `${hours}:${minutes}`;

    const options = { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' };
    const dateStr = now.toLocaleDateString('es-ES', options);
    dateEl.textContent = dateStr.charAt(0).toUpperCase() + dateStr.slice(1);
  }
  update();
  setInterval(update, 1000);
}

// 2. Omnibox con Atajos Rápidos
function initOmnibox() {
  const form = document.getElementById('omnibox-form');
  const input = document.getElementById('omnibox-input');
  const engineChip = document.getElementById('engine-chip');
  const chips = document.querySelectorAll('.chip-btn');

  let currentEngineKey = localStorage.getItem('aegis_search_engine') || 'duckduckgo';
  updateEngineDisplay(currentEngineKey);

  engineChip.addEventListener('click', () => {
    const keys = Object.keys(ENGINES);
    const nextIdx = (keys.indexOf(currentEngineKey) + 1) % keys.length;
    currentEngineKey = keys[nextIdx];
    localStorage.setItem('aegis_search_engine', currentEngineKey);
    updateEngineDisplay(currentEngineKey);
  });

  chips.forEach((btn) => {
    btn.addEventListener('click', () => {
      const prefix = btn.getAttribute('data-prefix');
      input.value = prefix + ' ';
      input.focus();
    });
  });

  form.addEventListener('submit', (e) => {
    e.preventDefault();
    const query = input.value.trim();
    if (!query) return;

    // Navegación directa
    if (/^(https?:\/\/|[a-zA-Z0-9-]+\.[a-zA-Z]{2,})/.test(query)) {
      const url = query.startsWith('http') ? query : `https://${query}`;
      window.location.href = url;
      return;
    }

    // Atajos de prefijo
    for (const [key, engine] of Object.entries(ENGINES)) {
      if (query.startsWith(engine.prefix + ' ')) {
        const cleanQuery = query.substring(engine.prefix.length + 1).trim();
        window.location.href = engine.url + encodeURIComponent(cleanQuery);
        return;
      }
    }

    // Búsqueda por defecto
    const defaultEngine = ENGINES[currentEngineKey] || ENGINES.duckduckgo;
    window.location.href = defaultEngine.url + encodeURIComponent(query);
  });

  function updateEngineDisplay(key) {
    const eng = ENGINES[key] || ENGINES.duckduckgo;
    engineChip.textContent = `${eng.name} (${eng.prefix})`;
    input.placeholder = `Buscar con ${eng.name} o escribir URL...`;
  }
}

// 3. Accesos Directos CRUD
function initShortcuts() {
  const grid = document.getElementById('shortcuts-grid');
  let shortcuts = JSON.parse(localStorage.getItem('aegis_shortcuts') || 'null') || DEFAULT_SHORTCUTS;

  render();

  function render() {
    grid.innerHTML = '';
    shortcuts.forEach((item, index) => {
      const tile = document.createElement('a');
      tile.className = 'shortcut-tile';
      tile.href = item.url;
      tile.innerHTML = `
        <button class="tile-del-btn" title="Eliminar" data-idx="${index}">✕</button>
        <div class="tile-icon-box">${item.icon || '🌐'}</div>
        <div class="tile-title">${item.title}</div>
      `;
      grid.appendChild(tile);
    });

    // Botón de Añadir
    const addTile = document.createElement('div');
    addTile.className = 'shortcut-tile';
    addTile.style.cursor = 'pointer';
    addTile.innerHTML = `
      <div class="tile-icon-box" style="border-style: dashed; color: var(--text-muted);">+</div>
      <div class="tile-title" style="color: var(--text-muted);">Añadir</div>
    `;
    addTile.addEventListener('click', () => {
      const title = prompt('Nombre del acceso directo:');
      if (!title) return;
      let url = prompt('URL del sitio (ej. https://ejemplo.com):');
      if (!url) return;
      if (!url.startsWith('http')) url = 'https://' + url;
      shortcuts.push({ id: String(Date.now()), title, url, icon: '⭐' });
      localStorage.setItem('aegis_shortcuts', JSON.stringify(shortcuts));
      render();
    });
    grid.appendChild(addTile);

    // Eventos de eliminar
    grid.querySelectorAll('.tile-del-btn').forEach((btn) => {
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        const idx = parseInt(btn.getAttribute('data-idx'), 10);
        shortcuts.splice(idx, 1);
        localStorage.setItem('aegis_shortcuts', JSON.stringify(shortcuts));
        render();
      });
    });
  }
}

// 4. Barra Rápida de Marcadores
function initBookmarksBar() {
  const bar = document.getElementById('bookmarks-bar');
  const toggleBtn = document.getElementById('toggle-bookmarks-btn');
  const addBtn = document.getElementById('add-bookmark-btn');

  let show = localStorage.getItem('aegis_show_bookmarks') !== 'false';
  bar.style.display = show ? 'flex' : 'none';

  toggleBtn.addEventListener('click', () => {
    show = !show;
    bar.style.display = show ? 'flex' : 'none';
    localStorage.setItem('aegis_show_bookmarks', show);
  });

  addBtn.addEventListener('click', () => {
    const name = prompt('Nombre del marcador:');
    if (!name) return;
    let url = prompt('URL del marcador:');
    if (!url) return;
    if (!url.startsWith('http')) url = 'https://' + url;

    const link = document.createElement('a');
    link.href = url;
    link.className = 'bookmark-item';
    link.textContent = `⭐ ${name}`;
    bar.insertBefore(link, addBtn);
  });
}

// 5. Bloc de Notas Privado (Scratchpad)
function initScratchpad() {
  const drawer = document.getElementById('notes-drawer');
  const toggleBtn = document.getElementById('toggle-notes-btn');
  const closeBtn = document.getElementById('close-notes-btn');
  const textarea = document.getElementById('scratchpad-text');

  textarea.value = localStorage.getItem('aegis_scratchpad') || '';

  toggleBtn.addEventListener('click', () => drawer.classList.toggle('open'));
  closeBtn.addEventListener('click', () => drawer.classList.remove('open'));

  textarea.addEventListener('input', () => {
    localStorage.setItem('aegis_scratchpad', textarea.value);
  });
}

// 6. Modal Inspector de Aegis Shields
function initShieldsModal() {
  const modal = document.getElementById('shields-modal');
  const openBtn = document.getElementById('open-shields-btn');
  const closeBtns = modal.querySelectorAll('.close-modal-btn');
  const navStat = document.getElementById('nav-trackers-stat');

  let blockedTotal = parseInt(localStorage.getItem('aegis_blocked_count') || '284', 10);
  navStat.textContent = blockedTotal.toLocaleString();

  openBtn.addEventListener('click', () => modal.classList.add('active'));
  closeBtns.forEach((b) => b.addEventListener('click', () => modal.classList.remove('active')));
  modal.addEventListener('click', (e) => {
    if (e.target === modal) modal.classList.remove('active');
  });
}

// 7. Centro de Configuración & Funciones (100x Hub)
function initSettingsHub() {
  const modal = document.getElementById('settings-modal');
  const openBtn = document.getElementById('open-settings-btn');
  const closeBtns = modal.querySelectorAll('.close-modal-btn');
  const tabBtns = modal.querySelectorAll('.tab-btn');
  const tabPanes = modal.querySelectorAll('.tab-pane');
  const tabsLayoutSelect = document.getElementById('tabs-layout-select');

  // Pestañas del Modal
  tabBtns.forEach((btn) => {
    btn.addEventListener('click', () => {
      tabBtns.forEach((b) => b.classList.remove('active'));
      tabPanes.forEach((p) => p.classList.remove('active'));
      btn.classList.add('active');
      const targetId = btn.getAttribute('data-tab');
      document.getElementById(targetId).classList.add('active');
    });
  });

  // Selector de Pestañas (Horizontal / Vertical)
  const isVertical = localStorage.getItem('aegis_vertical_tabs') === 'true';
  tabsLayoutSelect.value = isVertical ? 'vertical' : 'horizontal';

  tabsLayoutSelect.addEventListener('change', (e) => {
    const val = e.target.value === 'vertical';
    localStorage.setItem('aegis_vertical_tabs', val);
    if (window.chrome && window.chrome.aegisPrefs) {
      window.chrome.aegisPrefs.setBoolean('aegis.tabs.vertical_enabled', val);
    }
  });

  openBtn.addEventListener('click', () => modal.classList.add('active'));
  closeBtns.forEach((b) => b.addEventListener('click', () => modal.classList.remove('active')));
  modal.addEventListener('click', (e) => {
    if (e.target === modal) modal.classList.remove('active');
  });
}

// 8. Generador de Contraseñas de Alta Entropía
function initPasswordGenerator() {
  const output = document.getElementById('generated-password-output');
  const copyBtn = document.getElementById('copy-pass-btn');
  const regenBtn = document.getElementById('regen-pass-btn');
  const slider = document.getElementById('pass-length-slider');
  const lengthVal = document.getElementById('pass-length-val');
  const symbolsCheck = document.getElementById('pass-symbols-check');

  function generate() {
    const len = parseInt(slider.value, 10);
    lengthVal.textContent = len;
    let chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
    if (symbolsCheck.checked) chars += '!@#$%^&*()_+-=[]{}|;:,.<>?';

    const arr = new Uint32Array(len);
    window.crypto.getRandomValues(arr);
    let pass = '';
    for (let i = 0; i < len; i++) {
      pass += chars[arr[i] % chars.length];
    }
    output.value = pass;
  }

  generate();

  slider.addEventListener('input', generate);
  symbolsCheck.addEventListener('change', generate);
  regenBtn.addEventListener('click', generate);

  copyBtn.addEventListener('click', () => {
    navigator.clipboard.writeText(output.value);
    const prev = copyBtn.textContent;
    copyBtn.textContent = '¡Copiada!';
    setTimeout(() => { copyBtn.textContent = prev; }, 1500);
  });
}

// 9. Gestor de Historial Local
function initHistoryView() {
  const list = document.getElementById('history-list');
  const searchInput = document.getElementById('history-search-input');
  const clearBtn = document.getElementById('clear-history-btn');

  let historyItems = JSON.parse(localStorage.getItem('aegis_history') || 'null') || DEFAULT_HISTORY;

  render(historyItems);

  searchInput.addEventListener('input', () => {
    const q = searchInput.value.toLowerCase();
    const filtered = historyItems.filter(h => h.title.toLowerCase().includes(q) || h.url.toLowerCase().includes(q));
    render(filtered);
  });

  clearBtn.addEventListener('click', () => {
    if (confirm('¿Vaciar todo el historial local?')) {
      historyItems = [];
      localStorage.setItem('aegis_history', JSON.stringify([]));
      render([]);
    }
  });

  function render(items) {
    list.innerHTML = '';
    if (items.length === 0) {
      list.innerHTML = '<div style="color: var(--text-muted); font-size: 0.85rem; padding: 1rem 0;">Historial vacío.</div>';
      return;
    }
    items.forEach((item) => {
      const row = document.createElement('div');
      row.style.cssText = 'display: flex; justify-content: space-between; padding: 0.5rem 0.75rem; background: rgba(0,0,0,0.2); border-radius: var(--radius-sm); font-size: 0.85rem;';
      row.innerHTML = `
        <a href="${item.url}" style="color: var(--text-main); text-decoration: none; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 80%;">${item.title}</a>
        <span style="color: var(--text-muted); font-size: 0.75rem;">${item.time}</span>
      `;
      list.appendChild(row);
    });
  }
}

// 10. Gestor de Temas
function initThemeManager() {
  const dropdown = document.getElementById('theme-selector-dropdown');
  const modalSelect = document.getElementById('theme-modal-select');

  let savedTheme = localStorage.getItem('aegis_theme') || 'cyber';
  applyTheme(savedTheme);

  dropdown.addEventListener('change', (e) => setTheme(e.target.value));
  modalSelect.addEventListener('change', (e) => setTheme(e.target.value));

  function setTheme(t) {
    savedTheme = t;
    localStorage.setItem('aegis_theme', t);
    applyTheme(t);
  }

  function applyTheme(t) {
    document.documentElement.className = `theme-${t}`;
    dropdown.value = t;
    modalSelect.value = t;
  }
}
