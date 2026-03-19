// V2.0 Sidebar Panel Controller — manages collapsible sidebar with tabs
import { fetchAPIGet, fetchAPI } from '../api.js';

let sidebarOpen = false;
const STORAGE_KEY = 'zaiyi_sidebar_state';

export function initSidebar() {
  const panel = document.getElementById('sidebar-panel');
  const toggleBtn = document.getElementById('btn-sidebar-toggle');
  const closeBtn = document.getElementById('btn-sidebar-close');
  const content = document.getElementById('sidebar-content');

  if (!panel || !toggleBtn) return;

  // Restore state
  sidebarOpen = localStorage.getItem(STORAGE_KEY) === 'open';
  if (sidebarOpen) openSidebar();

  toggleBtn.addEventListener('click', () => {
    sidebarOpen ? closeSidebar() : openSidebar();
  });

  if (closeBtn) {
    closeBtn.addEventListener('click', closeSidebar);
  }

  // Tab switching
  panel.querySelectorAll('.sidebar-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      panel.querySelectorAll('.sidebar-tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      loadTabContent(tab.dataset.tab);
    });
  });

  // Load default tab
  loadTabContent('vocab');
}

function openSidebar() {
  const panel = document.getElementById('sidebar-panel');
  if (!panel) return;
  panel.classList.add('is-open');
  panel.setAttribute('aria-hidden', 'false');
  document.body.classList.add('sidebar-open');
  sidebarOpen = true;
  localStorage.setItem(STORAGE_KEY, 'open');
}

function closeSidebar() {
  const panel = document.getElementById('sidebar-panel');
  if (!panel) return;
  panel.classList.remove('is-open');
  panel.setAttribute('aria-hidden', 'true');
  document.body.classList.remove('sidebar-open');
  sidebarOpen = false;
  localStorage.setItem(STORAGE_KEY, 'closed');
}

function loadTabContent(tab) {
  const content = document.getElementById('sidebar-content');
  if (!content) return;

  switch (tab) {
    case 'vocab':
      renderVocabTab(content);
      break;
    case 'translate':
      renderTranslateTab(content);
      break;
    case 'notes':
      renderNotesTab(content);
      break;
  }
}

async function renderVocabTab(container) {
  container.innerHTML = `
    <div class="sidebar-section">
      <div class="sidebar-section__header">
        <span>📖 我的生词</span>
        <a href="#/vocab" class="sidebar-section__link">查看全部 →</a>
      </div>
      <div id="sidebar-vocab-list" class="sidebar-vocab-list">
        <div class="sidebar-loading">加载中...</div>
      </div>
    </div>
  `;

  try {
    const data = await fetchAPIGet('/vocab?limit=20&sort=created_at&order=desc');
    const list = document.getElementById('sidebar-vocab-list');
    if (!list) return;

    const items = data.items || data || [];
    if (!items.length) {
      list.innerHTML = `
        <div class="sidebar-empty">
          <div class="sidebar-empty__icon">📖</div>
          <div class="sidebar-empty__text">还没有生词<br>阅读文章时划词添加</div>
        </div>
      `;
      return;
    }

    list.innerHTML = items.slice(0, 15).map(w => `
      <div class="sidebar-vocab-item">
        <div class="sidebar-vocab-item__word">${w.word || ''}</div>
        <div class="sidebar-vocab-item__def">${w.definition_zh || ''}</div>
      </div>
    `).join('');
  } catch (_e) {
    const list = document.getElementById('sidebar-vocab-list');
    if (list) list.innerHTML = '<div class="sidebar-empty"><div class="sidebar-empty__text">加载失败</div></div>';
  }
}

function renderTranslateTab(container) {
  container.innerHTML = `
    <div class="sidebar-section">
      <div class="sidebar-section__header">🔤 快速翻译</div>
      <textarea class="sidebar-translate-input" id="sidebar-translate-input"
        placeholder="选中文章中的文本，或在此输入需要翻译的内容..."
        rows="4"></textarea>
      <button class="btn btn--primary btn--sm btn--full" id="sidebar-translate-btn"
        style="margin-top: 8px;">翻译</button>
      <div class="sidebar-translate-result" id="sidebar-translate-result"></div>
    </div>
  `;

  const btn = document.getElementById('sidebar-translate-btn');
  const input = document.getElementById('sidebar-translate-input');
  const result = document.getElementById('sidebar-translate-result');

  btn.addEventListener('click', async () => {
    const text = input.value.trim();
    if (!text) return;
    btn.disabled = true;
    btn.textContent = '翻译中...';
    result.innerHTML = '<div class="sidebar-loading">AI 翻译中...</div>';
    try {
      const data = await fetchAPI('/translation/run', {
        source_text: text,
        direction: 'en_to_zh',
        style: ['literal'],
      });
      const translations = data.translations || data.result || [];
      if (Array.isArray(translations) && translations.length) {
        result.innerHTML = translations.map(t => `
          <div class="sidebar-translate-item">
            <div class="sidebar-translate-item__style">${t.style_label || t.style || ''}</div>
            <div class="sidebar-translate-item__text">${t.text || ''}</div>
          </div>
        `).join('');
      } else if (typeof data === 'string') {
        result.innerHTML = `<div class="sidebar-translate-item"><div class="sidebar-translate-item__text">${data}</div></div>`;
      } else {
        result.innerHTML = `<div class="sidebar-translate-item"><div class="sidebar-translate-item__text">${JSON.stringify(data)}</div></div>`;
      }
    } catch (e) {
      result.innerHTML = `<div class="sidebar-empty"><div class="sidebar-empty__text">翻译失败: ${e.message}</div></div>`;
    }
    btn.disabled = false;
    btn.textContent = '翻译';
  });
}

function renderNotesTab(container) {
  container.innerHTML = `
    <div class="sidebar-section">
      <div class="sidebar-section__header">📝 阅读笔记</div>
      <div class="sidebar-empty">
        <div class="sidebar-empty__icon">📝</div>
        <div class="sidebar-empty__text">阅读文章时可以<br>随时添加笔记<br><br><em style="opacity:0.6;">此功能将在后续版本完善</em></div>
      </div>
    </div>
  `;
}

// Public API to programmatically trigger sidebar with content
export function openSidebarWithTranslation(text) {
  openSidebar();
  // Switch to translate tab
  const panel = document.getElementById('sidebar-panel');
  if (panel) {
    panel.querySelectorAll('.sidebar-tab').forEach(t => t.classList.remove('active'));
    const translateTab = panel.querySelector('[data-tab="translate"]');
    if (translateTab) translateTab.classList.add('active');
  }
  const content = document.getElementById('sidebar-content');
  if (content) {
    renderTranslateTab(content);
    const input = document.getElementById('sidebar-translate-input');
    if (input) {
      input.value = text;
      // Auto-trigger translate
      const btn = document.getElementById('sidebar-translate-btn');
      if (btn) btn.click();
    }
  }
}

export function openSidebarVocab() {
  openSidebar();
  const panel = document.getElementById('sidebar-panel');
  if (panel) {
    panel.querySelectorAll('.sidebar-tab').forEach(t => t.classList.remove('active'));
    const vocabTab = panel.querySelector('[data-tab="vocab"]');
    if (vocabTab) vocabTab.classList.add('active');
  }
  const content = document.getElementById('sidebar-content');
  if (content) renderVocabTab(content);
}
