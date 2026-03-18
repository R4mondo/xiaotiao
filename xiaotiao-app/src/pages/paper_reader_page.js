// PDF Reader Page — /papers/:id/read
import 'pdfjs-dist/web/pdf_viewer.css';
import { streamAI, renderMarkdown, startSimulatedProgress } from '../utils/stream.js';
import { authFetch } from '../utils/http.js';
import { addExtraButtons } from '../components/word_selector.js';

const RAW_API_BASE = import.meta.env.VITE_API_BASE_URL || '';
const API_BASE = RAW_API_BASE.replace(/\/api\/v1\/?$/, '');

export function renderPaperReaderPage(params) {
  return `
    <div style="display:flex;flex-direction:column;height:calc(100vh - 80px);margin-top:70px;">
      <!-- Top Bar -->
      <div class="glass-panel" style="padding:8px 20px;border-radius:0;display:flex;align-items:center;justify-content:space-between;flex-shrink:0;">
        <div style="display:flex;align-items:center;gap:12px;">
          <a href="#/papers/${params.id}" style="color:var(--accent);text-decoration:none;font-size:0.9rem;">← 返回详情</a>
          <span id="reader-title" style="color:var(--text-primary);font-size:0.9rem;font-weight:500;max-width:300px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;"></span>
        </div>
        <div style="display:flex;align-items:center;gap:16px;">
          <span id="page-indicator" style="color:var(--text-muted);font-size:0.85rem;">第 1 / ? 页</span>
          <input type="number" id="page-jump-input" min="1" style="width:60px;padding:4px 8px;border-radius:8px;border:1px solid rgba(0,0,0,0.1);font-size:0.85rem;text-align:center;" placeholder="页码">
          <div style="display:flex;gap:4px;">
            <button class="btn btn--secondary" id="btn-zoom-out" style="padding:4px 10px;font-size:0.85rem;">-</button>
            <span id="zoom-level" style="color:var(--text-muted);font-size:0.85rem;min-width:40px;text-align:center;">120%</span>
            <button class="btn btn--secondary" id="btn-zoom-in" style="padding:4px 10px;font-size:0.85rem;">+</button>
          </div>
        </div>
      </div>

      <!-- Main Content -->
      <div class="reader-layout" style="display:flex;flex:1;overflow:hidden;">
        <!-- PDF Viewer -->
        <div id="pdf-container" class="reader-pdf" style="flex:1;overflow-y:auto;padding:20px;background:rgba(0,0,0,0.02);display:flex;flex-direction:column;align-items:center;gap:8px;">
          <div id="pdf-loading" style="text-align:center;padding:60px;color:var(--text-muted);">
            正在加载 PDF 阅读器...
          </div>
        </div>

        <!-- Summary Sidebar -->
        <div class="reader-sidebar" style="width:360px;border-left:1px solid rgba(0,0,0,0.06);display:flex;flex-direction:column;overflow:hidden;flex-shrink:0;">
          <div style="padding:16px 20px;border-bottom:1px solid rgba(0,0,0,0.06);">
            <h3 style="color:var(--text-primary);font-size:1rem;font-weight:600;">阅读概要</h3>
            <p id="pages-read-count" style="color:var(--text-muted);font-size:0.8rem;margin-top:4px;">已读 0 页</p>
          </div>
          <div id="page-summaries" style="flex:1;overflow-y:auto;padding:16px 20px;display:flex;flex-direction:column;gap:16px;">
            <p style="color:var(--text-muted);font-size:0.85rem;text-align:center;padding:20px;">滚动阅读 PDF，AI 将自动生成逐页概要</p>
          </div>
          <!-- Context Chat -->
          <div style="padding:12px 20px;border-top:1px solid rgba(0,0,0,0.06);">
            <div style="display:flex;gap:8px;">
              <input type="text" id="reader-chat-input" class="input-field" placeholder="基于已读内容提问..." style="flex:1;font-size:0.85rem;padding:8px 12px;">
              <button class="btn btn--primary" id="btn-reader-chat" style="padding:8px 12px;font-size:0.85rem;">问</button>
            </div>
            <div id="reader-chat-response" style="margin-top:8px;display:none;"></div>
          </div>
        </div>
      </div>

      <!-- Selection Result Popover -->
      <div id="selection-result" style="display:none;position:fixed;z-index:201;background:var(--glass-bg-solid);backdrop-filter:blur(20px);border:1px solid rgba(0,0,0,0.1);border-radius:12px;padding:16px;box-shadow:var(--shadow-elevated);max-width:400px;max-height:300px;overflow-y:auto;"></div>
    </div>
  `;
}

export async function initPaperReaderPage(params) {
  const paperId = params.id;
  let scale = 1.2;
  let totalPages = 0;
  let pagesRead = new Set();
  let summariesGenerated = new Set();
  let pdfDoc = null;
  let observer = null;
  let pdfjsLibInstance = null;
  let lastReaderQuestion = '';
  let isChatBusy = false;

  // Load paper info
  try {
    const res = await authFetch(`${API_BASE}/papers/${paperId}`);
    const paper = await res.json();
    document.getElementById('reader-title').textContent = paper.title;
  } catch (e) { /* ignore */ }

  // Load PDF.js dynamically
  try {
    const [pdfjsLib, workerUrlModule] = await Promise.all([
      import('pdfjs-dist'),
      import('pdfjs-dist/build/pdf.worker.mjs?url')
    ]);
    pdfjsLibInstance = pdfjsLib;
    if (pdfjsLib.GlobalWorkerOptions.workerSrc !== workerUrlModule.default) {
      pdfjsLib.GlobalWorkerOptions.workerSrc = workerUrlModule.default;
    }

    // Fetch PDF
    const pdfRes = await authFetch(`${API_BASE}/papers/${paperId}/pdf`);
    if (!pdfRes.ok) throw new Error('无法获取 PDF');

    const contentType = pdfRes.headers.get('content-type');
    let pdfData;

    if (contentType && contentType.includes('application/json')) {
      const jsonData = await pdfRes.json();
      if (jsonData.pdf_url) {
        const proxyRes = await fetch(jsonData.pdf_url);
        pdfData = await proxyRes.arrayBuffer();
      } else {
        throw new Error('No PDF available');
      }
    } else {
      pdfData = await pdfRes.arrayBuffer();
    }

    pdfDoc = await pdfjsLib.getDocument({ data: pdfData }).promise;
    totalPages = pdfDoc.numPages;
    document.getElementById('page-indicator').textContent = `第 1 / ${totalPages} 页`;
    document.getElementById('page-jump-input').max = totalPages;

    renderAllPages(pdfDoc, scale, pdfjsLibInstance);

  } catch (e) {
    document.getElementById('pdf-loading').innerHTML = `
      <div style="color:#ef4444;font-size:1.1rem;margin-bottom:8px;">PDF 加载失败</div>
      <p style="color:var(--text-muted);">${e.message}</p>
      <p style="color:var(--text-muted);margin-top:12px;">如果论文来自 ArXiv，PDF 可能需要通过代理获取。</p>
    `;
  }

  async function renderAllPages(doc, currentScale, pdfjsLib) {
    const container = document.getElementById('pdf-container');
    container.innerHTML = '';

    // Use devicePixelRatio for HiDPI rendering (sharp text)
    const pixelRatio = window.devicePixelRatio || 1;
    const renderScale = currentScale * pixelRatio;

    for (let i = 1; i <= doc.numPages; i++) {
      const page = await doc.getPage(i);
      const cssViewport = page.getViewport({ scale: currentScale });
      const renderViewport = page.getViewport({ scale: renderScale });

      const wrapper = document.createElement('div');
      wrapper.className = 'pdf-page-wrapper';
      wrapper.style.cssText = `position:relative;margin-bottom:8px;width:${cssViewport.width}px;height:${cssViewport.height}px;`;
      wrapper.dataset.pageNum = i;

      const canvas = document.createElement('canvas');
      canvas.width = renderViewport.width;
      canvas.height = renderViewport.height;
      canvas.style.cssText = `display:block;width:${cssViewport.width}px;height:${cssViewport.height}px;background:white;box-shadow:0 2px 12px rgba(0,0,0,0.12);border-radius:4px;`;

      const textLayerDiv = document.createElement('div');
      textLayerDiv.className = 'textLayer';
      // pdfjs v5 requires --total-scale-factor for text positioning
      textLayerDiv.style.cssText = `position:absolute;inset:0;--total-scale-factor:${currentScale};`;

      wrapper.appendChild(canvas);
      wrapper.appendChild(textLayerDiv);
      container.appendChild(wrapper);

      const ctx = canvas.getContext('2d');
      await page.render({ canvasContext: ctx, viewport: renderViewport }).promise;

      try {
        const textContent = await page.getTextContent();
        if (pdfjsLib.TextLayer) {
          const textLayer = new pdfjsLib.TextLayer({
            textContentSource: textContent,
            container: textLayerDiv,
            viewport: cssViewport,
          });
          await textLayer.render();
        } else if (pdfjsLib.renderTextLayer) {
          await pdfjsLib.renderTextLayer({
            textContent,
            container: textLayerDiv,
            viewport: cssViewport,
          });
        }
      } catch (_e) {
        console.warn('[Reader] TextLayer render error:', _e);
      }
    }

    setupIntersectionObserver(doc);
  }

  function setupIntersectionObserver(doc) {
    if (observer) observer.disconnect();

    observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const pageNum = parseInt(entry.target.dataset.pageNum);
          pagesRead.add(pageNum);
          document.getElementById('pages-read-count').textContent = `已读 ${pagesRead.size} 页`;
          document.getElementById('page-indicator').textContent = `第 ${pageNum} / ${totalPages} 页`;

          // Persist reading progress (debounced)
          clearTimeout(window.__progressSaveTimer);
          window.__progressSaveTimer = setTimeout(() => {
            authFetch(`${API_BASE}/papers/${paperId}/reading-progress`, {
              method: 'PUT',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ pages_read: pagesRead.size, total_pages: totalPages })
            }).catch(() => {});
          }, 2000);

          // Auto-generate summary for new pages
          if (!summariesGenerated.has(pageNum)) {
            generatePageSummary(doc, pageNum, paperId);
          }
        }
      });
    }, { threshold: 0.3 });

    document.querySelectorAll('#pdf-container [data-page-num]').forEach(el => {
      observer.observe(el);
    });

    window.__readerObserver = observer;
  }

  async function generatePageSummary(doc, pageNum, paperId, force = false) {
    if (!force && summariesGenerated.has(pageNum)) return;
    summariesGenerated.add(pageNum);

    const page = await doc.getPage(pageNum);
    const textContent = await page.getTextContent();
    const text = textContent.items.map(item => item.str).join(' ');

    if (text.trim().length < 50) return;

    const summariesContainer = document.getElementById('page-summaries');

    // Remove placeholder text
    const placeholder = summariesContainer.querySelector('p');
    if (placeholder && placeholder.textContent.includes('滚动阅读')) {
      placeholder.remove();
    }

    let summaryDiv = document.getElementById(`summary-wrap-${pageNum}`);
    if (!summaryDiv) {
      summaryDiv = document.createElement('div');
      summaryDiv.id = `summary-wrap-${pageNum}`;
      summaryDiv.style.cssText = 'border-left:3px solid var(--accent);padding-left:12px;';
      summaryDiv.innerHTML = `
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;gap:8px;">
          <div style="font-size:0.75rem;color:var(--text-muted);">第 ${pageNum} 页</div>
          <button class="btn btn--ghost btn--sm" data-regenerate="${pageNum}">🔄 重新生成</button>
        </div>
        <div style="font-size:0.85rem;color:var(--text-secondary);line-height:1.6;" id="summary-${pageNum}">
          <span style="color:var(--text-muted);">生成中...</span>
          <div id="summary-progress-${pageNum}" style="margin-top:8px;"></div>
        </div>
      `;
      summariesContainer.appendChild(summaryDiv);
      summariesContainer.scrollTop = summariesContainer.scrollHeight;
      const regenBtn = summaryDiv.querySelector('[data-regenerate]');
      if (regenBtn) {
        regenBtn.addEventListener('click', () => generatePageSummary(doc, pageNum, paperId, true));
      }
    } else {
      const target = document.getElementById(`summary-${pageNum}`);
      if (target) {
        target.innerHTML = `
          <span style="color:var(--text-muted);">生成中...</span>
          <div id="summary-progress-${pageNum}" style="margin-top:8px;"></div>
        `;
      }
    }

    try {
      const target = document.getElementById(`summary-${pageNum}`);
      const progressEl = document.getElementById(`summary-progress-${pageNum}`);
      let progress = null;
      if (progressEl) {
        progress = startSimulatedProgress(progressEl, '');
      }
      let firstChunk = true;
      console.log(`[Reader] Generating summary for page ${pageNum}, text length: ${text.length}`);
      await streamAI(`/papers/${paperId}/page-summary`, { page_number: pageNum, page_text: text.slice(0, 3000) }, (accum) => {
        if (firstChunk && progress) {
          progress.complete();
          setTimeout(() => progress.bar.destroy(), 300);
          firstChunk = false;
        }
        if (target) target.innerHTML = renderMarkdown(accum);
      });
    } catch (e) {
      console.error(`[Reader] Summary generation failed for page ${pageNum}:`, e);
      const target = document.getElementById(`summary-${pageNum}`);
      if (target) target.innerHTML = `<span style="color:var(--text-muted);">概要生成失败: ${e.message}</span>`;
    }
  }

  // Zoom controls
  document.getElementById('btn-zoom-in').addEventListener('click', () => {
    if (scale < 3.0) {
      scale += 0.2;
      document.getElementById('zoom-level').textContent = `${Math.round(scale * 100)}%`;
      if (pdfDoc && pdfjsLibInstance) renderAllPages(pdfDoc, scale, pdfjsLibInstance);
    }
  });

  document.getElementById('btn-zoom-out').addEventListener('click', () => {
    if (scale > 0.5) {
      scale -= 0.2;
      document.getElementById('zoom-level').textContent = `${Math.round(scale * 100)}%`;
      if (pdfDoc && pdfjsLibInstance) renderAllPages(pdfDoc, scale, pdfjsLibInstance);
    }
  });

  // Page jump
  document.getElementById('page-jump-input').addEventListener('change', (e) => {
    const pageNum = parseInt(e.target.value);
    if (pageNum >= 1 && pageNum <= totalPages) {
      const target = document.querySelector(`[data-page-num="${pageNum}"]`);
      if (target) target.scrollIntoView({ behavior: 'smooth' });
    }
  });

  // Register paper-reader-specific buttons on the unified global toolbar
  const resultPopover = document.getElementById('selection-result');
  let lastSelectionAction = null;
  let lastSelectionText = '';

  const HIGHLIGHT_COLORS = [
    { name: '黄色', color: 'rgba(255,255,0,0.4)', bg: 'rgba(255,255,0,0.5)' },
    { name: '绿色', color: 'rgba(0,255,128,0.35)', bg: 'rgba(0,255,128,0.45)' },
    { name: '蓝色', color: 'rgba(100,180,255,0.35)', bg: 'rgba(100,180,255,0.45)' },
    { name: '粉色', color: 'rgba(255,130,180,0.35)', bg: 'rgba(255,130,180,0.45)' },
    { name: '橙色', color: 'rgba(255,180,50,0.35)', bg: 'rgba(255,180,50,0.45)' },
  ];

  const runSelectionAction = async (action, selectedText) => {
    if (!selectedText) return;
    lastSelectionAction = action;
    lastSelectionText = selectedText;

    if (action === 'highlight') {
      // Save selection before it gets lost
      const sel = window.getSelection();
      const savedRange = (sel && sel.rangeCount > 0) ? sel.getRangeAt(0).cloneRange() : null;

      // Create inline color picker popover
      let picker = document.getElementById('highlight-color-picker');
      if (picker) picker.remove();

      picker = document.createElement('div');
      picker.id = 'highlight-color-picker';
      picker.style.cssText = 'position:fixed;z-index:10000;background:var(--glass-bg-solid,#fff);backdrop-filter:blur(20px);border:1px solid rgba(0,0,0,0.1);border-radius:12px;padding:10px 12px;box-shadow:0 8px 32px rgba(0,0,0,0.18);display:flex;gap:8px;align-items:center;';

      HIGHLIGHT_COLORS.forEach(({ name, color, bg }) => {
        const btn = document.createElement('button');
        btn.title = name;
        btn.style.cssText = `width:26px;height:26px;border-radius:50%;border:2px solid rgba(0,0,0,0.1);background:${bg};cursor:pointer;transition:transform 0.15s ease;`;
        btn.addEventListener('mouseenter', () => { btn.style.transform = 'scale(1.2)'; });
        btn.addEventListener('mouseleave', () => { btn.style.transform = ''; });
        btn.addEventListener('click', async () => {
          picker.remove();
          // Apply visual highlight — wrap only the selected text, not the entire span
          try {
            if (savedRange) {
              // Use highlight wrapping: extract selected content and wrap in a <mark> element
              const mark = document.createElement('mark');
              mark.style.cssText = `background:${color};border-radius:2px;padding:0;`;
              mark.className = 'pdf-highlight';
              try {
                savedRange.surroundContents(mark);
              } catch (_e) {
                // surroundContents fails if range crosses element boundaries
                // Fallback: extract and re-insert wrapped content
                const fragment = savedRange.extractContents();
                mark.appendChild(fragment);
                savedRange.insertNode(mark);
              }
            }
            await authFetch(`${API_BASE}/papers/${paperId}/annotations`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ type: 'highlight', selected_text: selectedText, color, page_number: null })
            });
            window.showToast?.('已添加高亮', 'success');
          } catch (e) {
            window.showToast?.('添加失败', 'error');
          }
          window.getSelection()?.removeAllRanges();
        });
        picker.appendChild(btn);
      });

      document.body.appendChild(picker);

      // Position to the RIGHT of the toolbar (not below the selection)
      const toolbarEl = document.querySelector('.word-selector-bar.is-visible');
      if (toolbarEl) {
        const tbRect = toolbarEl.getBoundingClientRect();
        picker.style.left = `${tbRect.right + 8}px`;
        picker.style.top = `${tbRect.top}px`;
        // If would go off-screen right, put it to the left instead
        if (tbRect.right + 220 > window.innerWidth) {
          picker.style.left = `${tbRect.left - 220}px`;
        }
      } else if (savedRange) {
        const rect = savedRange.getBoundingClientRect();
        picker.style.left = `${rect.right + 8}px`;
        picker.style.top = `${rect.top}px`;
      }

      // Auto-close on outside click
      setTimeout(() => {
        const close = (e) => {
          if (!picker.contains(e.target)) {
            picker.remove();
            document.removeEventListener('mousedown', close);
          }
        };
        document.addEventListener('mousedown', close);
      }, 50);
      return;
    }

    // Translate or Summary
    resultPopover.style.display = 'block';
    resultPopover.style.left = `${Math.max(20, window.innerWidth / 2 - 200)}px`;
    resultPopover.style.top = `${window.innerHeight / 3}px`;
    resultPopover.innerHTML = `
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
        <span style="font-size:0.8rem;color:var(--text-muted);">${action === 'translate' ? '🌐 翻译' : '📝 摘要'}</span>
        <button class="btn btn--ghost btn--sm" id="btn-selection-regenerate">🔄 重新生成</button>
      </div>
      <div id="selection-progress-container" style="min-width:200px;"></div>
    `;

    const selProgressContainer = document.getElementById('selection-progress-container');
    const selProgress = startSimulatedProgress(selProgressContainer, action === 'translate' ? '翻译中...' : '生成摘要...');

    const regenBtn = document.getElementById('btn-selection-regenerate');
    if (regenBtn) {
      regenBtn.addEventListener('click', () => runSelectionAction(lastSelectionAction, lastSelectionText));
    }

    const endpoint = action === 'translate'
      ? `/papers/${paperId}/translate`
      : `/papers/${paperId}/summarize-selection`;

    try {
      let firstChunk = true;
      console.log(`[Reader] Running ${action} on text: "${selectedText.slice(0, 50)}..."`);
      await streamAI(endpoint, { text: selectedText }, (text) => {
        if (firstChunk) {
          selProgress.complete();
          firstChunk = false;
        }
        resultPopover.innerHTML = `
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
            <span style="font-size:0.8rem;color:var(--text-muted);">${action === 'translate' ? '🌐 翻译' : '📝 摘要'}</span>
            <button class="btn btn--ghost btn--sm" id="btn-selection-regenerate">🔄 重新生成</button>
          </div>
          <div style="font-size:0.85rem;color:var(--text-primary);line-height:1.6;">${renderMarkdown(text)}</div>
        `;
        const regenBtnAfter = document.getElementById('btn-selection-regenerate');
        if (regenBtnAfter) {
          regenBtnAfter.addEventListener('click', () => runSelectionAction(lastSelectionAction, lastSelectionText));
        }
      });
    } catch (e) {
      selProgress.stop();
      resultPopover.innerHTML = `<span style="color:#ef4444;font-size:0.85rem;">处理失败: ${e.message}</span>`;
    }
  };

  // Close result popover on click outside
  document.addEventListener('mousedown', (e) => {
    if (resultPopover && !resultPopover.contains(e.target)) {
      resultPopover.style.display = 'none';
    }
  });

  // Add extra buttons to the global word selector toolbar
  addExtraButtons([
    {
      label: '翻译',
      icon: '🌐',
      className: 'word-selector-bar__btn--extra',
      onClick: (text) => runSelectionAction('translate', text)
    },
    {
      label: '摘要',
      icon: '📝',
      className: 'word-selector-bar__btn--extra',
      onClick: (text) => runSelectionAction('summary', text)
    },
    {
      label: '高亮',
      icon: '🖍️',
      className: 'word-selector-bar__btn--extra',
      onClick: (text) => runSelectionAction('highlight', text)
    }
  ]);

  // Reader chat — send on click or Enter
  const chatBtn = document.getElementById('btn-reader-chat');
  const chatInput = document.getElementById('reader-chat-input');

  const sendChatMessage = async () => {
    const msg = chatInput.value.trim();
    if (!msg || isChatBusy) return;
    isChatBusy = true;
    chatInput.value = '';

    // Visual: show active state
    chatBtn.disabled = true;
    chatBtn.textContent = '...';

    const responseDiv = document.getElementById('reader-chat-response');
    responseDiv.style.display = 'block';
    lastReaderQuestion = msg;
    responseDiv.innerHTML = `<span style="color:var(--text-muted);font-size:0.85rem;">思考中...</span><div id="reader-chat-progress"></div>`;

    const chatProgressEl = document.getElementById('reader-chat-progress');
    const chatProgress = startSimulatedProgress(chatProgressEl, '');

    try {
      let firstChunk = true;
      console.log(`[Reader] Chat: "${msg}"`);
      await streamAI(`/papers/${paperId}/chat`, { message: msg }, (text) => {
        if (firstChunk) {
          chatProgress.complete();
          setTimeout(() => chatProgress.bar?.destroy(), 300);
          firstChunk = false;
        }
        responseDiv.innerHTML = `
          <div style="display:flex;justify-content:flex-end;margin-bottom:6px;">
            <button class="btn btn--ghost btn--sm" id="btn-reader-chat-regenerate">🔄 重新生成</button>
          </div>
          <div style="font-size:0.85rem;color:var(--text-primary);line-height:1.6;max-height:200px;overflow-y:auto;">${renderMarkdown(text)}</div>
        `;
        const regenBtn = document.getElementById('btn-reader-chat-regenerate');
        if (regenBtn) {
          regenBtn.addEventListener('click', () => {
            if (!lastReaderQuestion) return;
            chatInput.value = lastReaderQuestion;
            sendChatMessage();
          });
        }
      });
    } catch (e) {
      chatProgress.stop();
      chatProgress.bar?.destroy();
      responseDiv.innerHTML = `<span style="color:#ef4444;font-size:0.85rem;">回答失败: ${e.message}</span>`;
    } finally {
      isChatBusy = false;
      chatBtn.disabled = false;
      chatBtn.textContent = '问';
    }
  };

  chatBtn.addEventListener('click', sendChatMessage);
  chatInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendChatMessage();
    }
  });

  // Cleanup on page leave
  window.__readerCleanup = () => {
    if (window.__readerObserver) {
      window.__readerObserver.disconnect();
      window.__readerObserver = null;
    }
  };
}
