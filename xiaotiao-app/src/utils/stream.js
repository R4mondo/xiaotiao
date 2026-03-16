// Streaming AI response utility for Vanilla JS
// Used by paper detail, PDF reader, and chat components

const RAW_API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:3000';
const API_BASE = RAW_API_BASE.replace(/\/api\/v1\/?$/, '');

/**
 * Stream an AI response from the server and call onChunk for each piece.
 * @param {string} endpoint - API endpoint path (e.g., '/papers/{id}/chat')
 * @param {Object} payload - Request body
 * @param {Function} onChunk - Called with accumulated text on each chunk
 * @param {Object} [options] - Optional settings
 * @param {AbortSignal} [options.signal] - AbortController signal
 * @returns {Promise<string>} The complete response text
 */
export async function streamAI(endpoint, payload, onChunk, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
    signal: options.signal
  });

  if (!response.ok) {
    let errorMsg = `HTTP ${response.status}`;
    try {
      const errData = await response.json();
      errorMsg = errData.detail || errorMsg;
    } catch (_) {}
    throw new Error(errorMsg);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let result = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    const chunk = decoder.decode(value, { stream: true });
    result += chunk;
    if (onChunk) onChunk(result);
  }

  return result;
}

// ============ Progress Simulation Utility ============

/**
 * Create a simulated progress bar with percentage that advances realistically.
 * Returns a controller object to update/complete the progress.
 * @param {HTMLElement} container - The container element to render progress bar into
 * @param {string} [label] - Optional label text to show above the bar
 * @returns {{ update: (pct: number) => void, complete: () => void, destroy: () => void, element: HTMLElement }}
 */
export function createProgressBar(container, label = '') {
  const wrapper = document.createElement('div');
  wrapper.className = 'sim-progress-wrapper';
  wrapper.innerHTML = `
    ${label ? `<div style="color:var(--text-muted);font-size:0.85rem;margin-bottom:6px;">${label}</div>` : ''}
    <div style="display:flex;align-items:center;gap:10px;">
      <div class="progress-bar" style="flex:1;"><span class="progress-bar__fill" style="width:0%;animation:none;transition:width 0.3s ease;"></span></div>
      <span class="sim-progress-pct" style="color:var(--text-muted);font-size:0.8rem;min-width:36px;text-align:right;">0%</span>
    </div>
  `;
  container.appendChild(wrapper);

  const fill = wrapper.querySelector('.progress-bar__fill');
  const pctLabel = wrapper.querySelector('.sim-progress-pct');

  const update = (pct) => {
    const clamped = Math.min(100, Math.max(0, Math.round(pct)));
    fill.style.width = `${clamped}%`;
    pctLabel.textContent = `${clamped}%`;
  };

  const complete = () => {
    update(100);
    fill.style.background = '#34c759';
  };

  const destroy = () => {
    wrapper.remove();
  };

  return { update, complete, destroy, element: wrapper };
}

/**
 * Start a simulated progress animation that looks realistic.
 * Fast at start, slow in middle, pauses near 90%.
 * Call .complete() to jump to 100%, .stop() to halt.
 * @param {HTMLElement} container - The container to render into
 * @param {string} [label] - Optional label
 * @returns {{ complete: () => void, stop: () => void, bar: object }}
 */
export function startSimulatedProgress(container, label = '') {
  const bar = createProgressBar(container, label);
  let current = 0;
  let stopped = false;
  let intervalId = null;

  const tick = () => {
    if (stopped) return;
    if (current < 30) {
      current += Math.random() * 4 + 2; // fast: 2-6% per tick
    } else if (current < 60) {
      current += Math.random() * 2 + 0.5; // medium: 0.5-2.5%
    } else if (current < 85) {
      current += Math.random() * 0.8 + 0.2; // slow: 0.2-1%
    } else if (current < 92) {
      current += Math.random() * 0.3 + 0.05; // very slow: near 90%
    }
    // Cap at 92 during simulation
    current = Math.min(current, 92);
    bar.update(current);
  };

  intervalId = setInterval(tick, 300);

  const complete = () => {
    stopped = true;
    if (intervalId) clearInterval(intervalId);
    bar.complete();
  };

  const stop = () => {
    stopped = true;
    if (intervalId) clearInterval(intervalId);
  };

  return { complete, stop, bar };
}

/**
 * Render a progress bar HTML string for inline use (non-interactive).
 * Use startSimulatedProgress() for interactive progress.
 */
export function progressBarHTML(label = '处理中...') {
  return `
    <div style="display:flex;flex-direction:column;gap:8px;">
      <span style="color:var(--text-muted);font-size:0.85rem;">${label}</span>
      <div style="display:flex;align-items:center;gap:10px;">
        <div class="progress-bar" style="flex:1;"><span class="progress-bar__fill" style="width:0%;animation:none;transition:width 0.3s ease;"></span></div>
        <span style="color:var(--text-muted);font-size:0.8rem;min-width:36px;text-align:right;">0%</span>
      </div>
    </div>
  `;
}

/**
 * Simple markdown-to-HTML converter for AI responses.
 * Handles headers, bold, italic, lists, code blocks, and paragraphs.
 */
export function renderMarkdown(md) {
  if (!md) return '';
  let html = md
    // Code blocks
    .replace(/```(\w*)\n([\s\S]*?)```/g, '<pre><code class="lang-$1">$2</code></pre>')
    // Inline code
    .replace(/`([^`]+)`/g, '<code style="background:rgba(0,0,0,0.06);padding:2px 6px;border-radius:4px;font-size:0.9em;">$1</code>')
    // Headers
    .replace(/^### (.+)$/gm, '<h4 style="color:var(--text-primary);margin:20px 0 8px;font-size:1.05rem;">$1</h4>')
    .replace(/^## (.+)$/gm, '<h3 style="color:var(--text-primary);margin:24px 0 10px;font-size:1.15rem;">$1</h3>')
    .replace(/^# (.+)$/gm, '<h2 style="color:var(--text-primary);margin:28px 0 12px;font-size:1.3rem;">$1</h2>')
    // Bold
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    // Italic
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    // Unordered lists
    .replace(/^[-*] (.+)$/gm, '<li style="margin:4px 0;margin-left:20px;">$1</li>')
    // Ordered lists
    .replace(/^\d+\. (.+)$/gm, '<li style="margin:4px 0;margin-left:20px;">$1</li>')
    // Line breaks → paragraphs
    .replace(/\n\n/g, '</p><p style="margin:10px 0;line-height:1.7;">')
    .replace(/\n/g, '<br>');

  return `<p style="margin:10px 0;line-height:1.7;">${html}</p>`;
}
