// V2.1 Translation History Page
import { getTranslationHistory, deleteTranslationHistory } from '../api.js';
import { escapeHtml } from '../utils/sanitize.js';

export function renderTranslationHistoryPage() {
  return `
    <section class="container" style="max-width:900px;margin:0 auto;padding:24px 16px;">
      <div class="glass-panel" style="padding:24px 28px;">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;">
          <div>
            <h1 style="color:var(--text-primary);font-size:1.5rem;font-weight:700;margin:0;">翻译历史</h1>
            <p style="color:var(--text-secondary);font-size:0.88rem;margin-top:4px;">所有翻译记录自动保存，可随时查看</p>
          </div>
          <a href="#/translation" class="btn btn--primary btn--sm" style="padding:6px 14px;">← 返回翻译</a>
        </div>
        <div id="translation-history-list">
          <div style="text-align:center;color:var(--text-muted);padding:24px;">加载中...</div>
        </div>
        <div id="translation-history-pagination" style="display:flex;justify-content:center;gap:8px;margin-top:16px;"></div>
      </div>
    </section>
  `;
}

export async function initTranslationHistoryPage() {
  let currentPage = 1;

  async function loadPage(page) {
    currentPage = page;
    const list = document.getElementById('translation-history-list');
    if (!list) return;
    list.innerHTML = '<div style="text-align:center;color:var(--text-muted);padding:24px;">加载中...</div>';

    try {
      const data = await getTranslationHistory(page, 20);
      const items = data.items || [];

      if (!items.length) {
        list.innerHTML = `
          <div style="text-align:center;padding:40px;color:var(--text-muted);">
            <div style="font-size:2rem;margin-bottom:8px;">🔤</div>
            <div>还没有翻译记录</div>
            <a href="#/translation" style="color:var(--text-accent);font-size:0.9rem;">去翻译 →</a>
          </div>
        `;
        return;
      }

      const DIRECTION_LABELS = { en_to_zh: '英→中', zh_to_en: '中→英' };

      list.innerHTML = items.map(item => `
        <div class="history-card" style="margin-bottom:10px;padding:14px 18px;cursor:pointer;" data-id="${item.id}">
          <div style="display:flex;justify-content:space-between;align-items:center;">
            <div style="flex:1;min-width:0;">
              <div style="font-size:0.75rem;color:var(--text-muted);margin-bottom:4px;">
                ${DIRECTION_LABELS[item.direction] || item.direction} · ${formatTime(item.created_at)}
              </div>
              <div style="color:var(--text-primary);font-size:0.92rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">
                ${escapeHtml(item.source_text)}
              </div>
            </div>
            <button class="btn-delete-history" data-id="${item.id}" style="background:none;border:none;cursor:pointer;color:var(--text-muted);padding:4px;font-size:1rem;" title="删除">✕</button>
          </div>
        </div>
      `).join('');

      // Detail click
      list.querySelectorAll('.history-card').forEach(card => {
        card.addEventListener('click', (e) => {
          if (e.target.closest('.btn-delete-history')) return;
          const id = card.dataset.id;
          showTranslationDetail(id, card);
        });
      });

      // Delete handlers
      list.querySelectorAll('.btn-delete-history').forEach(btn => {
        btn.addEventListener('click', async (e) => {
          e.stopPropagation();
          if (!confirm('确定删除此翻译记录？')) return;
          try {
            await deleteTranslationHistory(btn.dataset.id);
            if (window.showToast) window.showToast('已删除', 'success');
            loadPage(currentPage);
          } catch (err) {
            if (window.showToast) window.showToast('删除失败', 'error');
          }
        });
      });

      // Pagination
      const pagination = document.getElementById('translation-history-pagination');
      if (pagination && data.total > 20) {
        const totalPages = Math.ceil(data.total / 20);
        pagination.innerHTML = `
          <button class="btn btn--ghost btn--sm" ${page <= 1 ? 'disabled' : ''} id="th-prev">← 上一页</button>
          <span style="color:var(--text-secondary);font-size:0.85rem;padding:4px 8px;">${page}/${totalPages}</span>
          <button class="btn btn--ghost btn--sm" ${page >= totalPages ? 'disabled' : ''} id="th-next">下一页 →</button>
        `;
        if (document.getElementById('th-prev')) {
          document.getElementById('th-prev').addEventListener('click', () => loadPage(page - 1));
        }
        if (document.getElementById('th-next')) {
          document.getElementById('th-next').addEventListener('click', () => loadPage(page + 1));
        }
      }
    } catch (e) {
      list.innerHTML = `<div style="text-align:center;color:var(--text-muted);padding:24px;">加载失败: ${e.message}</div>`;
    }
  }

  async function showTranslationDetail(id, card) {
    // Toggle detail view
    const existing = card.querySelector('.translation-detail');
    if (existing) {
      existing.remove();
      return;
    }

    try {
      const { getTranslationDetail } = await import('../api.js');
      const detail = await getTranslationDetail(id);
      const result = detail.result;

      let html = `<div class="translation-detail" style="margin-top:12px;padding-top:12px;border-top:1px solid rgba(128,128,128,0.2);">`;
      html += `<div style="font-size:0.85rem;color:var(--text-secondary);margin-bottom:8px;"><strong>原文:</strong></div>`;
      html += `<div style="color:var(--text-primary);font-size:0.88rem;margin-bottom:12px;white-space:pre-wrap;">${escapeHtml(detail.source_text)}</div>`;

      if (result && result.translations) {
        result.translations.forEach(t => {
          html += `
            <div style="margin-bottom:8px;">
              <div style="font-size:0.75rem;color:var(--text-accent);font-weight:600;margin-bottom:2px;">${escapeHtml(t.style_label || t.style || '')}</div>
              <div style="color:var(--text-primary);font-size:0.88rem;white-space:pre-wrap;">${escapeHtml(t.text || '')}</div>
            </div>
          `;
        });
      }
      html += `</div>`;
      card.insertAdjacentHTML('beforeend', html);
    } catch (e) {
      card.insertAdjacentHTML('beforeend', `<div class="translation-detail" style="margin-top:8px;color:var(--text-muted);">加载详情失败</div>`);
    }
  }

  loadPage(1);
}

function formatTime(ts) {
  if (!ts) return '';
  const d = new Date(ts);
  const now = new Date();
  if (d.toDateString() === now.toDateString()) return d.toTimeString().slice(0, 5);
  return `${d.getFullYear()}-${(d.getMonth()+1).toString().padStart(2,'0')}-${d.getDate().toString().padStart(2,'0')} ${d.toTimeString().slice(0,5)}`;
}
