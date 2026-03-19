import { fetchAPI } from './api.js';
import { authFetch } from './utils/http.js';
import { getAuthToken } from './auth.js';

export function renderVocabPage() {
    return `
    <div class="vocab-shell">
      <div class="page-header__badge" style="margin-bottom:12px;display:inline-flex;align-items:center;gap:8px;padding:6px 12px;background:var(--glass-bg);border-radius:20px;font-size:0.85rem;color:var(--text-secondary);">
        <span class="nav-dot" style="background:var(--accent);width:8px;height:8px;border-radius:50%;display:inline-block;"></span>
        模块 · 生词本
      </div>
      <h1 style="color:var(--text-primary);font-size:1.5rem;font-weight:700;margin-bottom:4px;">我的生词本</h1>
      <p style="color:var(--text-secondary);margin-bottom:20px;font-size:0.9rem;">管理词汇库，间隔重复高效学习。</p>

      <!-- Stats Row -->
      <div class="vocab-stats-row" id="vocab-stats-container">
        <div class="glass-panel vocab-stat-card">
          <div class="vocab-stat-card__label">总词汇量</div>
          <div class="vocab-stat-card__value" id="stat-total">—</div>
        </div>
        <div class="glass-panel vocab-stat-card">
          <div class="vocab-stat-card__label">今日新增</div>
          <div class="vocab-stat-card__value" id="stat-today" style="color:var(--accent);">—</div>
        </div>
        <div class="glass-panel vocab-stat-card">
          <div class="vocab-stat-card__label">本月新增</div>
          <div class="vocab-stat-card__value" id="stat-month">—</div>
        </div>
        <div class="glass-panel vocab-stat-card">
          <div class="vocab-stat-card__label">已掌握</div>
          <div class="vocab-stat-card__value" id="stat-mastered" style="color:#4ade80;">—</div>
        </div>
        <div class="glass-panel vocab-stat-card">
          <div class="vocab-stat-card__label">今日待复习</div>
          <div class="vocab-stat-card__value" id="stat-due" style="color:#fbbf24;">—</div>
        </div>
        <div class="glass-panel vocab-stat-card">
          <div class="vocab-stat-card__label">易忘生词</div>
          <div class="vocab-stat-card__value" id="stat-forgotten" style="color:#ef4444;">—</div>
        </div>
      </div>

      <!-- Actions -->
      <div style="display:flex;gap:10px;margin-bottom:20px;flex-wrap:wrap;align-items:center;">
        <button class="btn btn--primary" id="btn-add-word" style="padding:6px 14px;font-size:0.85rem;">
          <span class="material-symbols-rounded" style="font-size:16px;">add</span> 添加新词
        </button>
        <button class="btn btn--secondary" id="btn-upload-vocab" style="padding:6px 14px;font-size:0.85rem;">
          <span class="material-symbols-rounded" style="font-size:16px;">upload_file</span> 上传词汇文件
        </button>
        <input type="file" id="vocab-file-input" style="display:none;" accept=".txt,.md,.csv,.xlsx,.xls,.docx,.doc,.png,.jpg,.jpeg">
      </div>

      <!-- Batch Actions Bar -->
      <div id="vocab-batch-bar" style="display:none;padding:10px 16px;margin-bottom:12px;background:var(--glass-bg);border:1px solid rgba(88,86,214,0.3);border-radius:12px;align-items:center;gap:12px;">
        <span style="color:var(--text-primary);font-size:0.9rem;font-weight:600;" id="batch-count-label">已选 0 项</span>
        <button class="btn btn--primary btn--sm" id="btn-batch-master" style="padding:4px 12px;font-size:0.82rem;">✅ 批量标为已掌握</button>
        <button class="btn btn--secondary btn--sm" id="btn-batch-unmaster" style="padding:4px 12px;font-size:0.82rem;">🔄 批量标为未掌握</button>
        <button class="btn btn--ghost btn--sm" id="btn-batch-cancel" style="padding:4px 12px;font-size:0.82rem;margin-left:auto;">取消选择</button>
      </div>

      <div class="vocab-main">
        <!-- Sidebar -->
        <aside class="glass-panel vocab-sidebar">
          <div class="vocab-sidebar__section">
            <div class="vocab-sidebar__title">分类视图</div>
            <button class="vocab-nav-item active" data-filter="all">📚 全部生词</button>
            <button class="vocab-nav-item" data-filter="today">📅 当日生词本</button>
            <button class="vocab-nav-item" data-filter="month">📆 当月生词本</button>
            <button class="vocab-nav-item" data-filter="year">📅 当年生词本</button>
          </div>
          <div class="vocab-sidebar__section">
            <div class="vocab-sidebar__title">掌握状态</div>
            <button class="vocab-nav-item" data-filter="mastered">✅ 已掌握</button>
            <button class="vocab-nav-item" data-filter="unmastered">🔵 未掌握</button>
            <button class="vocab-nav-item" data-filter="easily_forgotten">⚠️ 易忘生词</button>
          </div>
        </aside>

        <!-- Content -->
        <section class="vocab-content">
          <div style="display:flex;gap:12px;margin-bottom:16px;">
            <div class="input-wrapper" style="flex:1;">
              <input type="text" id="vocab-search" class="input-field" placeholder="🔍 搜索生词...">
            </div>
            <div class="input-wrapper" style="width:160px;">
              <select id="vocab-domain-filter" class="input-field">
                <option value="">所有领域</option>
                <option value="general">通用</option>
                <option value="international arbitration">国际仲裁</option>
                <option value="data governance">数据治理</option>
              </select>
            </div>
          </div>

          <!-- Inline Date Nav + Download -->
          <div id="vocab-date-nav" class="vocab-date-nav" style="display:none;">
            <div style="display:flex;align-items:center;gap:8px;">
              <button class="btn btn--ghost btn--sm" id="btn-date-prev" style="font-size:0.8rem;padding:4px 10px;">◀ <span id="prev-label"></span></button>
              <span id="vocab-date-label" style="color:var(--text-primary);font-weight:600;font-size:0.9rem;min-width:120px;text-align:center;"></span>
              <button class="btn btn--ghost btn--sm" id="btn-date-next" style="font-size:0.8rem;padding:4px 10px;"><span id="next-label"></span> ▶</button>
            </div>
            <button class="btn btn--secondary btn--sm" id="btn-download-vocab" style="margin-left:auto;font-size:0.8rem;padding:4px 10px;">
              <span class="material-symbols-rounded" style="font-size:14px;">download</span> 导出Word
            </button>
          </div>
          <div id="vocab-no-date-download" style="display:flex;justify-content:flex-end;margin-bottom:8px;">
            <button class="btn btn--secondary btn--sm" id="btn-download-vocab-all" style="font-size:0.8rem;padding:4px 10px;">
              <span class="material-symbols-rounded" style="font-size:14px;">download</span> 导出Word
            </button>
          </div>

          <div class="glass-table-wrap">
            <div class="glass-table-scroll">
              <table class="glass-table">
                <thead>
                  <tr>
                    <th style="width:36px;"><input type="checkbox" id="vocab-select-all" style="width:16px;height:16px;accent-color:var(--accent);cursor:pointer;"></th>
                    <th>单词</th>
                    <th>中文释义</th>
                    <th class="col-domain">专业领域</th>
                    <th class="col-next-review">下次复习</th>
                    <th>状态</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody id="vocab-table-body">
                  <tr><td colspan="6" style="padding:24px;text-align:center;color:var(--text-muted);">词汇加载中...</td></tr>
                </tbody>
              </table>
            </div>
          </div>

          <div style="display:flex;justify-content:space-between;align-items:center;margin-top:16px;">
            <p style="color:var(--text-muted);font-size:0.9rem;"><span id="vocab-page-info">0</span></p>
            <div style="display:flex;gap:8px;">
              <button class="btn btn--secondary" id="btn-prev-page" style="padding:8px 16px;">上一页</button>
              <button class="btn btn--secondary" id="btn-next-page" style="padding:8px 16px;">下一页</button>
            </div>
          </div>
        </section>
      </div>
    </div>

    <!-- Upload Progress Overlay -->
    <div id="modal-upload-progress" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,0.6);backdrop-filter:blur(10px);z-index:1001;align-items:center;justify-content:center;">
      <div class="glass-panel" style="width:420px;padding:40px;border-radius:20px;text-align:center;">
        <div style="margin-bottom:20px;">
          <span class="material-symbols-rounded" style="font-size:48px;color:var(--accent);animation:spin 1.2s linear infinite;">progress_activity</span>
        </div>
        <h3 style="color:var(--text-primary);font-size:1.3rem;margin-bottom:12px;" id="upload-progress-title">正在解析文件...</h3>
        <p style="color:var(--text-muted);font-size:0.9rem;" id="upload-progress-desc">AI 正在识别词汇，请稍候</p>
      </div>
    </div>

    <!-- Import Preview Modal -->
    <div id="modal-import-preview" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,0.6);backdrop-filter:blur(10px);z-index:1000;align-items:center;justify-content:center;">
      <div class="glass-panel" style="width:700px;max-height:80vh;padding:32px;border-radius:20px;display:flex;flex-direction:column;">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;">
          <h3 style="color:var(--text-primary);font-size:1.5rem;margin:0;">词汇导入预览</h3>
          <span style="color:var(--text-muted);font-size:0.9rem;" id="import-preview-count"></span>
        </div>
        <div style="display:flex;gap:12px;margin-bottom:16px;">
          <button class="btn btn--secondary" id="btn-import-select-all" style="padding:6px 14px;font-size:0.85rem;">全选</button>
          <button class="btn btn--secondary" id="btn-import-deselect-all" style="padding:6px 14px;font-size:0.85rem;">取消全选</button>
          <div style="flex:1;"></div>
          <div class="input-wrapper" style="width:160px;">
            <select id="import-domain-select" class="input-field" style="padding:6px 12px;font-size:0.85rem;">
              <option value="general">通用</option>
              <option value="international-law">国际法</option>
              <option value="commercial-law">商法</option>
              <option value="constitutional-law">宪法学</option>
              <option value="criminal-law">刑法学</option>
              <option value="ip-law">知识产权法</option>
            </select>
          </div>
        </div>
        <div style="flex:1;overflow-y:auto;border:1px solid rgba(255,255,255,0.08);border-radius:12px;" id="import-preview-list"></div>
        <div style="display:flex;justify-content:flex-end;gap:12px;margin-top:20px;">
          <button class="btn btn--secondary" id="btn-import-cancel">取消</button>
          <button class="btn btn--primary" id="btn-import-confirm">
            <span class="material-symbols-rounded" style="font-size:18px;">download</span> 导入选中词汇
          </button>
        </div>
      </div>
    </div>

    <!-- Add Word Modal -->
    <div id="modal-add-word" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,0.6);backdrop-filter:blur(10px);z-index:1000;align-items:center;justify-content:center;">
      <div class="glass-panel" style="width:500px;padding:32px;border-radius:20px;">
        <h3 style="color:var(--text-primary);font-size:1.5rem;margin-bottom:24px;">添加新单词</h3>
        <div class="settings-group">
          <label class="settings-label">单词 (英文) <span style="color:var(--accent);">*</span></label>
          <input type="text" id="add-word-input" class="input-field" placeholder="如：jurisdiction">
        </div>
        <div class="settings-group">
          <label class="settings-label">中文释义</label>
          <input type="text" id="add-def-input" class="input-field" placeholder="如：管辖权">
        </div>
        <div class="settings-group" style="display:flex;gap:16px;align-items:flex-start;">
          <div style="flex:1;">
            <label class="settings-label">词性</label>
            <select id="add-pos-input" class="input-field">
              <option value="n.">名词 (n.)</option>
              <option value="v.">动词 (v.)</option>
              <option value="adj.">形容词 (adj.)</option>
              <option value="adv.">副词 (adv.)</option>
              <option value="prep.">介词 (prep.)</option>
            </select>
          </div>
          <div style="flex:1;">
            <label class="settings-label">专业领域</label>
            <select id="add-domain-input" class="input-field">
              <option value="general">通用</option>
              <option value="international-law">国际法</option>
              <option value="commercial-law">商法</option>
              <option value="constitutional-law">宪法学</option>
              <option value="criminal-law">刑法学</option>
              <option value="ip-law">知识产权法</option>
            </select>
          </div>
        </div>
        <div class="settings-group">
          <label class="settings-label">例句参考</label>
          <textarea id="add-ex-input" class="input-field textarea" rows="2" placeholder="He asserted jurisdiction over the matter."></textarea>
        </div>
        <div style="display:flex;justify-content:flex-end;gap:12px;margin-top:32px;">
          <button class="btn btn--secondary" onclick="document.getElementById('modal-add-word').style.display='none'">取消</button>
          <button class="btn btn--primary" id="btn-submit-word">保存单词</button>
        </div>
      </div>
    </div>
    `;
}

let currentVocabPage = 1;
let currentFilter = 'all';
let currentDate = null;

export async function initVocabPage() {
    window.__vocabRefreshStats = loadVocabStats;
    await loadVocabStats();
    await loadVocabList();

    document.getElementById('btn-add-word').addEventListener('click', () => {
        document.getElementById('modal-add-word').style.display = 'flex';
        document.getElementById('add-word-input').focus();
    });
    document.getElementById('btn-submit-word').addEventListener('click', submitNewWord);

    // File upload flow
    document.getElementById('btn-upload-vocab').addEventListener('click', () => {
        document.getElementById('vocab-file-input').click();
    });
    document.getElementById('vocab-file-input').addEventListener('change', handleFileUpload);
    document.getElementById('btn-import-cancel').addEventListener('click', () => {
        document.getElementById('modal-import-preview').style.display = 'none';
        window.__pendingImportWords = [];
    });
    document.getElementById('btn-import-confirm').addEventListener('click', confirmImportWords);
    document.getElementById('btn-import-select-all').addEventListener('click', () => {
        document.querySelectorAll('#import-preview-list input[type="checkbox"]').forEach(cb => cb.checked = true);
        updateImportCount();
    });
    document.getElementById('btn-import-deselect-all').addEventListener('click', () => {
        document.querySelectorAll('#import-preview-list input[type="checkbox"]').forEach(cb => cb.checked = false);
        updateImportCount();
    });

    // Sidebar nav
    document.querySelector('.vocab-sidebar').addEventListener('click', (e) => {
        const btn = e.target.closest('.vocab-nav-item');
        if (!btn) return;
        currentFilter = btn.dataset.filter;
        // Set default date for time-based filters
        if (currentFilter === 'today') currentDate = new Date().toISOString().split('T')[0];
        else if (currentFilter === 'month') currentDate = new Date().toISOString().slice(0, 7);
        else currentDate = null;
        currentVocabPage = 1;
        document.querySelectorAll('.vocab-nav-item').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        updateDateNavVisibility();
        loadVocabList();
    });

    // Inline date nav
    document.getElementById('btn-date-prev').addEventListener('click', () => stepDate(-1));
    document.getElementById('btn-date-next').addEventListener('click', () => stepDate(1));

    // Download buttons
    document.getElementById('btn-download-vocab').addEventListener('click', downloadVocab);
    document.getElementById('btn-download-vocab-all').addEventListener('click', downloadVocab);

    // Search & filter
    let searchTimeout;
    document.getElementById('vocab-search').addEventListener('input', () => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => { currentVocabPage = 1; loadVocabList(); }, 500);
    });
    document.getElementById('vocab-domain-filter').addEventListener('change', () => {
        currentVocabPage = 1; loadVocabList();
    });

    // Pagination
    document.getElementById('btn-prev-page').addEventListener('click', () => {
        if (currentVocabPage > 1) { currentVocabPage--; loadVocabList(); }
    });
    document.getElementById('btn-next-page').addEventListener('click', () => {
        currentVocabPage++; loadVocabList();
    });

    // Select-all checkbox
    document.getElementById('vocab-select-all').addEventListener('change', (e) => {
        const checked = e.target.checked;
        document.querySelectorAll('.vocab-row-check').forEach(cb => cb.checked = checked);
        updateBatchBar();
    });

    // Delegated checkbox change for batch bar
    document.getElementById('vocab-table-body').addEventListener('change', (e) => {
        if (e.target.classList.contains('vocab-row-check')) updateBatchBar();
    });

    // Batch mastery buttons
    document.getElementById('btn-batch-master').addEventListener('click', () => batchSetMastery(true));
    document.getElementById('btn-batch-unmaster').addEventListener('click', () => batchSetMastery(false));
    document.getElementById('btn-batch-cancel').addEventListener('click', () => {
        document.querySelectorAll('.vocab-row-check').forEach(cb => cb.checked = false);
        document.getElementById('vocab-select-all').checked = false;
        updateBatchBar();
    });
}

// ── Mastery Toggle ────────────────────────

window.__toggleMastery = async (id, setMastered) => {
    try {
        const RAW_API_BASE = import.meta.env.VITE_API_BASE_URL || '';
        const API_BASE = RAW_API_BASE.replace(/\/api\/v1\/?$/, '');
        const res = await authFetch(`${API_BASE}/vocab/${id}/mastery`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ is_mastered: setMastered })
        });
        if (!res.ok) throw new Error('Failed');
        showToast(setMastered ? '已标为掌握 ✅' : '已标为未掌握', 'success');
        loadVocabStats();
        loadVocabList();
    } catch (e) {
        showToast('操作失败: ' + e.message, 'error');
    }
};

function updateBatchBar() {
    const checks = document.querySelectorAll('.vocab-row-check:checked');
    const bar = document.getElementById('vocab-batch-bar');
    if (checks.length > 0) {
        bar.style.display = 'flex';
        document.getElementById('batch-count-label').textContent = `已选 ${checks.length} 项`;
    } else {
        bar.style.display = 'none';
    }
}

async function batchSetMastery(mastered) {
    const checks = document.querySelectorAll('.vocab-row-check:checked');
    const ids = [...checks].map(cb => cb.dataset.id);
    if (ids.length === 0) return;

    try {
        const RAW_API_BASE = import.meta.env.VITE_API_BASE_URL || '';
        const API_BASE = RAW_API_BASE.replace(/\/api\/v1\/?$/, '');
        const res = await authFetch(`${API_BASE}/vocab/batch-mastery`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ids, is_mastered: mastered })
        });
        if (!res.ok) throw new Error('Failed');
        const data = await res.json();
        showToast(`已${mastered ? '标为掌握' : '取消掌握'} ${data.updated} 个词汇`, 'success');
        document.getElementById('vocab-select-all').checked = false;
        updateBatchBar();
        loadVocabStats();
        loadVocabList();
    } catch (e) {
        showToast('批量操作失败: ' + e.message, 'error');
    }
}

function updateDateNavVisibility() {
    const nav = document.getElementById('vocab-date-nav');
    const noDateDl = document.getElementById('vocab-no-date-download');
    const hasDateNav = currentFilter === 'today' || currentFilter === 'month';
    nav.style.display = hasDateNav ? 'flex' : 'none';
    noDateDl.style.display = hasDateNav ? 'none' : 'flex';
    if (hasDateNav) {
        updateDateLabel();
        updateNavButtonLabels();
    }
}

function updateNavButtonLabels() {
    const unit = currentFilter === 'today' ? '天' : '月';
    document.getElementById('prev-label').textContent = `上一${unit}`;
    document.getElementById('next-label').textContent = `下一${unit}`;
}

function updateDateLabel() {
    const label = document.getElementById('vocab-date-label');
    if (!label) return;
    label.textContent = getDateLabel();
}

function getDateLabel() {
    if (currentFilter === 'today') {
        const d = currentDate || new Date().toISOString().split('T')[0];
        const parts = d.split('-');
        return `${parts[0]}年${parseInt(parts[1])}月${parseInt(parts[2])}日`;
    } else if (currentFilter === 'month') {
        const m = currentDate || new Date().toISOString().slice(0, 7);
        const parts = m.split('-');
        return `${parts[0]}年${parseInt(parts[1])}月`;
    }
    return '';
}

function stepDate(direction) {
    if (currentFilter === 'today') {
        const d = new Date(currentDate + 'T12:00:00');
        d.setDate(d.getDate() + direction);
        const y = d.getFullYear();
        const m = String(d.getMonth() + 1).padStart(2, '0');
        const day = String(d.getDate()).padStart(2, '0');
        currentDate = `${y}-${m}-${day}`;
    } else if (currentFilter === 'month') {
        const parts = currentDate.split('-');
        const d = new Date(parseInt(parts[0]), parseInt(parts[1]) - 1 + direction, 1);
        const y = d.getFullYear();
        const m = String(d.getMonth() + 1).padStart(2, '0');
        currentDate = `${y}-${m}`;
    }
    currentVocabPage = 1;
    updateDateLabel();
    loadVocabList();
}

function downloadVocab() {
    const RAW_API_BASE = import.meta.env.VITE_API_BASE_URL || '';
    const API_BASE = RAW_API_BASE.replace(/\/api\/v1\/?$/, '');
    const token = getAuthToken();
    if (!token) { showToast('请先登录', 'error'); return; }
    let url = `${API_BASE}/vocab/export?token=${encodeURIComponent(token)}`;
    if (currentFilter && currentFilter !== 'all') url += `&filter=${currentFilter}`;
    if (currentDate) url += `&date=${currentDate}`;
    const search = document.getElementById('vocab-search')?.value;
    if (search) url += `&search=${encodeURIComponent(search)}`;
    const domain = document.getElementById('vocab-domain-filter')?.value;
    if (domain) url += `&domain=${encodeURIComponent(domain)}`;
    window.open(url, '_blank');
}

// ── API helpers ──────────────────────────

async function getJSON(url) {
    const RAW_API_BASE = import.meta.env.VITE_API_BASE_URL || '';
    const API_BASE = RAW_API_BASE.replace(/\/api\/v1\/?$/, '');
    const res = await authFetch(`${API_BASE}${url}`);
    if (!res.ok) throw new Error('Failed to fetch data');
    return await res.json();
}

async function postJSON(url, payload) {
    const RAW_API_BASE = import.meta.env.VITE_API_BASE_URL || '';
    const API_BASE = RAW_API_BASE.replace(/\/api\/v1\/?$/, '');
    const res = await authFetch(`${API_BASE}${url}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    });
    if (!res.ok) {
        const error = await res.json();
        throw new Error(error.detail || 'Failed');
    }
    return await res.json();
}

// ── Stats ──────────────────────────────────

async function loadVocabStats() {
    try {
        const stats = await getJSON('/vocab/stats');
        document.getElementById('stat-total').textContent = stats.total ?? 0;
        document.getElementById('stat-today').textContent = stats.today_count ?? 0;
        document.getElementById('stat-month').textContent = stats.month_count ?? 0;
        document.getElementById('stat-mastered').textContent = stats.mastered ?? 0;
        document.getElementById('stat-due').textContent = stats.need_review_today ?? 0;
        document.getElementById('stat-forgotten').textContent = stats.easily_forgotten ?? 0;
    } catch (e) {
        console.error("Stats Error:", e);
    }
}

// ── List ──────────────────────────────────

async function loadVocabList() {
    const tbody = document.getElementById('vocab-table-body');
    tbody.innerHTML = '<tr><td colspan="6" style="padding:24px;text-align:center;color:var(--text-muted);">词汇加载中...</td></tr>';

    const search = document.getElementById('vocab-search').value;
    const domain = document.getElementById('vocab-domain-filter').value;

    let url = `/vocab?page=${currentVocabPage}&limit=15`;
    if (search) url += `&search=${encodeURIComponent(search)}`;
    if (domain) url += `&domain=${encodeURIComponent(domain)}`;
    if (currentFilter && currentFilter !== 'all') url += `&filter=${currentFilter}`;
    if (currentDate) url += `&date=${currentDate}`;

    try {
        const data = await getJSON(url);

        if (data.items.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" style="padding:24px;text-align:center;color:var(--text-muted);">该分类暂无生词。</td></tr>';
        } else {
            tbody.innerHTML = data.items.map(item => `
                <tr style="border-bottom:1px solid rgba(0,0,0,0.04);transition:background 0.2s;" data-vocab-id="${item.id}">
                    <td style="padding:14px 8px 14px 20px;width:36px;">
                        <input type="checkbox" class="vocab-row-check" data-id="${item.id}" style="width:16px;height:16px;accent-color:var(--accent);cursor:pointer;">
                    </td>
                    <td style="padding:14px 20px;">
                        <span style="font-weight:600;font-size:1.05rem;color:var(--text-primary);">${escapeHtml(item.word)}</span>
                        <span style="color:var(--text-secondary);font-size:0.8rem;margin-left:6px;">${item.part_of_speech || ''}</span>
                        ${item.is_easily_forgotten ? '<span style="margin-left:6px;font-size:0.7rem;padding:2px 6px;border-radius:6px;background:rgba(239,68,68,0.15);color:#ef4444;font-weight:600;">易忘</span>' : ''}
                        ${item.duplicate_count > 0 ? `<span style="margin-left:4px;font-size:0.65rem;color:var(--text-muted);">×${item.duplicate_count + 1}</span>` : ''}
                    </td>
                    <td style="padding:14px 20px;max-width:250px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:var(--text-primary);">
                        ${item.definition_zh || '-'}
                    </td>
                    <td style="padding:14px 20px;">
                        <span style="background:var(--glass-bg-input);padding:3px 8px;border-radius:10px;font-size:0.75rem;color:var(--text-secondary);">
                            ${item.domain}
                        </span>
                    </td>
                    <td style="padding:14px 20px;font-variant-numeric:tabular-nums;">
                        ${formatNextReview(item.next_review_date)}
                    </td>
                    <td style="padding:14px 20px;">
                        ${getStatusBadge(item)}
                    </td>
                    <td style="padding:14px 20px;white-space:nowrap;">
                        <button class="icon-btn" onclick="window.__toggleMastery('${item.id}', ${!item.is_mastered})" title="${item.is_mastered ? '取消掌握' : '标为已掌握'}" style="background:transparent;border:none;cursor:pointer;color:${item.is_mastered ? '#4ade80' : 'var(--text-muted)'};">
                            <span class="material-symbols-rounded" style="font-size:20px;">${item.is_mastered ? 'check_circle' : 'radio_button_unchecked'}</span>
                        </button>
                        <button class="icon-btn" onclick="window.__deleteVocab('${item.id}')" style="background:transparent;border:none;cursor:pointer;color:var(--text-muted);">
                            <span class="material-symbols-rounded" style="font-size:20px;">delete</span>
                        </button>
                    </td>
                </tr>
            `).join('');
        }

        document.getElementById('vocab-page-info').textContent =
            `${(data.page - 1) * 15 + Math.min(1, data.items.length)} - ${(data.page - 1) * 15 + data.items.length} / ${data.total_count} 项`;
        document.getElementById('btn-prev-page').disabled = data.page <= 1;
        document.getElementById('btn-next-page').disabled = data.page >= data.total_pages;

    } catch (e) {
        tbody.innerHTML = `<tr><td colspan="6" style="padding:24px;text-align:center;color:#ef4444;">Error: ${e.message}</td></tr>`;
    }
}

function getStatusBadge(item) {
    if (item.is_mastered) {
        return `<span style="display:inline-flex;align-items:center;gap:4px;color:#4ade80;font-size:0.85rem;"><span style="width:6px;height:6px;border-radius:50%;background:#4ade80;"></span>已掌握</span>`;
    }
    if (item.is_easily_forgotten) {
        return `<span style="display:inline-flex;align-items:center;gap:4px;color:#ef4444;font-size:0.85rem;"><span style="width:6px;height:6px;border-radius:50%;background:#ef4444;"></span>易忘</span>`;
    }
    if (item.traversal_count === 0) {
        return `<span style="display:inline-flex;align-items:center;gap:4px;color:var(--accent);font-size:0.85rem;"><span style="width:6px;height:6px;border-radius:50%;background:var(--accent);"></span>新词</span>`;
    }
    return `<span style="display:inline-flex;align-items:center;gap:4px;color:#fbbf24;font-size:0.85rem;"><span style="width:6px;height:6px;border-radius:50%;background:#fbbf24;"></span>学习中 L${item.traversal_count}</span>`;
}

function formatNextReview(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    const today = new Date();
    today.setHours(0,0,0,0);
    const compareDate = new Date(date);
    compareDate.setHours(0,0,0,0);
    const diffDays = Math.ceil((compareDate - today) / (1000 * 60 * 60 * 24));
    if (diffDays <= 0) return `<span style="color:#fbbf24;font-weight:500;">今日</span>`;
    if (diffDays === 1) return `明日`;
    return `${diffDays} 天后`;
}

// ── Add Word ──────────────────────────────

async function submitNewWord() {
    const word = document.getElementById('add-word-input').value.trim();
    if (!word) return showToast('请输入英文单词', 'warning');

    const payload = {
        word, definition_zh: document.getElementById('add-def-input').value.trim(),
        part_of_speech: document.getElementById('add-pos-input').value,
        domain: document.getElementById('add-domain-input').value,
        example_sentence: document.getElementById('add-ex-input').value.trim(),
        source: 'manual'
    };

    const btn = document.getElementById('btn-submit-word');
    const originalText = btn.textContent;
    btn.textContent = '保存中...'; btn.disabled = true;

    try {
        const result = await postJSON('/vocab', payload);
        document.getElementById('modal-add-word').style.display = 'none';
        document.getElementById('add-word-input').value = '';
        document.getElementById('add-def-input').value = '';
        document.getElementById('add-ex-input').value = '';

        if (result.duplicate) {
            showToast(`"${word}" 已加入易忘生词 (第${result.duplicate_count}次重复)`, 'warning');
        } else {
            showToast(`已添加 "${word}"`, 'success');
        }
        loadVocabStats();
        loadVocabList();
    } catch (e) {
        showToast(e.message, 'error');
    } finally {
        btn.textContent = originalText; btn.disabled = false;
    }
}

// ── File Upload & Import ──────────────────

window.__pendingImportWords = [];

async function handleFileUpload(e) {
    const file = e.target.files[0];
    if (!file) return;
    e.target.value = '';

    const TEXT_EXTENSIONS = ['.txt', '.md', '.csv'];
    const fileName = file.name.toLowerCase();
    const isTextFile = TEXT_EXTENSIONS.some(ext => fileName.endsWith(ext));

    document.getElementById('modal-upload-progress').style.display = 'flex';
    document.getElementById('upload-progress-title').textContent = '正在解析文件...';
    document.getElementById('upload-progress-desc').textContent = isTextFile ? '正在读取并分析文本内容' : 'AI 正在识别词汇，请稍候';

    try {
        const words = await uploadFileToServer(file);
        if (!words || words.length === 0) { showToast('未能从文件中识别出词汇', 'warning'); return; }
        window.__pendingImportWords = words;
        showImportPreview(words);
    } catch (err) {
        showToast(`文件解析失败：${err.message}`, 'error');
    } finally {
        document.getElementById('modal-upload-progress').style.display = 'none';
    }
}

async function uploadFileToServer(file) {
    const RAW_API_BASE = import.meta.env.VITE_API_BASE_URL || '';
    const API_BASE = RAW_API_BASE.replace(/\/api\/v1\/?$/, '');
    const formData = new FormData();
    formData.append('file', file);
    formData.append('domain', 'general');
    const res = await authFetch(`${API_BASE}/vocab/import-file`, { method: 'POST', body: formData });
    if (!res.ok) { const err = await res.json().catch(() => ({})); throw new Error(err.detail || `上传失败 (${res.status})`); }
    const data = await res.json();
    return data.words || [];
}

function showImportPreview(words) {
    const list = document.getElementById('import-preview-list');
    list.innerHTML = words.map((w, i) => `
        <div style="display:flex;align-items:center;gap:12px;padding:12px 16px;border-bottom:1px solid rgba(0,0,0,0.04);${i % 2 === 0 ? 'background:var(--glass-bg);' : ''}">
            <input type="checkbox" checked data-index="${i}" style="width:18px;height:18px;accent-color:var(--accent);cursor:pointer;flex-shrink:0;" onchange="window.__updateImportCount()">
            <div style="flex:1;min-width:0;">
                <div style="display:flex;align-items:baseline;gap:8px;margin-bottom:4px;">
                    <span style="font-weight:600;color:var(--text-primary);font-size:1.05rem;">${escapeHtml(w.word)}</span>
                    <span style="color:var(--text-muted);font-size:0.8rem;">${escapeHtml(w.part_of_speech || '')}</span>
                </div>
                <div style="color:var(--text-muted);font-size:0.9rem;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">
                    ${escapeHtml(w.definition_zh || '(无释义)')}
                </div>
            </div>
        </div>
    `).join('');
    updateImportCount();
    document.getElementById('modal-import-preview').style.display = 'flex';
}

window.__updateImportCount = updateImportCount;
function updateImportCount() {
    const checkboxes = document.querySelectorAll('#import-preview-list input[type="checkbox"]');
    const checked = [...checkboxes].filter(cb => cb.checked).length;
    document.getElementById('import-preview-count').textContent = `已选 ${checked} / ${checkboxes.length} 词`;
}

async function confirmImportWords() {
    const checkboxes = document.querySelectorAll('#import-preview-list input[type="checkbox"]');
    const domain = document.getElementById('import-domain-select').value;
    const selectedWords = [];
    checkboxes.forEach(cb => {
        if (cb.checked) {
            const w = window.__pendingImportWords[parseInt(cb.dataset.index)];
            if (w) selectedWords.push({ word: w.word, definition_zh: w.definition_zh || '', part_of_speech: w.part_of_speech || 'n.', domain, source: 'file_import', example_sentence: w.example_sentence || '' });
        }
    });
    if (selectedWords.length === 0) { showToast('请至少选择一个词汇', 'warning'); return; }

    const btn = document.getElementById('btn-import-confirm');
    const originalHTML = btn.innerHTML;
    btn.innerHTML = '<span class="material-symbols-rounded" style="font-size:18px;animation:spin 1s linear infinite;">progress_activity</span> 导入中...';
    btn.disabled = true;

    try {
        const result = await postJSON('/vocab/batch', selectedWords);
        document.getElementById('modal-import-preview').style.display = 'none';
        window.__pendingImportWords = [];
        showToast(`成功导入 ${result.imported} 个词汇${result.skipped > 0 ? `，跳过 ${result.skipped} 个重复词` : ''}`, 'success');
        loadVocabStats(); loadVocabList();
    } catch (err) {
        showToast(`导入失败：${err.message}`, 'error');
    } finally {
        btn.innerHTML = originalHTML; btn.disabled = false;
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ── Delete ──────────────────────────────

window.__deleteVocab = async (id) => {
    const ok = await showGlassConfirm('删除术语', '确定要删除该核心术语吗？这也会删除其复习历史。', { danger: true, confirmText: '删除', cancelText: '取消' });
    if (ok) {
        const RAW_API_BASE = import.meta.env.VITE_API_BASE_URL || '';
        const API_BASE = RAW_API_BASE.replace(/\/api\/v1\/?$/, '');
        try {
            const res = await authFetch(`${API_BASE}/vocab/${id}`, { method: 'DELETE' });
            if (!res.ok) throw new Error('删除失败');
            showToast('术语已删除', 'success');
            loadVocabStats(); loadVocabList();
        } catch (e) {
            showToast('删除发生错误', 'error');
        }
    }
};
