// Paper Detail Page — /papers/:id
import { streamAI, renderMarkdown } from '../utils/stream.js';

const RAW_API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:3000';
const API_BASE = RAW_API_BASE.replace(/\/api\/v1\/?$/, '');

export function renderPaperDetailPage(params) {
  return `
    <div class="page-container" style="max-width:1200px;margin:40px auto;padding:0 20px;">
      <!-- Header -->
      <div style="margin-bottom:24px;">
        <a href="#/papers" style="color:var(--accent);text-decoration:none;font-size:0.9rem;display:inline-flex;align-items:center;gap:4px;">
          ← 返回论文库
        </a>
      </div>

      <div id="paper-header" style="margin-bottom:32px;">
        <div style="color:var(--text-muted);font-size:0.9rem;">加载中...</div>
      </div>

      <!-- Two Column Layout -->
      <div style="display:grid;grid-template-columns:1fr 380px;gap:24px;align-items:start;">
        <!-- Left: AI Insight -->
        <div class="glass-panel" style="padding:32px;border-radius:20px;" id="insight-panel">
          <h2 style="color:var(--text-primary);font-size:1.3rem;margin-bottom:20px;font-weight:600;">AI 解读</h2>
          <div id="insight-content" style="color:var(--text-secondary);line-height:1.8;">
            加载中...
          </div>
        </div>

        <!-- Right: Sidebar -->
        <div style="display:flex;flex-direction:column;gap:16px;position:sticky;top:80px;">
          <!-- Tab Switcher -->
          <div class="glass-panel" style="padding:8px;border-radius:16px;display:flex;gap:4px;">
            <button class="btn btn--secondary detail-sidebar-tab active" data-panel="chat" style="flex:1;font-size:0.85rem;padding:8px;">AI 对话</button>
            <button class="btn btn--secondary detail-sidebar-tab" data-panel="annotations" style="flex:1;font-size:0.85rem;padding:8px;">批注</button>
          </div>

          <!-- Chat Panel -->
          <div class="glass-panel" id="chat-panel" style="padding:20px;border-radius:20px;display:flex;flex-direction:column;height:500px;">
            <div id="chat-messages" style="flex:1;overflow-y:auto;margin-bottom:16px;display:flex;flex-direction:column;gap:12px;">
              <!-- Quick questions -->
              <div id="chat-quick-questions" style="display:flex;flex-direction:column;gap:8px;">
                <p style="color:var(--text-muted);font-size:0.85rem;margin-bottom:4px;">快捷提问：</p>
                <button class="btn btn--ghost quick-q" style="text-align:left;font-size:0.85rem;padding:8px 12px;" data-q="这篇论文的主要贡献是什么？">这篇论文的主要贡献是什么？</button>
                <button class="btn btn--ghost quick-q" style="text-align:left;font-size:0.85rem;padding:8px 12px;" data-q="实验方法有什么局限？">实验方法有什么局限？</button>
                <button class="btn btn--ghost quick-q" style="text-align:left;font-size:0.85rem;padding:8px 12px;" data-q="与相关工作有什么区别？">与相关工作有什么区别？</button>
              </div>
            </div>
            <div style="display:flex;gap:8px;">
              <input type="text" id="chat-input" class="input-field" placeholder="基于论文内容提问..."
                style="flex:1;font-size:0.9rem;" />
              <button class="btn btn--primary" id="btn-chat-send" style="padding:8px 16px;">发送</button>
            </div>
            <div style="display:flex;justify-content:flex-end;margin-top:10px;">
              <button class="btn btn--ghost btn--sm" id="btn-chat-add-vocab">+ 加入生词本</button>
            </div>
          </div>

          <!-- Annotations Panel (hidden by default) -->
          <div class="glass-panel" id="annotations-panel" style="padding:20px;border-radius:20px;display:none;max-height:500px;overflow-y:auto;">
            <div id="annotations-list" style="display:flex;flex-direction:column;gap:12px;">
              <p style="color:var(--text-muted);font-size:0.9rem;">暂无批注</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  `;
}

export async function initPaperDetailPage(params) {
  const paperId = params.id;
  if (!paperId) return;
  let lastAssistantText = '';

  // Load paper data
  try {
    const res = await fetch(`${API_BASE}/papers/${paperId}`);
    if (!res.ok) throw new Error('Paper not found');
    const paper = await res.json();
    renderHeader(paper);
    renderInsight(paper);
    renderChatHistory(paper.chats || []);
    loadAnnotations(paperId);
    if (paper.chats && paper.chats.length > 0) {
      const last = [...paper.chats].reverse().find(c => c.role === 'assistant');
      if (last && last.content) {
        lastAssistantText = last.content;
      }
    }
  } catch (e) {
    document.getElementById('paper-header').innerHTML = `<div style="color:#ef4444;">加载失败: ${e.message}</div>`;
  }

  // Tab switching
  document.querySelectorAll('.detail-sidebar-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('.detail-sidebar-tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      const panel = tab.dataset.panel;
      document.getElementById('chat-panel').style.display = panel === 'chat' ? 'flex' : 'none';
      document.getElementById('annotations-panel').style.display = panel === 'annotations' ? 'block' : 'none';
    });
  });

  // Chat send
  document.getElementById('btn-chat-send').addEventListener('click', () => sendChat(paperId));
  document.getElementById('chat-input').addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendChat(paperId); }
  });

  document.getElementById('btn-chat-add-vocab').addEventListener('click', () => {
    if (!lastAssistantText) {
      window.showToast('暂无可加入的内容', 'warning');
      return;
    }
    const selection = window.getSelection();
    let picked = '';
    if (selection && selection.toString().trim()) {
      const anchor = selection.anchorNode;
      const chatBox = document.getElementById('chat-messages');
      if (anchor && chatBox && chatBox.contains(anchor)) {
        picked = selection.toString().trim();
      }
    }
    const base = picked || lastAssistantText;
    const word = base.split(/\s+/).slice(0, 4).join(' ');
    addToVocab(word);
  });

  // Quick questions
  document.querySelectorAll('.quick-q').forEach(btn => {
    btn.addEventListener('click', () => {
      document.getElementById('chat-input').value = btn.dataset.q;
      sendChat(paperId);
    });
  });
}

function renderHeader(paper) {
  const header = document.getElementById('paper-header');
  const authors = paper.authors ? (() => { try { return JSON.parse(paper.authors); } catch { return []; } })() : [];

  header.innerHTML = `
    <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:16px;">
      <div style="flex:1;">
        <h1 style="color:var(--text-primary);font-size:1.6rem;font-weight:700;line-height:1.4;margin-bottom:12px;">
          ${escapeHtml(paper.title)}
        </h1>
        ${authors.length > 0 ? `<p style="color:var(--text-muted);font-size:0.9rem;margin-bottom:8px;">${authors.join(', ')}</p>` : ''}
        <div style="display:flex;gap:12px;align-items:center;flex-wrap:wrap;">
          <span style="color:var(--text-muted);font-size:0.85rem;">${paper.source || ''}</span>
          ${paper.arxiv_id ? `<span style="background:rgba(88,86,214,0.1);color:var(--accent);padding:2px 8px;border-radius:8px;font-size:0.8rem;">arXiv: ${paper.arxiv_id}</span>` : ''}
          <span style="color:var(--text-muted);font-size:0.85rem;">${new Date(paper.created_at).toLocaleDateString('zh-CN')}</span>
        </div>
      </div>
      <div style="display:flex;gap:8px;flex-shrink:0;">
        <button class="btn btn--secondary" onclick="window.__toggleFav('${paper.id}');location.reload();" style="padding:8px 12px;">
          ${paper.is_favorite ? '⭐' : '☆'} ${paper.is_favorite ? '已收藏' : '收藏'}
        </button>
        ${paper.pdf_path || paper.pdf_url ? `<button class="btn btn--primary" onclick="location.hash='/papers/${paper.id}/read'" style="padding:8px 16px;">阅读 PDF</button>` : ''}
        <button class="btn btn--secondary" onclick="window.__deletePaper('${paper.id}');location.hash='/papers';" style="padding:8px 12px;color:#ef4444;">删除</button>
      </div>
    </div>
  `;
}

function renderInsight(paper) {
  const container = document.getElementById('insight-content');

  if (paper.insight) {
    container.innerHTML = renderMarkdown(paper.insight);
  } else if (paper.status === 'ready') {
    container.innerHTML = `
      <div style="text-align:center;padding:40px;">
        <p style="color:var(--text-muted);margin-bottom:16px;">尚未生成 AI 解读</p>
        <button class="btn btn--primary" id="btn-generate-insight">生成 AI 解读</button>
      </div>
    `;
    document.getElementById('btn-generate-insight').addEventListener('click', () => generateInsight(paper.id));
  } else if (paper.status === 'processing') {
    container.innerHTML = `<div style="text-align:center;padding:40px;color:var(--text-muted);">论文正在处理中，请稍候...</div>`;
  } else {
    container.innerHTML = `<div style="text-align:center;padding:40px;color:var(--text-muted);">论文状态: ${paper.status}</div>`;
  }
}

async function generateInsight(paperId) {
  const container = document.getElementById('insight-content');
  container.innerHTML = `<div style="color:var(--text-muted);">正在生成 AI 解读...</div>`;

  try {
    await streamAI(`/papers/${paperId}/insight`, {}, (text) => {
      container.innerHTML = renderMarkdown(text);
    });
  } catch (e) {
    container.innerHTML = `<div style="color:#ef4444;">生成失败: ${e.message}</div>`;
  }
}

function renderChatHistory(chats) {
  if (chats.length === 0) return;

  const container = document.getElementById('chat-messages');
  // Hide quick questions if there's history
  const qqs = document.getElementById('chat-quick-questions');
  if (qqs) qqs.style.display = 'none';

  chats.forEach(c => {
    appendChatMessage(c.role, c.content);
  });
}

function buildAssistantMessage(content) {
  const msg = document.createElement('div');
  msg.style.cssText = 'padding:12px 16px;border-radius:12px;font-size:0.9rem;line-height:1.6;max-width:90%;background:var(--glass-bg);color:var(--text-primary);align-self:flex-start;';

  const contentEl = document.createElement('div');
  contentEl.className = 'chat-msg__content';
  contentEl.innerHTML = renderMarkdown(content);
  msg.appendChild(contentEl);

  const actions = document.createElement('div');
  actions.style.cssText = 'display:flex;justify-content:flex-end;margin-top:8px;';
  const btn = document.createElement('button');
  btn.className = 'btn btn--ghost btn--sm';
  btn.textContent = '+ 加入生词本';
  btn.addEventListener('click', () => {
    const selection = window.getSelection();
    let picked = '';
    if (selection && selection.toString().trim()) {
      const anchor = selection.anchorNode;
      if (anchor && msg.contains(anchor)) {
        picked = selection.toString().trim();
      }
    }
    const base = picked || (contentEl.textContent || '');
    const word = base.trim().split(/\s+/).slice(0, 4).join(' ');
    addToVocab(word);
  });
  actions.appendChild(btn);
  msg.appendChild(actions);

  return { msg, contentEl };
}

function appendChatMessage(role, content) {
  const container = document.getElementById('chat-messages');
  const isUser = role === 'user';
  if (isUser) {
    const msg = document.createElement('div');
    msg.style.cssText = 'padding:12px 16px;border-radius:12px;font-size:0.9rem;line-height:1.6;max-width:90%;background:var(--accent);color:white;align-self:flex-end;';
    msg.innerHTML = escapeHtml(content);
    container.appendChild(msg);
  } else {
    const built = buildAssistantMessage(content);
    container.appendChild(built.msg);
  }
  container.scrollTop = container.scrollHeight;
}

async function sendChat(paperId) {
  const input = document.getElementById('chat-input');
  const message = input.value.trim();
  if (!message) return;

  input.value = '';
  const btn = document.getElementById('btn-chat-send');
  btn.disabled = true;

  // Hide quick questions
  const qqs = document.getElementById('chat-quick-questions');
  if (qqs) qqs.style.display = 'none';

  // Add user message
  appendChatMessage('user', message);

  // Add streaming AI response
  const container = document.getElementById('chat-messages');
  const built = buildAssistantMessage('<span style="color:var(--text-muted);">思考中...</span>');
  const aiMsg = built.msg;
  const aiContent = built.contentEl;
  container.appendChild(aiMsg);
  container.scrollTop = container.scrollHeight;

  try {
    await streamAI(`/papers/${paperId}/chat`, { message }, (text) => {
      lastAssistantText = text;
      aiContent.innerHTML = renderMarkdown(text);
      container.scrollTop = container.scrollHeight;
    });
  } catch (e) {
    aiContent.innerHTML = `<span style="color:#ef4444;">回答失败: ${e.message}</span>`;
  } finally {
    btn.disabled = false;
  }
}

async function addToVocab(word) {
  const cleaned = (word || '').trim();
  if (!cleaned) return;
  try {
    await fetch(`${API_BASE}/vocab`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ word: cleaned, source: 'paper', domain: 'general' })
    });
    window.showToast(`"${cleaned}" 已加入生词本`, 'success');
  } catch (e) {
    window.showToast('加入失败', 'error');
  }
}

async function loadAnnotations(paperId) {
  try {
    const res = await fetch(`${API_BASE}/papers/${paperId}/annotations`);
    const anns = await res.json();
    const container = document.getElementById('annotations-list');

    if (anns.length === 0) {
      container.innerHTML = `<p style="color:var(--text-muted);font-size:0.9rem;text-align:center;padding:20px;">暂无批注，在 PDF 阅读器中选中文字添加。</p>`;
      return;
    }

    container.innerHTML = anns.map(a => `
      <div style="padding:12px;border-radius:12px;background:var(--glass-bg);border-left:3px solid ${a.type === 'highlight' ? '#fbbf24' : 'var(--accent)'};">
        ${a.selected_text ? `<p style="font-size:0.85rem;color:var(--text-primary);font-style:italic;margin-bottom:6px;">"${escapeHtml(a.selected_text)}"</p>` : ''}
        ${a.note ? `<p style="font-size:0.85rem;color:var(--text-secondary);">${escapeHtml(a.note)}</p>` : ''}
        <div style="display:flex;justify-content:space-between;align-items:center;margin-top:8px;">
          <span style="font-size:0.75rem;color:var(--text-muted);">${a.page_number ? `第${a.page_number}页` : ''} · ${a.type}</span>
          <button onclick="window.__deleteAnnotation('${a.id}','${paperId}')" style="background:none;border:none;color:var(--text-muted);cursor:pointer;font-size:0.8rem;">删除</button>
        </div>
      </div>
    `).join('');
  } catch (e) {
    console.error('Failed to load annotations:', e);
  }
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str || '';
  return div.innerHTML;
}

window.__deleteAnnotation = async (annId, paperId) => {
  try {
    await fetch(`${API_BASE}/papers/annotations/${annId}`, { method: 'DELETE' });
    loadAnnotations(paperId);
  } catch (e) {
    window.showToast('删除失败', 'error');
  }
};
