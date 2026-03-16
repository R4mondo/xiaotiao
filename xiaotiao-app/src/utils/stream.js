// Streaming AI response utility for Vanilla JS
// Used by paper detail, PDF reader, and chat components

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:3000/api/v1';

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
