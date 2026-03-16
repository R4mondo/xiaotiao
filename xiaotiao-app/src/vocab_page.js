import { fetchAPI } from './api.js';

export function renderVocabPage() {
    return `
    <div class="page-container glass-panel" style="max-width: 1200px; margin: 40px auto; padding: 40px; border-radius: 24px;">
        <div class="vocab-page__header">
            <div>
                <h1 class="vocab-page__title">我的生词本</h1>
                <p class="vocab-page__subtitle">管理您的词汇库，通过间隔重复算法高效学习。</p>
            </div>
            <div style="display: flex; gap: 16px;">
                <button class="btn btn--secondary" onclick="window.__vocabRefreshStats()">
                    <span class="material-symbols-rounded" style="font-size: 18px;">refresh</span>
                    刷新
                </button>
                <button class="btn btn--primary" id="btn-upload-vocab">
                    <span class="material-symbols-rounded" style="font-size: 18px;">upload_file</span>
                    上传词汇文件
                </button>
                <input type="file" id="vocab-file-input" style="display: none;"
                    accept=".txt,.md,.csv,.xlsx,.xls,.docx,.doc,.png,.jpg,.jpeg">
                <button class="btn btn--primary" id="btn-add-word">
                    <span class="material-symbols-rounded" style="font-size: 18px;">add</span>
                    添加新词
                </button>
            </div>
        </div>

        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 40px;" id="vocab-stats-container">
            <!-- Stats loaded dynamically -->
            <div class="panel p-4" style="background: rgba(255,255,255,0.02);"><p>统计数据加载中...</p></div>
        </div>

        <div class="settings-group" style="padding: 0; background: transparent;">
            <div style="display: flex; gap: 16px; margin-bottom: 24px;">
                <div class="input-wrapper" style="flex: 1;">
                    <span class="material-symbols-rounded input-icon">search</span>
                    <input type="text" id="vocab-search" class="input-field" placeholder="搜索生词..." style="padding-left: 48px;">
                </div>
                <div class="input-wrapper" style="width: 200px;">
                    <select id="vocab-domain-filter" class="input-field">
                        <option value="">所有领域</option>
                        <option value="general">通用</option>
                        <option value="international arbitration">国际仲裁</option>
                        <option value="data governance">数据治理</option>
                    </select>
                </div>
            </div>

            <div class="glass-table-wrap">
             <div class="glass-table-scroll">
                <table class="glass-table">
                    <thead>
                        <tr>
                            <th>单词</th>
                            <th>中文释义</th>
                            <th class="col-domain">专业领域</th>
                            <th class="col-next-review">下次复习</th>
                            <th>状态</th>
                            <th>操作</th>
                        </tr>
                    </thead>
                    <tbody id="vocab-table-body">
                        <tr><td colspan="6" style="padding: 24px; text-align: center; color: var(--text-muted);">词汇加载中...</td></tr>
                    </tbody>
                </table>
             </div>
            </div>
            
            <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 24px;" id="vocab-pagination">
                <p style="color: var(--text-muted);">显示 <span id="vocab-page-info">0</span> 项</p>
                <div style="display: flex; gap: 8px;">
                    <button class="btn btn--secondary" id="btn-prev-page" style="padding: 8px 16px;">上一页</button>
                    <button class="btn btn--secondary" id="btn-next-page" style="padding: 8px 16px;">下一页</button>
                </div>
            </div>
        </div>
    </div>

    <!-- Upload Progress Overlay -->
    <div id="modal-upload-progress" style="display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.6); backdrop-filter: blur(10px); z-index: 1001; align-items: center; justify-content: center;">
        <div class="glass-panel" style="width: 420px; padding: 40px; border-radius: 20px; text-align: center;">
            <div style="margin-bottom: 20px;">
                <span class="material-symbols-rounded" style="font-size: 48px; color: var(--accent); animation: spin 1.2s linear infinite;">progress_activity</span>
            </div>
            <h3 style="color: var(--text-primary); font-size: 1.3rem; margin-bottom: 12px;" id="upload-progress-title">正在解析文件...</h3>
            <p style="color: var(--text-muted); font-size: 0.9rem;" id="upload-progress-desc">AI 正在识别词汇，请稍候</p>
        </div>
    </div>

    <!-- Import Preview Modal -->
    <div id="modal-import-preview" style="display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.6); backdrop-filter: blur(10px); z-index: 1000; align-items: center; justify-content: center;">
        <div class="glass-panel" style="width: 700px; max-height: 80vh; padding: 32px; border-radius: 20px; display: flex; flex-direction: column;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                <h3 style="color: var(--text-primary); font-size: 1.5rem; margin: 0;">词汇导入预览</h3>
                <span style="color: var(--text-muted); font-size: 0.9rem;" id="import-preview-count"></span>
            </div>

            <div style="display: flex; gap: 12px; margin-bottom: 16px;">
                <button class="btn btn--secondary" id="btn-import-select-all" style="padding: 6px 14px; font-size: 0.85rem;">全选</button>
                <button class="btn btn--secondary" id="btn-import-deselect-all" style="padding: 6px 14px; font-size: 0.85rem;">取消全选</button>
                <div style="flex:1;"></div>
                <div class="input-wrapper" style="width: 160px;">
                    <select id="import-domain-select" class="input-field" style="padding: 6px 12px; font-size: 0.85rem;">
                        <option value="general">通用</option>
                        <option value="international-law">国际法</option>
                        <option value="commercial-law">商法</option>
                        <option value="constitutional-law">宪法学</option>
                        <option value="criminal-law">刑法学</option>
                        <option value="ip-law">知识产权法</option>
                    </select>
                </div>
            </div>

            <div style="flex: 1; overflow-y: auto; border: 1px solid rgba(255,255,255,0.08); border-radius: 12px;" id="import-preview-list">
                <!-- Dynamically filled -->
            </div>

            <div style="display: flex; justify-content: flex-end; gap: 12px; margin-top: 20px;">
                <button class="btn btn--secondary" id="btn-import-cancel">取消</button>
                <button class="btn btn--primary" id="btn-import-confirm">
                    <span class="material-symbols-rounded" style="font-size: 18px;">download</span>
                    导入选中词汇
                </button>
            </div>
        </div>
    </div>

    <!-- Add Word Modal -->
    <div id="modal-add-word" style="display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.6); backdrop-filter: blur(10px); z-index: 1000; align-items: center; justify-content: center;">
        <div class="glass-panel" style="width: 500px; padding: 32px; border-radius: 20px;">
            <h3 style="color: var(--text-primary); font-size: 1.5rem; margin-bottom: 24px;">添加新单词</h3>
            
            <div class="settings-group">
                <label class="settings-label">单词 (英文) <span style="color:var(--accent);">*</span></label>
                <input type="text" id="add-word-input" class="input-field" placeholder="如：jurisdiction">
            </div>
            
            <div class="settings-group">
                <label class="settings-label">中文释义</label>
                <input type="text" id="add-def-input" class="input-field" placeholder="如：管辖权">
            </div>

            <div class="settings-group" style="display: flex; gap: 16px; align-items: flex-start;">
                <div style="flex: 1;">
                    <label class="settings-label">词性</label>
                    <select id="add-pos-input" class="input-field">
                        <option value="n.">名词 (n.)</option>
                        <option value="v.">动词 (v.)</option>
                        <option value="adj.">形容词 (adj.)</option>
                        <option value="adv.">副词 (adv.)</option>
                        <option value="prep.">介词 (prep.)</option>
                    </select>
                </div>
                <div style="flex: 1;">
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

            <div style="display: flex; justify-content: flex-end; gap: 12px; margin-top: 32px;">
                <button class="btn btn--secondary" onclick="document.getElementById('modal-add-word').style.display='none'">取消</button>
                <button class="btn btn--primary" id="btn-submit-word">保存单词</button>
            </div>
        </div>
    </div>
    `;
}

let currentVocabPage = 1;

export async function initVocabPage() {
    // 1. Load Stats
    window.__vocabRefreshStats = async () => {
        try {
            const stats = await fetchAPI('/vocab/stats', {}, 'GET'); // We need to expose a generic GET in api.js or use raw fetch
            // Hack for now since fetchAPI is hardcoded to POST in my previous edit.
        } catch (e) {
            console.error(e);
        }
    };
    
    // We'll write direct fetch for GET since our fetchAPI wrapper was hardcoded for POST
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
    
    // Filters & Pagination
    let searchTimeout;
    document.getElementById('vocab-search').addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            currentVocabPage = 1;
            loadVocabList();
        }, 500);
    });
    
    document.getElementById('vocab-domain-filter').addEventListener('change', () => {
        currentVocabPage = 1;
        loadVocabList();
    });
    
    document.getElementById('btn-prev-page').addEventListener('click', () => {
        if (currentVocabPage > 1) {
            currentVocabPage--;
            loadVocabList();
        }
    });
    document.getElementById('btn-next-page').addEventListener('click', () => {
        currentVocabPage++;
        loadVocabList();
    });
}

// Helper to make GET requests (our api.js fetchAPI was hardcoded to POST)
async function getJSON(url) {
    const RAW_API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:3000';
    const API_BASE = RAW_API_BASE.replace(/\/api\/v1\/?$/, '');
    const res = await fetch(`${API_BASE}${url}`);
    if (!res.ok) throw new Error('Failed to fetch data');
    return await res.json();
}

// Helper to make POST requests directly
async function postJSON(url, payload) {
    const RAW_API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:3000';
    const API_BASE = RAW_API_BASE.replace(/\/api\/v1\/?$/, '');
    const res = await fetch(`${API_BASE}${url}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
    });
    
    if (!res.ok) {
        const error = await res.json();
        throw new Error(error.detail || 'Failed');
    }
    return await res.json();
}

async function loadVocabStats() {
    try {
        const stats = await getJSON('/vocab/stats');
        const container = document.getElementById('vocab-stats-container');
        container.innerHTML = `
            <div class="panel" style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); padding: 24px; border-radius: 16px;">
                <div style="color: var(--text-muted); font-size: 0.9rem; margin-bottom: 8px;">总词汇量</div>
                <div style="color: white; font-size: 2rem; font-weight: 500;">${stats.total}</div>
            </div>
            <div class="panel" style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); padding: 24px; border-radius: 16px;">
                <div style="color: var(--text-muted); font-size: 0.9rem; margin-bottom: 8px;">复习中</div>
                <div style="color: var(--accent); font-size: 2rem; font-weight: 500;">${stats.active}</div>
            </div>
            <div class="panel" style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); padding: 24px; border-radius: 16px;">
                <div style="color: var(--text-muted); font-size: 0.9rem; margin-bottom: 8px;">已掌握</div>
                <div style="color: #4ade80; font-size: 2rem; font-weight: 500;">${stats.mastered}</div>
            </div>
            <div class="panel" style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); padding: 24px; border-radius: 16px; position: relative; overflow: hidden;">
                <div style="position: absolute; top:0; left:0; right:0; height: 4px; background: #fbbf24;"></div>
                <div style="color: var(--text-muted); font-size: 0.9rem; margin-bottom: 8px;">今日待复习</div>
                <div style="color: #fbbf24; font-size: 2rem; font-weight: 500;">${stats.need_review_today}</div>
            </div>
        `;
    } catch (e) {
        console.error("Stats Error:", e);
    }
}

async function loadVocabList() {
    const tbody = document.getElementById('vocab-table-body');
    tbody.innerHTML = '<tr><td colspan="6" style="padding: 24px; text-align: center; color: var(--text-muted);">词汇加载中...</td></tr>';
    
    const search = document.getElementById('vocab-search').value;
    const domain = document.getElementById('vocab-domain-filter').value;
    
    let url = `/vocab?page=${currentVocabPage}&limit=10`;
    if (search) url += `&search=${encodeURIComponent(search)}`;
    if (domain) url += `&domain=${encodeURIComponent(domain)}`;
    
    try {
        const data = await getJSON(url);
        
        if (data.items.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" style="padding: 24px; text-align: center; color: var(--text-muted);">没有找到对应的生词数据。</td></tr>';
        } else {
            tbody.innerHTML = data.items.map(item => `
                <tr style="border-bottom: 1px solid rgba(255,255,255,0.05); transition: background 0.2s;">
                    <td style="padding: 16px 24px;">
                        <span style="font-weight: 500; font-size: 1.1rem; color: #fff;">${item.word}</span>
                        <span style="color: var(--text-muted); font-size: 0.85rem; margin-left: 8px;">${item.part_of_speech || ''}</span>
                    </td>
                    <td style="padding: 16px 24px; max-width: 250px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                        ${item.definition_zh || '-'}
                    </td>
                    <td style="padding: 16px 24px;">
                        <span style="background: rgba(255,255,255,0.1); padding: 4px 10px; border-radius: 12px; font-size: 0.8rem; color: var(--text-muted);">
                            ${item.domain}
                        </span>
                    </td>
                    <td style="padding: 16px 24px; font-variant-numeric: tabular-nums;">
                        ${formatNextReview(item.next_review_date)}
                    </td>
                    <td style="padding: 16px 24px;">
                        ${getStatusBadge(item)}
                    </td>
                    <td style="padding: 16px 24px;">
                        <button class="icon-btn" onclick="window.__deleteVocab('${item.id}')" style="background:transparent; border:none; cursor:pointer; color:var(--text-muted);">
                            <span class="material-symbols-rounded" style="font-size: 20px;">delete</span>
                        </button>
                    </td>
                </tr>
            `).join('');
        }
        
        document.getElementById('vocab-page-info').textContent = `${(data.page - 1) * 10 + Math.min(1, data.items.length)} - ${(data.page - 1) * 10 + data.items.length} of ${data.total_count}`;
        document.getElementById('btn-prev-page').disabled = data.page <= 1;
        document.getElementById('btn-next-page').disabled = data.page >= data.total_pages;
        
    } catch (e) {
        tbody.innerHTML = `<tr><td colspan="6" style="padding: 24px; text-align: center; color: #ef4444;">Error: ${e.message}</td></tr>`;
    }
}

function getStatusBadge(item) {
    if (item.is_mastered) {
         return `<span style="display:inline-flex; align-items:center; gap:4px; color: #4ade80; font-size: 0.9rem;"><span style="width:6px;height:6px;border-radius:50%;background:#4ade80;"></span>已掌握 (Mastered)</span>`;
    }
    if (item.traversal_count === 0) {
        return `<span style="display:inline-flex; align-items:center; gap:4px; color: var(--accent); font-size: 0.9rem;"><span style="width:6px;height:6px;border-radius:50%;background:var(--accent);"></span>新词 (New)</span>`;
    }
    return `<span style="display:inline-flex; align-items:center; gap:4px; color: #fbbf24; font-size: 0.9rem;"><span style="width:6px;height:6px;border-radius:50%;background:#fbbf24;"></span>学习中 (L${item.traversal_count})</span>`;
}

function formatNextReview(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    const today = new Date();
    today.setHours(0,0,0,0);
    const compareDate = new Date(date);
    compareDate.setHours(0,0,0,0);
    
    const diffTime = compareDate - today;
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays <= 0) return `<span style="color: #fbbf24; font-weight: 500;">今日</span>`;
    if (diffDays === 1) return `明日`;
    return `${diffDays} 天后`;
}

async function submitNewWord() {
    const word = document.getElementById('add-word-input').value.trim();
    if (!word) return showToast('请输入英文单词', 'warning');
    
    const payload = {
        word: word,
        definition_zh: document.getElementById('add-def-input').value.trim(),
        part_of_speech: document.getElementById('add-pos-input').value,
        domain: document.getElementById('add-domain-input').value,
        example_sentence: document.getElementById('add-ex-input').value.trim(),
        source: 'manual'
    };
    
    const btn = document.getElementById('btn-submit-word');
    const originalText = btn.textContent;
    btn.textContent = '保存中...';
    btn.disabled = true;
    
    try {
        await postJSON('/vocab', payload);
        document.getElementById('modal-add-word').style.display = 'none';
        
        // Clear form
        document.getElementById('add-word-input').value = '';
        document.getElementById('add-def-input').value = '';
        document.getElementById('add-ex-input').value = '';
        
        // Refresh 
        loadVocabStats();
        loadVocabList();
    } catch (e) {
        showToast(e.message, 'error');
    } finally {
        btn.textContent = originalText;
        btn.disabled = false;
    }
}

// --- File Upload & Import Logic ---
window.__pendingImportWords = [];

async function handleFileUpload(e) {
    const file = e.target.files[0];
    if (!file) return;

    // Reset input so the same file can be re-uploaded
    e.target.value = '';

    const TEXT_EXTENSIONS = ['.txt', '.md', '.csv'];
    const fileName = file.name.toLowerCase();
    const isTextFile = TEXT_EXTENSIONS.some(ext => fileName.endsWith(ext));

    // Show progress
    document.getElementById('modal-upload-progress').style.display = 'flex';
    document.getElementById('upload-progress-title').textContent = '正在解析文件...';
    document.getElementById('upload-progress-desc').textContent = isTextFile
        ? '正在读取并分析文本内容'
        : 'AI 正在识别词汇，请稍候';

    try {
        let words = [];

        if (isTextFile) {
            // Read client-side first, then send text to server for AI parsing
            const textContent = await readFileAsText(file);
            if (!textContent.trim()) {
                showToast('文件内容为空', 'warning');
                return;
            }
            // Still send to server for AI extraction
            words = await uploadFileToServer(file);
        } else {
            // Binary files: upload directly
            words = await uploadFileToServer(file);
        }

        if (!words || words.length === 0) {
            showToast('未能从文件中识别出词汇', 'warning');
            return;
        }

        // Store and show preview
        window.__pendingImportWords = words;
        showImportPreview(words);
    } catch (err) {
        console.error('File upload error:', err);
        showToast(`文件解析失败：${err.message}`, 'error');
    } finally {
        document.getElementById('modal-upload-progress').style.display = 'none';
    }
}

function readFileAsText(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result);
        reader.onerror = () => reject(new Error('读取文件失败'));
        reader.readAsText(file, 'utf-8');
    });
}

async function uploadFileToServer(file) {
    const RAW_API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:3000';
    const API_BASE = RAW_API_BASE.replace(/\/api\/v1\/?$/, '');

    const formData = new FormData();
    formData.append('file', file);
    formData.append('domain', 'general');

    const res = await fetch(`${API_BASE}/vocab/import-file`, {
        method: 'POST',
        body: formData,
    });

    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `上传失败 (${res.status})`);
    }

    const data = await res.json();
    return data.words || [];
}

function showImportPreview(words) {
    const list = document.getElementById('import-preview-list');
    list.innerHTML = words.map((w, i) => `
        <div style="display: flex; align-items: center; gap: 12px; padding: 12px 16px; border-bottom: 1px solid rgba(255,255,255,0.05); ${i % 2 === 0 ? 'background: rgba(255,255,255,0.02);' : ''}">
            <input type="checkbox" checked data-index="${i}"
                style="width: 18px; height: 18px; accent-color: var(--accent); cursor: pointer; flex-shrink: 0;"
                onchange="window.__updateImportCount()">
            <div style="flex: 1; min-width: 0;">
                <div style="display: flex; align-items: baseline; gap: 8px; margin-bottom: 4px;">
                    <span style="font-weight: 600; color: #fff; font-size: 1.05rem;">${escapeHtml(w.word)}</span>
                    <span style="color: var(--text-muted); font-size: 0.8rem;">${escapeHtml(w.part_of_speech || '')}</span>
                </div>
                <div style="color: var(--text-muted); font-size: 0.9rem; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                    ${escapeHtml(w.definition_zh || '(无释义)')}
                </div>
                ${w.example_sentence ? `<div style="color: rgba(255,255,255,0.3); font-size: 0.8rem; margin-top: 4px; font-style: italic; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${escapeHtml(w.example_sentence)}</div>` : ''}
            </div>
        </div>
    `).join('');

    updateImportCount();
    document.getElementById('modal-import-preview').style.display = 'flex';
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

window.__updateImportCount = updateImportCount;
function updateImportCount() {
    const checkboxes = document.querySelectorAll('#import-preview-list input[type="checkbox"]');
    const checked = [...checkboxes].filter(cb => cb.checked).length;
    const total = checkboxes.length;
    document.getElementById('import-preview-count').textContent = `已选 ${checked} / ${total} 词`;
}

async function confirmImportWords() {
    const checkboxes = document.querySelectorAll('#import-preview-list input[type="checkbox"]');
    const domain = document.getElementById('import-domain-select').value;
    const selectedWords = [];

    checkboxes.forEach(cb => {
        if (cb.checked) {
            const idx = parseInt(cb.dataset.index);
            const w = window.__pendingImportWords[idx];
            if (w) {
                selectedWords.push({
                    word: w.word,
                    definition_zh: w.definition_zh || '',
                    part_of_speech: w.part_of_speech || 'n.',
                    domain: domain,
                    source: 'file_import',
                    example_sentence: w.example_sentence || '',
                });
            }
        }
    });

    if (selectedWords.length === 0) {
        showToast('请至少选择一个词汇', 'warning');
        return;
    }

    const btn = document.getElementById('btn-import-confirm');
    const originalHTML = btn.innerHTML;
    btn.innerHTML = '<span class="material-symbols-rounded" style="font-size: 18px; animation: spin 1s linear infinite;">progress_activity</span> 导入中...';
    btn.disabled = true;

    try {
        const result = await postJSON('/vocab/batch', selectedWords);
        document.getElementById('modal-import-preview').style.display = 'none';
        window.__pendingImportWords = [];

        showToast(`成功导入 ${result.imported} 个词汇${result.skipped > 0 ? `，跳过 ${result.skipped} 个重复词` : ''}`, 'success');

        loadVocabStats();
        loadVocabList();
    } catch (err) {
        showToast(`导入失败：${err.message}`, 'error');
    } finally {
        btn.innerHTML = originalHTML;
        btn.disabled = false;
    }
}

// Global delete exposed for inline onclick
window.__deleteVocab = async (id) => {
    const ok = await showGlassConfirm('删除术语', '确定要删除该核心术语吗？这也会删除其复习历史。', { danger: true, confirmText: '删除', cancelText: '取消' });
    if (ok) {
        const RAW_API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:3000';
        const API_BASE = RAW_API_BASE.replace(/\/api\/v1\/?$/, '');
        try {
            const res = await fetch(`${API_BASE}/vocab/${id}`, { method: 'DELETE' });
            if (!res.ok) throw new Error('删除失败');
            showToast('术语已删除', 'success');
            loadVocabStats();
            loadVocabList();
        } catch (e) {
            console.error(e);
            showToast('删除发生错误，请检查网络。', 'error');
        }
    }
};
