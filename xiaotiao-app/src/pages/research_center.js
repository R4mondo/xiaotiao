// V2.0 Research Center — Hub page for 文献研究中心
import { escapeHtml } from '../utils/sanitize.js';
import { fetchAPIGet } from '../api.js';

export function renderResearchCenter() {
  return `
    <div class="container">
      <div class="page-header">
        <div class="page-header__badge">
          <span class="nav-dot" style="background:var(--research)"></span>
          文献研究中心
        </div>
        <h1 class="page-header__title">文献研究中心</h1>
        <p class="page-header__subtitle">
          论文管理 · AI 文章生成 · 主题追踪 — 一站式学术研究平台
        </p>
      </div>

      <div class="research-hub">
        <!-- 论文库 -->
        <a class="research-hub__card" href="#/research/papers" id="rc-papers">
          <div class="research-hub__icon">📚</div>
          <div class="research-hub__info">
            <div class="research-hub__title">论文库</div>
            <div class="research-hub__desc">搜索、管理和阅读学术论文。支持 AI 解读、PDF 阅读和论文对话。</div>
          </div>
          <div class="research-hub__stat" id="rc-papers-count">
            <span class="research-hub__stat-value">—</span>
            <span class="research-hub__stat-label">已收藏论文</span>
          </div>
          <div class="research-hub__arrow">→</div>
        </a>

        <!-- AI 文章生成 -->
        <a class="research-hub__card" href="#/research/generate" id="rc-generate">
          <div class="research-hub__icon">✨</div>
          <div class="research-hub__info">
            <div class="research-hub__title">AI 文章生成器</div>
            <div class="research-hub__desc">粘贴英文法律文本，AI 为你逐段解读重点、生成翻译和注释。</div>
          </div>
          <div class="research-hub__arrow">→</div>
        </a>

        <!-- 主题追踪 -->
        <a class="research-hub__card" href="#/research/tracker" id="rc-tracker">
          <div class="research-hub__icon">🔍</div>
          <div class="research-hub__info">
            <div class="research-hub__title">主题追踪</div>
            <div class="research-hub__desc">追踪学术领域的最新论文动态，多源检索自动发现论文。</div>
          </div>
          <div class="research-hub__stat" id="rc-tracker-count">
            <span class="research-hub__stat-value">—</span>
            <span class="research-hub__stat-label">追踪主题</span>
          </div>
          <div class="research-hub__arrow">→</div>
        </a>
      </div>

      <!-- 最近阅读 -->
      <div class="glass-panel" style="margin-top: 24px; padding: 24px;">
        <div class="panel__header" style="margin-bottom: 16px;">
          <div class="panel__title">
            <span class="panel__title-icon" style="background:var(--research)"></span>
            近期活动
          </div>
        </div>
        <div id="rc-recent" class="rc-recent">
          <div class="result-empty">
            <div class="result-empty__icon">📖</div>
            <div class="result-empty__text">开始阅读论文后，最近活动会显示在这里</div>
          </div>
        </div>
      </div>
    </div>
  `;
}

export function initResearchCenter() {
  // Load paper count
  fetchAPIGet('/papers?limit=1').then(data => {
    const countEl = document.querySelector('#rc-papers-count .research-hub__stat-value');
    if (countEl && data && typeof data.total === 'number') {
      countEl.textContent = data.total;
    }
  }).catch(() => {});

  // Load tracker topic count
  fetchAPIGet('/tracker/topics').then(data => {
    const countEl = document.querySelector('#rc-tracker-count .research-hub__stat-value');
    if (countEl && Array.isArray(data)) {
      countEl.textContent = data.length;
    }
  }).catch(() => {});
}
