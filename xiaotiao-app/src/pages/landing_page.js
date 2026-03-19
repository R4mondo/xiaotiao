// Public Landing Page — 公开门面介绍页 (登录前展示)
import { fetchAPIGet } from '../api.js';

export function renderLandingPage() {
  return `
    <div class="landing">
      <!-- Hero Section -->
      <section class="landing__hero">
        <div class="landing__hero-content">
          <div class="landing__badge">🎓 华东政法大学</div>
          <h1 class="landing__title">
            <span class="landing__title-accent">再译</span>
            <br>涉外法治多模态学习平台
          </h1>
          <p class="landing__subtitle">
            融合 AI 智能分析，打造法学英语学习新范式。<br>
            主题探索 · 文献研究 · 智能翻译 · 一站式学术助手
          </p>
          <div class="landing__hero-actions">
            <button class="btn btn--primary btn--lg landing__cta" onclick="location.hash='#/login'">
              🚀 立即开始
            </button>
            <button class="btn btn--secondary btn--lg" onclick="document.getElementById('landing-features').scrollIntoView({behavior:'smooth'})">
              📖 了解更多
            </button>
          </div>
          <div class="landing__stats">
            <div class="landing__stat">
              <div class="landing__stat-num">3+</div>
              <div class="landing__stat-label">核心功能模块</div>
            </div>
            <div class="landing__stat">
              <div class="landing__stat-num">AI</div>
              <div class="landing__stat-label">多模型智能驱动</div>
            </div>
            <div class="landing__stat">
              <div class="landing__stat-num">∞</div>
              <div class="landing__stat-label">学术文献支持</div>
            </div>
          </div>
        </div>
      </section>

      <!-- Features Section -->
      <section class="landing__section" id="landing-features">
        <div class="container">
          <div class="landing__section-header">
            <div class="landing__section-badge">✨ 核心功能</div>
            <h2 class="landing__section-title">为法学英语学习量身打造</h2>
            <p class="landing__section-desc">三大核心模块，覆盖你的全部学术英语需求</p>
          </div>
          <div class="landing__features-grid">
            <div class="landing__feature-card landing__feature-card--explore">
              <div class="landing__feature-icon">🔍</div>
              <h3 class="landing__feature-title">主题探索</h3>
              <p class="landing__feature-desc">
                输入任意法学主题，AI 自动生成专业学习内容。
                涵盖术语解析、案例分析、双语对照等多维度内容，
                帮助你快速掌握涉外法治前沿知识。
              </p>
              <ul class="landing__feature-list">
                <li>🎯 AI 智能生成学习素材</li>
                <li>📝 中英双语专业术语</li>
                <li>⚖️ 真实法律案例分析</li>
              </ul>
            </div>
            <div class="landing__feature-card landing__feature-card--research">
              <div class="landing__feature-icon">📚</div>
              <h3 class="landing__feature-title">文献研究</h3>
              <p class="landing__feature-desc">
                内置论文库与 PDF 智能阅读器。上传或搜索学术论文，
                AI 自动逐页生成摘要、支持划词翻译与高亮批注，
                让学术阅读事半功倍。
              </p>
              <ul class="landing__feature-list">
                <li>📄 PDF 智能阅读器</li>
                <li>🤖 AI 逐页自动摘要</li>
                <li>🖍️ 划词翻译与高亮批注</li>
              </ul>
            </div>
            <div class="landing__feature-card landing__feature-card--translate">
              <div class="landing__feature-icon">🌐</div>
              <h3 class="landing__feature-title">翻译工作室</h3>
              <p class="landing__feature-desc">
                专业法律文本翻译工具，支持多种翻译风格选择。
                从合同条款到判决书，AI 提供精准的法律术语翻译，
                并附带详细的术语解读。
              </p>
              <ul class="landing__feature-list">
                <li>🔄 多风格翻译选择</li>
                <li>📋 法律术语精准翻译</li>
                <li>💡 翻译解读与建议</li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      <!-- How It Works Section -->
      <section class="landing__section landing__section--alt">
        <div class="container">
          <div class="landing__section-header">
            <div class="landing__section-badge">📋 使用指南</div>
            <h2 class="landing__section-title">三步开始你的学习之旅</h2>
          </div>
          <div class="landing__steps">
            <div class="landing__step">
              <div class="landing__step-num">01</div>
              <div class="landing__step-content">
                <h3>注册账号</h3>
                <p>快速注册，设置你的学科领域和英语水平，系统将为你提供个性化推荐</p>
              </div>
            </div>
            <div class="landing__step-arrow">→</div>
            <div class="landing__step">
              <div class="landing__step-num">02</div>
              <div class="landing__step-content">
                <h3>选择模块</h3>
                <p>根据学习需求选择主题探索、文献研究或翻译工作室</p>
              </div>
            </div>
            <div class="landing__step-arrow">→</div>
            <div class="landing__step">
              <div class="landing__step-num">03</div>
              <div class="landing__step-content">
                <h3>AI 辅助学习</h3>
                <p>AI 自动生成学习内容、智能翻译、论文分析，全程辅助提升</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- Team Section -->
      <section class="landing__section" id="landing-team">
        <div class="container">
          <div class="landing__section-header">
            <div class="landing__section-badge">👥 团队介绍</div>
            <h2 class="landing__section-title">我们的团队</h2>
            <p class="landing__section-desc">来自华东政法大学的跨学科研究团队</p>
          </div>
          <div class="landing__team-grid" id="landing-team-grid">
            <div style="text-align:center;color:var(--text-muted);padding:40px;">
              加载中...
            </div>
          </div>
        </div>
      </section>

      <!-- CTA Section -->
      <section class="landing__section landing__section--cta">
        <div class="container" style="text-align:center;">
          <h2 class="landing__section-title" style="color:#fff;">准备好开始了吗？</h2>
          <p class="landing__section-desc" style="color:rgba(255,255,255,0.8);">
            注册账号，即刻体验 AI 驱动的法学英语学习新方式
          </p>
          <button class="btn btn--primary btn--lg landing__cta" onclick="location.hash='#/login'" style="margin-top:24px;">
            🚀 免费注册开始
          </button>
        </div>
      </section>
    </div>
  `;
}

export async function initLandingPage() {
  // Load team members from public API
  try {
    const res = await fetch((import.meta.env.VITE_API_BASE_URL || '').replace(/\/api\/v1\/?$/, '') + '/api/team-members');
    if (res.ok) {
      const data = await res.json();
      const members = data.members || [];
      const grid = document.getElementById('landing-team-grid');
      if (grid && members.length > 0) {
        grid.innerHTML = members.map(m => `
          <div class="landing__team-card">
            <div class="landing__team-avatar" style="background-image:url('${m.avatar_url || ''}');">
              ${!m.avatar_url ? '<span>' + (m.name || '?')[0] + '</span>' : ''}
            </div>
            <div class="landing__team-name">${m.name || '成员'}</div>
            <div class="landing__team-role">${m.role || ''}</div>
            <div class="landing__team-bio">${m.bio || ''}</div>
          </div>
        `).join('');
      } else if (grid) {
        grid.innerHTML = '<div style="text-align:center;color:var(--text-muted);padding:40px;grid-column:1/-1;">团队成员信息即将更新</div>';
      }
    }
  } catch (_e) {
    const grid = document.getElementById('landing-team-grid');
    if (grid) grid.innerHTML = '<div style="text-align:center;color:var(--text-muted);padding:40px;grid-column:1/-1;">团队成员信息即将更新</div>';
  }

  // Scroll-in animations
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('in-view');
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.1 });

  document.querySelectorAll('.landing__feature-card, .landing__step, .landing__team-card').forEach(el => {
    observer.observe(el);
  });
}
