// Tracker Page — /tracker
const RAW_API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:3000';
const API_BASE = RAW_API_BASE.replace(/\/api\/v1\/?$/, '');

export function renderTrackerPage() {
  return `
    <div class="page-container glass-panel" style="max-width:1200px;margin:40px auto;padding:40px;border-radius:24px;">
      <div class="page-header__badge" style="margin-bottom:12px;display:inline-flex;align-items:center;gap:8px;padding:6px 12px;background:var(--glass-bg);border-radius:20px;font-size:0.85rem;color:var(--text-secondary);">
        <span class="nav-dot" style="background:#f472b6;width:8px;height:8px;border-radius:50%;display:inline-block;"></span>
        模块 · 主题追踪
      </div>
      <h1 style="color:var(--text-primary);font-size:2rem;font-weight:700;margin-bottom:8px;">主题追踪</h1>
      <p style="color:var(--text-secondary);margin-bottom:32px;">追踪感兴趣的研究主题，自动发现最新论文。</p>

      <!-- Add Topic -->
      <div class="glass-panel" style="padding:24px;border-radius:16px;margin-bottom:32px;">
        <div style="display:flex;gap:12px;align-items:flex-end;margin-bottom:16px;">
          <div style="flex:1;">
            <label style="color:var(--text-secondary);font-size:0.85rem;margin-bottom:6px;display:block;">追踪主题</label>
            <input type="text" id="tracker-topic-input" class="input-field"
              placeholder="输入追踪主题关键词，如 LLM reasoning, diffusion model..."
              style="width:100%;">
          </div>
          <div>
            <label style="color:var(--text-secondary);font-size:0.85rem;margin-bottom:6px;display:block;">检查频率</label>
            <select id="tracker-frequency" class="input-field" style="min-width:120px;">
              <option value="daily">每日检查</option>
              <option value="weekly">每周检查</option>
            </select>
          </div>
        </div>
        <!-- Source Selection -->
        <div style="margin-bottom:16px;">
          <label style="color:var(--text-secondary);font-size:0.85rem;margin-bottom:8px;display:block;">来源选择</label>
          <div style="display:flex;flex-wrap:wrap;gap:10px;">
            <label style="display:inline-flex;align-items:center;gap:6px;padding:6px 12px;background:var(--glass-bg);border-radius:10px;cursor:pointer;font-size:0.85rem;color:var(--text-primary);border:1px solid transparent;transition:border-color 0.2s;" class="source-checkbox-label">
              <input type="checkbox" class="tracker-source-cb" value="arxiv" checked style="accent-color:#f472b6;">
              <span>ArXiv</span>
            </label>
            <label style="display:inline-flex;align-items:center;gap:6px;padding:6px 12px;background:var(--glass-bg);border-radius:10px;cursor:pointer;font-size:0.85rem;color:var(--text-primary);border:1px solid transparent;transition:border-color 0.2s;" class="source-checkbox-label">
              <input type="checkbox" class="tracker-source-cb" value="ssrn" style="accent-color:#f472b6;">
              <span>SSRN</span>
              <span style="font-size:0.7rem;color:var(--text-muted);background:rgba(244,114,182,0.1);padding:1px 6px;border-radius:6px;">即将上线</span>
            </label>
            <label style="display:inline-flex;align-items:center;gap:6px;padding:6px 12px;background:var(--glass-bg);border-radius:10px;cursor:pointer;font-size:0.85rem;color:var(--text-primary);border:1px solid transparent;transition:border-color 0.2s;" class="source-checkbox-label">
              <input type="checkbox" class="tracker-source-cb" value="cnki" style="accent-color:#f472b6;">
              <span>CNKI (中国知网)</span>
              <span style="font-size:0.7rem;color:var(--text-muted);background:rgba(244,114,182,0.1);padding:1px 6px;border-radius:6px;">即将上线</span>
            </label>
            <label style="display:inline-flex;align-items:center;gap:6px;padding:6px 12px;background:var(--glass-bg);border-radius:10px;cursor:pointer;font-size:0.85rem;color:var(--text-primary);border:1px solid transparent;transition:border-color 0.2s;" class="source-checkbox-label">
              <input type="checkbox" class="tracker-source-cb" value="heinonline" style="accent-color:#f472b6;">
              <span>HeinOnline</span>
              <span style="font-size:0.7rem;color:var(--text-muted);background:rgba(244,114,182,0.1);padding:1px 6px;border-radius:6px;">即将上线</span>
            </label>
            <label style="display:inline-flex;align-items:center;gap:6px;padding:6px 12px;background:var(--glass-bg);border-radius:10px;cursor:pointer;font-size:0.85rem;color:var(--text-primary);border:1px solid transparent;transition:border-color 0.2s;" class="source-checkbox-label">
              <input type="checkbox" class="tracker-source-cb" value="google_scholar" style="accent-color:#f472b6;">
              <span>Google Scholar</span>
              <span style="font-size:0.7rem;color:var(--text-muted);background:rgba(244,114,182,0.1);padding:1px 6px;border-radius:6px;">即将上线</span>
            </label>
          </div>
        </div>
        <button class="btn btn--primary" id="btn-add-topic" style="padding:10px 20px;white-space:nowrap;width:100%;">
          添加追踪
        </button>
      </div>

      <!-- Active Topics -->
      <h2 style="color:var(--text-primary);font-size:1.2rem;font-weight:600;margin-bottom:16px;">正在追踪的主题</h2>
      <div id="topics-list" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:16px;margin-bottom:40px;">
        <div style="color:var(--text-muted);padding:24px;">加载中...</div>
      </div>

      <!-- Discovered Papers -->
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
        <h2 style="color:var(--text-primary);font-size:1.2rem;font-weight:600;">
          发现的论文 <span id="discovered-count" style="color:var(--text-muted);font-weight:400;font-size:0.9rem;"></span>
        </h2>
        <div style="display:flex;gap:8px;">
          <button class="btn btn--secondary discovered-tab active" data-filter="pending" style="font-size:0.85rem;padding:6px 14px;">待处理</button>
          <button class="btn btn--secondary discovered-tab" data-filter="done" style="font-size:0.85rem;padding:6px 14px;">已收录</button>
          <button class="btn btn--secondary discovered-tab" data-filter="ignored" style="font-size:0.85rem;padding:6px 14px;">已忽略</button>
          <button class="btn btn--secondary discovered-tab" data-filter="" style="font-size:0.85rem;padding:6px 14px;">全部</button>
        </div>
      </div>
      <div id="discovered-papers" style="display:flex;flex-direction:column;gap:12px;">
        <div style="color:var(--text-muted);padding:24px;text-align:center;">加载中...</div>
      </div>
    </div>
  `;
}

let currentFilter = 'pending';

export function initTrackerPage() {
  loadTopics();
  loadDiscoveredPapers();

  document.getElementById('btn-add-topic').addEventListener('click', addTopic);
  document.getElementById('tracker-topic-input').addEventListener('keydown', (e) => {
    if (e.key === 'Enter') addTopic();
  });

  // Filter tabs
  document.querySelectorAll('.discovered-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('.discovered-tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      currentFilter = tab.dataset.filter;
      loadDiscoveredPapers();
    });
  });

  // Poll every 15 seconds
  window.__trackerPollInterval = setInterval(loadDiscoveredPapers, 15000);
}

// Cleanup on page leave
window.__trackerCleanup = () => {
  if (window.__trackerPollInterval) {
    clearInterval(window.__trackerPollInterval);
    window.__trackerPollInterval = null;
  }
};

async function loadTopics() {
  const container = document.getElementById('topics-list');
  try {
    const res = await fetch(`${API_BASE}/topics`);
    const topics = await res.json();

    if (topics.length === 0) {
      container.innerHTML = `<div style="grid-column:1/-1;text-align:center;color:var(--text-muted);padding:32px;">暂无追踪主题，添加一个开始吧！</div>`;
      return;
    }

    container.innerHTML = topics.map(t => {
      const lastChecked = t.last_checked_at ? formatRelativeTime(t.last_checked_at) : '从未';
      const freqLabel = t.check_frequency === 'daily' ? '每日' : '每周';
      const sources = Array.isArray(t.sources) ? t.sources : ['arxiv'];
      const sourceTags = sources.map(s => {
        const label = SOURCE_LABELS[s] || s;
        const isComingSoon = COMING_SOON_SOURCES.includes(s);
        return `<span style="background:rgba(244,114,182,0.08);color:${isComingSoon ? 'var(--text-muted)' : '#f472b6'};padding:2px 8px;border-radius:8px;font-size:0.7rem;">${escapeHtml(label)}${isComingSoon ? ' (即将)' : ''}</span>`;
      }).join('');

      return `
        <div class="glass-panel" style="padding:20px;border-radius:14px;border-left:3px solid #f472b6;">
          <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:12px;">
            <h3 style="color:var(--text-primary);font-size:1rem;font-weight:600;">${escapeHtml(t.title)}</h3>
            <button onclick="window.__deleteTopic('${t.id}')" style="background:none;border:none;color:var(--text-muted);cursor:pointer;font-size:0.9rem;">✕</button>
          </div>
          <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-bottom:8px;">
            <span style="background:rgba(244,114,182,0.1);color:#f472b6;padding:2px 8px;border-radius:8px;font-size:0.75rem;">${freqLabel}</span>
            <span style="color:var(--text-muted);font-size:0.8rem;">上次检查: ${lastChecked}</span>
          </div>
          <div style="display:flex;gap:4px;flex-wrap:wrap;margin-bottom:12px;">
            ${sourceTags}
          </div>
          <button class="btn btn--secondary" onclick="window.__checkNow('${t.id}')" style="width:100%;padding:8px;font-size:0.85rem;">
            立即检查
          </button>
        </div>
      `;
    }).join('');
  } catch (e) {
    container.innerHTML = `<div style="color:#ef4444;padding:24px;">加载失败: ${e.message}</div>`;
  }
}

async function loadDiscoveredPapers() {
  const container = document.getElementById('discovered-papers');
  try {
    let url = `${API_BASE}/topics/papers`;
    if (currentFilter) url += `?status=${currentFilter}`;

    const res = await fetch(url);
    const papers = await res.json();

    document.getElementById('discovered-count').textContent = `(${papers.length})`;

    if (papers.length === 0) {
      container.innerHTML = `<div style="text-align:center;color:var(--text-muted);padding:32px;">
        ${currentFilter === 'pending' ? '暂无待处理的发现论文。点击"立即检查"搜索新论文。' : '暂无论文。'}
      </div>`;
      return;
    }

    container.innerHTML = papers.map(p => {
      const statusBadge = p.status === 'done'
        ? '<span style="color:#34c759;font-size:0.8rem;">已收录</span>'
        : p.status === 'ignored'
        ? '<span style="color:var(--text-muted);font-size:0.8rem;">已忽略</span>'
        : '';

      return `
        <div class="glass-panel" style="padding:20px;border-radius:14px;">
          <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:16px;">
            <div style="flex:1;">
              <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
                <h4 style="color:var(--text-primary);font-size:0.95rem;font-weight:500;line-height:1.4;">${escapeHtml(p.title)}</h4>
                ${statusBadge}
              </div>
              <p style="color:var(--text-muted);font-size:0.8rem;margin-bottom:6px;">
                来源主题: ${escapeHtml(p.topic_title || '')} · ${formatRelativeTime(p.discovered_at)}
              </p>
              ${p.brief ? `<p style="color:var(--text-secondary);font-size:0.85rem;line-height:1.5;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;">${escapeHtml(p.brief)}</p>` : ''}
            </div>
            ${p.status === 'pending' ? `
              <div style="display:flex;gap:8px;flex-shrink:0;">
                <button class="btn btn--primary" onclick="window.__importPaper('${p.id}')" style="padding:6px 14px;font-size:0.85rem;">收录</button>
                <button class="btn btn--secondary" onclick="window.__ignorePaper('${p.id}')" style="padding:6px 14px;font-size:0.85rem;">忽略</button>
              </div>
            ` : ''}
          </div>
        </div>
      `;
    }).join('');
  } catch (e) {
    container.innerHTML = `<div style="color:#ef4444;padding:24px;">加载失败: ${e.message}</div>`;
  }
}

const SOURCE_LABELS = {
  arxiv: 'ArXiv',
  ssrn: 'SSRN',
  cnki: 'CNKI',
  heinonline: 'HeinOnline',
  google_scholar: 'Google Scholar',
};

const COMING_SOON_SOURCES = ['ssrn', 'cnki', 'heinonline', 'google_scholar'];

function getSelectedSources() {
  const checkboxes = document.querySelectorAll('.tracker-source-cb:checked');
  return Array.from(checkboxes).map(cb => cb.value);
}

async function addTopic() {
  const input = document.getElementById('tracker-topic-input');
  const title = input.value.trim();
  if (!title) return window.showToast('请输入主题关键词', 'warning');

  const frequency = document.getElementById('tracker-frequency').value;
  const sources = getSelectedSources();

  if (sources.length === 0) return window.showToast('请至少选择一个来源', 'warning');

  // Check if any coming-soon sources are selected alongside arxiv
  const comingSoon = sources.filter(s => COMING_SOON_SOURCES.includes(s));
  if (comingSoon.length > 0) {
    const comingSoonLabels = comingSoon.map(s => SOURCE_LABELS[s]).join('、');
    const hasArxiv = sources.includes('arxiv');
    if (!hasArxiv) {
      window.showToast(`${comingSoonLabels} 尚未上线，请至少选择 ArXiv`, 'warning');
      return;
    }
    window.showToast(`${comingSoonLabels} 即将上线，目前仅 ArXiv 生效`, 'info');
  }

  const btn = document.getElementById('btn-add-topic');
  btn.disabled = true;

  try {
    await fetch(`${API_BASE}/topics`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title, check_frequency: frequency, sources })
    });
    input.value = '';
    window.showToast('追踪主题已添加', 'success');
    loadTopics();
  } catch (e) {
    window.showToast('添加失败', 'error');
  } finally {
    btn.disabled = false;
  }
}

function formatRelativeTime(dateStr) {
  if (!dateStr) return '未知';
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now - date;
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return '刚刚';
  if (diffMins < 60) return `${diffMins} 分钟前`;
  if (diffHours < 24) return `${diffHours} 小时前`;
  if (diffDays < 30) return `${diffDays} 天前`;
  return date.toLocaleDateString('zh-CN');
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str || '';
  return div.innerHTML;
}

// Global handlers
window.__deleteTopic = async (id) => {
  const ok = await window.showGlassConfirm('删除追踪主题', '确定要删除这个追踪主题吗？相关的发现论文也将被删除。', { danger: true, confirmText: '删除' });
  if (ok) {
    try {
      await fetch(`${API_BASE}/topics/${id}`, { method: 'DELETE' });
      window.showToast('追踪主题已删除', 'success');
      loadTopics();
      loadDiscoveredPapers();
    } catch (e) {
      window.showToast('删除失败', 'error');
    }
  }
};

window.__checkNow = async (id) => {
  try {
    await fetch(`${API_BASE}/topics/${id}/check-now`, { method: 'POST' });
    window.showToast('正在搜索最新论文...', 'info');
    // Refresh after a short delay to show results
    setTimeout(() => {
      loadTopics();
      loadDiscoveredPapers();
    }, 5000);
  } catch (e) {
    window.showToast('检查失败', 'error');
  }
};

window.__importPaper = async (id) => {
  try {
    const res = await fetch(`${API_BASE}/topics/papers/${id}/import`, { method: 'POST' });
    const data = await res.json();
    window.showToast(data.duplicate ? '该论文已存在于论文库' : '已收录到论文库', 'success');
    loadDiscoveredPapers();
  } catch (e) {
    window.showToast('收录失败', 'error');
  }
};

window.__ignorePaper = async (id) => {
  try {
    await fetch(`${API_BASE}/topics/papers/${id}`, { method: 'DELETE' });
    loadDiscoveredPapers();
  } catch (e) {
    window.showToast('操作失败', 'error');
  }
};
