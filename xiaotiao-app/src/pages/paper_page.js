// Paper Library Page — /papers
const RAW_API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:3000';
const API_BASE = RAW_API_BASE.replace(/\/api\/v1\/?$/, '');

export function renderPaperPage() {
  return `
    <div class="papers-shell">
      <div class="page-header__badge" style="margin-bottom:12px;display:inline-flex;align-items:center;gap:8px;padding:6px 12px;background:var(--glass-bg);border-radius:20px;font-size:0.85rem;color:var(--text-secondary);">
        <span class="nav-dot" style="background:var(--research);width:8px;height:8px;border-radius:50%;display:inline-block;"></span>
        模块 · 论文库
      </div>
      <h1 style="color:var(--text-primary);font-size:2rem;font-weight:700;margin-bottom:8px;">论文库</h1>
      <p style="color:var(--text-secondary);margin-bottom:24px;">批量导入学术论文，AI 智能解读，管理你的研究文献库。</p>

      <!-- Import Section -->
      <div class="papers-import-grid">
        <div class="glass-panel papers-import-box">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
            <div style="color:var(--text-primary);font-weight:600;">批量导入链接</div>
            <span style="color:var(--text-muted);font-size:0.8rem;">每行一个 URL</span>
          </div>
          <textarea id="paper-url-input" class="input-field textarea" rows="4"
            placeholder="粘贴 ArXiv / Semantic Scholar 论文链接..."
            style="width:100%;resize:none;font-size:0.95rem;"></textarea>
          <div style="display:flex;gap:8px;margin-top:12px;justify-content:flex-end;">
            <button class="btn btn--ghost" id="btn-clear-urls" style="font-size:0.85rem;padding:8px 14px;">清空</button>
            <button class="btn btn--primary" id="btn-import-urls" style="font-size:0.9rem;padding:8px 18px;">批量导入</button>
          </div>
        </div>
        <div class="glass-panel papers-dropzone" id="pdf-dropzone">
          <div class="papers-dropzone__icon">📎</div>
          <div style="color:var(--text-primary);font-weight:600;">拖拽 PDF 到此处</div>
          <div style="color:var(--text-muted);font-size:0.85rem;">支持多文件，单文件 ≤ 50MB</div>
          <button class="btn btn--secondary" id="btn-upload-pdf" style="margin-top:8px;padding:8px 16px;">选择文件</button>
          <input type="file" id="pdf-file-input" accept=".pdf" multiple style="display:none;">
        </div>
      </div>

      <div class="papers-main">
        <!-- Left: Collections -->
        <aside class="glass-panel papers-sidebar">
          <div class="papers-sidebar__section">
            <div class="papers-sidebar__title">筛选</div>
            <button class="papers-nav-item active" data-tab="all">全部论文</button>
            <button class="papers-nav-item" data-tab="favorites">收藏</button>
          </div>
          <div class="papers-sidebar__section">
            <div class="papers-sidebar__title">合集</div>
            <div id="collection-tabs" class="papers-collection-list"></div>
            <button class="btn btn--ghost btn--sm" id="btn-new-collection" style="margin-top:10px;">+ 新建合集</button>
          </div>
        </aside>

        <!-- Right: Grid -->
        <section class="papers-content">
          <div class="papers-content__header">
            <span id="paper-count" style="color:var(--text-muted);font-size:0.9rem;"></span>
            <div style="display:flex;gap:8px;">
              <button class="btn btn--secondary" id="btn-paper-prev" style="padding:8px 16px;">上一页</button>
              <button class="btn btn--secondary" id="btn-paper-next" style="padding:8px 16px;">下一页</button>
            </div>
          </div>
          <div id="paper-grid" class="papers-grid">
            <div style="text-align:center;color:var(--text-muted);padding:48px;">论文加载中...</div>
          </div>
        </section>
      </div>
    </div>
  `;
}

let currentPage = 1;
let currentTab = 'all';
let pollTimer = null;

export function initPaperPage() {
  loadPapers();
  loadCollections();

  document.getElementById('btn-import-urls').addEventListener('click', importUrls);
  document.getElementById('btn-clear-urls').addEventListener('click', () => {
    document.getElementById('paper-url-input').value = '';
  });
  document.getElementById('btn-upload-pdf').addEventListener('click', () => {
    document.getElementById('pdf-file-input').click();
  });
  document.getElementById('pdf-file-input').addEventListener('change', (e) => {
    if (e.target.files.length > 0) uploadPdfs(e.target.files);
  });
  const dropzone = document.getElementById('pdf-dropzone');
  if (dropzone) {
    dropzone.addEventListener('click', (e) => {
      if (e.target.closest('#btn-upload-pdf')) return;
      document.getElementById('pdf-file-input').click();
    });
    dropzone.addEventListener('dragover', (e) => {
      e.preventDefault();
      dropzone.classList.add('is-dragover');
    });
    dropzone.addEventListener('dragleave', () => {
      dropzone.classList.remove('is-dragover');
    });
    dropzone.addEventListener('drop', (e) => {
      e.preventDefault();
      dropzone.classList.remove('is-dragover');
      const files = Array.from(e.dataTransfer.files || []).filter(f => f.name.toLowerCase().endsWith('.pdf'));
      if (files.length === 0) {
        window.showToast('请拖入 PDF 文件', 'warning');
        return;
      }
      uploadPdfs(files);
    });
  }
  document.getElementById('btn-new-collection').addEventListener('click', createCollection);
  document.getElementById('btn-paper-prev').addEventListener('click', () => {
    if (currentPage > 1) { currentPage--; loadPapers(); }
  });
  document.getElementById('btn-paper-next').addEventListener('click', () => {
    currentPage++; loadPapers();
  });

  // Nav clicks (filters + collections)
  document.querySelector('.papers-sidebar').addEventListener('click', (e) => {
    const tab = e.target.closest('.papers-nav-item');
    if (!tab) return;
    setActiveTab(tab.dataset.tab);
  });

  // Start polling for processing papers
  pollTimer = setInterval(checkProcessingPapers, 5000);
  window.__paperPollTimer = pollTimer;
}

function setActiveTab(tab, shouldReload = true) {
  currentTab = tab;
  updateActiveNav();
  if (shouldReload) {
    currentPage = 1;
    loadPapers();
  }
}

function updateActiveNav() {
  document.querySelectorAll('.papers-nav-item').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.tab === currentTab);
  });
}

// Cleanup polling on page leave
const origCleanup = window.__paperCleanup;
window.__paperCleanup = () => {
  if (window.__paperPollTimer) {
    clearInterval(window.__paperPollTimer);
    window.__paperPollTimer = null;
  }
  if (origCleanup) origCleanup();
};

async function loadPapers() {
  const grid = document.getElementById('paper-grid');
  let url = `/papers?page=${currentPage}&limit=12`;
  if (currentTab === 'favorites') url += '&favorites_only=true';
  else if (currentTab !== 'all') url += `&collection_id=${currentTab}`;

  try {
    const res = await fetch(`${API_BASE}${url}`);
    const data = await res.json();

    if (!data.items || data.items.length === 0) {
      grid.innerHTML = `<div style="grid-column:1/-1;text-align:center;color:var(--text-muted);padding:48px;">
        ${currentTab === 'all' ? '暂无论文，粘贴链接或上传 PDF 开始吧！' : '该分类暂无论文。'}
      </div>`;
    } else {
      grid.innerHTML = data.items.map(p => renderPaperCard(p)).join('');
    }

    document.getElementById('paper-count').textContent = `共 ${data.total} 篇论文`;
    document.getElementById('btn-paper-prev').disabled = data.page <= 1;
    document.getElementById('btn-paper-next').disabled = data.page >= data.total_pages;
  } catch (e) {
    grid.innerHTML = `<div style="grid-column:1/-1;text-align:center;color:#ef4444;padding:48px;">加载失败: ${e.message}</div>`;
  }
}

function renderPaperCard(p) {
  const statusColors = { pending: '#9e9bb0', processing: '#007aff', ready: '#34c759', failed: '#ef4444' };
  const statusLabels = { pending: '等待中', processing: '处理中', ready: '就绪', failed: '失败' };
  const color = statusColors[p.status] || '#9e9bb0';
  const label = statusLabels[p.status] || p.status;

  const tags = p.tags ? (() => { try { return JSON.parse(p.tags); } catch { return []; } })() : [];

  return `
    <div class="glass-panel" style="padding:24px;border-radius:16px;cursor:pointer;transition:all 0.2s;border:1px solid rgba(255,255,255,0.1);"
         onclick="location.hash='/papers/${p.id}'" data-paper-id="${p.id}" data-status="${p.status}">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:12px;">
        <span style="display:inline-flex;align-items:center;gap:4px;font-size:0.8rem;color:${color};${p.status === 'processing' ? 'animation:pulse 1.5s infinite;' : ''}">
          <span style="width:6px;height:6px;border-radius:50%;background:${color};display:inline-block;"></span>
          ${label}
        </span>
        <div style="display:flex;gap:8px;" onclick="event.stopPropagation()">
          <button onclick="window.__toggleFav('${p.id}')" style="background:none;border:none;cursor:pointer;font-size:1.2rem;"
            title="${p.is_favorite ? '取消收藏' : '收藏'}">${p.is_favorite ? '⭐' : '☆'}</button>
          <button onclick="window.__deletePaper('${p.id}')" style="background:none;border:none;cursor:pointer;color:var(--text-muted);font-size:1rem;"
            title="删除">✕</button>
        </div>
      </div>
      <h3 style="color:var(--text-primary);font-size:1.05rem;font-weight:600;margin-bottom:8px;line-height:1.4;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;">
        ${escapeHtml(p.title)}
      </h3>
      <p style="color:var(--text-muted);font-size:0.85rem;margin-bottom:12px;">
        ${p.source || 'unknown'} · ${new Date(p.created_at).toLocaleDateString('zh-CN')}
      </p>
      ${tags.length > 0 ? `<div style="display:flex;gap:6px;flex-wrap:wrap;">${tags.slice(0, 3).map(t =>
        `<span style="background:rgba(88,86,214,0.1);color:var(--accent);padding:2px 8px;border-radius:10px;font-size:0.75rem;">${t}</span>`
      ).join('')}</div>` : ''}
    </div>
  `;
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str || '';
  return div.innerHTML;
}

async function importUrls() {
  const textarea = document.getElementById('paper-url-input');
  const urls = textarea.value.split('\n').map(u => u.trim()).filter(u => u);
  if (urls.length === 0) return window.showToast('请输入至少一个论文链接', 'warning');

  const btn = document.getElementById('btn-import-urls');
  btn.disabled = true;
  btn.textContent = '导入中...';

  try {
    const res = await fetch(`${API_BASE}/papers/batch-url`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ urls })
    });
    const data = await res.json();
    const dupes = data.papers.filter(p => p.duplicate).length;
    const newCount = data.papers.length - dupes;
    window.showToast(`已导入 ${newCount} 篇论文${dupes > 0 ? `，跳过 ${dupes} 篇重复` : ''}`, 'success');
    textarea.value = '';
    loadPapers();
  } catch (e) {
    window.showToast('导入失败: ' + e.message, 'error');
  } finally {
    btn.disabled = false;
    btn.textContent = '导入论文';
  }
}

async function uploadPdfs(files) {
  for (const file of files) {
    const formData = new FormData();
    formData.append('file', file);
    try {
      await fetch(`${API_BASE}/papers/upload-pdf`, { method: 'POST', body: formData });
      window.showToast(`已上传: ${file.name}`, 'success');
    } catch (e) {
      window.showToast(`上传失败: ${file.name}`, 'error');
    }
  }
  loadPapers();
}

async function loadCollections() {
  try {
    const res = await fetch(`${API_BASE}/collections`);
    const cols = await res.json();
    const container = document.getElementById('collection-tabs');
    if (container) {
      container.innerHTML = cols.map(c =>
        `<button class="papers-nav-item" data-tab="${c.id}">${escapeHtml(c.name)}</button>`
      ).join('');
      updateActiveNav();
    }
  } catch (e) {
    console.error('Failed to load collections:', e);
  }
}

async function createCollection() {
  const name = prompt('请输入合集名称：');
  if (!name) return;
  try {
    await fetch(`${API_BASE}/collections`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name })
    });
    window.showToast('合集已创建', 'success');
    loadCollections();
  } catch (e) {
    window.showToast('创建失败', 'error');
  }
}

async function checkProcessingPapers() {
  const cards = document.querySelectorAll('[data-status="pending"],[data-status="processing"]');
  if (cards.length === 0) return;

  for (const card of cards) {
    const id = card.dataset.paperId;
    try {
      const res = await fetch(`${API_BASE}/papers/${id}`);
      const paper = await res.json();
      if (paper.status !== card.dataset.status) {
        loadPapers(); // Reload all if any status changed
        return;
      }
    } catch (e) { /* ignore */ }
  }
}

// Global handlers for inline onclick
window.__toggleFav = async (id) => {
  try {
    await fetch(`${API_BASE}/papers/${id}/toggle-favorite`, { method: 'POST' });
    loadPapers();
  } catch (e) {
    window.showToast('操作失败', 'error');
  }
};

window.__deletePaper = async (id) => {
  const ok = await window.showGlassConfirm('删除论文', '确定要删除这篇论文吗？此操作不可撤销。', { danger: true, confirmText: '删除' });
  if (ok) {
    try {
      await fetch(`${API_BASE}/papers/${id}`, { method: 'DELETE' });
      window.showToast('论文已删除', 'success');
      loadPapers();
    } catch (e) {
      window.showToast('删除失败', 'error');
    }
  }
};
