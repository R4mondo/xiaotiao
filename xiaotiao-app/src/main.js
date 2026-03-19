// ZaiYi App — Main Entry with Liquid Glass Interaction System — V2.0
import './style.css';
import { Router } from './router.js';
import {
  renderHome, initHome, renderTopicExplorer, initTopicExplorer,
  renderArticleLab, initArticleLab,
  renderTranslationStudio, initTranslationStudio
} from './pages.js';
import { renderLoginPage, initLoginPage } from './pages/login_page.js';
import { renderLandingPage, initLandingPage } from './pages/landing_page.js';
import { renderVocabPage, initVocabPage } from './vocab_page.js';
import { renderProgressPage, initProgressPage } from './progress_page.js';
import { renderPaperPage, initPaperPage } from './pages/paper_page.js';
import { renderPaperDetailPage, initPaperDetailPage } from './pages/paper_detail_page.js';
import { renderPaperReaderPage, initPaperReaderPage } from './pages/paper_reader_page.js';
import { renderTrackerPage, initTrackerPage } from './pages/tracker_page.js';
import { renderOnboardingPage, initOnboardingPage } from './pages/onboarding_page.js';
import { renderResearchCenter, initResearchCenter } from './pages/research_center.js';
import { renderProfileSettingsPage, initProfileSettingsPage } from './pages/profile_settings_page.js';
import { renderTranslationHistoryPage, initTranslationHistoryPage } from './pages/translation_history_page.js';
import { isAuthed, logout, getAuthUser } from './auth.js';
import { initGlobalWordSelector, destroyGlobalWordSelector } from './components/word_selector.js';
import { initTaskManager } from './components/task_manager.js';
import { initSidebar } from './components/sidebar.js';

const router = new Router('app');

// V2.0: Updated route guard with onboarding check
router.setGuard((path) => {
  // Public pages accessible without login
  const publicPaths = ['/', '/landing', '/login'];
  if (!isAuthed() && !publicPaths.includes(path)) return '/landing';
  if (isAuthed() && (path === '/' || path === '/landing' || path === '/login')) {
    const profile = localStorage.getItem('zaiyi_profile');
    if (!profile || !JSON.parse(profile).onboarding_completed) return '/onboarding';
    return '/home';
  }
  return null;
});

// V2.0: Core routes
router.register('/', renderLandingPage, initLandingPage);
router.register('/landing', renderLandingPage, initLandingPage);
router.register('/login', renderLoginPage, initLoginPage);
router.register('/home', renderHome, initHome);
router.register('/onboarding', renderOnboardingPage, initOnboardingPage);

// V2.0: Research Center (merged)
router.register('/research', renderResearchCenter, initResearchCenter);
router.register('/research/papers', renderPaperPage, initPaperPage);
router.register('/research/papers/:id', renderPaperDetailPage, initPaperDetailPage);
router.register('/research/papers/:id/read', renderPaperReaderPage, initPaperReaderPage);
router.register('/research/generate', renderArticleLab, initArticleLab);
router.register('/research/tracker', renderTrackerPage, initTrackerPage);

// V2.0: Topic Explorer (renamed route)
router.register('/explore', renderTopicExplorer, initTopicExplorer);

// V2.0: Settings
router.register('/settings/profile', renderProfileSettingsPage, initProfileSettingsPage);

// Legacy routes still functional (hidden from nav)
router.register('/vocab', renderVocabPage, initVocabPage);
router.register('/progress', renderProgressPage, initProgressPage);
router.register('/translation', renderTranslationStudio, initTranslationStudio);
router.register('/translation/history', renderTranslationHistoryPage, initTranslationHistoryPage);

// Legacy route redirects (backwards compatibility)
router.register('/papers', () => { location.hash = '#/research/papers'; return '<div></div>'; });
router.register('/papers/:id', (p) => { location.hash = `#/research/papers/${p.id}`; return '<div></div>'; });
router.register('/papers/:id/read', (p) => { location.hash = `#/research/papers/${p.id}/read`; return '<div></div>'; });
router.register('/topic', () => { location.hash = '#/explore'; return '<div></div>'; });
router.register('/article', () => { location.hash = '#/research/generate'; return '<div></div>'; });
router.register('/tracker', () => { location.hash = '#/research/tracker'; return '<div></div>'; });

router.resolve();

// ══════════════════════════════════════════════
// INTERACTION SYSTEM — Apple Liquid Glass
// ══════════════════════════════════════════════

// ── 0. Global Initializations ────────────────
function initGlobalInteractions() {
  // Handle internal navigation links (e.g., from hero section)
  document.querySelectorAll('a[data-route]').forEach(node => {
    node.addEventListener('click', (e) => {
      e.preventDefault();
      const path = new URL(node.href).hash || '#/';
      window.location.hash = path;
    });
  });

  // Interactive card tilts in JS for any element requesting it
  // (Currently not implemented, placeholder for future feature)
}

function initAuthActions() {
  const logoutBtn = document.getElementById('btn-logout');
  if (!logoutBtn) return;
  logoutBtn.addEventListener('click', async () => {
    logoutBtn.disabled = true;
    logoutBtn.textContent = '退出中...';
    await logout();
    localStorage.removeItem('zaiyi_profile');
    logoutBtn.textContent = '退出登录';
    logoutBtn.disabled = false;
    window.location.hash = '#/';
  });
}

// V2.0: User avatar dropdown
function initUserMenu() {
  const avatar = document.getElementById('btn-user-avatar');
  const dropdown = document.getElementById('user-dropdown');
  if (!avatar || !dropdown) return;

  avatar.addEventListener('click', (e) => {
    e.stopPropagation();
    dropdown.classList.toggle('is-open');
  });
  document.addEventListener('click', () => {
    dropdown.classList.remove('is-open');
  });

  // Display username
  const user = getAuthUser();
  const nameEl = document.getElementById('dropdown-username');
  if (user && nameEl) {
    nameEl.textContent = user.username || '用户';
  }
}

// ── Theme Config System ──────────────────────
function initThemeConfig() {
  const fab = document.getElementById('theme-config-fab');
  const overlay = document.getElementById('theme-config-overlay');
  if (!fab || !overlay) return;

  const closeBtn = overlay.querySelector('[data-theme-close]');
  const buttons = Array.from(overlay.querySelectorAll('.theme-btn'));
  const root = document.documentElement;
  const storageKey = 'xt-theme';

  const updateActive = (theme) => {
    buttons.forEach(btn => {
      btn.classList.toggle('active', btn.dataset.theme === theme);
    });
  };

  const setTheme = (theme) => {
    if (theme) {
      root.setAttribute('data-theme', theme);
      localStorage.setItem(storageKey, theme);
    } else {
      root.removeAttribute('data-theme');
      localStorage.removeItem(storageKey);
    }
    updateActive(theme);
  };

  const open = () => {
    overlay.classList.add('is-open');
    overlay.setAttribute('aria-hidden', 'false');
  };
  const close = () => {
    overlay.classList.remove('is-open');
    overlay.setAttribute('aria-hidden', 'true');
  };

  const saved = localStorage.getItem(storageKey);
  if (saved) {
    setTheme(saved);
  } else {
    updateActive(root.dataset.theme || '');
  }

  fab.addEventListener('click', open);
  if (closeBtn) closeBtn.addEventListener('click', close);
  overlay.addEventListener('click', (e) => {
    if (e.target === overlay) close();
  });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && overlay.classList.contains('is-open')) {
      close();
    }
  });
  buttons.forEach(btn => {
    btn.addEventListener('click', () => {
      setTheme(btn.dataset.theme || '');
    });
  });
}


// ── 1. Button Ripple Effect ──────────────────
// Creates a radial glow ripple from the click point.
// Uses CSS @keyframes rippleExpand for the animation.

function initRippleSystem() {
  document.addEventListener('mousedown', (e) => {
    const btn = e.target.closest('.btn');
    if (!btn || btn.disabled) return;

    // Remove any existing ripple
    const old = btn.querySelector('.ripple');
    if (old) old.remove();

    // Create ripple element positioned at click point
    const ripple = document.createElement('span');
    ripple.className = 'ripple';

    const rect = btn.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height) * 1.4;
    const x = e.clientX - rect.left - size / 2;
    const y = e.clientY - rect.top - size / 2;

    ripple.style.width = size + 'px';
    ripple.style.height = size + 'px';
    ripple.style.left = x + 'px';
    ripple.style.top = y + 'px';

    btn.appendChild(ripple);

    // Cleanup after animation
    ripple.addEventListener('animationend', () => ripple.remove());
  });
}

// ── 2. Segmented Control Slider ──────────────
// Positions a glass indicator behind the active button.
// Uses spring easing for fluid movement with overshoot.

function updateSegmentedSlider(containerId) {
  const container = document.getElementById(containerId);
  if (!container) return;

  const slider = container.querySelector('.segmented__slider');
  const activeBtn = container.querySelector('.segmented__btn.active');
  if (!slider || !activeBtn) return;

  const containerRect = container.getBoundingClientRect();
  const btnRect = activeBtn.getBoundingClientRect();

  // Position slider relative to container (account for padding)
  const left = btnRect.left - containerRect.left;
  const width = btnRect.width;

  slider.style.left = left + 'px';
  slider.style.width = width + 'px';
}

// Expose globally so pages.js can call it
window.__updateSegmentedSlider = updateSegmentedSlider;

// Initialize all segmented controls on page render
function initSegmentedControls() {
  const containers = document.querySelectorAll('.segmented');
  containers.forEach(container => {
    if (container.id) {
      const slider = container.querySelector('.segmented__slider');
      if (slider) {
        // Special case: Navbar segmented slider should NOT reset its transition
        // on every route change because it persists between pages.
        // It should seamlessly slide to the new active link.
        if (container.id === 'navbar-segmented' && window.__navbarInitialized) {
          updateSegmentedSlider(container.id);
          return;
        }
        
        // Normal case: newly rendered controls (like in Article / Translation pages)
        // should avoid animating from 0 width on load.
        // ANIM-05: Use forced reflow instead of double-rAF for reliable init
        slider.style.transition = 'none';
        updateSegmentedSlider(container.id);
        slider.offsetWidth; // force synchronous reflow
        slider.style.transition = '';
        if (container.id === 'navbar-segmented') {
           window.__navbarInitialized = true;
        }
      }
    }
  });
}

// Boot
initGlobalInteractions();
initThemeConfig();
initSegmentedControls();
initAuthActions();
initUserMenu();
initTaskManager();
initSidebar();

// ── 3. Navbar Scroll Enhancement ─────────────
// Increases glass opacity when scrolled, creating depth.

function updateNavbar() {
  const navbar = document.getElementById('navbar');
  if (!navbar) return;

  if (window.scrollY > 30) {
    navbar.classList.add('scrolled');
  } else {
    navbar.classList.remove('scrolled');
  }
}

// ── 4. Background Parallax ───────────────────
// ANIM-01: Use CSS custom property to avoid overriding CSS orbFloat animation.

function updateParallax() {
  const scrollY = window.scrollY;
  const orbs = document.querySelectorAll('.orb');
  orbs.forEach((orb, i) => {
    const speed = 0.015 + i * 0.008;
    orb.style.setProperty('--parallax-y', `${scrollY * speed}px`);
  });
}

// ── 5. Scroll-driven Animation Trigger ───────
// Observes elements entering viewport and triggers entrance.

function initScrollAnimations() {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('in-view');
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });

  // Observe module cards for staggered entrance
  document.querySelectorAll('.module-card, .panel, .hero__stat').forEach(el => {
    observer.observe(el);
  });
}

// ── 6. Combined Scroll Handler ───────────────
// Uses rAF throttle for 60fps performance.

let ticking = false;
window.addEventListener('scroll', () => {
  if (!ticking) {
    requestAnimationFrame(() => {
      updateNavbar();
      updateParallax();
      ticking = false;
    });
    ticking = true;
  }
}, { passive: true });

// ── 7. Page Transition Hook ──────────────
// ANIM-04: Add fade out/in transition on route change.

const originalResolve = router.resolve.bind(router);
router.resolve = function () {
  const appEl = document.getElementById('app');

  // ANIM-04: page leave transition
  // Skip transition on auth-view (login page) to prevent redirect stalling
  const isAuthView = document.body.classList.contains('auth-view');
  if (appEl && appEl.children.length > 0 && window.__routeInitialized && !isAuthView) {
    appEl.classList.add('page-transition-leave');
    let resolved = false;
    const finish = () => {
      if (resolved) return;
      resolved = true;
      appEl.classList.remove('page-transition-leave');
      doResolve();
    };
    appEl.addEventListener('animationend', function handler() {
      appEl.removeEventListener('animationend', handler);
      finish();
    }, { once: true });
    // Timeout fallback: if animationend never fires, proceed anyway
    setTimeout(finish, 200);
  } else {
    doResolve();
  }

  function doResolve() {
    originalResolve();
    window.__routeInitialized = true;

    // Wait for DOM to be ready
    requestAnimationFrame(() => {
      // ANIM-04: page enter transition
      if (appEl) {
        appEl.classList.add('page-transition-enter');
        appEl.addEventListener('animationend', function handler() {
          appEl.removeEventListener('animationend', handler);
          appEl.classList.remove('page-transition-enter');
        }, { once: true });
      }

      updateNavbar();
      
      // Update Active Nav Link
      const hash = window.location.hash.slice(1) || '/';
      // V2.0: Active nav link logic for 3-item navbar
      const navLinks = document.querySelectorAll('.navbar__nav .nav-link');
      navLinks.forEach(link => {
        const route = link.dataset.route;
        const isActive = route === hash || (route !== '/home' && hash.startsWith(route));
        if (isActive) {
          link.classList.add('active');
          const segmentedContainer = document.getElementById('navbar-segmented');
          if (segmentedContainer) {
            segmentedContainer.className = 'navbar__nav segmented';
            if (hash.startsWith('/home')) segmentedContainer.classList.add('segmented--home');
            if (hash.startsWith('/research')) segmentedContainer.classList.add('segmented--research');
            if (hash.startsWith('/explore')) segmentedContainer.classList.add('segmented--explore');
          }
        } else {
          link.classList.remove('active');
        }
      });

      initSegmentedControls();
      initScrollAnimations();

      // Trigger word count on article page
      const articleInput = document.getElementById('article-input');
      if (articleInput) {
        articleInput.dispatchEvent(new Event('input'));
      }

      // Initialize global word selector on all authenticated pages
      if (!document.body.classList.contains('auth-view')) {
        initGlobalWordSelector();
      }
    });
  }
};

// ── Initialize Everything ────────────────────
initRippleSystem();
initThemeConfig();
updateNavbar();

window.addEventListener('resize', () => {
    requestAnimationFrame(() => {
        initSegmentedControls();
    });
});

// Re-resolve to apply post-render hooks
router.resolve();

// ══════════════════════════════════════════════
// IOS-01: TOAST & MODAL UTILITIES — Liquid Glass
// ══════════════════════════════════════════════

// Ensure toast container exists
function getToastContainer() {
  let c = document.querySelector('.toast-container');
  if (!c) {
    c = document.createElement('div');
    c.className = 'toast-container';
    document.body.appendChild(c);
  }
  return c;
}

/**
 * Show a Liquid Glass toast notification.
 * @param {string} message - The message to display
 * @param {'info'|'success'|'error'|'warning'} type - Toast type
 * @param {number} duration - Auto-dismiss in ms (default 3000)
 */
window.showToast = function(message, type = 'info', duration = 3000) {
  const container = getToastContainer();
  const toast = document.createElement('div');
  toast.className = `toast ${type !== 'info' ? 'toast--' + type : ''}`;
  toast.textContent = message;
  container.appendChild(toast);
  setTimeout(() => {
    toast.classList.add('leaving');
    toast.addEventListener('animationend', () => toast.remove());
  }, duration);
};

/**
 * Show a Liquid Glass modal confirm dialog.
 * @param {string} title
 * @param {string} body
 * @param {Object} options
 * @returns {Promise<boolean>}
 */
window.showGlassConfirm = function(title, body, options = {}) {
  return new Promise((resolve) => {
    const overlay = document.createElement('div');
    overlay.className = 'modal-glass-overlay';
    const btnClass = options.danger ? 'modal-glass__btn--danger' : 'modal-glass__btn--confirm';
    const confirmLabel = options.confirmText || '确认';
    const cancelLabel = options.cancelText || '取消';
    overlay.innerHTML = `
      <div class="modal-glass">
        <div class="modal-glass__title">${title}</div>
        <div class="modal-glass__body">${body}</div>
        <div class="modal-glass__actions">
          <button class="modal-glass__btn modal-glass__btn--cancel" id="modal-cancel">${cancelLabel}</button>
          <button class="modal-glass__btn ${btnClass}" id="modal-confirm">${confirmLabel}</button>
        </div>
      </div>
    `;
    document.body.appendChild(overlay);
    overlay.querySelector('#modal-cancel').addEventListener('click', () => {
      overlay.remove();
      resolve(false);
    });
    overlay.querySelector('#modal-confirm').addEventListener('click', () => {
      overlay.remove();
      resolve(true);
    });
    overlay.addEventListener('click', (e) => {
      if (e.target === overlay) { overlay.remove(); resolve(false); }
    });
  });
};
