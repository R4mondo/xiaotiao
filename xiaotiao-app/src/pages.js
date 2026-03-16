// Page renderers for all views — Apple Liquid Glass v2
import {
  analyzeArticle,
  createVocabItem,
  generateTopic,
  runTranslation
} from './api.js';

// ============ Shared Layout — Liquid Glass ============
// Render layout shell is now handled centrally in index.html

// ============ HOME PAGE ============

export function renderHome() {
  return `
    <section class="hero">
      <div class="container">
        <div class="hero__content">
          <div class="hero__badge">
            ✨ 涉外法治英语学习平台 · V1 MVP
          </div>
          <h1 class="hero__title">
            专业语境下的<br>
            <span class="gradient-text">智能英语学习引擎</span>
          </h1>
          <p class="hero__desc">
            输入法律主题，即刻获得专业英文学习材料。<br>
            粘贴法律文本，AI 为你逐段解读重点。中英互译，三种法律风格对照提升。
          </p>
          <div class="hero__actions">
            <button class="btn btn--primary btn--lg" onclick="location.hash='/topic'">
              开始探索主题 →
            </button>
            <button class="btn btn--ghost btn--lg" onclick="location.hash='/article'">
              解读法律文本
            </button>
          </div>
          <div class="hero__stats">
            <div class="hero__stat">
              <div class="hero__stat-value">6</div>
              <div class="hero__stat-label">核心学习模块</div>
            </div>
            <div class="hero__stat">
              <div class="hero__stat-value">&lt;15s</div>
              <div class="hero__stat-label">AI 响应时间</div>
            </div>
            <div class="hero__stat">
              <div class="hero__stat-value">∞</div>
              <div class="hero__stat-label">可生成主题数</div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section class="modules">
      <div class="container">
        <div class="modules__grid">
          <!-- Paper Library Card -->
          <div class="module-card module-card--research" onclick="location.hash='/papers'" id="card-papers">
            <div class="module-card__icon">📄</div>
            <div class="module-card__subtitle">模块 · 论文</div>
            <h3 class="module-card__title">论文库 (Paper Library)</h3>
            <p class="module-card__desc">
              批量导入学术论文，AI 智能解读核心要点，管理你的研究文献库。
            </p>
            <ul class="module-card__features">
              <li class="module-card__feature">URL 批量导入 / PDF 上传</li>
              <li class="module-card__feature">AI Insight 结构化解读</li>
              <li class="module-card__feature">论文对话问答</li>
              <li class="module-card__feature">PDF 逐页阅读 + 摘要</li>
            </ul>
            <div class="module-card__cta">
              进入论文库 <span class="arrow">→</span>
            </div>
          </div>

          <!-- Topic Explorer Card -->
          <div class="module-card module-card--topic" onclick="location.hash='/topic'" id="card-topic">
            <div class="module-card__icon">🔍</div>
            <div class="module-card__subtitle">模块 01</div>
            <h3 class="module-card__title">主题探索 (Topic Explorer)</h3>
            <p class="module-card__desc">
              输入涉外法治主题，AI 即刻生成专业英文学习材料，配套术语解析与法律概念说明。
            </p>
            <ul class="module-card__features">
              <li class="module-card__feature">主题关键词生成英文文章</li>
              <li class="module-card__feature">关键术语列表 + 中文释义</li>
              <li class="module-card__feature">术语可展开查看例句</li>
              <li class="module-card__feature">一键跳转翻译训练</li>
            </ul>
            <div class="module-card__cta">
              探索主题 <span class="arrow">→</span>
            </div>
          </div>

          <!-- Article Lab Card -->
          <div class="module-card module-card--article" onclick="location.hash='/article'" id="card-article">
            <div class="module-card__icon">📖</div>
            <div class="module-card__subtitle">模块 02</div>
            <h3 class="module-card__title">文章实验室 (Article Lab)</h3>
            <p class="module-card__desc">
              粘贴英文法律文本，获得 AI 分段解读、术语提取和关键句说明，减少阅读障碍。
            </p>
            <ul class="module-card__features">
              <li class="module-card__feature">支持粘贴文本或上传文件</li>
              <li class="module-card__feature">基础解读 / 法律重点解读</li>
              <li class="module-card__feature">分段中文解释 + 术语提取</li>
              <li class="module-card__feature">关键句标注与说明</li>
            </ul>
            <div class="module-card__cta">
              开始解读 <span class="arrow">→</span>
            </div>
          </div>

          <!-- Translation Studio Card -->
          <div class="module-card module-card--translation" onclick="location.hash='/translation'" id="card-translation">
            <div class="module-card__icon">🌐</div>
            <div class="module-card__subtitle">模块 03</div>
            <h3 class="module-card__title">翻译工作室 (Translation Studio)</h3>
            <p class="module-card__desc">
              中英法律文本互译，提供直译、法律表达、简明三种风格对照，附带表达建议。
            </p>
            <ul class="module-card__features">
              <li class="module-card__feature">EN→ZH / ZH→EN 双向翻译</li>
              <li class="module-card__feature">直译版 / 法律版 / 简明版</li>
              <li class="module-card__feature">表达建议与常见错误提示</li>
              <li class="module-card__feature">可复制每种风格翻译结果</li>
            </ul>
            <div class="module-card__cta">
              翻译训练 <span class="arrow">→</span>
            </div>
          </div>

          <div class="module-card module-card--vocab" onclick="location.hash='/vocab'" id="card-vocab">
            <div class="module-card__icon">🗂️</div>
            <div class="module-card__subtitle">模块 04</div>
            <h3 class="module-card__title">生词本 (Vocabulary)</h3>
            <p class="module-card__desc">
              收集学习过程中的关键词，统一管理并复习，形成长期词汇积累。
            </p>
            <ul class="module-card__features">
              <li class="module-card__feature">一键加入并自动去重</li>
              <li class="module-card__feature">按领域筛选与检索</li>
              <li class="module-card__feature">查看复习进度和状态</li>
              <li class="module-card__feature">支持补充释义与例句</li>
            </ul>
            <div class="module-card__cta">
              打开生词本 <span class="arrow">→</span>
            </div>
          </div>

          <!-- Tracker Card -->
          <div class="module-card" onclick="location.hash='/tracker'" id="card-tracker" style="border-top: 3px solid #f472b6;">
            <div class="module-card__icon">🔔</div>
            <div class="module-card__subtitle">模块 · 追踪</div>
            <h3 class="module-card__title">主题追踪 (Tracker)</h3>
            <p class="module-card__desc">
              追踪感兴趣的研究主题，自动发现最新论文，构建你的学术信息漏斗。
            </p>
            <ul class="module-card__features">
              <li class="module-card__feature">关键词追踪主题</li>
              <li class="module-card__feature">ArXiv 自动检索</li>
              <li class="module-card__feature">一键收录到论文库</li>
              <li class="module-card__feature">每日/每周自动检查</li>
            </ul>
            <div class="module-card__cta">
              开始追踪 <span class="arrow">→</span>
            </div>
          </div>

        </div>
      </div>
    </section>
  `;
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

      <button class="topic-config-fab" id="topic-config-fab" title="打开主题配置">
        ⚙️
      </button>

      <div class="topic-config-overlay is-open" id="topic-config-overlay">
        <div class="topic-config-dialog">
          <div class="topic-config-dialog__header">
            <div>
              <div class="topic-config-dialog__title">模块 01 配置向导</div>
              <div class="topic-config-dialog__hint">先选主题，再设参数，最后生成学习内容</div>
            </div>
            <button class="btn btn--secondary btn--sm" id="topic-config-minimize">最小化</button>
          </div>
          <div class="topic-config-dialog__body">
            <div class="topic-stepper">
              <button class="topic-stepper__item is-active" id="topic-step-indicator-1" type="button">
                <span class="topic-stepper__index">1</span>
                <span class="topic-stepper__label">主题与方向</span>
              </button>
              <button class="topic-stepper__item" id="topic-step-indicator-2" type="button">
                <span class="topic-stepper__index">2</span>
                <span class="topic-stepper__label">参数与生成</span>
              </button>
            </div>

            <div class="topic-step-pane is-active" id="topic-step-1">
              <div class="form-group">
                <label class="form-label">主题关键词 *</label>
                <input type="text" class="form-input" id="topic-input"
                  placeholder="例如：international arbitration, treaty law, cross-border data..."
                  value="international arbitration">
              </div>

              <div class="form-group">
                <label class="form-label">专业方向 (多选)</label>
                <div class="checkbox-group topic-domain-grid" id="topic-domain-checklist">
                  <label class="checkbox-label"><input type="checkbox" value="international-law" checked><span></span> 国际法</label>
                  <label class="checkbox-label"><input type="checkbox" value="commercial-law"><span></span> 商法</label>
                  <label class="checkbox-label"><input type="checkbox" value="constitutional-law"><span></span> 宪法学</label>
                  <label class="checkbox-label"><input type="checkbox" value="criminal-law"><span></span> 刑法学</label>
                  <label class="checkbox-label"><input type="checkbox" value="ip-law"><span></span> 知识产权法</label>
                </div>
                <div class="topic-domain-actions">
                   <input type="text" class="custom-domain-field" id="topic-custom-domain" placeholder="在此输入自定义方向并回车...">
                   <button class="btn btn--secondary topic-domain-add-btn" id="btn-add-domain">添加方向</button>
                </div>
              </div>

              <div class="form-group">
                <label class="form-label">标签（可选，回车添加）</label>
                <div class="tags-input" id="topic-tags-input">
                  <span class="tag">international-law <span class="tag__remove" data-tag="international-law">×</span></span>
                  <span class="tag">dispute-resolution <span class="tag__remove" data-tag="dispute-resolution">×</span></span>
                  <input type="text" class="tags-input__input" placeholder="输入标签..." id="topic-tag-field">
                </div>
              </div>

              <div class="topic-step-actions">
                <button class="btn btn--topic btn--full btn--lg" id="topic-next-step">
                  下一步：设置参数 →
                </button>
              </div>
            </div>

            <div class="topic-step-pane" id="topic-step-2">
              <div class="form-row">
                <div class="form-group">
                  <label class="form-label">难度等级</label>
                  <select class="form-select" id="topic-level">
                    <option value="beginner">初级 Beginner</option>
                    <option value="intermediate" selected>中级 Intermediate</option>
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
                <label class="form-label">文章长度 (Words): <span id="label-len">400</span></label>
                <input type="range" id="topic-len-slider" min="100" max="1000" step="50" value="400" style="width: 100%;">
              </div>

              <div class="form-row">
                <div class="form-group">
                  <label class="form-label">需复习的生词量: <span id="label-db-words">8</span></label>
                  <input type="range" id="topic-db-words-slider" min="0" max="20" step="1" value="8" style="width: 100%;">
                </div>
                <div class="form-group">
                  <label class="form-label">引入新词数量: <span id="label-new-words">5</span></label>
                  <input type="range" id="topic-new-words-slider" min="0" max="15" step="1" value="5" style="width: 100%;">
                </div>
              </div>

              <div class="topic-step-actions topic-step-actions--double">
                <button class="btn btn--ghost btn--lg" id="topic-prev-step">
                  ← 返回上一步
                </button>
                <button class="btn btn--topic btn--lg" id="topic-submit">
                  🔍 生成学习内容
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

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
                <button class="btn btn--secondary btn--sm" id="topic-reopen-config">调整配置</button>
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
  `;
}

export function initTopicExplorer() {
  let currentStep = 1;
  const configOverlay = document.getElementById('topic-config-overlay');
  const configFab = document.getElementById('topic-config-fab');
  const minimizeConfigBtn = document.getElementById('topic-config-minimize');
  const reopenConfigBtn = document.getElementById('topic-reopen-config');
  const step1Pane = document.getElementById('topic-step-1');
  const step2Pane = document.getElementById('topic-step-2');
  const stepIndicator1 = document.getElementById('topic-step-indicator-1');
  const stepIndicator2 = document.getElementById('topic-step-indicator-2');
  const nextStepBtn = document.getElementById('topic-next-step');
  const prevStepBtn = document.getElementById('topic-prev-step');
  const submitBtn = document.getElementById('topic-submit');
  const resultArea = document.getElementById('topic-result');
  const tagField = document.getElementById('topic-tag-field');
  const tagsInput = document.getElementById('topic-tags-input');
  const topicInput = document.getElementById('topic-input');

  if (window.__topicQuickAddCleanup) {
    window.__topicQuickAddCleanup();
    window.__topicQuickAddCleanup = null;
  }

  let quickAddWord = '';
  let quickAddWarnMessage = '';
  const quickAddToolbar = document.createElement('div');
  quickAddToolbar.className = 'selection-quickbar';
  quickAddToolbar.innerHTML = `<button class="selection-quickbar__btn" type="button">+ 生词本</button>`;
  document.body.appendChild(quickAddToolbar);
  const quickAddBtn = quickAddToolbar.querySelector('.selection-quickbar__btn');

  const hideQuickAdd = () => {
    quickAddToolbar.classList.remove('is-visible');
    quickAddWord = '';
    quickAddWarnMessage = '';
  };

  const normalizeSelectionWord = (raw) => {
    const cleaned = raw
      .replace(/[\r\n\t]+/g, ' ')
      .replace(/[，。！？、；：,.!?;:()[\]{}"“”]/g, ' ')
      .trim();
    if (!cleaned) return null;
    const words = cleaned.split(/\s+/).filter(Boolean);
    if (!words.length) return null;
    if (words.length > 4) {
      return { warning: '请选择 1-4 个词后再加入生词本' };
    }
    const enLike = words.every((w) => /^[A-Za-z][A-Za-z'-]*$/.test(w));
    if (!enLike) {
      return { warning: '仅支持加入英文词汇，请重新选择' };
    }
    return { word: words.join(' ').toLowerCase() };
  };

  const updateQuickAddBySelection = () => {
    const sel = window.getSelection();
    if (!sel || sel.rangeCount === 0 || sel.isCollapsed) {
      hideQuickAdd();
      return;
    }

    const range = sel.getRangeAt(0);
    const anchorNode = range.commonAncestorContainer;
    const anchorEl = anchorNode.nodeType === Node.TEXT_NODE ? anchorNode.parentElement : anchorNode;
    if (!anchorEl || !resultArea.contains(anchorEl)) {
      hideQuickAdd();
      return;
    }

    const parsed = normalizeSelectionWord(sel.toString());
    if (!parsed) {
      hideQuickAdd();
      return;
    }
    quickAddWord = parsed.word || '';
    quickAddWarnMessage = parsed.warning || '';

    const rect = range.getBoundingClientRect();
    if (!rect || (rect.width === 0 && rect.height === 0)) {
      hideQuickAdd();
      return;
    }

    const top = window.scrollY + rect.top - 10;
    const left = window.scrollX + rect.left + rect.width / 2;
    quickAddToolbar.style.top = `${Math.max(window.scrollY + 8, top)}px`;
    quickAddToolbar.style.left = `${Math.max(16, Math.min(window.scrollX + window.innerWidth - 16, left))}px`;
    quickAddToolbar.classList.add('is-visible');
  };

  quickAddBtn.addEventListener('click', async (e) => {
    e.preventDefault();
    e.stopPropagation();

    if (quickAddWarnMessage) {
      showToast(quickAddWarnMessage, 'warning');
      return;
    }
    if (!quickAddWord) return;

    const selectedDomain = document.querySelector('#topic-domain-checklist input:checked');
    const domain = selectedDomain ? selectedDomain.value : 'general';

    quickAddBtn.disabled = true;
    quickAddBtn.textContent = '加入中...';
    try {
      await createVocabItem({
        word: quickAddWord,
        domain,
        source: 'topic_selection'
      });
      showToast(`已加入生词本：${quickAddWord}`, 'success');
    } catch (err) {
      const message = String(err?.message || '');
      if (message.includes('already exists')) {
        showToast(`生词本已存在：${quickAddWord}`, 'warning');
      } else {
        showToast(`加入失败：${message}`, 'error');
      }
    } finally {
      quickAddBtn.disabled = false;
      quickAddBtn.textContent = '+ 生词本';
      window.getSelection()?.removeAllRanges();
      hideQuickAdd();
    }
  });

  const onDocumentMouseUp = () => setTimeout(updateQuickAddBySelection, 0);
  const onDocumentKeyUp = (e) => {
    if (e.key.includes('Arrow') || e.key === 'Shift') {
      setTimeout(updateQuickAddBySelection, 0);
    }
  };
  const onDocumentMouseDown = (e) => {
    if (!quickAddToolbar.contains(e.target)) hideQuickAdd();
  };
  const onWindowScroll = () => hideQuickAdd();

  document.addEventListener('mouseup', onDocumentMouseUp);
  document.addEventListener('keyup', onDocumentKeyUp);
  document.addEventListener('mousedown', onDocumentMouseDown);
  window.addEventListener('scroll', onWindowScroll, true);

  const openConfig = () => {
    configOverlay.classList.add('is-open');
    configFab.classList.remove('is-visible');
  };

  const minimizeConfig = () => {
    configOverlay.classList.remove('is-open');
    configFab.classList.add('is-visible');
  };

  const setStep = (step) => {
    currentStep = step;
    step1Pane.classList.toggle('is-active', step === 1);
    step2Pane.classList.toggle('is-active', step === 2);

    stepIndicator1.classList.toggle('is-active', step === 1);
    stepIndicator2.classList.toggle('is-active', step === 2);

    stepIndicator1.classList.toggle('is-complete', step > 1);
    stepIndicator2.classList.toggle('is-complete', false);
  };

  const validateStep1 = () => {
    const topic = topicInput.value.trim();
    if (!topic) {
      topicInput.style.borderColor = 'rgba(239,68,68,0.5)';
      topicInput.focus();
      return false;
    }
    topicInput.style.borderColor = '';
    return true;
  };

  nextStepBtn.addEventListener('click', () => {
    if (!validateStep1()) return;
    setStep(2);
  });

  prevStepBtn.addEventListener('click', () => setStep(1));
  stepIndicator1.addEventListener('click', () => setStep(1));
  stepIndicator2.addEventListener('click', () => {
    if (!validateStep1()) return;
    setStep(2);
  });

  topicInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && currentStep === 1) {
      e.preventDefault();
      nextStepBtn.click();
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
      });
  });

  submitBtn.addEventListener('click', async () => {
    const topic = topicInput.value.trim();
    if (!validateStep1()) return;

    submitBtn.disabled = true;
    nextStepBtn.disabled = true;
    prevStepBtn.disabled = true;
    minimizeConfigBtn.disabled = true;
    submitBtn.innerHTML = '<span class="spinner"></span> AI 正在生成...';

    resultArea.innerHTML = `
      <div class="loading-state">
        <div class="loading-dots"><span></span><span></span><span></span></div>
        <div class="loading-text">正在为「${topic}」生成学习内容...</div>
      </div>
    `;

    try {
      const level = document.getElementById('topic-level').value;
      const domainCheckboxes = document.querySelectorAll('#topic-domain-checklist input:checked');
      const domains = Array.from(domainCheckboxes).map(cb => cb.parentElement.textContent.trim());
      
      const style = document.getElementById('topic-style').value;
      const length = parseInt(document.getElementById('topic-len-slider').value, 10);
      const dbWords = parseInt(document.getElementById('topic-db-words-slider').value, 10);
      const newWords = parseInt(document.getElementById('topic-new-words-slider').value, 10);

      const data = await generateTopic({ 
          topic, 
          level, 
          domains: domains.length ? domains : ['General'],
          style,
          length,
          dbWords,
          newWords
      });

      document.getElementById('topic-confidence').textContent = `可信度: ${data.confidence_hint}`;
      minimizeConfig();

      resultArea.innerHTML = `
        <div class="gen-article">
          <div class="gen-article__section">
            <div class="gen-article__section-title">📄 英文学习文章</div>
            <div class="gen-article__text">${data.result_text}</div>
          </div>

          <div class="gen-article__section">
            <div class="gen-article__section-title">📚 关键术语 (${data.terms.length})</div>
            <div class="terms-grid">
              ${data.terms.map(t => `
                <div class="term-card" onclick="this.classList.toggle('expanded')">
                  <div class="term-card__en">${t.term}</div>
                  <div class="term-card__zh">${t.zh}</div>
                  <div class="term-card__example">
                    <strong>Example:</strong> ${t.example}
                  </div>
                </div>
              `).join('')}
            </div>
          </div>

          <div class="notes-section">
            <div class="notes-section__title">💡 核心概念说明</div>
            ${data.notes.map(n => `<div class="notes-section__item">${n}</div>`).join('')}
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
    } catch (err) {
      resultArea.innerHTML = `
        <div class="result-empty">
          <div class="result-empty__icon">❌</div>
          <div class="result-empty__text">生成失败，请重试<br>${err.message}</div>
        </div>
      `;
    }

    nextStepBtn.disabled = false;
    prevStepBtn.disabled = false;
    minimizeConfigBtn.disabled = false;
    submitBtn.innerHTML = '🔍 生成学习内容';
    submitBtn.disabled = false;
  });

  setStep(1);
  openConfig();

  window.__topicQuickAddCleanup = () => {
    document.removeEventListener('mouseup', onDocumentMouseUp);
    document.removeEventListener('keyup', onDocumentKeyUp);
    document.removeEventListener('mousedown', onDocumentMouseDown);
    window.removeEventListener('scroll', onWindowScroll, true);
    document.removeEventListener('keydown', onEscape);
    quickAddToolbar.remove();
  };
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
                </label>
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

    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="spinner"></span> AI 正在解读...';

    resultArea.innerHTML = `
      <div class="loading-state">
        <div class="loading-dots"><span></span><span></span><span></span></div>
        <div class="loading-text">正在解读文本 (${words} 词)...</div>
      </div>
    `;

    try {
      const data = await analyzeArticle({
        source_text: text,
        analysis_mode: window.__articleMode,
        target_lang: 'zh',
        grounded: Boolean(groundedInput && groundedInput.checked),
        top_k: 4
      });

      resultArea.innerHTML = `
        <div class="analysis-result">
          <div class="gen-article__section">
            <div class="gen-article__section-title">📝 分段解读</div>
            ${data.paragraphs.map((p, i) => `
              <div class="analysis-paragraph">
                <div class="analysis-paragraph__label analysis-paragraph__label--original">段落 ${i + 1} · 原文</div>
                <div class="analysis-paragraph__original">${p.original}</div>
                <div class="analysis-paragraph__label analysis-paragraph__label--explain">中文解读</div>
                <div class="analysis-paragraph__explanation">${p.explanation}</div>
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
                  <div class="term-card__en">${t.term}</div>
                  <div class="term-card__zh">${t.definition_zh}</div>
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
                    <div class="key-sentence__text">"${s.text}"</div>
                    <div class="key-sentence__reason">${s.reason}</div>
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
    } catch (err) {
      resultArea.innerHTML = `
        <div class="result-empty">
          <div class="result-empty__icon">❌</div>
          <div class="result-empty__text">解读失败，请重试<br>${err.message}</div>
        </div>
      `;
    }

    submitBtn.disabled = false;
    submitBtn.innerHTML = '📖 开始解读';
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
  
  try {
    // Dynamically retrieve the module scope api import or simply wrap in closure.
    // Since analyzeArticle is imported in pages.js, we can call it.
    const mode = window.__articleMode || 'plain';
    const { analyzeArticle } = await import('./api.js');
    const data = await analyzeArticle({ source_text: enText, analysis_mode: mode });
    
    zhEl.innerText = data.paragraphs[0].explanation;
    
    // Success flash highlight
    container.style.transition = 'background-color 0.4s ease';
    container.style.backgroundColor = 'rgba(52, 199, 89, 0.1)';
    setTimeout(() => {
        container.style.backgroundColor = '';
    }, 1000);
  } catch (err) {
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

    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="spinner"></span> AI 正在翻译...';

    resultArea.innerHTML = `
      <div class="loading-state">
        <div class="loading-dots"><span></span><span></span><span></span></div>
        <div class="loading-text">正在生成三种风格翻译...</div>
      </div>
    `;

    try {
      const userTranslation = document.getElementById('translation-user').value.trim();
      const data = await runTranslation({
        source_text: text,
        direction: window.__translationDirection,
        style: ['literal', 'legal', 'plain'],
        user_translation: userTranslation
      });

      document.getElementById('trans-confidence').textContent =
        `可信度: ${data.confidence_hint}`;

      resultArea.innerHTML = `
        <div class="translation-result">
          ${data.critique ? `
            <div class="gen-article__section" style="margin-bottom: 24px; background: rgba(52, 199, 89, 0.05); padding: 18px; border-radius: 12px; border: 1px solid rgba(52, 199, 89, 0.2);">
              <div class="gen-article__section-title" style="color: var(--translation); margin-bottom: 12px;">🤖 译文对照点评</div>
              <div style="margin-bottom: 12px; font-size: 14px;">
                <strong>评分：</strong> <span style="color: var(--translation); font-weight: bold;">${data.critique.score}</span><br>
                <div style="margin-top: 6px; color: var(--text-base);">${data.critique.feedback}</div>
              </div>
              ${data.critique.improvements.map(imp => `
                <div style="font-size: 13px; margin-bottom: 10px; padding-left: 12px; border-left: 2px solid var(--translation);">
                  <div style="text-decoration: line-through; color: var(--text-muted); margin-bottom: 2px;">${imp.original}</div>
                  <div style="color: var(--text-base);">👉 ${imp.suggested} <br><span style="color: var(--text-muted); font-size: 12px;">💡 ${imp.reason}</span></div>
                </div>
              `).join('')}
            </div>
          ` : ''}
          ${data.variants.map(v => `
            <div class="translation-variant translation-variant--${v.style}">
              <div class="translation-variant__label">
                ${v.style === 'literal' ? '📋' : v.style === 'legal' ? '⚖️' : '💬'} ${v.label}
              </div>
              <div class="translation-variant__text">${v.text}</div>
              <button class="translation-variant__copy" onclick="copyText(\`${v.text.replace(/`/g, '\\`')}\`, this)">复制</button>
              <div style="clear:both"></div>
            </div>
          `).join('')}

          <div class="gen-article__section" style="margin-top:20px">
            <div class="gen-article__section-title">📚 相关术语</div>
            <div class="terms-grid">
              ${data.terms.map(t => `
                <div class="term-card">
                  <div class="term-card__en">${t.term}</div>
                  <div class="term-card__zh">${t.definition_zh}</div>
                </div>
              `).join('')}
            </div>
          </div>

          <div class="notes-section">
            <div class="notes-section__title">💡 表达建议</div>
            ${data.notes.map(n => `<div class="notes-section__item">${n}</div>`).join('')}
          </div>

          <div class="feedback">
            <span class="feedback__label">翻译结果是否有帮助？</span>
            <div class="feedback__btns">
              <button class="feedback__btn" onclick="submitFeedback(this, 'Translation_Studio', 'Positive')">👍 有帮助</button>
              <button class="feedback__btn" onclick="submitFeedback(this, 'Translation_Studio', 'Negative')">👎 需改进</button>
            </div>
          </div>
        </div>
      `;
    } catch (err) {
      resultArea.innerHTML = `
        <div class="result-empty">
          <div class="result-empty__icon">❌</div>
          <div class="result-empty__text">翻译失败，请重试<br>${err.message}</div>
        </div>
      `;
    }

    submitBtn.disabled = false;
    submitBtn.innerHTML = '🌐 开始翻译';
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

// Global Analytics Hook
window.submitFeedback = function(btn, moduleName, selection) {
  const container = btn.closest('.feedback__btns');
  container.querySelectorAll('.feedback__btn').forEach(b => b.classList.remove('selected'));
  btn.classList.add('selected');
  // Log the PRD tracking event to console
  console.log(`[Analytics] Event: feedback_submit, Module: ${moduleName}, Selection: ${selection}, Timestamp: ${new Date().toISOString()}`);
};
