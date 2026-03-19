// Page renderers for all views — Apple Liquid Glass v2
import {
  analyzeArticle,
  createVocabItem,
  generateTopic,
  runTranslation,
  fetchAPI,
  getArticleHistory,
  getArticleDetail,
  deleteArticle,
  exportArticleWord
} from './api.js';
import { escapeHtml, sanitizeHtml } from './utils/sanitize.js';
import { getTaskManager } from './components/task_manager.js';

// Confidence hint Chinese labels
const CONFIDENCE_LABELS = { high: '高', medium: '中', low: '低' };
function confidenceLabel(hint) {
  return `可信度: ${CONFIDENCE_LABELS[hint] || hint}`;
}
import { startSimulatedProgress } from './utils/stream.js';

// ============ Shared Layout — Liquid Glass ============
// Render layout shell is now handled centrally in index.html

// ============ HOME PAGE — V2.0 Personalized ============

export function renderHome() {
  return `
    <section class="hero hero--v2">
      <div class="container">
        <div class="hero__content">
          <div class="hero__greeting" id="home-greeting">
            <h1 class="hero__title">
              👋 <span id="home-username">你好</span>，欢迎回来
            </h1>
            <p class="hero__profile-tags" id="home-profile-tags">
              <span class="hero__tag">涉外法治英语学习平台</span>
            </p>
            <a href="#/settings/profile" class="hero__edit-profile">修改偏好 →</a>
          </div>
        </div>
      </div>
    </section>

    <section class="home-hub">
      <div class="container">
        <div class="home-hub__grid">
          <!-- 文献研究中心 -->
          <a class="home-hub__card home-hub__card--research" href="#/research">
            <div class="home-hub__card-icon">📚</div>
            <div class="home-hub__card-content">
              <div class="home-hub__card-title">文献研究中心</div>
              <div class="home-hub__card-desc">论文管理 · AI 文章解读 · 主题追踪</div>
              <div class="home-hub__card-hint" id="home-research-hint">
                搜索和阅读学术论文，AI 辅助深度学习
              </div>
            </div>
            <div class="home-hub__card-arrow">→</div>
          </a>

          <!-- 主题探索 -->
          <a class="home-hub__card home-hub__card--explore" href="#/explore">
            <div class="home-hub__card-icon">🧭</div>
            <div class="home-hub__card-content">
              <div class="home-hub__card-title">主题探索</div>
              <div class="home-hub__card-desc">AI 生成专业英文学习材料</div>
              <div class="home-hub__card-hint" id="home-explore-hint">
                输入任意法治主题，获取系统化学习内容
              </div>
            </div>
            <div class="home-hub__card-arrow">→</div>
          </a>
        </div>

        <!-- 学习概览 -->
        <div class="home-stats glass-panel" id="home-stats">
          <div class="home-stats__item">
            <div class="home-stats__value" id="home-stat-articles">—</div>
            <div class="home-stats__label">已阅读文章</div>
          </div>
          <div class="home-stats__item">
            <div class="home-stats__value" id="home-stat-vocab">—</div>
            <div class="home-stats__label">积累生词</div>
          </div>
          <div class="home-stats__item">
            <div class="home-stats__value" id="home-stat-papers">—</div>
            <div class="home-stats__label">收藏论文</div>
          </div>
        </div>

        <!-- 快捷入口 -->
        <div class="home-quick-links">
          <a class="home-quick-link" href="#/vocab">
            <span class="home-quick-link__icon">📖</span>
            <span>生词本</span>
          </a>
          <a class="home-quick-link" href="#/research/generate">
            <span class="home-quick-link__icon">✨</span>
            <span>AI 文章解读</span>
          </a>
          <a class="home-quick-link" href="#/research/tracker">
            <span class="home-quick-link__icon">🔍</span>
            <span>主题追踪</span>
          </a>
          <a class="home-quick-link" href="#/settings/profile">
            <span class="home-quick-link__icon">⚙️</span>
            <span>画像设置</span>
          </a>
        </div>
      </div>
    </section>
  `;
}

export function initHome() {
  // Personalize greeting from stored profile
  const user = JSON.parse(localStorage.getItem('zaiyi_user') || '{}');
  const profile = JSON.parse(localStorage.getItem('zaiyi_profile') || '{}');

  const usernameEl = document.getElementById('home-username');
  if (usernameEl && user.username) {
    usernameEl.textContent = user.username;
  }

  // Show profile tags
  const tagsEl = document.getElementById('home-profile-tags');
  if (tagsEl && profile.subject_field) {
    const FIELD_MAP = { law: '法学', finance: '金融', cs: '计算机', medicine: '医学', engineering: '工程', humanities: '人文' };
    const LEVEL_MAP = { cet4: 'CET-4', cet6: 'CET-6', ielts5: '雅思5-6', ielts7: '雅思7+', native: '接近母语' };
    const tags = [];
    if (profile.subject_field) tags.push(FIELD_MAP[profile.subject_field] || profile.subject_field);
    if (profile.specialty) tags.push(profile.specialty);
    if (profile.eng_level) tags.push(LEVEL_MAP[profile.eng_level] || profile.eng_level);
    if (tags.length) {
      tagsEl.innerHTML = tags.map(t => `<span class="hero__tag">${t}</span>`).join('');
    }
  }

  // Load simple stats (best-effort, no blocking)
  import('./api.js').then(({ fetchAPIGet }) => {
    fetchAPIGet('/vocab?limit=1').then(data => {
      const el = document.getElementById('home-stat-vocab');
      if (el && data) el.textContent = data.total ?? (Array.isArray(data) ? data.length : '—');
    }).catch(() => {});
    fetchAPIGet('/papers?limit=1').then(data => {
      const el = document.getElementById('home-stat-papers');
      if (el && data && typeof data.total === 'number') el.textContent = data.total;
    }).catch(() => {});
  });
}


// ============ TOPIC EXPLORER PAGE ============

export function renderTopicExplorer() {
  return `
    <div class="container">
      <div class="page-header">
        <div class="page-header__badge">
          <span class="nav-dot" style="background:var(--topic)"></span>
          模块 01 · 主题探索
        </div>
        <h1 class="page-header__title">主题探索</h1>
        <p class="page-header__subtitle">
          输入任意涉外法治主题，AI 为你生成系统化的英文学习材料与术语解析
        </p>
      </div>

      <!-- FIX 5: Topic keywords, domains, tags moved to main page -->
      <div class="glass-panel" style="padding:24px;border-radius:20px;margin-bottom:20px;">
        <div class="form-group" style="margin-bottom:16px;">
          <label class="form-label">主题关键词 *</label>
          <input type="text" class="form-input" id="topic-input"
            placeholder="例如：international arbitration, treaty law, cross-border data..."
            value="international arbitration">
        </div>

        <div class="form-group" style="margin-bottom:16px;">
          <label class="form-label">专业方向 (多选)</label>
          <div class="checkbox-group topic-domain-grid" id="topic-domain-checklist">
            <label class="checkbox-label"><input type="checkbox" value="international-law" checked><span></span> 国际法</label>
            <label class="checkbox-label"><input type="checkbox" value="commercial-law" checked><span></span> 商法</label>
            <label class="checkbox-label"><input type="checkbox" value="constitutional-law"><span></span> 宪法学</label>
            <label class="checkbox-label"><input type="checkbox" value="criminal-law"><span></span> 刑法学</label>
            <label class="checkbox-label"><input type="checkbox" value="ip-law"><span></span> 知识产权法</label>
          </div>
          <div class="topic-domain-actions">
            <input type="text" class="form-input custom-domain-field" id="topic-custom-domain" placeholder="在此输入自定义方向并回车...">
            <button class="btn btn--secondary topic-domain-add-btn" id="btn-add-domain">添加方向</button>
          </div>
        </div>

        <div class="form-group" style="margin-bottom:16px;">
          <label class="form-label">标签（可选，回车添加）</label>
          <div class="tags-input" id="topic-tags-input">
            <span class="tag">international-law <span class="tag__remove" data-tag="international-law">×</span></span>
            <span class="tag">dispute-resolution <span class="tag__remove" data-tag="dispute-resolution">×</span></span>
            <input type="text" class="tags-input__input" placeholder="输入标签..." id="topic-tag-field">
          </div>
        </div>
      </div>

      <!-- FIX 6: Summary bar with current params and generate button -->
      <div class="glass-panel" id="topic-summary-bar" style="padding:16px 24px;border-radius:16px;margin-bottom:20px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;">
        <div style="display:flex;align-items:center;gap:16px;flex-wrap:wrap;flex:1;">
          <div style="display:flex;align-items:center;gap:6px;">
            <span style="color:var(--text-muted);font-size:0.8rem;">方向：</span>
            <span id="summary-domains" style="color:var(--text-primary);font-size:0.85rem;font-weight:500;">国际法, 商法</span>
          </div>
          <div style="display:flex;align-items:center;gap:6px;">
            <span style="color:var(--text-muted);font-size:0.8rem;">等级：</span>
            <span id="summary-level" style="color:var(--text-primary);font-size:0.85rem;">初级</span>
          </div>
          <div style="display:flex;align-items:center;gap:6px;">
            <span style="color:var(--text-muted);font-size:0.8rem;">风格：</span>
            <span id="summary-style" style="color:var(--text-primary);font-size:0.85rem;">经济学人</span>
          </div>
          <div style="display:flex;align-items:center;gap:6px;">
            <span style="color:var(--text-muted);font-size:0.8rem;">长度：</span>
            <span id="summary-length" style="color:var(--text-primary);font-size:0.85rem;">250 词</span>
          </div>
        </div>
        <div style="display:flex;gap:8px;flex-shrink:0;">
          <button class="btn btn--secondary btn--sm" id="topic-reopen-config">调整参数</button>
          <button class="btn btn--topic" id="topic-submit-main" style="padding:8px 20px;">生成学习内容</button>
        </div>
      </div>

      <button class="topic-config-fab is-visible" id="topic-config-fab" title="打开参数配置">
        ⚙️
      </button>

      <!-- FIX 4: Config overlay starts minimized (no is-open) -->
      <!-- FIX 5: Config wizard only contains Step 2 (parameters) -->
      <div class="topic-config-overlay" id="topic-config-overlay">
        <div class="topic-config-dialog">
          <div class="topic-config-dialog__header">
            <div>
              <div class="topic-config-dialog__title">参数配置</div>
              <div class="topic-config-dialog__hint">调整生成参数后点击生成</div>
            </div>
            <button class="btn btn--secondary btn--sm" id="topic-config-minimize">最小化</button>
          </div>
          <div class="topic-config-dialog__body">
            <div class="topic-step-pane is-active" id="topic-step-2">
              <div class="form-row">
                <div class="form-group">
                  <label class="form-label">难度等级</label>
                  <select class="form-select" id="topic-level">
                    <option value="beginner" selected>初级 Beginner</option>
                    <option value="intermediate">中级 Intermediate</option>
                    <option value="advanced">高级 Advanced</option>
                  </select>
                </div>
                <div class="form-group">
                  <label class="form-label">文章风格 (生成模版)</label>
                  <select class="form-select" id="topic-style">
                    <option value="economist" selected>The Economist (经济学人)</option>
                    <option value="guardian">The Guardian (卫报)</option>
                    <option value="ft">Financial Times (金融时报)</option>
                    <option value="academic">Academic (学术期刊)</option>
                    <option value="plain_english">Plain English (简明日常)</option>
                  </select>
                </div>
              </div>

              <div class="form-group">
                <label class="form-label">文章长度 (Words): <span id="label-len">250</span></label>
                <input type="range" id="topic-len-slider" min="100" max="1000" step="50" value="250" style="width: 100%;">
              </div>

              <div class="form-row">
                <div class="form-group">
                  <label class="form-label">需复习的生词量: <span id="label-db-words">4</span></label>
                  <input type="range" id="topic-db-words-slider" min="0" max="20" step="1" value="4" style="width: 100%;">
                </div>
                <div class="form-group">
                  <label class="form-label">引入新词数量: <span id="label-new-words">4</span></label>
                  <input type="range" id="topic-new-words-slider" min="0" max="15" step="1" value="4" style="width: 100%;">
                </div>
              </div>

              <div class="topic-step-actions">
                <button class="btn btn--topic btn--full btn--lg" id="topic-submit">
                  生成学习内容
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Tab Switcher -->
      <div class="topic-tabs" style="display:flex;gap:4px;margin-bottom:16px;background:var(--glass-bg);border:var(--glass-border);border-radius:var(--r-pill);padding:4px;width:fit-content;">
        <button class="topic-tab is-active" id="tab-generate" style="padding:8px 20px;border:none;border-radius:var(--r-pill);font-size:13px;font-weight:600;cursor:pointer;transition:all 150ms ease;background:var(--grad-topic);color:#fff;">📝 生成结果</button>
        <button class="topic-tab" id="tab-history" style="padding:8px 20px;border:none;border-radius:var(--r-pill);font-size:13px;font-weight:600;cursor:pointer;transition:all 150ms ease;background:transparent;color:var(--text-secondary);">📚 历史文章</button>
      </div>

      <!-- Generate Result Panel -->
      <div id="topic-generate-panel">
        <div class="module-page">
          <div class="module-page__layout module-page__layout--single">
            <div class="panel panel--topic-result">
              <div class="panel__header">
                <div class="panel__title">
                  <span class="panel__title-icon" style="background:var(--topic)"></span>
                  学习内容
                </div>
                <div style="display:flex; align-items:center; gap:8px;">
                  <span style="font-size:12px;color:var(--text-muted)" id="topic-confidence"></span>
                </div>
              </div>
              <div class="panel__body">
                <div id="topic-result">
                  <div class="result-empty">
                    <div class="result-empty__icon">🔍</div>
                    <div class="result-empty__text">
                      输入主题关键词并点击生成，<br>AI 将为你创建专属学习材料
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- History Panel -->
      <div id="topic-history-panel" style="display:none;">
        <div class="module-page">
          <div class="module-page__layout module-page__layout--single">
            <div class="panel">
              <div class="panel__header">
                <div class="panel__title">
                  <span class="panel__title-icon" style="background:var(--topic)"></span>
                  历史文章
                </div>
                <button class="btn btn--sm btn--ghost" id="btn-refresh-history">🔄 刷新</button>
              </div>
              <div class="panel__body">
                <div id="history-list">
                  <div class="result-empty">
                    <div class="result-empty__icon">📚</div>
                    <div class="result-empty__text">加载中...</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  `;
}

export function initTopicExplorer() {
  const configOverlay = document.getElementById('topic-config-overlay');
  const configFab = document.getElementById('topic-config-fab');
  const minimizeConfigBtn = document.getElementById('topic-config-minimize');
  const reopenConfigBtn = document.getElementById('topic-reopen-config');
  const submitBtn = document.getElementById('topic-submit');
  const submitMainBtn = document.getElementById('topic-submit-main');
  const resultArea = document.getElementById('topic-result');
  const tagField = document.getElementById('topic-tag-field');
  const tagsInput = document.getElementById('topic-tags-input');
  const topicInput = document.getElementById('topic-input');
  let lastTopicPayload = null;
  let lastTopicLabel = '';

  // Style label map for summary bar
  const styleLabelMap = {
    'economist': '经济学人', 'guardian': '卫报', 'ft': '金融时报',
    'academic': '学术期刊', 'plain_english': '简明日常'
  };
  const levelLabelMap = {
    'beginner': '初级', 'intermediate': '中级', 'advanced': '高级'
  };

  // FIX 6: Update summary bar whenever params change
  const updateSummaryBar = () => {
    const domainCheckboxes = document.querySelectorAll('#topic-domain-checklist input:checked');
    const domains = Array.from(domainCheckboxes).map(cb => cb.parentElement.textContent.trim());
    const level = document.getElementById('topic-level').value;
    const style = document.getElementById('topic-style').value;
    const length = document.getElementById('topic-len-slider').value;

    const domainsEl = document.getElementById('summary-domains');
    const levelEl = document.getElementById('summary-level');
    const styleEl = document.getElementById('summary-style');
    const lengthEl = document.getElementById('summary-length');

    if (domainsEl) domainsEl.textContent = domains.length ? domains.join(', ') : '未选择';
    if (levelEl) levelEl.textContent = levelLabelMap[level] || level;
    if (styleEl) styleEl.textContent = styleLabelMap[style] || style;
    if (lengthEl) lengthEl.textContent = `${length} 词`;
  };


  const openConfig = () => {
    configOverlay.classList.add('is-open');
    configFab.classList.remove('is-visible');
  };

  const minimizeConfig = () => {
    configOverlay.classList.remove('is-open');
    configFab.classList.add('is-visible');
    updateSummaryBar();
  };

  const validateTopic = () => {
    const topic = topicInput.value.trim();
    if (!topic) {
      topicInput.style.borderColor = 'rgba(239,68,68,0.5)';
      topicInput.focus();
      return false;
    }
    topicInput.style.borderColor = '';
    return true;
  };

  topicInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      if (submitMainBtn) submitMainBtn.click();
    }
  });

  configFab.addEventListener('click', openConfig);
  reopenConfigBtn.addEventListener('click', openConfig);
  minimizeConfigBtn.addEventListener('click', minimizeConfig);
  configOverlay.addEventListener('click', (e) => {
    if (e.target === configOverlay) minimizeConfig();
  });
  const onEscape = (e) => {
    if (e.key === 'Escape' && configOverlay.classList.contains('is-open')) {
      minimizeConfig();
    }
  };
  document.addEventListener('keydown', onEscape);

  // Update summary bar when config changes
  ['topic-level', 'topic-style'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.addEventListener('change', updateSummaryBar);
  });
  document.getElementById('topic-domain-checklist').addEventListener('change', updateSummaryBar);

  // Tags input
  tagField.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && tagField.value.trim()) {
      e.preventDefault();
      const val = tagField.value.trim();
      const tag = document.createElement('span');
      tag.className = 'tag';
      tag.innerHTML = `${val} <span class="tag__remove" data-tag="${val}">×</span>`;
      tagsInput.insertBefore(tag, tagField);
      tagField.value = '';
    }
  });

  tagsInput.addEventListener('click', (e) => {
    if (e.target.classList.contains('tag__remove')) {
      e.target.parentElement.remove();
    }
    tagField.focus();
  });

  // Custom Domain Adding Logic
  const btnAddDomain = document.getElementById('btn-add-domain');
  const customDomainInput = document.getElementById('topic-custom-domain');
  const checklist = document.getElementById('topic-domain-checklist');
  
  const addDomain = (e) => {
    e.preventDefault();
    const val = customDomainInput.value.trim();
    if (val) {
        // Build the checkbox block manually
        const rawLabel = document.createElement('label');
        rawLabel.className = 'checkbox-label';
        
        const cb = document.createElement('input');
        cb.type = 'checkbox';
        cb.value = val.toLowerCase().replace(/\s+/g, '-');
        cb.checked = true;
        
        const span = document.createElement('span'); // The actual visual box designed in css
        const textNode = document.createTextNode(' ' + val);
        
        rawLabel.appendChild(cb);
        rawLabel.appendChild(span);
        rawLabel.appendChild(textNode);
        
        checklist.appendChild(rawLabel);
        customDomainInput.value = '';
    }
  };
  
  btnAddDomain.addEventListener('click', addDomain);
  customDomainInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') addDomain(e);
  });

  // Slider label bindings
  ['len', 'db-words', 'new-words'].forEach(id => {
      document.getElementById(`topic-${id}-slider`).addEventListener('input', (e) => {
          document.getElementById(`label-${id}`).textContent = e.target.value;
          updateSummaryBar();
      });
  });

  const runTopicGeneration = async (payload, topicLabel) => {
    if (!payload) return;

    submitBtn.disabled = true;
    if (submitMainBtn) submitMainBtn.disabled = true;
    minimizeConfigBtn.disabled = true;
    submitBtn.innerHTML = '<span class="spinner"></span> AI 正在生成...';
    if (submitMainBtn) submitMainBtn.innerHTML = '<span class="spinner"></span> 生成中...';

    resultArea.innerHTML = `
      <div class="loading-state">
        <div class="loading-dots"><span></span><span></span><span></span></div>
        <div class="loading-text">正在为「${topicLabel}」生成学习内容...</div>
        <div id="topic-gen-progress" style="margin-top:12px;max-width:400px;margin-left:auto;margin-right:auto;"></div>
      </div>
    `;

    const progressEl = document.getElementById('topic-gen-progress');
    const progress = startSimulatedProgress(progressEl, '正在调用 AI 生成...');

    const taskId = `topic-${Date.now()}`;
    const tm = getTaskManager();
    tm.addTask(taskId, `生成: ${topicLabel}`, 'topic');
    tm.updateTask(taskId, 10, '调用 AI 生成中...');

    try {
      const data = await generateTopic(payload);
      tm.updateTask(taskId, 100, '生成完成 ✓');
      progress.complete();

      document.getElementById('topic-confidence').textContent = confidenceLabel(data.confidence_hint);
      minimizeConfig();

      // Build new words section if available
      const newWordsHtml = (data.new_words && data.new_words.length) ? `
          <div class="gen-article__section">
            <div class="gen-article__section-title" style="display:flex;align-items:center;justify-content:space-between;">
              <span>🆕 新词 (${data.new_words.length})</span>
              <button class="btn btn--sm btn--ghost" id="btn-batch-add-vocab">📥 批量加入生词本</button>
            </div>
            <div class="terms-grid">
              ${data.new_words.map(w => `
                <div class="term-card" data-word="${escapeHtml(w.word)}" data-def="${escapeHtml(w.definition_zh)}" data-sentence="${escapeHtml(w.in_sentence)}" onclick="this.classList.toggle('expanded')">
                  <div class="term-card__en">${escapeHtml(w.word)}</div>
                  <div class="term-card__zh">${escapeHtml(w.definition_zh)}</div>
                  <div class="term-card__example">
                    <strong>Example:</strong> ${escapeHtml(w.in_sentence)}
                  </div>
                </div>
              `).join('')}
            </div>
          </div>
      ` : '';

      resultArea.innerHTML = `
        <div class="gen-article">
          <div style="display:flex;justify-content:flex-end;margin-bottom:10px;">
            <button class="btn btn--ghost btn--sm" id="btn-topic-regenerate">🔄 重新生成</button>
          </div>
          <div class="gen-article__section">
            <div class="gen-article__section-title">📄 英文学习文章</div>
            <div class="gen-article__text">${sanitizeHtml(data.result_text)}</div>
          </div>

          ${data.translation_text ? `
          <div class="gen-article__section">
            <div class="gen-article__section-title" style="display:flex;align-items:center;justify-content:space-between;">
              <span>🀄 逐段中文翻译</span>
              <button class="btn btn--sm btn--ghost" onclick="this.closest('.gen-article__section').querySelector('.gen-article__translation').classList.toggle('collapsed')">
                收起/展开
              </button>
            </div>
            <div class="gen-article__translation" style="background:rgba(255,255,255,0.03);border-radius:8px;padding:16px;margin-top:8px;line-height:1.8;color:#94a3b8;font-size:0.95em;">
              ${sanitizeHtml(data.translation_text)}
            </div>
          </div>
          ` : ''}

          <div class="gen-article__section">
            <div class="gen-article__section-title">📚 关键术语 (${data.terms.length})</div>
            <div class="terms-grid">
              ${data.terms.map(t => `
                <div class="term-card" onclick="this.classList.toggle('expanded')">
                  <div class="term-card__en">${escapeHtml(t.term)}</div>
                  <div class="term-card__zh">${escapeHtml(t.zh)}</div>
                  <div class="term-card__example">
                    <strong>Example:</strong> ${escapeHtml(t.example)}
                  </div>
                </div>
              `).join('')}
            </div>
          </div>

          ${newWordsHtml}

          <div class="notes-section">
            <div class="notes-section__title">💡 核心概念说明</div>
            ${data.notes.map(n => `<div class="notes-section__item">${escapeHtml(n)}</div>`).join('')}
          </div>

          <div class="feedback">
            <span class="feedback__label">结果是否有帮助？</span>
            <div class="feedback__btns">
              <button class="feedback__btn" onclick="submitFeedback(this, 'Topic_Explorer', 'Positive')">👍 有帮助</button>
              <button class="feedback__btn" onclick="submitFeedback(this, 'Topic_Explorer', 'Negative')">👎 需改进</button>
            </div>
          </div>

          <div class="cross-cta">
            <div class="cross-cta__text">
              <strong>继续学习：</strong>基于本文内容进入翻译训练
            </div>
            <button class="btn btn--translation" onclick="jumpToTranslation(this)">
              进入 Translation Studio →
            </button>
          </div>
        </div>
      `;
      const regenBtn = document.getElementById('btn-topic-regenerate');
      if (regenBtn) regenBtn.addEventListener('click', () => runTopicGeneration(lastTopicPayload, lastTopicLabel));

      // Batch add new words to vocabulary
      const batchBtn = document.getElementById('btn-batch-add-vocab');
      if (batchBtn) {
        batchBtn.addEventListener('click', async () => {
          const cards = resultArea.querySelectorAll('.term-card[data-word]');
          if (!cards.length) { showToast('没有可添加的新词', 'warning'); return; }
          batchBtn.disabled = true;
          batchBtn.textContent = '添加中...';
          let added = 0;
          for (const card of cards) {
            try {
              await createVocabItem({
                word: card.dataset.word,
                definition_zh: card.dataset.def,
                example_sentence: card.dataset.sentence,
                domain: 'topic_generation',
                source: 'topic_explorer'
              });
              added++;
            } catch (_e) { /* skip duplicates */ }
          }
          batchBtn.textContent = `✓ 已添加 ${added} 词`;
          showToast(`已将 ${added} 个新词加入生词本`, 'success');
        });
      }
    } catch (err) {
      progress.stop();
      resultArea.innerHTML = `
        <div class="result-empty">
          <div class="result-empty__icon">❌</div>
          <div class="result-empty__text">生成失败，请重试<br><span style="color:#ef4444;">${err.message}</span><br><br><span style="font-size:0.85rem;color:var(--text-muted);">提示：请检查 LLM 服务配置是否正确，或稍后重试。</span></div>
        </div>
      `;
      tm.removeTask(taskId);
    }

    minimizeConfigBtn.disabled = false;
    submitBtn.innerHTML = '生成学习内容';
    submitBtn.disabled = false;
    if (submitMainBtn) {
      submitMainBtn.innerHTML = '生成学习内容';
      submitMainBtn.disabled = false;
    }
  };

  const doSubmit = async () => {
    const topic = topicInput.value.trim();
    if (!validateTopic()) return;

    const level = document.getElementById('topic-level').value;
    const domainCheckboxes = document.querySelectorAll('#topic-domain-checklist input:checked');
    const domains = Array.from(domainCheckboxes).map(cb => cb.parentElement.textContent.trim());
    const style = document.getElementById('topic-style').value;
    const length = parseInt(document.getElementById('topic-len-slider').value, 10);
    const dbWords = parseInt(document.getElementById('topic-db-words-slider').value, 10);
    const newWords = parseInt(document.getElementById('topic-new-words-slider').value, 10);

    lastTopicPayload = {
      topic,
      level,
      domains: domains.length ? domains : ['General'],
      style,
      length,
      dbWords,
      newWords
    };
    lastTopicLabel = topic;
    minimizeConfig();
    await runTopicGeneration(lastTopicPayload, lastTopicLabel);
  };

  submitBtn.addEventListener('click', doSubmit);
  if (submitMainBtn) submitMainBtn.addEventListener('click', doSubmit);

  // FIX 4: Config starts minimized, FAB is visible by default
  updateSummaryBar();

  // ══════════════════════════════════════════════
  // HISTORY TAB LOGIC
  // ══════════════════════════════════════════════
  const tabGenerate = document.getElementById('tab-generate');
  const tabHistory = document.getElementById('tab-history');
  const generatePanel = document.getElementById('topic-generate-panel');
  const historyPanel = document.getElementById('topic-history-panel');
  const historyList = document.getElementById('history-list');
  const refreshHistoryBtn = document.getElementById('btn-refresh-history');

  const LEVEL_MAP = { beginner: '初级', intermediate: '中级', advanced: '高级' };
  const STYLE_MAP = { economist: '经济学人', guardian: '卫报', ft: '金融时报', academic: '学术期刊', plain_english: '简明日常' };

  const switchTab = (tab) => {
    if (tab === 'generate') {
      tabGenerate.style.background = 'var(--grad-topic)';
      tabGenerate.style.color = '#fff';
      tabGenerate.classList.add('is-active');
      tabHistory.style.background = 'transparent';
      tabHistory.style.color = 'var(--text-secondary)';
      tabHistory.classList.remove('is-active');
      generatePanel.style.display = '';
      historyPanel.style.display = 'none';
    } else {
      tabHistory.style.background = 'var(--grad-topic)';
      tabHistory.style.color = '#fff';
      tabHistory.classList.add('is-active');
      tabGenerate.style.background = 'transparent';
      tabGenerate.style.color = 'var(--text-secondary)';
      tabGenerate.classList.remove('is-active');
      generatePanel.style.display = 'none';
      historyPanel.style.display = '';
      loadHistory();
    }
  };

  tabGenerate.addEventListener('click', () => switchTab('generate'));
  tabHistory.addEventListener('click', () => switchTab('history'));
  if (refreshHistoryBtn) refreshHistoryBtn.addEventListener('click', () => loadHistory());

  let historyPage = 1;

  async function loadHistory(page = 1) {
    historyPage = page;
    historyList.innerHTML = `<div class="result-empty"><div class="loading-dots"><span></span><span></span><span></span></div><div class="loading-text">加载历史文章...</div></div>`;
    try {
      const data = await getArticleHistory(page, 10);
      if (!data.items || data.items.length === 0) {
        historyList.innerHTML = `<div class="result-empty"><div class="result-empty__icon">📚</div><div class="result-empty__text">暂无历史文章<br>生成一篇文章后会自动保存在这里</div></div>`;
        return;
      }
      let html = '<div class="history-cards">';
      for (const item of data.items) {
        const date = item.created_at ? new Date(item.created_at).toLocaleString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : '';
        const domains = (item.domains || []).join(', ');
        const preview = (item.preview || '').replace(/<[^>]+>/g, '').substring(0, 120);
        html += `
          <div class="history-card" data-id="${escapeHtml(item.id)}">
            <div class="history-card__header">
              <div class="history-card__topic">${escapeHtml(item.topic)}</div>
              <div class="history-card__date">${date}</div>
            </div>
            <div class="history-card__meta">
              <span class="history-card__tag">${LEVEL_MAP[item.level] || item.level}</span>
              <span class="history-card__tag">${STYLE_MAP[item.style] || item.style}</span>
              <span class="history-card__tag">${item.article_length || '?'} 词</span>
              ${domains ? `<span class="history-card__tag">${escapeHtml(domains)}</span>` : ''}
            </div>
            <div class="history-card__preview">${escapeHtml(preview)}...</div>
            <div class="history-card__actions">
              <button class="btn btn--sm btn--topic history-view-btn" data-id="${item.id}">📖 查看全文</button>
              <button class="btn btn--sm btn--ghost history-export-btn" data-id="${item.id}">📥 下载 Word</button>
              <button class="btn btn--sm btn--ghost history-delete-btn" data-id="${item.id}" style="color:#ef4444;">🗑️ 删除</button>
            </div>
            <div class="history-card__detail" id="detail-${item.id}" style="display:none;"></div>
          </div>
        `;
      }
      html += '</div>';

      // Pagination
      const totalPages = Math.ceil(data.total / data.size);
      if (totalPages > 1) {
        html += `<div style="display:flex;justify-content:center;gap:8px;margin-top:16px;">`;
        for (let p = 1; p <= totalPages; p++) {
          html += `<button class="btn btn--sm ${p === page ? 'btn--topic' : 'btn--ghost'}" onclick="window.__loadHistory(${p})">${p}</button>`;
        }
        html += '</div>';
      }

      historyList.innerHTML = html;

      // Bind actions
      historyList.querySelectorAll('.history-view-btn').forEach(btn => {
        btn.addEventListener('click', () => viewArticleDetail(btn.dataset.id));
      });
      historyList.querySelectorAll('.history-export-btn').forEach(btn => {
        btn.addEventListener('click', () => downloadArticleWord(btn.dataset.id, btn));
      });
      historyList.querySelectorAll('.history-delete-btn').forEach(btn => {
        btn.addEventListener('click', () => deleteArticleItem(btn.dataset.id));
      });
    } catch (err) {
      historyList.innerHTML = `<div class="result-empty"><div class="result-empty__icon">❌</div><div class="result-empty__text">加载失败：${err.message}</div></div>`;
    }
  }

  window.__loadHistory = loadHistory;

  async function viewArticleDetail(id) {
    const detailEl = document.getElementById(`detail-${id}`);
    if (!detailEl) return;
    if (detailEl.style.display !== 'none') {
      detailEl.style.display = 'none';
      return;
    }
    detailEl.innerHTML = `<div style="text-align:center;padding:20px;"><div class="loading-dots"><span></span><span></span><span></span></div></div>`;
    detailEl.style.display = 'block';
    try {
      const data = await getArticleDetail(id);
      const newWordsHtml = (data.new_words && data.new_words.length) ? `
        <div class="gen-article__section">
          <div class="gen-article__section-title">🆕 新词 (${data.new_words.length})</div>
          <div class="terms-grid">
            ${data.new_words.map(w => `
              <div class="term-card" onclick="this.classList.toggle('expanded')">
                <div class="term-card__en">${escapeHtml(w.word)}</div>
                <div class="term-card__zh">${escapeHtml(w.definition_zh)}</div>
                <div class="term-card__example"><strong>Example:</strong> ${escapeHtml(w.in_sentence)}</div>
              </div>
            `).join('')}
          </div>
        </div>
      ` : '';

      detailEl.innerHTML = `
        <div class="gen-article" style="margin-top:16px;border-top:1px solid rgba(0,0,0,0.06);padding-top:16px;">
          <div class="gen-article__section">
            <div class="gen-article__section-title">📄 英文学习文章</div>
            <div class="gen-article__text">${sanitizeHtml(data.result_text)}</div>
          </div>
          ${data.translation_text ? `
          <div class="gen-article__section">
            <div class="gen-article__section-title">🀄 逐段中文翻译</div>
            <div class="gen-article__translation" style="background:rgba(255,255,255,0.03);border-radius:8px;padding:16px;margin-top:8px;line-height:1.8;color:#94a3b8;font-size:0.95em;">
              ${sanitizeHtml(data.translation_text)}
            </div>
          </div>
          ` : ''}
          <div class="gen-article__section">
            <div class="gen-article__section-title">📚 关键术语 (${data.terms.length})</div>
            <div class="terms-grid">
              ${data.terms.map(t => `
                <div class="term-card" onclick="this.classList.toggle('expanded')">
                  <div class="term-card__en">${escapeHtml(t.term)}</div>
                  <div class="term-card__zh">${escapeHtml(t.zh)}</div>
                  <div class="term-card__example"><strong>Example:</strong> ${escapeHtml(t.example)}</div>
                </div>
              `).join('')}
            </div>
          </div>
          ${newWordsHtml}
          ${data.notes && data.notes.length ? `
          <div class="notes-section">
            <div class="notes-section__title">💡 核心概念说明</div>
            ${data.notes.map(n => `<div class="notes-section__item">${escapeHtml(n)}</div>`).join('')}
          </div>
          ` : ''}
        </div>
      `;
    } catch (err) {
      detailEl.innerHTML = `<div style="color:#ef4444;padding:12px;">加载失败：${err.message}</div>`;
    }
  }

  async function downloadArticleWord(id, btn) {
    const origText = btn.textContent;
    btn.disabled = true;
    btn.textContent = '⏳ 导出中...';
    try {
      const blob = await exportArticleWord(id);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `article_${id.substring(0, 8)}.docx`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
      btn.textContent = '✅ 已下载';
      setTimeout(() => { btn.textContent = origText; btn.disabled = false; }, 2000);
    } catch (err) {
      btn.textContent = '❌ 失败';
      setTimeout(() => { btn.textContent = origText; btn.disabled = false; }, 2000);
      if (typeof showToast === 'function') showToast('导出失败：' + err.message, 'error');
    }
  }

  async function deleteArticleItem(id) {
    if (!confirm('确定删除这篇历史文章？')) return;
    try {
      await deleteArticle(id);
      if (typeof showToast === 'function') showToast('已删除', 'success');
      loadHistory(historyPage);
    } catch (err) {
      if (typeof showToast === 'function') showToast('删除失败：' + err.message, 'error');
    }
  }
}

// Global handoff function
window.jumpToTranslation = function(btnElement) {
  // Find the generated text in the same result area
  const articleBox = btnElement.closest('#topic-result').querySelector('.gen-article__text');
  if (articleBox) {
    const textToTranslate = articleBox.innerText || articleBox.textContent;
    sessionStorage.setItem('__xiao_tiao_handoff_text', textToTranslate.trim());
  }
  location.hash = '/translation';
};


// ============ ARTICLE LAB PAGE ============

export function renderArticleLab() {
  return `
    <div class="container">
      <div class="page-header">
        <div class="page-header__badge">
          <span class="nav-dot" style="background:var(--article)"></span>
          模块 02 · 文章实验室
        </div>
        <h1 class="page-header__title">文章解读</h1>
        <p class="page-header__subtitle">
          粘贴英文法律文本，AI 为你分段解读、提取术语、标注关键句
        </p>
      </div>

      <div class="module-page">
        <div class="module-page__layout">
          <!-- Input Panel -->
          <div class="panel">
            <div class="panel__header">
              <div class="panel__title">
                <span class="panel__title-icon" style="background:var(--article)"></span>
                输入文本
              </div>
              <span style="font-size:12px;color:var(--text-muted)" id="article-word-count">0 词</span>
            </div>
            <div class="panel__body">
              <div class="form-group">
                <label class="form-label">解读模式</label>
                <div class="segmented segmented--article" id="article-segmented">
                  <div class="segmented__slider" id="article-slider"></div>
                  <button class="segmented__btn active" id="mode-plain" onclick="selectMode('plain')">
                    📝 基础解读
                  </button>
                  <button class="segmented__btn" id="mode-legal" onclick="selectMode('legal_focus')">
                    ⚖️ 法律重点解读
                  </button>
                </div>
              </div>

              <div class="form-group">
                <label class="checkbox-label" style="display:flex; align-items:center; gap:8px;">
                  <input type="checkbox" id="article-grounded">
                  <span></span>
                  使用 Grounded 模式（RAG 检索证据）
                  <button type="button" id="grounded-info-toggle" style="background:none;border:1px solid var(--text-muted);color:var(--text-muted);border-radius:50%;width:20px;height:20px;font-size:12px;cursor:pointer;display:inline-flex;align-items:center;justify-content:center;margin-left:4px;flex-shrink:0;" title="了解 Grounded 模式">?</button>
                </label>
                <div id="grounded-info-panel" style="display:none;margin-top:10px;padding:16px;background:rgba(88,86,214,0.05);border:1px solid rgba(88,86,214,0.15);border-radius:12px;font-size:0.85rem;line-height:1.7;color:var(--text-secondary);">
                  <div style="font-weight:600;color:var(--text-primary);margin-bottom:8px;">Grounded 模式说明</div>
                  <p style="margin-bottom:8px;"><strong>什么是 Grounded 模式？</strong><br>
                  Grounded 模式使用 RAG（检索增强生成）技术，在生成解读前先从知识库中检索相关证据和案例，确保 AI 的分析有据可依。</p>
                  <p style="margin-bottom:8px;"><strong>RAG 检索如何工作？</strong><br>
                  系统会将你的输入文本与知识库中的 GitHub 案例、法律文献片段进行语义匹配，选取最相关的 top-K 条结果作为上下文，辅助 AI 生成更准确的解读。</p>
                  <p style="margin-bottom:8px;"><strong>提供什么类型的证据？</strong><br>
                  引用来源包括：GitHub 开源法律 AI 项目案例、相关法律条文片段、学术文献摘要等。每条引用会标注来源和相关度。</p>
                  <p style="margin:0;"><strong>使用技巧：</strong><br>
                  - 建议先通过"Research Finder"刷新并入库 GitHub 案例<br>
                  - 输入越具体的法律文本，检索效果越好<br>
                  - 适合用于需要引用佐证的学术分析场景</p>
                </div>
              </div>

              <div class="form-group">
                <div style="display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 8px;">
                  <label class="form-label" style="margin-bottom: 0;">英文法律文本 *</label>
                  <label class="btn btn--sm btn--ghost" style="padding: 4px 12px; font-size: 12px; cursor: pointer; border-radius: var(--r-pill);">
                    📄 上传 .txt / .md / .pdf
                    <input type="file" id="article-file-upload" accept=".txt,.md,.pdf,application/pdf,text/plain,text/markdown" style="display: none;">
                  </label>
                </div>
                <textarea class="form-input" id="article-input" rows="12"
                  placeholder="粘贴英文法律文本，如判例、条约、法规段落等...&#10;&#10;支持最多 3500 词">The doctrine of sovereign immunity has long been a cornerstone of international law. It provides that a sovereign state cannot be subjected to the jurisdiction of another state's courts without its consent. However, the absolute theory of sovereign immunity has gradually given way to the restrictive theory, which distinguishes between acts performed in the exercise of sovereign authority (acta jure imperii) and those of a commercial nature (acta jure gestionis). Under the restrictive approach, immunity is only granted for public acts, while commercial activities may be subject to the jurisdiction of foreign courts. This evolution reflects the changing nature of state participation in commercial transactions and the need to provide legal remedies for private parties dealing with state entities.</textarea>
              </div>

              <button class="btn btn--article btn--full btn--lg" id="article-submit">
                📖 开始解读
              </button>
            </div>
          </div>

          <!-- Output Panel -->
          <div class="panel">
            <div class="panel__header">
              <div class="panel__title">
                <span class="panel__title-icon" style="background:var(--article)"></span>
                解读结果
              </div>
            </div>
            <div class="panel__body">
              <div id="article-result">
                <div class="result-empty">
                  <div class="result-empty__icon">📖</div>
                  <div class="result-empty__text">
                    输入或粘贴英文法律文本，<br>AI 将为你进行智能解读
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  `;
}

// Expose mode selection globally — BUG-03: scoped selector
window.selectMode = function (mode) {
  window.__articleMode = mode;
  document.querySelectorAll('#article-segmented .segmented__btn').forEach(btn => btn.classList.remove('active'));
  if (mode === 'legal_focus') {
    document.getElementById('mode-legal').classList.add('active');
  } else {
    document.getElementById('mode-plain').classList.add('active');
  }
  
  if (window.__updateSegmentedSlider) {
    window.__updateSegmentedSlider('article-segmented');
  }
};

export function initArticleLab() {
  window.__articleMode = 'plain';

  const submitBtn = document.getElementById('article-submit');
  const resultArea = document.getElementById('article-result');
  const articleInput = document.getElementById('article-input');
  const wordCount = document.getElementById('article-word-count');
  const fileUpload = document.getElementById('article-file-upload');
  const groundedInput = document.getElementById('article-grounded');
  let lastArticlePayload = null;
  let lastArticleWords = 0;

  // FIX 7: Grounded mode info panel toggle
  const groundedInfoToggle = document.getElementById('grounded-info-toggle');
  const groundedInfoPanel = document.getElementById('grounded-info-panel');
  if (groundedInfoToggle && groundedInfoPanel) {
    groundedInfoToggle.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();
      const isOpen = groundedInfoPanel.style.display !== 'none';
      groundedInfoPanel.style.display = isOpen ? 'none' : 'block';
      groundedInfoToggle.textContent = isOpen ? '?' : '×';
    });
  }

  const extractTextFromPdfFile = async (file) => {
    const [pdfjsLib, workerUrlModule] = await Promise.all([
      import('pdfjs-dist'),
      import('pdfjs-dist/build/pdf.worker.mjs?url')
    ]);
    const pdfjsWorkerUrl = workerUrlModule.default;

    if (pdfjsLib.GlobalWorkerOptions.workerSrc !== pdfjsWorkerUrl) {
      pdfjsLib.GlobalWorkerOptions.workerSrc = pdfjsWorkerUrl;
    }

    const buffer = await file.arrayBuffer();
    const task = pdfjsLib.getDocument({ data: buffer });
    const pdf = await task.promise;
    const pageLimit = Math.min(pdf.numPages, 30);

    const chunks = [];
    for (let i = 1; i <= pageLimit; i++) {
      const page = await pdf.getPage(i);
      const text = await page.getTextContent();
      const line = text.items
        .map((item) => ('str' in item ? item.str : ''))
        .join(' ')
        .replace(/\s+/g, ' ')
        .trim();
      if (line) chunks.push(line);
    }
    return chunks.join('\n\n');
  };

  if (fileUpload) {
    fileUpload.addEventListener('change', async (e) => {
      const file = e.target.files[0];
      if (!file) return;
      const filename = (file.name || '').toLowerCase();
      try {
        if (filename.endsWith('.pdf')) {
          showToast('正在解析 PDF 文本...', 'info', 1500);
          const extracted = await extractTextFromPdfFile(file);
          if (!extracted.trim()) {
            throw new Error('未提取到文本，可能是扫描版 PDF');
          }
          articleInput.value = extracted;
          articleInput.dispatchEvent(new Event('input'));
          showToast('PDF 文本已导入，可直接解读', 'success');
        } else {
          const text = await file.text();
          articleInput.value = text;
          articleInput.dispatchEvent(new Event('input'));
        }
      } catch (err) {
        showToast(`文件解析失败：${err.message || '请重试'}`, 'error');
      } finally {
        e.target.value = '';
      }
    });
  }

  articleInput.addEventListener('input', () => {
    const words = articleInput.value.trim().split(/\s+/).filter(Boolean).length;
    wordCount.textContent = `${words} 词`;
    if (words > 3500) {
      wordCount.style.color = '#ef4444';
    } else {
      wordCount.style.color = 'var(--text-muted)';
    }
  });

  // Trigger initial count
  articleInput.dispatchEvent(new Event('input'));

  const runArticleAnalysis = async (payload, words) => {
    if (!payload) return;
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="spinner"></span> AI 正在解读...';

    resultArea.innerHTML = `
      <div class="loading-state">
        <div class="loading-dots"><span></span><span></span><span></span></div>
        <div class="loading-text">正在解读文本 (${words} 词)...</div>
        <div id="article-gen-progress" style="margin-top:12px;max-width:400px;margin-left:auto;margin-right:auto;"></div>
      </div>
    `;

    const articleProgressEl = document.getElementById('article-gen-progress');
    const articleProgress = startSimulatedProgress(articleProgressEl, '正在调用 AI 解读...');

    try {
      const data = await analyzeArticle(payload);
      articleProgress.complete();

      resultArea.innerHTML = `
        <div class="analysis-result">
          <div style="display:flex;justify-content:flex-end;margin-bottom:10px;">
            <button class="btn btn--ghost btn--sm" id="btn-article-regenerate">🔄 重新解读全文</button>
          </div>
          <div class="gen-article__section">
            <div class="gen-article__section-title">📝 分段解读</div>
            ${data.paragraphs.map((p, i) => `
              <div class="analysis-paragraph">
                <div class="analysis-paragraph__label analysis-paragraph__label--original">段落 ${i + 1} · 原文</div>
                <div class="analysis-paragraph__original">${escapeHtml(p.original)}</div>
                <div class="analysis-paragraph__label analysis-paragraph__label--explain">中文解读</div>
                <div class="analysis-paragraph__explanation">${escapeHtml(p.explanation)}</div>
                <div style="text-align: right; margin-top: 10px;">
                  <button class="btn btn--sm btn--ghost" onclick="window.retryParagraph(this)">
                    🔄 重新解读此段
                  </button>
                </div>
              </div>
            `).join('')}
          </div>

          <div class="gen-article__section">
            <div class="gen-article__section-title">📚 关键术语</div>
            <div class="terms-grid">
              ${data.terms.map(t => `
                <div class="term-card">
                  <div class="term-card__en">${escapeHtml(t.term)}</div>
                  <div class="term-card__zh">${escapeHtml(t.definition_zh)}</div>
                </div>
              `).join('')}
            </div>
          </div>

          ${data.key_sentences.length > 0 ? `
            <div class="gen-article__section">
              <div class="gen-article__section-title">⭐ 关键句 (${data.key_sentences.length})</div>
              <div class="key-sentences">
                ${data.key_sentences.map(s => `
                  <div class="key-sentence">
                    <div class="key-sentence__text">"${escapeHtml(s.text)}"</div>
                    <div class="key-sentence__reason">${escapeHtml(s.reason)}</div>
                  </div>
                `).join('')}
              </div>
            </div>
          ` : ''}

          <div class="feedback">
            <span class="feedback__label">解读结果是否有帮助？</span>
            <div class="feedback__btns">
              <button class="feedback__btn" onclick="submitFeedback(this, 'Article_Lab', 'Positive')">👍 有帮助</button>
              <button class="feedback__btn" onclick="submitFeedback(this, 'Article_Lab', 'Negative')">👎 需改进</button>
            </div>
          </div>

          <div class="cross-cta">
            <div class="cross-cta__text">
              <strong>继续学习：</strong>将本文内容进行翻译训练
            </div>
            <button class="btn btn--translation" onclick="location.hash='/translation'">
              进入 Translation Studio →
            </button>
          </div>
        </div>
      `;

      const regenBtn = document.getElementById('btn-article-regenerate');
      if (regenBtn) regenBtn.addEventListener('click', () => runArticleAnalysis(lastArticlePayload, lastArticleWords));
    } catch (err) {
      articleProgress.stop();
      resultArea.innerHTML = `
        <div class="result-empty">
          <div class="result-empty__icon">❌</div>
          <div class="result-empty__text">解读失败<br><span style="color:#ef4444;">${err.message}</span><br><br><span style="font-size:0.85rem;color:var(--text-muted);">提示：请检查网络连接或 LLM 服务配置。</span></div>
          <button class="btn btn--article btn--sm" id="btn-article-retry" style="margin-top:16px;">🔄 重新解读</button>
        </div>
      `;
      const retryBtn = document.getElementById('btn-article-retry');
      if (retryBtn) retryBtn.addEventListener('click', () => runArticleAnalysis(lastArticlePayload, lastArticleWords));
    }

    submitBtn.disabled = false;
    submitBtn.innerHTML = '📖 开始解读';
  };

  submitBtn.addEventListener('click', async () => {
    const text = articleInput.value.trim();
    if (!text) {
      articleInput.style.borderColor = 'rgba(239,68,68,0.5)';
      return;
    }

    const words = text.split(/\s+/).filter(Boolean).length;
    if (words > 3500) {
      showToast('文本超过 3500 词限制，请缩短输入或分段处理。', 'warning');
      return;
    }

    lastArticlePayload = {
      source_text: text,
      analysis_mode: window.__articleMode,
      target_lang: 'zh',
      grounded: Boolean(groundedInput && groundedInput.checked),
      top_k: 4
    };
    lastArticleWords = words;
    await runArticleAnalysis(lastArticlePayload, lastArticleWords);
  });
}

// Global Single Paragraph Retry Function
window.retryParagraph = async function(btn) {
  const container = btn.closest('.analysis-paragraph');
  const enText = container.querySelector('.analysis-paragraph__original').innerText;
  const zhEl = container.querySelector('.analysis-paragraph__explanation');
  
  btn.disabled = true;
  const originalBtnText = btn.innerHTML;
  btn.innerHTML = '<span class="spinner" style="width:12px;height:12px;border-width:2px;margin-right:6px"></span> 解读中...';
  if (zhEl) {
    zhEl.innerHTML = `<span style="color:var(--text-muted);">正在生成该段解读...</span><div id="para-retry-progress"></div>`;
  }

  const { startSimulatedProgress: startProgress } = await import('./utils/stream.js');
  const paraProgressEl = document.getElementById('para-retry-progress');
  const paraProgress = paraProgressEl ? startProgress(paraProgressEl, '') : null;

  try {
    const mode = window.__articleMode || 'plain';
    const { analyzeArticle } = await import('./api.js');
    const data = await analyzeArticle({ source_text: enText, analysis_mode: mode });
    if (paraProgress) paraProgress.complete();
    
    if (zhEl) {
      zhEl.innerText = data.paragraphs[0].explanation;
    }
    
    // Success flash highlight
    container.style.transition = 'background-color 0.4s ease';
    container.style.backgroundColor = 'rgba(52, 199, 89, 0.1)';
    setTimeout(() => {
        container.style.backgroundColor = '';
    }, 1000);
  } catch (err) {
    if (paraProgress) paraProgress.stop();
    showToast('段落重新解读失败：' + err.message, 'error');
  } finally {
    btn.disabled = false;
    btn.innerHTML = originalBtnText;
  }
};

// ============ TRANSLATION STUDIO PAGE ============

export function renderTranslationStudio() {
  return `
    <div class="container">
      <div class="page-header">
        <div class="page-header__badge">
          <span class="nav-dot" style="background:var(--translation)"></span>
          模块 03 · 翻译工作室
        </div>
        <h1 class="page-header__title">翻译训练</h1>
        <p class="page-header__subtitle">
          中英法律文本互译，获取三种风格翻译与专业表达建议
        </p>
      </div>

      <div class="module-page">
        <div class="module-page__layout">
          <!-- Input Panel -->
          <div class="panel">
            <div class="panel__header">
              <div class="panel__title">
                <span class="panel__title-icon" style="background:var(--translation)"></span>
                翻译输入
              </div>
            </div>
            <div class="panel__body">
              <div class="form-group">
                <label class="form-label">翻译方向</label>
                <div class="segmented segmented--translation" id="direction-segmented">
                  <div class="segmented__slider" id="direction-slider"></div>
                  <button class="segmented__btn active" id="dir-zh2en" onclick="setDirection('zh_to_en')">
                    中文 → 英文
                  </button>
                  <button class="segmented__btn" id="dir-en2zh" onclick="setDirection('en_to_zh')">
                    英文 → 中文
                  </button>
                </div>
              </div>

              <div class="form-group">
                <label class="form-label">源文本 *</label>
                <textarea class="form-input" id="translation-input" rows="8"
                  placeholder="输入需要翻译的法律文本...">跨境数据治理规则仍处于快速演化阶段。各国和各地区持续调整其监管框架，以应对数据跨国流动带来的挑战。</textarea>
              </div>

              <div class="form-group">
                <label class="form-label">你的翻译（可选，用于对照点评）</label>
                <textarea class="form-input" id="translation-user" rows="4"
                  placeholder="输入你自己的翻译，AI 将与生成结果进行对照..."></textarea>
              </div>

              <button class="btn btn--translation btn--full btn--lg" id="translation-submit">
                🌐 生成翻译
              </button>
            </div>
          </div>

          <!-- Output Panel -->
          <div class="panel">
            <div class="panel__header">
              <div class="panel__title">
                <span class="panel__title-icon" style="background:var(--translation)"></span>
                翻译结果
              </div>
              <span style="font-size:12px;color:var(--text-muted)" id="trans-confidence"></span>
            </div>
            <div class="panel__body">
              <div id="translation-result">
                <div class="result-empty">
                  <div class="result-empty__icon">🌐</div>
                  <div class="result-empty__text">
                    输入文本并点击生成，<br>获取三种风格的法律翻译
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  `;
}

// BUG-03: scoped selector — only clear buttons inside #direction-segmented
window.setDirection = function (dir) {
  window.__translationDirection = dir;
  document.querySelectorAll('#direction-segmented .segmented__btn').forEach(btn => btn.classList.remove('active'));
  if (dir === 'zh_to_en') {
    document.getElementById('dir-zh2en').classList.add('active');
  } else {
    document.getElementById('dir-en2zh').classList.add('active');
  }
  // Update slider position
  if (window.__updateSegmentedSlider) {
    window.__updateSegmentedSlider('direction-segmented');
  }
};

// CODE-02: pass button element explicitly to avoid stale global event
window.copyText = function (text, btn) {
  navigator.clipboard.writeText(text).then(() => {
    if (btn) {
      btn.textContent = '✓ 已复制';
      setTimeout(() => { btn.textContent = '复制'; }, 1500);
    }
  });
};

export function initTranslationStudio() {
  window.__translationDirection = 'zh_to_en';

  const transInput = document.getElementById('translation-input');
  let lastTranslationPayload = null;
  
  // Check for handoff text from Topic Explorer
  const handoffText = sessionStorage.getItem('__xiao_tiao_handoff_text');
  if (handoffText) {
    transInput.value = handoffText;
    // Optional: flash animation to show it was populated
    transInput.style.transition = 'box-shadow 0.3s ease, border-color 0.3s ease';
    transInput.style.borderColor = 'var(--translation)';
    transInput.style.boxShadow = '0 0 0 4px rgba(52, 199, 89, 0.15)';
    setTimeout(() => {
      transInput.style.borderColor = '';
      transInput.style.boxShadow = '';
    }, 1500);
    // Remove the item so it only happens once
    sessionStorage.removeItem('__xiao_tiao_handoff_text');
    
    // Automatically switch to EN -> ZH since topic generated is English
    window.setDirection('en_to_zh');
  }

  const submitBtn = document.getElementById('translation-submit');
  const resultArea = document.getElementById('translation-result');

  const runTranslationRequest = async (payload) => {
    if (!payload) return;
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="spinner"></span> AI 正在翻译...';

    resultArea.innerHTML = `
      <div class="loading-state">
        <div class="loading-dots"><span></span><span></span><span></span></div>
        <div class="loading-text">正在生成三种风格翻译...</div>
        <div id="trans-gen-progress" style="margin-top:12px;max-width:400px;margin-left:auto;margin-right:auto;"></div>
      </div>
    `;

    const transProgressEl = document.getElementById('trans-gen-progress');
    const transProgress = startSimulatedProgress(transProgressEl, '正在调用 AI 翻译...');

    try {
      const data = await runTranslation(payload);
      transProgress.complete();

      document.getElementById('trans-confidence').textContent = confidenceLabel(data.confidence_hint);

      // Store variant texts for safe copy via data attributes
      const variantsCopyData = data.variants.map(v => v.text);
      window.__translationVariants = variantsCopyData;

      resultArea.innerHTML = `
        <div class="translation-result">
          <div style="display:flex;justify-content:flex-end;margin-bottom:10px;">
            <button class="btn btn--ghost btn--sm" id="btn-translation-regenerate">🔄 重新生成翻译</button>
          </div>
          ${data.critique ? `
            <div class="gen-article__section" style="margin-bottom: 24px; background: rgba(52, 199, 89, 0.05); padding: 18px; border-radius: 12px; border: 1px solid rgba(52, 199, 89, 0.2);">
              <div class="gen-article__section-title" style="color: var(--translation); margin-bottom: 12px;">🤖 译文对照点评</div>
              <div style="margin-bottom: 12px; font-size: 14px;">
                <strong>评分：</strong> <span style="color: var(--translation); font-weight: bold;">${escapeHtml(data.critique.score)}</span><br>
                <div style="margin-top: 6px; color: var(--text-base);">${escapeHtml(data.critique.feedback)}</div>
              </div>
              ${data.critique.improvements.map(imp => `
                <div style="font-size: 13px; margin-bottom: 10px; padding-left: 12px; border-left: 2px solid var(--translation);">
                  <div style="text-decoration: line-through; color: var(--text-muted); margin-bottom: 2px;">${escapeHtml(imp.original)}</div>
                  <div style="color: var(--text-base);">👉 ${escapeHtml(imp.suggested)} <br><span style="color: var(--text-muted); font-size: 12px;">💡 ${escapeHtml(imp.reason)}</span></div>
                </div>
              `).join('')}
            </div>
          ` : ''}
          ${data.variants.map((v, idx) => `
            <div class="translation-variant translation-variant--${escapeHtml(v.style)}">
              <div class="translation-variant__label">
                ${v.style === 'literal' ? '📋' : v.style === 'legal' ? '⚖️' : '💬'} ${escapeHtml(v.label)}
              </div>
              <div class="translation-variant__text">${escapeHtml(v.text)}</div>
              <button class="translation-variant__copy" data-variant-idx="${idx}">复制</button>
              <div style="clear:both"></div>
            </div>
          `).join('')}

          <div class="gen-article__section" style="margin-top:20px">
            <div class="gen-article__section-title">📚 相关术语</div>
            <div class="terms-grid">
              ${data.terms.map(t => `
                <div class="term-card">
                  <div class="term-card__en">${escapeHtml(t.term)}</div>
                  <div class="term-card__zh">${escapeHtml(t.definition_zh)}</div>
                </div>
              `).join('')}
            </div>
          </div>

          <div class="notes-section">
            <div class="notes-section__title">💡 表达建议</div>
            ${data.notes.map(n => `<div class="notes-section__item">${escapeHtml(n)}</div>`).join('')}
          </div>

          ${data.common_errors && data.common_errors.length ? `
            <div class="notes-section" style="margin-top:12px;">
              <div class="notes-section__title">⚠️ 常见错误提示</div>
              ${data.common_errors.map(n => `<div class="notes-section__item">${escapeHtml(n)}</div>`).join('')}
            </div>
          ` : ''}

          <div class="feedback">
            <span class="feedback__label">翻译结果是否有帮助？</span>
            <div class="feedback__btns">
              <button class="feedback__btn" onclick="submitFeedback(this, 'Translation_Studio', 'Positive')">👍 有帮助</button>
              <button class="feedback__btn" onclick="submitFeedback(this, 'Translation_Studio', 'Negative')">👎 需改进</button>
            </div>
          </div>
        </div>
      `;

      // Bind copy buttons via data attributes (avoids XSS from inline template literals)
      resultArea.querySelectorAll('.translation-variant__copy[data-variant-idx]').forEach(btn => {
        btn.addEventListener('click', () => {
          const idx = parseInt(btn.dataset.variantIdx, 10);
          const text = (window.__translationVariants || [])[idx] || '';
          copyText(text, btn);
        });
      });
      const regenBtn = document.getElementById('btn-translation-regenerate');
      if (regenBtn) regenBtn.addEventListener('click', () => runTranslationRequest(lastTranslationPayload));
    } catch (err) {
      transProgress.stop();
      resultArea.innerHTML = `
        <div class="result-empty">
          <div class="result-empty__icon">❌</div>
          <div class="result-empty__text">翻译失败<br><span style="color:#ef4444;">${err.message}</span><br><br><span style="font-size:0.85rem;color:var(--text-muted);">提示：请检查网络连接或 LLM 服务配置。</span></div>
          <button class="btn btn--translation btn--sm" id="btn-translation-retry" style="margin-top:16px;">🔄 重新翻译</button>
        </div>
      `;
      const retryBtn = document.getElementById('btn-translation-retry');
      if (retryBtn) retryBtn.addEventListener('click', () => runTranslationRequest(lastTranslationPayload));
    }

    submitBtn.disabled = false;
    submitBtn.innerHTML = '🌐 开始翻译';
  };

  submitBtn.addEventListener('click', async () => {
    const text = document.getElementById('translation-input').value.trim();
    if (!text) {
      document.getElementById('translation-input').style.borderColor = 'rgba(239,68,68,0.5)';
      return;
    }

    if (text.length > 5000) {
      showToast('输入文本过长，请控制在 5000 字符以内。', 'warning');
      return;
    }

    const userTranslation = document.getElementById('translation-user').value.trim();
    lastTranslationPayload = {
      source_text: text,
      direction: window.__translationDirection,
      style: ['literal', 'legal', 'plain'],
      user_translation: userTranslation
    };

    await runTranslationRequest(lastTranslationPayload);
  });
}

// ============ RESEARCH FINDER PAGE ============

export function renderResearchPage() {
  return `
    <div class="container">
      <div class="page-header">
        <div class="page-header__badge">
          <span class="nav-dot" style="background:var(--research)"></span>
          模块 04 · 研究与检索
        </div>
        <h1 class="page-header__title">Research Finder</h1>
        <p class="page-header__subtitle">
          GitHub 相似案例检索 + RAG 入库 + Grounded 问答
        </p>
      </div>

      <div class="module-page">
        <div class="module-page__layout">
          <div class="panel">
            <div class="panel__header">
              <div class="panel__title">
                <span class="panel__title-icon" style="background:var(--research)"></span>
                数据刷新与索引
              </div>
            </div>
            <div class="panel__body">
              <div style="display:flex; gap:10px; flex-wrap: wrap; margin-bottom: 12px;">
                <button class="btn btn--research" id="research-refresh">刷新 GitHub 案例</button>
                <button class="btn btn--secondary" id="research-ingest">写入 RAG 索引</button>
              </div>
              <div id="research-status" class="notes-section__item">等待操作</div>

              <div class="gen-article__section" style="margin-top:16px;">
                <div class="gen-article__section-title">🧩 Grounded Q&A</div>
                <textarea class="form-input" id="rag-query-input" rows="5" placeholder="例如：在 legal ai assistant 场景里，FastAPI 方案常见技术栈是什么？"></textarea>
                <button class="btn btn--research btn--full" id="rag-query-submit" style="margin-top:12px;">检索并回答</button>
              </div>
            </div>
          </div>

          <div class="panel">
            <div class="panel__header">
              <div class="panel__title">
                <span class="panel__title-icon" style="background:var(--research)"></span>
                检索结果
              </div>
            </div>
            <div class="panel__body">
              <div class="gen-article__section">
                <div class="gen-article__section-title">📚 GitHub Cases</div>
                <div id="research-cases" class="notes-section__item">加载中...</div>
              </div>
              <div class="gen-article__section">
                <div class="gen-article__section-title">🏢 组织架构</div>
                <div id="research-org" class="notes-section__item">加载中...</div>
              </div>
              <div class="gen-article__section">
                <div class="gen-article__section-title">🧠 RAG 回答</div>
                <pre id="rag-answer" class="gen-article__text">尚未提问</pre>
                <div id="rag-citations" class="notes-section__item">暂无引用</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  `;
}

export function initResearchPage() {
  const statusEl = document.getElementById('research-status');
  const casesEl = document.getElementById('research-cases');
  const orgEl = document.getElementById('research-org');
  const answerEl = document.getElementById('rag-answer');
  const citationsEl = document.getElementById('rag-citations');

  async function loadBaseData() {
    try {
      const [casesData, orgData] = await Promise.all([
        getResearchGithubCases(20),
        getOrgUnits()
      ]);
      const cases = Array.isArray(casesData.items) ? casesData.items : [];
      const orgUnits = Array.isArray(orgData.items) ? orgData.items : [];

      if (cases.length === 0) {
        casesEl.innerHTML = '暂无案例，请点击“刷新 GitHub 案例”';
      } else {
        casesEl.innerHTML = cases.map((item) => `
          <div class="term-card" style="margin-bottom:10px;">
            <div class="term-card__en"><a href="${item.html_url}" target="_blank" rel="noreferrer">${item.full_name}</a></div>
            <div class="term-card__zh">⭐ ${item.stars || 0} · ${item.language || 'Unknown'}</div>
            <div class="term-card__example">${item.query || ''}</div>
          </div>
        `).join('');
      }

      if (orgUnits.length === 0) {
        orgEl.innerHTML = '暂无组织架构数据';
      } else {
        orgEl.innerHTML = orgUnits.map((unit) => `
          <div class="notes-section__item">
            <strong>${unit.unit_name}</strong> · ${unit.owner_role}<br>
            ${unit.responsibility}
          </div>
        `).join('');
      }
    } catch (err) {
      casesEl.innerHTML = `加载失败：${err.message}`;
      orgEl.innerHTML = `加载失败：${err.message}`;
    }
  }

  document.getElementById('research-refresh').addEventListener('click', async () => {
    statusEl.textContent = '正在刷新 GitHub 案例...';
    try {
      const result = await refreshResearchGithubCases();
      statusEl.textContent = `刷新完成：新增/更新 ${result.saved_total} 条`;
      await loadBaseData();
    } catch (err) {
      statusEl.textContent = `刷新失败：${err.message}`;
    }
  });

  document.getElementById('research-ingest').addEventListener('click', async () => {
    statusEl.textContent = '正在写入 RAG 索引...';
    try {
      const result = await ingestGithubCasesToRag(30);
      statusEl.textContent = `入库完成：docs=${result.ingested_documents}, chunks=${result.ingested_chunks}`;
    } catch (err) {
      statusEl.textContent = `入库失败：${err.message}`;
    }
  });

  document.getElementById('rag-query-submit').addEventListener('click', async () => {
    const query = document.getElementById('rag-query-input').value.trim();
    if (!query) {
      statusEl.textContent = '请输入问题';
      return;
    }
    statusEl.textContent = '正在检索并回答...';
    try {
      const result = await queryRag({ query, top_k: 5 });
      answerEl.textContent = result.answer || '无回答';
      const citations = Array.isArray(result.citations) ? result.citations : [];
      citationsEl.innerHTML = citations.length
        ? citations.map((c) => `<div class="notes-section__item">[${c.id}] ${c.title}${c.url ? ` · <a href="${c.url}" target="_blank" rel="noreferrer">${c.url}</a>` : ''}</div>`).join('')
        : '暂无引用';
      statusEl.textContent = '检索完成';
    } catch (err) {
      statusEl.textContent = `检索失败：${err.message}`;
    }
  });

  loadBaseData();
}

// Global Analytics Hook — submits feedback to backend
window.submitFeedback = async function(btn, moduleName, selection) {
  const container = btn.closest('.feedback__btns');
  container.querySelectorAll('.feedback__btn').forEach(b => b.classList.remove('selected'));
  btn.classList.add('selected');
  const payload = {
    module: moduleName,
    selection: selection,
    timestamp: new Date().toISOString()
  };
  console.log(`[Analytics] Event: feedback_submit`, payload);
  try {
    await fetchAPI('/feedback', payload, { retries: 0, timeoutMs: 5000 });
  } catch (_e) {
    // Feedback submission is non-critical, silently ignore failures
  }
};
