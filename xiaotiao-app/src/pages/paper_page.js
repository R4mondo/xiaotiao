import { authFetch } from '../utils/http.js';

// Paper Library Page — /papers
const RAW_API_BASE = import.meta.env.VITE_API_BASE_URL || '';
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

      <!-- Reading Stats Dashboard -->
      <div class="papers-stats-row" id="papers-stats-row">
        <div class="glass-panel papers-stat-card" id="stat-reading-count">
          <div class="papers-stat-card__label">近期阅读量</div>
          <div class="papers-stat-card__value" id="stat-today-pages">—</div>
          <div class="papers-stat-card__sub">今日已读页数</div>
          <button class="papers-stat-card__expand" id="btn-expand-stats" title="查看趋势">📊</button>
        </div>
        <div class="glass-panel papers-stat-card">
          <div class="papers-stat-card__label">文献阅读率</div>
          <div class="papers-stat-card__value" id="stat-completion-rate">—</div>
          <div class="papers-stat-card__sub" id="stat-completion-detail">已读 0 / 共 0 篇</div>
        </div>
        <div class="glass-panel papers-stat-card">
          <div class="papers-stat-card__label">阅读中</div>
          <div class="papers-stat-card__value" id="stat-reading-papers">—</div>
          <div class="papers-stat-card__sub">篇论文</div>
        </div>
      </div>

      <!-- Stats Chart (collapsed by default) -->
      <div class="glass-panel papers-chart-panel" id="stats-chart-panel" style="display:none;">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
          <div style="color:var(--text-primary);font-weight:600;font-size:0.95rem;">每日阅读量趋势</div>
          <div style="display:flex;gap:8px;">
            <button class="btn btn--ghost btn--sm chart-range-btn active" data-range="30">近30天</button>
            <button class="btn btn--ghost btn--sm chart-range-btn" data-range="90">近90天</button>
            <button class="btn btn--ghost btn--sm" id="btn-close-chart">✕</button>
          </div>
        </div>
        <canvas id="reading-chart" height="200" style="display:block;"></canvas>
      </div>

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
          <div style="color:var(--text-primary);font-weight:600;">拖拽 PDF / Word 到此处</div>
          <div style="color:var(--text-muted);font-size:0.85rem;">支持多文件（PDF / DOCX），单文件 ≤ 50MB</div>
          <button class="btn btn--secondary" id="btn-upload-pdf" style="margin-top:8px;padding:8px 16px;">选择文件</button>
          <input type="file" id="pdf-file-input" accept=".pdf,.docx" multiple style="display:none;">
        </div>
      </div>

      <div class="papers-main">
        <!-- Left: Folders -->
        <aside class="glass-panel papers-sidebar">
          <div class="papers-sidebar__section">
            <div class="papers-sidebar__title">筛选</div>
            <button class="papers-nav-item active" data-tab="all">📚 全部论文</button>
            <button class="papers-nav-item" data-tab="favorites">⭐ 收藏</button>
            <button class="papers-nav-item" data-tab="unread">🔵 未读</button>
            <button class="papers-nav-item" data-tab="reading">📖 阅读中</button>
            <button class="papers-nav-item" data-tab="read">✅ 已读</button>
          </div>
          <div class="papers-sidebar__section">
            <div class="papers-sidebar__title">文件夹</div>
            <div id="folder-tree" class="papers-folder-tree"></div>
            <button class="btn btn--ghost btn--sm" id="btn-new-folder" style="margin-top:10px;">+ 新建文件夹</button>
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
let allFolders = [];
let chartInstance = null;
let statsData = null;

export function initPaperPage() {
  loadPapers();
  loadFolders();
  loadStats();

  document.getElementById('btn-import-urls').addEventListener('click', importUrls);
  document.getElementById('btn-clear-urls').addEventListener('click', () => {
    document.getElementById('paper-url-input').value = '';
  });
  document.getElementById('btn-upload-pdf').addEventListener('click', () => {
    document.getElementById('pdf-file-input').click();
  });
  document.getElementById('pdf-file-input').addEventListener('change', (e) => {
    if (e.target.files.length > 0) uploadFiles(e.target.files);
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
      const files = Array.from(e.dataTransfer.files || []).filter(f => {
        const name = f.name.toLowerCase();
        return name.endsWith('.pdf') || name.endsWith('.docx');
      });
      if (files.length === 0) {
        window.showToast('请拖入 PDF 或 Word 文档', 'warning');
        return;
      }
      uploadFiles(files);
    });
  }

  document.getElementById('btn-new-folder').addEventListener('click', createFolder);
  document.getElementById('btn-paper-prev').addEventListener('click', () => {
    if (currentPage > 1) { currentPage--; loadPapers(); }
  });
  document.getElementById('btn-paper-next').addEventListener('click', () => {
    currentPage++; loadPapers();
  });

  // Nav clicks (filters)
  document.querySelector('.papers-sidebar').addEventListener('click', (e) => {
    const tab = e.target.closest('.papers-nav-item');
    if (!tab) return;
    setActiveTab(tab.dataset.tab);
  });

  // Stats expand/close
  document.getElementById('btn-expand-stats').addEventListener('click', toggleChart);
  document.getElementById('btn-close-chart').addEventListener('click', () => {
    document.getElementById('stats-chart-panel').style.display = 'none';
  });
  document.querySelectorAll('.chart-range-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.chart-range-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      renderChart(parseInt(btn.dataset.range));
    });
  });

  // Polling
  pollTimer = setInterval(checkProcessingPapers, 5000);
  window.__paperPollTimer = pollTimer;
}

function setActiveTab(tab) {
  currentTab = tab;
  updateActiveNav();
  currentPage = 1;
  loadPapers();
}

function updateActiveNav() {
  document.querySelectorAll('.papers-nav-item').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.tab === currentTab);
  });
  document.querySelectorAll('.papers-folder-item').forEach(el => {
    el.classList.toggle('active', el.dataset.tab === currentTab);
  });
}

// Cleanup
const origCleanup = window.__paperCleanup;
window.__paperCleanup = () => {
  if (window.__paperPollTimer) {
    clearInterval(window.__paperPollTimer);
    window.__paperPollTimer = null;
  }
  if (origCleanup) origCleanup();
};

// ── Stats ──────────────────────────────────────

async function loadStats() {
  try {
    const res = await authFetch(`${API_BASE}/papers/stats`);
    statsData = await res.json();
    document.getElementById('stat-today-pages').textContent = statsData.today_pages;
    document.getElementById('stat-completion-rate').textContent = `${statsData.completion_rate}%`;
    document.getElementById('stat-completion-detail').textContent =
      `已读 ${statsData.read_papers} / 共 ${statsData.total_papers} 篇`;
    document.getElementById('stat-reading-papers').textContent = statsData.reading_papers;
  } catch (e) {
    console.error('Failed to load stats:', e);
  }
}

function toggleChart() {
  const panel = document.getElementById('stats-chart-panel');
  if (panel.style.display === 'none') {
    panel.style.display = 'block';
    renderChart(30);
  } else {
    panel.style.display = 'none';
  }
}

function renderChart(days) {
  if (!statsData?.daily_history) return;
  const canvas = document.getElementById('reading-chart');
  const ctx = canvas.getContext('2d');

  // Prepare data for the last N days
  const today = new Date();
  const labels = [];
  const dataMap = {};
  statsData.daily_history.forEach(d => { dataMap[d.date] = d.pages; });

  const values = [];
  for (let i = days - 1; i >= 0; i--) {
    const d = new Date(today);
    d.setDate(d.getDate() - i);
    const key = d.toISOString().split('T')[0];
    labels.push(`${d.getMonth() + 1}/${d.getDate()}`);
    values.push(dataMap[key] || 0);
  }

  // Reset canvas to prevent it from pushing parent wider
  canvas.width = 0;
  canvas.height = 0;
  canvas.style.width = '0px';

  // Now measure parent correctly
  const panelEl = document.getElementById('stats-chart-panel');
  const panelStyle = getComputedStyle(panelEl);
  const padLeft = parseFloat(panelStyle.paddingLeft) || 0;
  const padRight = parseFloat(panelStyle.paddingRight) || 0;
  const availableWidth = panelEl.clientWidth - padLeft - padRight;

  const w = Math.floor(availableWidth);
  const h = 200;
  canvas.width = w;
  canvas.height = h;
  canvas.style.width = w + 'px';
  canvas.style.height = h + 'px';
  const pad = { top: 20, right: 20, bottom: 30, left: 40 };
  const cw = w - pad.left - pad.right;
  const ch = h - pad.top - pad.bottom;
  const maxVal = Math.max(...values, 1);

  ctx.clearRect(0, 0, w, h);

  // Grid lines
  ctx.strokeStyle = 'rgba(255,255,255,0.08)';
  ctx.lineWidth = 1;
  for (let i = 0; i <= 4; i++) {
    const y = pad.top + (ch / 4) * i;
    ctx.beginPath();
    ctx.moveTo(pad.left, y);
    ctx.lineTo(w - pad.right, y);
    ctx.stroke();
  }

  // Y-axis labels
  ctx.fillStyle = 'rgba(255,255,255,0.4)';
  ctx.font = '10px system-ui';
  ctx.textAlign = 'right';
  for (let i = 0; i <= 4; i++) {
    const y = pad.top + (ch / 4) * i;
    const val = Math.round(maxVal * (1 - i / 4));
    ctx.fillText(val, pad.left - 6, y + 3);
  }

  // X-axis labels (show every Nth)
  ctx.textAlign = 'center';
  const step = Math.max(1, Math.floor(labels.length / 8));
  for (let i = 0; i < labels.length; i += step) {
    const x = pad.left + (cw / (labels.length - 1)) * i;
    ctx.fillText(labels[i], x, h - 8);
  }

  // Line + fill
  ctx.beginPath();
  for (let i = 0; i < values.length; i++) {
    const x = pad.left + (cw / (values.length - 1)) * i;
    const y = pad.top + ch - (values[i] / maxVal) * ch;
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  }
  ctx.strokeStyle = '#5856d6';
  ctx.lineWidth = 2;
  ctx.stroke();

  // Fill area
  const lastX = pad.left + cw;
  const baseY = pad.top + ch;
  ctx.lineTo(lastX, baseY);
  ctx.lineTo(pad.left, baseY);
  ctx.closePath();
  const grad = ctx.createLinearGradient(0, pad.top, 0, baseY);
  grad.addColorStop(0, 'rgba(88, 86, 214, 0.3)');
  grad.addColorStop(1, 'rgba(88, 86, 214, 0)');
  ctx.fillStyle = grad;
  ctx.fill();

  // Dots
  ctx.fillStyle = '#5856d6';
  for (let i = 0; i < values.length; i++) {
    if (values[i] > 0) {
      const x = pad.left + (cw / (values.length - 1)) * i;
      const y = pad.top + ch - (values[i] / maxVal) * ch;
      ctx.beginPath();
      ctx.arc(x, y, 3, 0, Math.PI * 2);
      ctx.fill();
    }
  }
}

// ── Folders ────────────────────────────────────

async function loadFolders() {
  try {
    const res = await authFetch(`${API_BASE}/papers/folders`);
    allFolders = await res.json();
    renderFolderTree();
  } catch (e) {
    console.error('Failed to load folders:', e);
  }
}

function buildTree(folders, parentId = null) {
  return folders
    .filter(f => f.parent_id === parentId)
    .map(f => ({
      ...f,
      children: buildTree(folders, f.id)
    }));
}

function renderFolderTree() {
  const container = document.getElementById('folder-tree');
  if (!container) return;
  const tree = buildTree(allFolders);
  container.innerHTML = tree.length === 0
    ? '<div style="color:var(--text-muted);font-size:0.8rem;padding:4px 0;">暂无文件夹</div>'
    : renderFolderNodes(tree, 0);
  updateActiveNav();

  // Add drag-drop listeners to folder items
  container.querySelectorAll('.papers-folder-item').forEach(el => {
    el.addEventListener('dragover', (e) => {
      e.preventDefault();
      el.classList.add('is-drop-target');
    });
    el.addEventListener('dragleave', () => {
      el.classList.remove('is-drop-target');
    });
    el.addEventListener('drop', async (e) => {
      e.preventDefault();
      el.classList.remove('is-drop-target');
      const paperId = e.dataTransfer.getData('text/paper-id');
      if (paperId) {
        await movePaperToFolder(paperId, el.dataset.folderId);
      }
    });
    // Double-click to rename
    el.addEventListener('dblclick', () => renameFolder(el.dataset.folderId, el.dataset.folderName));
  });

  // Expand/collapse toggles
  container.querySelectorAll('.folder-toggle').forEach(tog => {
    tog.addEventListener('click', (e) => {
      e.stopPropagation();
      const subList = tog.closest('.papers-folder-node').querySelector('.papers-folder-sub');
      if (subList) subList.classList.toggle('collapsed');
      tog.textContent = subList?.classList.contains('collapsed') ? '▶' : '▼';
    });
  });
}

function renderFolderNodes(nodes, depth) {
  return nodes.map(n => {
    const hasChildren = n.children && n.children.length > 0;
    const icon = n.source === 'tracker' ? '🔍' : '📁';
    return `
      <div class="papers-folder-node">
        <div class="papers-folder-item papers-nav-item" data-tab="folder:${n.id}" data-folder-id="${n.id}" data-folder-name="${escapeHtml(n.name)}"
             style="padding-left:${8 + depth * 16}px;">
          ${hasChildren ? '<span class="folder-toggle">▼</span>' : '<span style="width:14px;display:inline-block;"></span>'}
          ${icon} ${escapeHtml(n.name)}
          <span class="papers-folder-count">${n.paper_count || 0}</span>
        </div>
        ${hasChildren ? `<div class="papers-folder-sub">${renderFolderNodes(n.children, depth + 1)}</div>` : ''}
      </div>
    `;
  }).join('');
}

async function createFolder() {
  const name = await showInputDialog('新建文件夹', '请输入文件夹名称');
  if (!name) return;
  try {
    await authFetch(`${API_BASE}/papers/folders`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name })
    });
    window.showToast('文件夹已创建', 'success');
    loadFolders();
  } catch (e) {
    window.showToast('创建失败', 'error');
  }
}

async function renameFolder(folderId, currentName) {
  const name = await showInputDialog('重命名文件夹', '输入新名称', currentName);
  if (!name || name === currentName) return;
  try {
    await authFetch(`${API_BASE}/papers/folders/${folderId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name })
    });
    loadFolders();
  } catch (e) {
    window.showToast('重命名失败', 'error');
  }
}

/** Custom input dialog (replaces browser prompt) */
function showInputDialog(title, placeholder, defaultValue = '') {
  return new Promise((resolve) => {
    const overlay = document.createElement('div');
    overlay.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,0.5);z-index:10000;display:flex;align-items:center;justify-content:center;';
    overlay.innerHTML = `
      <div style="background:var(--glass-bg-solid,#1a1a2e);border:1px solid rgba(255,255,255,0.12);border-radius:16px;padding:24px;min-width:320px;box-shadow:0 24px 48px rgba(0,0,0,0.3);">
        <div style="color:var(--text-primary,#fff);font-weight:600;margin-bottom:12px;font-size:1rem;">${title}</div>
        <input type="text" class="input-field" placeholder="${placeholder}" value="${escapeHtml(defaultValue)}"
          style="width:100%;padding:10px 14px;border-radius:10px;border:1px solid rgba(255,255,255,0.15);background:rgba(255,255,255,0.06);color:var(--text-primary,#fff);font-size:0.95rem;outline:none;box-sizing:border-box;" />
        <div style="display:flex;gap:8px;justify-content:flex-end;margin-top:14px;">
          <button class="btn btn--ghost" style="padding:8px 16px;" data-action="cancel">取消</button>
          <button class="btn btn--primary" style="padding:8px 16px;" data-action="confirm">确定</button>
        </div>
      </div>
    `;
    document.body.appendChild(overlay);
    const input = overlay.querySelector('input');
    input.focus();
    input.select();

    const close = (value) => { overlay.remove(); resolve(value); };
    overlay.querySelector('[data-action="cancel"]').addEventListener('click', () => close(null));
    overlay.querySelector('[data-action="confirm"]').addEventListener('click', () => close(input.value.trim() || null));
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') close(input.value.trim() || null);
      if (e.key === 'Escape') close(null);
    });
    overlay.addEventListener('click', (e) => { if (e.target === overlay) close(null); });
  });
}

async function movePaperToFolder(paperId, folderId) {
  try {
    await authFetch(`${API_BASE}/papers/${paperId}/folder`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ folder_id: folderId })
    });
    window.showToast('已移动到文件夹', 'success');
    loadPapers();
    loadFolders();
  } catch (e) {
    window.showToast('移动失败', 'error');
  }
}

// ── Papers ─────────────────────────────────────

async function loadPapers() {
  const grid = document.getElementById('paper-grid');
  let url = `/papers?page=${currentPage}&limit=12`;

  if (currentTab === 'favorites') url += '&favorites_only=true';
  else if (currentTab === 'unread') url += '&root_only=false'; // we'll filter client-side for status
  else if (currentTab === 'reading') url += '&root_only=false';
  else if (currentTab === 'read') url += '&root_only=false';
  else if (currentTab.startsWith('folder:')) url += `&folder_id=${currentTab.split(':')[1]}`;
  // 'all' uses default

  try {
    const res = await authFetch(`${API_BASE}${url}`);
    const data = await res.json();

    let items = data.items || [];
    // Client-side filter for read status tabs
    if (currentTab === 'unread') items = items.filter(p => p.read_status === 'unread' || !p.read_status);
    if (currentTab === 'reading') items = items.filter(p => p.read_status === 'reading');
    if (currentTab === 'read') items = items.filter(p => p.read_status === 'read');

    if (!items.length) {
      grid.innerHTML = `<div style="grid-column:1/-1;text-align:center;color:var(--text-muted);padding:48px;">
        ${currentTab === 'all' ? '暂无论文，粘贴链接或上传 PDF 开始吧！' : '该分类暂无论文。'}
      </div>`;
    } else {
      grid.innerHTML = items.map(p => renderPaperCard(p)).join('');
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

  const readStatusBadge = getReadStatusBadge(p);
  const progressBar = renderProgressBar(p);

  const tags = p.tags ? (() => { try { return JSON.parse(p.tags); } catch { return []; } })() : [];

  return `
    <div class="glass-panel paper-card" draggable="true"
         ondragstart="event.dataTransfer.setData('text/paper-id','${p.id}')"
         onclick="location.hash='/papers/${p.id}'" data-paper-id="${p.id}" data-status="${p.status}">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:8px;">
        <div style="display:flex;gap:6px;align-items:center;">
          <span style="display:inline-flex;align-items:center;gap:4px;font-size:0.8rem;color:${color};${p.status === 'processing' ? 'animation:pulse 1.5s infinite;' : ''}">
            <span style="width:6px;height:6px;border-radius:50%;background:${color};display:inline-block;"></span>
            ${label}
          </span>
          ${readStatusBadge}
        </div>
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
      <p style="color:var(--text-muted);font-size:0.85rem;margin-bottom:8px;">
        ${p.source || 'unknown'} · ${new Date(p.created_at).toLocaleDateString('zh-CN')}
      </p>
      ${progressBar}
      ${tags.length > 0 ? `<div style="display:flex;gap:6px;flex-wrap:wrap;margin-top:8px;">${tags.slice(0, 3).map(t =>
        `<span style="background:rgba(88,86,214,0.1);color:var(--accent);padding:2px 8px;border-radius:10px;font-size:0.75rem;">${t}</span>`
      ).join('')}</div>` : ''}
    </div>
  `;
}

function getReadStatusBadge(p) {
  const s = p.read_status || 'unread';
  const map = {
    unread: { color: '#9e9bb0', bg: 'rgba(158,155,176,0.15)', text: '未读' },
    reading: { color: '#007aff', bg: 'rgba(0,122,255,0.12)', text: '阅读中' },
    read: { color: '#34c759', bg: 'rgba(52,199,89,0.12)', text: '已读' },
  };
  const st = map[s] || map.unread;
  return `<span style="font-size:0.7rem;padding:2px 8px;border-radius:8px;background:${st.bg};color:${st.color};font-weight:600;">${st.text}</span>`;
}

function renderProgressBar(p) {
  const total = p.total_pages || 0;
  const read = p.pages_read || 0;
  if (total === 0) return '';
  const pct = Math.min(100, Math.round((read / total) * 100));
  return `
    <div class="paper-progress">
      <div class="paper-progress__bar">
        <div class="paper-progress__fill" style="width:${pct}%;"></div>
      </div>
      <span class="paper-progress__text">${read}/${total} 页 (${pct}%)</span>
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
    const res = await authFetch(`${API_BASE}/papers/batch-url`, {
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

async function uploadFiles(files) {
  for (const file of files) {
    const formData = new FormData();
    formData.append('file', file);
    try {
      await authFetch(`${API_BASE}/papers/upload-pdf`, { method: 'POST', body: formData });
      window.showToast(`已上传: ${file.name}`, 'success');
    } catch (e) {
      window.showToast(`上传失败: ${file.name}`, 'error');
    }
  }
  loadPapers();
}

async function checkProcessingPapers() {
  const cards = document.querySelectorAll('[data-status="pending"],[data-status="processing"]');
  if (cards.length === 0) return;

  for (const card of cards) {
    const id = card.dataset.paperId;
    try {
      const res = await authFetch(`${API_BASE}/papers/${id}`);
      const paper = await res.json();
      if (paper.status !== card.dataset.status) {
        loadPapers();
        return;
      }
    } catch (e) { /* ignore */ }
  }
}

// Global handlers
window.__toggleFav = async (id) => {
  try {
    await authFetch(`${API_BASE}/papers/${id}/toggle-favorite`, { method: 'POST' });
    loadPapers();
  } catch (e) {
    window.showToast('操作失败', 'error');
  }
};

window.__deletePaper = async (id) => {
  const ok = await window.showGlassConfirm('删除论文', '确定要删除这篇论文吗？此操作不可撤销。', { danger: true, confirmText: '删除' });
  if (ok) {
    try {
      await authFetch(`${API_BASE}/papers/${id}`, { method: 'DELETE' });
      window.showToast('论文已删除', 'success');
      loadPapers();
    } catch (e) {
      window.showToast('删除失败', 'error');
    }
  }
};
