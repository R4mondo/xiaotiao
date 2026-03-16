// Paper Library Page — /papers
const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:3000/api/v1';

export function renderPaperPage() {
  return `
    <div class="page-container glass-panel" style="max-width:1200px;margin:40px auto;padding:40px;border-radius:24px;">
      <div class="page-header__badge" style="margin-bottom:12px;display:inline-flex;align-items:center;gap:8px;padding:6px 12px;background:var(--glass-bg);border-radius:20px;font-size:0.85rem;color:var(--text-secondary);">
        <span class="nav-dot" style="background:var(--research);width:8px;height:8px;border-radius:50%;display:inline-block;"></span>
        模块 · 论文库
      </div>
      <h1 style="color:var(--text-primary);font-size:2rem;font-weight:700;margin-bottom:8px;">论文库</h1>
      <p style="color:var(--text-secondary);margin-bottom:32px;">批量导入学术论文，AI 智能解读，管理你的研究文献库。</p>

      <!-- Import Section -->
      <div style="display:grid;grid-template-columns:1fr auto;gap:16px;margin-bottom:32px;">
        <div style="position:relative;">
          <textarea id="paper-url-input" class="input-field textarea" rows="3"
            placeholder="粘贴 ArXiv / Semantic Scholar 论文链接，每行一个..."
            style="width:100%;resize:none;font-size:0.95rem;"></textarea>
        </div>
        <div style="display:flex;flex-direction:column;gap:12px;">
          <button class="btn btn--primary" id="btn-import-urls" style="height:fit-content;">
            导入论文
          </button>
          <button class="btn btn--secondary" id="btn-upload-pdf" style="height:fit-content;">
            上传 PDF
          </button>
          <input type="file" id="pdf-file-input" accept=".pdf" multiple style="display:none;">
        </div>
      </div>

      <!-- Tabs -->
      <div style="display:flex;gap:8px;margin-bottom:24px;flex-wrap:wrap;" id="paper-tabs">
        <button class="btn btn--secondary paper-tab active" data-tab="all" style="font-size:0.9rem;padding:8px 16px;">全部论文</button>
        <button class="btn btn--secondary paper-tab" data-tab="favorites" style="font-size:0.9rem;padding:8px 16px;">收藏</button>
        <div id="collection-tabs"></div>
        <button class="btn btn--ghost" id="btn-new-collection" style="font-size:0.85rem;padding:6px 12px;">+ 新建合集</button>
      </div>

      <!-- Paper Grid -->
      <div id="paper-grid" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:20px;">
        <div style="text-align:center;color:var(--text-muted);padding:48px;">论文加载中...</div>
      </div>

      <!-- Pagination -->
      <div style="display:flex;justify-content:space-between;align-items:center;margin-top:24px;">
        <span id="paper-count" style="color:var(--text-muted);font-size:0.9rem;"></span>
        <div style="display:flex;gap:8px;">
          <button class="btn btn--secondary" id="btn-paper-prev" style="padding:8px 16px;">上一页</button>
          <button class="btn btn--secondary" id="btn-paper-next" style="padding:8px 16px;">下一页</button>
        </div>
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
  document.getElementById('btn-upload-pdf').addEventListener('click', () => {
    document.getElementById('pdf-file-input').click();
  });
  document.getElementById('pdf-file-input').addEventListener('change', (e) => {
    if (e.target.files.length > 0) uploadPdfs(e.target.files);
  });
  document.getElementById('btn-new-collection').addEventListener('click', createCollection);
  document.getElementById('btn-paper-prev').addEventListener('click', () => {
    if (currentPage > 1) { currentPage--; loadPapers(); }
  });
  document.getElementById('btn-paper-next').addEventListener('click', () => {
    currentPage++; loadPapers();
  });

  // Tab clicks
  document.getElementById('paper-tabs').addEventListener('click', (e) => {
    const tab = e.target.closest('.paper-tab');
    if (!tab) return;
    document.querySelectorAll('.paper-tab').forEach(t => t.classList.remove('active'));
    tab.classList.add('active');
    currentTab = tab.dataset.tab;
    currentPage = 1;
    loadPapers();
  });

  // Start polling for processing papers
  pollTimer = setInterval(checkProcessingPapers, 5000);
  window.__paperPollTimer = pollTimer;
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
        `<button class="btn btn--secondary paper-tab" data-tab="${c.id}" style="font-size:0.9rem;padding:8px 16px;">${escapeHtml(c.name)}</button>`
      ).join('');
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
