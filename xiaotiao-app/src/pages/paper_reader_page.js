// PDF Reader Page — /papers/:id/read
import { streamAI, renderMarkdown, startSimulatedProgress } from '../utils/stream.js';

const RAW_API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:3000';
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

      <!-- Selection Toolbar (hidden, shown on text select) -->
      <div id="selection-toolbar" style="display:none;position:fixed;z-index:200;background:var(--glass-bg-solid);backdrop-filter:blur(20px);border:1px solid rgba(0,0,0,0.1);border-radius:12px;padding:6px;box-shadow:var(--shadow-elevated);display:none;gap:4px;">
        <button class="sel-btn" data-action="translate" style="padding:6px 12px;border:none;background:none;cursor:pointer;color:var(--text-primary);font-size:0.85rem;border-radius:8px;">翻译</button>
        <button class="sel-btn" data-action="summary" style="padding:6px 12px;border:none;background:none;cursor:pointer;color:var(--text-primary);font-size:0.85rem;border-radius:8px;">摘要</button>
        <button class="sel-btn" data-action="vocab" style="padding:6px 12px;border:none;background:none;cursor:pointer;color:var(--text-primary);font-size:0.85rem;border-radius:8px;">生词本</button>
        <button class="sel-btn" data-action="highlight" style="padding:6px 12px;border:none;background:none;cursor:pointer;color:var(--text-primary);font-size:0.85rem;border-radius:8px;">高亮</button>
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
  let lastSelectionAction = null;
  let lastSelectionText = '';
  let lastReaderQuestion = '';

  // Load paper info
  try {
    const res = await fetch(`${API_BASE}/papers/${paperId}`);
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
    const pdfRes = await fetch(`${API_BASE}/papers/${paperId}/pdf`);
    if (!pdfRes.ok) throw new Error('无法获取 PDF');

    const contentType = pdfRes.headers.get('content-type');
    let pdfData;

    if (contentType && contentType.includes('application/json')) {
      // Server returned a URL instead of binary
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

    for (let i = 1; i <= doc.numPages; i++) {
      const page = await doc.getPage(i);
      const viewport = page.getViewport({ scale: currentScale });

      const wrapper = document.createElement('div');
      wrapper.style.cssText = `position:relative;margin-bottom:4px;width:${viewport.width}px;height:${viewport.height}px;`;
      wrapper.dataset.pageNum = i;

      const canvas = document.createElement('canvas');
      canvas.width = viewport.width;
      canvas.height = viewport.height;
      canvas.style.cssText = 'display:block;background:white;box-shadow:0 2px 8px rgba(0,0,0,0.1);border-radius:4px;position:relative;z-index:1;';

      const textLayerDiv = document.createElement('div');
      textLayerDiv.className = 'textLayer';
      textLayerDiv.style.cssText = `position:absolute;left:0;top:0;height:${viewport.height}px;width:${viewport.width}px;z-index:2;`;

      wrapper.appendChild(canvas);
      wrapper.appendChild(textLayerDiv);
      container.appendChild(wrapper);

      const ctx = canvas.getContext('2d');
      await page.render({ canvasContext: ctx, viewport }).promise;

      try {
        const textContent = await page.getTextContent();
        if (pdfjsLib.TextLayer) {
          const textLayer = new pdfjsLib.TextLayer({
            textContentSource: textContent,
            container: textLayerDiv,
            viewport
          });
          await textLayer.render();
        } else if (pdfjsLib.renderTextLayer) {
          await pdfjsLib.renderTextLayer({
            textContent,
            container: textLayerDiv,
            viewport
          });
        }
      } catch (_e) {
        // Ignore text layer rendering errors
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

          // Auto-generate summary for new pages
          if (!summariesGenerated.has(pageNum)) {
            summariesGenerated.add(pageNum);
            generatePageSummary(doc, pageNum, paperId);
          }
        }
      });
    }, { threshold: 0.5 });

    document.querySelectorAll('#pdf-container [data-page-num]').forEach(el => {
      observer.observe(el);
    });

    // Store for cleanup
    window.__readerObserver = observer;
  }

  async function generatePageSummary(doc, pageNum, paperId, force = false) {
    if (!force && summariesGenerated.has(pageNum)) return;
    if (force) summariesGenerated.add(pageNum);
    const page = await doc.getPage(pageNum);
    const textContent = await page.getTextContent();
    const text = textContent.items.map(item => item.str).join(' ');

    if (text.trim().length < 50) return; // Skip nearly empty pages

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
      await streamAI(`/papers/${paperId}/page-summary`, { page_number: pageNum, page_text: text.slice(0, 3000) }, (accum) => {
        if (firstChunk && progress) {
          progress.complete();
          setTimeout(() => progress.bar.destroy(), 300);
          firstChunk = false;
        }
        if (target) target.innerHTML = renderMarkdown(accum);
      });
    } catch (e) {
      const target = document.getElementById(`summary-${pageNum}`);
      if (target) target.innerHTML = `<span style="color:var(--text-muted);">概要生成失败</span>`;
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

  // Selection toolbar
  const pdfContainer = document.getElementById('pdf-container');
  const toolbar = document.getElementById('selection-toolbar');
  const resultPopover = document.getElementById('selection-result');

  let currentPageForSelection = null;
  pdfContainer.addEventListener('mouseup', (e) => {
    const sel = window.getSelection();
    const text = sel.toString().trim();
    if (text.length > 0) {
      const pageEl = e.target.closest('[data-page-num]');
      currentPageForSelection = pageEl ? parseInt(pageEl.dataset.pageNum, 10) : null;
      toolbar.style.display = 'flex';
      toolbar.style.left = `${e.clientX - 100}px`;
      toolbar.style.top = `${e.clientY - 50}px`;
      toolbar.dataset.selectedText = text;
    } else {
      toolbar.style.display = 'none';
      resultPopover.style.display = 'none';
      currentPageForSelection = null;
    }
  });

  document.addEventListener('mousedown', (e) => {
    if (!toolbar.contains(e.target) && !resultPopover.contains(e.target)) {
      toolbar.style.display = 'none';
      resultPopover.style.display = 'none';
    }
  });

  const runSelectionAction = async (action, selectedText) => {
    if (!selectedText) return;
    lastSelectionAction = action;
    lastSelectionText = selectedText;

    if (action === 'vocab') {
      try {
        await fetch(`${API_BASE}/vocab`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ word: selectedText, source: 'paper', domain: 'general' })
        });
        window.showToast(`"${selectedText}" 已加入生词本`, 'success');
      } catch (e) {
        window.showToast('加入失败', 'error');
      }
      return;
    }

    if (action === 'highlight') {
      try {
        await fetch(`${API_BASE}/papers/${paperId}/annotations`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            type: 'highlight',
            selected_text: selectedText,
            page_number: currentPageForSelection
          })
        });
        window.showToast('已添加高亮', 'success');
      } catch (e) {
        window.showToast('添加失败', 'error');
      }
      return;
    }

    resultPopover.style.display = 'block';
    resultPopover.innerHTML = `
      <div style="display:flex;justify-content:flex-end;margin-bottom:6px;">
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
      await streamAI(endpoint, { text: selectedText }, (text) => {
        if (firstChunk) {
          selProgress.complete();
          firstChunk = false;
        }
        resultPopover.innerHTML = `
          <div style="display:flex;justify-content:flex-end;margin-bottom:6px;">
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

  toolbar.querySelectorAll('.sel-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
      const action = btn.dataset.action;
      const selectedText = toolbar.dataset.selectedText;
      toolbar.style.display = 'none';
      const rect = btn.getBoundingClientRect();
      resultPopover.style.left = `${rect.left}px`;
      resultPopover.style.top = `${rect.bottom + 8}px`;
      await runSelectionAction(action, selectedText);
    });
  });

  // Reader chat
  document.getElementById('btn-reader-chat').addEventListener('click', async () => {
    const input = document.getElementById('reader-chat-input');
    const msg = input.value.trim();
    if (!msg) return;
    input.value = '';

    const responseDiv = document.getElementById('reader-chat-response');
    responseDiv.style.display = 'block';
    lastReaderQuestion = msg;
    responseDiv.innerHTML = `<span style="color:var(--text-muted);font-size:0.85rem;">思考中...</span><div id="reader-chat-progress"></div>`;

    const chatProgressEl = document.getElementById('reader-chat-progress');
    const chatProgress = startSimulatedProgress(chatProgressEl, '');

    try {
      let firstChunk = true;
      await streamAI(`/papers/${paperId}/chat`, { message: msg }, (text) => {
        if (firstChunk) {
          chatProgress.complete();
          setTimeout(() => chatProgress.bar.destroy(), 300);
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
            document.getElementById('reader-chat-input').value = lastReaderQuestion;
            document.getElementById('btn-reader-chat').click();
          });
        }
      });
    } catch (e) {
      chatProgress.stop();
      chatProgress.bar.destroy();
      responseDiv.innerHTML = `<span style="color:#ef4444;font-size:0.85rem;">回答失败: ${e.message}</span>`;
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
