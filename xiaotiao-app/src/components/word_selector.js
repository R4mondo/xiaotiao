/**
 * Global Word Selector — 全局英文选词工具
 * Apple-style: subtle selection, floating toolbar follows scroll, spinner loading.
 */
import { createVocabItem, fetchAPI } from '../api.js';

let _toolbar = null;
let _conceptPanel = null;
let _currentWord = '';
let _currentWarning = '';
let _currentRange = null;
let _currentRawText = '';
let _listeners = {};
let _extraBtns = [];

/** Normalize a text selection to 1-4 English words */
function normalizeSelection(raw) {
  const cleaned = raw
    .replace(/[\r\n\t]+/g, ' ')
    .replace(/[，。！？、；：,.!?;:()\[\]{}"'""]/g, ' ')
    .trim();
  if (!cleaned) return null;
  const words = cleaned.split(/\s+/).filter(Boolean);
  if (!words.length) return null;
  if (words.length > 4) return { warning: '请选择 1-4 个英文单词' };
  const isEnglish = words.every(w => /^[A-Za-z][A-Za-z'\-]*$/.test(w));
  if (!isEnglish) return { warning: '仅支持英文词汇选取' };
  return { word: words.join(' ').toLowerCase() };
}

/** Create the floating toolbar DOM */
function createToolbar() {
  const bar = document.createElement('div');
  bar.className = 'word-selector-bar';
  bar.innerHTML = `
    <button class="word-selector-bar__btn word-selector-bar__btn--vocab" type="button">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
      生词本
    </button>
    <button class="word-selector-bar__btn word-selector-bar__btn--concept" type="button">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
      概念解析
    </button>
  `;
  document.body.appendChild(bar);
  return bar;
}

/** Create the concept analysis panel DOM */
function createConceptPanel() {
  const panel = document.createElement('div');
  panel.className = 'concept-analysis-panel';
  panel.innerHTML = `
    <div class="concept-analysis-panel__header">
      <span class="concept-analysis-panel__title">概念解析</span>
      <button class="concept-analysis-panel__close" type="button">✕</button>
    </div>
    <div class="concept-analysis-panel__body"></div>
  `;
  document.body.appendChild(panel);
  return panel;
}

function hideToolbar() {
  if (_toolbar) _toolbar.classList.remove('is-visible');
  _currentWord = '';
  _currentWarning = '';
  _currentRange = null;
}

function hideConceptPanel() {
  if (_conceptPanel) _conceptPanel.classList.remove('is-visible');
}

/** Reposition toolbar above selected text using viewport-relative coords */
function updateToolbarPosition() {
  if (!_toolbar || !_currentRange || !_toolbar.classList.contains('is-visible')) return;
  const rect = _currentRange.getBoundingClientRect();
  if (!rect || (rect.width === 0 && rect.height === 0)) {
    hideToolbar();
    return;
  }
  // Position to the right of the selection, vertically centered
  _toolbar.style.top = `${rect.top + rect.height / 2}px`;
  _toolbar.style.left = `${rect.right + 8}px`;
}

function positionToolbar(range) {
  if (!_toolbar) return;
  const rect = range.getBoundingClientRect();
  if (!rect || (rect.width === 0 && rect.height === 0)) {
    hideToolbar();
    return;
  }
  _currentRange = range;
  updateToolbarPosition();
  _toolbar.classList.add('is-visible');
}

function handleSelectionChange() {
  const sel = window.getSelection();
  if (!sel || sel.rangeCount === 0 || sel.isCollapsed) {
    hideToolbar();
    return;
  }
  const range = sel.getRangeAt(0);
  const anchorNode = range.commonAncestorContainer;
  const anchorEl = anchorNode.nodeType === Node.TEXT_NODE ? anchorNode.parentElement : anchorNode;
  if (!anchorEl) { hideToolbar(); return; }
  if (_toolbar && _toolbar.contains(anchorEl)) return;
  // Allow selections inside concept panel to trigger toolbar (for recursive analysis)
  const tag = anchorEl.tagName;
  if (tag === 'INPUT' || tag === 'TEXTAREA' || anchorEl.isContentEditable) {
    hideToolbar(); return;
  }
  if (document.body.classList.contains('auth-view')) {
    hideToolbar(); return;
  }

  const rawText = sel.toString().trim();
  if (!rawText) { hideToolbar(); return; }

  _currentRawText = rawText;

  // Check if it's English for vocab/concept buttons
  const parsed = normalizeSelection(rawText);
  _currentWord = parsed?.word || '';
  _currentWarning = parsed?.warning || '';

  // Show vocab/concept buttons only for English words
  if (_toolbar) {
    const vocabBtn = _toolbar.querySelector('.word-selector-bar__btn--vocab');
    const conceptBtn = _toolbar.querySelector('.word-selector-bar__btn--concept');
    const hasEnglish = !!_currentWord || !!_currentWarning;
    if (vocabBtn) vocabBtn.style.display = hasEnglish ? '' : 'none';
    if (conceptBtn) conceptBtn.style.display = hasEnglish ? '' : 'none';
  }

  // Show toolbar if we have English text OR extra buttons registered
  const hasExtraBtns = _extraBtns.length > 0;
  const hasEnglish = !!_currentWord || !!_currentWarning;
  if (!hasEnglish && !hasExtraBtns) { hideToolbar(); return; }

  positionToolbar(range);
}

/** Show a fun "word flies into book" collection animation
 *  @param {'success'|'duplicate'} variant */
function showCollectAnimation(word, startX, startY, variant = 'success') {
  const wordEl = document.createElement('div');
  wordEl.className = 'vocab-collect-word';
  wordEl.textContent = word;
  wordEl.style.left = `${startX}px`;
  wordEl.style.top = `${startY}px`;
  document.body.appendChild(wordEl);

  const bookEl = document.createElement('div');
  bookEl.className = 'vocab-collect-book';
  bookEl.innerHTML = '📖';
  document.body.appendChild(bookEl);

  const doneIcon = variant === 'duplicate' ? '⚠️' : '✅';
  const doneMsg = variant === 'duplicate' ? '已加入易忘' : '';

  requestAnimationFrame(() => {
    wordEl.classList.add('vocab-collect-word--float');

    setTimeout(() => {
      wordEl.classList.add('vocab-collect-word--fly');
      bookEl.classList.add('vocab-collect-book--catch');
    }, 350);

    setTimeout(() => {
      wordEl.remove();
      bookEl.classList.add('vocab-collect-book--done');
      bookEl.innerHTML = doneIcon;
      if (doneMsg) {
        const label = document.createElement('div');
        label.className = 'vocab-collect-label';
        label.textContent = doneMsg;
        bookEl.appendChild(label);
      }
    }, 750);

    setTimeout(() => {
      bookEl.classList.add('vocab-collect-book--fade');
      setTimeout(() => bookEl.remove(), 400);
    }, 1400);
  });
}

async function addToVocab() {
  if (_currentWarning) {
    window.showToast(_currentWarning, 'warning');
    return;
  }
  if (!_currentWord) return;

  const word = _currentWord;
  // Capture toolbar position for animation start
  const barRect = _toolbar ? _toolbar.getBoundingClientRect() : null;
  const startX = barRect ? barRect.left + barRect.width / 2 : window.innerWidth / 2;
  const startY = barRect ? barRect.top : window.innerHeight / 2;

  const vocabBtn = _toolbar.querySelector('.word-selector-bar__btn--vocab');
  vocabBtn.disabled = true;
  vocabBtn.textContent = '加入中...';

  try {
    const result = await createVocabItem({
      word,
      domain: 'general',
      source: 'text_selection'
    });
    if (result?.duplicate) {
      showCollectAnimation(word, startX, startY, 'duplicate');
    } else {
      showCollectAnimation(word, startX, startY);
    }
  } catch (err) {
    const msg = String(err?.message || '');
    window.showToast(`加入失败：${msg}`, 'error');
  } finally {
    vocabBtn.disabled = false;
    vocabBtn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg> 生词本';
    window.getSelection()?.removeAllRanges();
    hideToolbar();
  }
}

async function showConceptAnalysis() {
  if (_currentWarning) {
    window.showToast(_currentWarning, 'warning');
    return;
  }
  if (!_currentWord) return;

  const word = _currentWord;
  hideToolbar();
  window.getSelection()?.removeAllRanges();

  if (!_conceptPanel) _conceptPanel = createConceptPanel();
  const body = _conceptPanel.querySelector('.concept-analysis-panel__body');
  const title = _conceptPanel.querySelector('.concept-analysis-panel__title');
  title.textContent = `概念解析：${word}`;

  // Animated loading spinner with percentage
  body.innerHTML = `
    <div class="concept-analysis-panel__loader">
      <svg class="concept-spinner" viewBox="0 0 36 36">
        <circle class="concept-spinner__track" cx="18" cy="18" r="15.5" fill="none" stroke-width="3"/>
        <circle class="concept-spinner__fill" cx="18" cy="18" r="15.5" fill="none" stroke-width="3"
                stroke-dasharray="97.4" stroke-dashoffset="97.4"/>
      </svg>
      <span class="concept-spinner__pct">0%</span>
    </div>
    <div class="concept-analysis-panel__loader-text">正在分析「${word}」...</div>
  `;

  _conceptPanel.style.top = `${window.scrollY + 120}px`;
  _conceptPanel.style.right = '24px';
  _conceptPanel.classList.add('is-visible');

  // Animate loading progress
  const fillCircle = body.querySelector('.concept-spinner__fill');
  const pctLabel = body.querySelector('.concept-spinner__pct');
  let progress = 0;
  const totalDash = 97.4;
  const progressInterval = setInterval(() => {
    if (progress < 85) {
      progress += Math.random() * 8 + 2;
      if (progress > 85) progress = 85;
    }
    const offset = totalDash - (totalDash * progress / 100);
    if (fillCircle) fillCircle.style.strokeDashoffset = offset;
    if (pctLabel) pctLabel.textContent = `${Math.round(progress)}%`;
  }, 200);

  try {
    const data = await fetchAPI('/vocab/concept', {
      word: word
    }, {
      timeoutMs: 30000,
      retries: 1,
      timeoutMessage: '概念解析超时'
    });

    // Finish progress to 100%
    clearInterval(progressInterval);
    progress = 100;
    if (fillCircle) fillCircle.style.strokeDashoffset = '0';
    if (pctLabel) pctLabel.textContent = '100%';

    await new Promise(r => setTimeout(r, 300));

    // Build rich content from /vocab/concept response
    let contentHtml = '';
    if (data.definition_zh || data.definition_en) {
      contentHtml += `<div style="margin-bottom:10px;">`;
      if (data.phonetic) contentHtml += `<span style="color:#6e6e73;font-size:0.85em;margin-right:8px;">${data.phonetic}</span>`;
      if (data.part_of_speech) contentHtml += `<span style="color:#5856d6;font-size:0.82em;">${data.part_of_speech}</span>`;
      contentHtml += `</div>`;
      if (data.definition_zh) contentHtml += `<div style="color:#1d1d1f;font-size:0.95em;margin-bottom:6px;">📖 ${data.definition_zh}</div>`;
      if (data.definition_en) contentHtml += `<div style="color:#6e6e73;font-size:0.88em;margin-bottom:8px;font-style:italic;">${data.definition_en}</div>`;
    }
    if (data.explanation) {
      contentHtml += `<div style="color:#3a3a3c;font-size:0.9em;line-height:1.6;margin-bottom:10px;padding:8px;background:rgba(88,86,214,0.04);border-radius:6px;">${data.explanation}</div>`;
    }
    if (data.examples && data.examples.length > 0) {
      contentHtml += `<div style="margin-bottom:8px;"><div style="font-size:0.82em;color:#5856d6;margin-bottom:4px;">📝 例句</div>`;
      data.examples.forEach(ex => {
        contentHtml += `<div style="margin-bottom:6px;padding-left:8px;border-left:2px solid rgba(88,86,214,0.25);">
          <div style="color:#1d1d1f;font-size:0.88em;">${ex.en || ''}</div>
          <div style="color:#6e6e73;font-size:0.82em;">${ex.zh || ''}</div>
        </div>`;
      });
      contentHtml += `</div>`;
    }
    if (data.related_terms && data.related_terms.length > 0) {
      contentHtml += `<div style="padding-top:6px;border-top:1px solid rgba(0,0,0,0.06);">
        <div style="font-size:0.82em;color:#5856d6;margin-bottom:4px;">🔗 相关词汇 <span style="font-size:0.9em;color:#6e6e73;">(点击词汇可解析)</span></div>
        ${data.related_terms.map(t => `<span class="concept-related-word" data-word="${(t.term || '').replace(/"/g, '&quot;')}" style="display:inline-flex;align-items:center;gap:4px;background:rgba(88,86,214,0.08);padding:3px 10px;border-radius:6px;margin:2px 4px 2px 0;font-size:0.82em;color:#5856d6;cursor:pointer;transition:background 120ms ease;"><span class="concept-related-word__text" style="border-bottom:1px dashed rgba(88,86,214,0.3);">${t.term}</span><span style="color:#6e6e73;">${t.zh ? ': ' + t.zh : ''}</span><button class="concept-related-vocab-btn" data-word="${(t.term || '').replace(/"/g, '&quot;')}" title="加入生词本" style="background:none;border:none;cursor:pointer;font-size:13px;padding:0 2px;line-height:1;opacity:0.6;transition:opacity 100ms;">+</button></span>`).join('')}
      </div>`;
    }
    // Fallback for old-format responses
    if (!contentHtml) {
      const resultText = data.result_text || data.analysis || data.summary || '';
      if (data.paragraphs && data.paragraphs.length > 0) {
        contentHtml = data.paragraphs.map(p => `<div style="margin-bottom:8px;"><div style="color:#e2e8f0;">${p.original || ''}</div><div style="color:#94a3b8;font-size:0.88em;">${p.explanation || ''}</div></div>`).join('');
      } else {
        contentHtml = resultText || '暂无解析结果';
      }
    }
    body.innerHTML = `
      <div class="concept-analysis-panel__word">${word}</div>
      <div class="concept-analysis-panel__content">${contentHtml}</div>
      <button class="btn btn--secondary btn--sm concept-analysis-panel__add-vocab" type="button">
        + 同时加入生词本
      </button>
    `;
    // "Add to vocab" button for the main word
    const addBtn = body.querySelector('.concept-analysis-panel__add-vocab');
    if (addBtn) {
      addBtn.addEventListener('click', async () => {
        addBtn.disabled = true;
        addBtn.textContent = '加入中...';
        try {
          const result = await createVocabItem({ word, domain: 'general', source: 'concept_analysis' });
          if (result?.duplicate) {
            window.showToast(`已加入易忘生词：${word}`, 'warning');
            addBtn.textContent = '⚠ 易忘';
          } else {
            window.showToast(`已加入生词本：${word}`, 'success');
            addBtn.textContent = '✓ 已加入';
          }
        } catch (err) {
          window.showToast(`加入失败：${String(err?.message || '')}`, 'error');
          addBtn.disabled = false;
          addBtn.textContent = '+ 同时加入生词本';
        }
      });
    }

    // Click related term → recursive concept analysis
    body.querySelectorAll('.concept-related-word__text').forEach(el => {
      el.addEventListener('click', (e) => {
        e.stopPropagation();
        const termWord = el.closest('.concept-related-word')?.dataset.word;
        if (termWord) {
          _currentWord = termWord.toLowerCase();
          _currentWarning = '';
          showConceptAnalysis();
        }
      });
    });

    // Click "+" on related term → add to vocab
    body.querySelectorAll('.concept-related-vocab-btn').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        e.stopPropagation();
        const termWord = btn.dataset.word;
        if (!termWord) return;
        btn.textContent = '⏳';
        btn.disabled = true;
        try {
          const result = await createVocabItem({ word: termWord.toLowerCase(), domain: 'general', source: 'concept_analysis' });
          btn.textContent = result?.duplicate ? '⚠' : '✓';
          window.showToast(result?.duplicate ? `已加入易忘：${termWord}` : `已加入：${termWord}`, result?.duplicate ? 'warning' : 'success');
        } catch (err) {
          btn.textContent = '✗';
          window.showToast(`加入失败`, 'error');
        }
      });
    });
  } catch (err) {
    clearInterval(progressInterval);
    body.innerHTML = `
      <div class="concept-analysis-panel__error">
        解析失败：${err.message}<br>
        <button class="btn btn--secondary btn--sm" onclick="this.closest('.concept-analysis-panel').classList.remove('is-visible')">关闭</button>
      </div>
    `;
  }
}

/** Initialize the global word selector. Call on every route change. */
export function initGlobalWordSelector() {
  destroyGlobalWordSelector();

  _toolbar = createToolbar();
  _conceptPanel = createConceptPanel();

  _conceptPanel.querySelector('.concept-analysis-panel__close').addEventListener('click', hideConceptPanel);

  _toolbar.querySelector('.word-selector-bar__btn--vocab').addEventListener('click', (e) => {
    e.preventDefault();
    e.stopPropagation();
    addToVocab();
  });
  _toolbar.querySelector('.word-selector-bar__btn--concept').addEventListener('click', (e) => {
    e.preventDefault();
    e.stopPropagation();
    showConceptAnalysis();
  });

  // Use selectionchange for reliable first-selection detection
  const onSelectionChange = () => setTimeout(handleSelectionChange, 10);
  const onMouseDown = (e) => {
    if (_toolbar && !_toolbar.contains(e.target)) hideToolbar();
    if (_conceptPanel && !_conceptPanel.contains(e.target) && _conceptPanel.classList.contains('is-visible')) {
      hideConceptPanel();
    }
  };
  const onScroll = () => updateToolbarPosition();

  document.addEventListener('selectionchange', onSelectionChange);
  document.addEventListener('mousedown', onMouseDown);
  window.addEventListener('scroll', onScroll, { passive: true, capture: true });

  _listeners = { onSelectionChange, onMouseDown, onScroll };

  window.__wordSelectorCleanup = destroyGlobalWordSelector;
}

/** Add extra buttons to the toolbar (for page-specific actions like 翻译/摘要) */
export function addExtraButtons(buttons) {
  if (!_toolbar) return;
  // Remove any previously added extra buttons to avoid duplicates
  _extraBtns.forEach(btn => btn.remove());
  _extraBtns = [];

  buttons.forEach(({ label, icon, className, onClick }) => {
    const btn = document.createElement('button');
    btn.className = `word-selector-bar__btn ${className || ''}`;
    btn.type = 'button';
    btn.innerHTML = `${icon || ''} ${label}`;
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();
      onClick(_currentRawText);
    });
    _toolbar.appendChild(btn);
    _extraBtns.push(btn);
  });
}

/** Get current selected raw text */
export function getCurrentSelectedText() {
  return _currentRawText;
}

/** Destroy the global word selector */
export function destroyGlobalWordSelector() {
  if (_listeners.onSelectionChange) {
    document.removeEventListener('selectionchange', _listeners.onSelectionChange);
  }
  if (_listeners.onMouseDown) {
    document.removeEventListener('mousedown', _listeners.onMouseDown);
  }
  if (_listeners.onScroll) {
    window.removeEventListener('scroll', _listeners.onScroll, { capture: true });
  }
  _listeners = {};
  _extraBtns = [];
  if (_toolbar) { _toolbar.remove(); _toolbar = null; }
  if (_conceptPanel) { _conceptPanel.remove(); _conceptPanel = null; }
  _currentWord = '';
  _currentWarning = '';
  _currentRange = null;
  _currentRawText = '';
}
