// Enhanced hash-based router for SPA — supports dynamic routes like /papers/:id
export class Router {
  constructor(containerId) {
    this.container = document.getElementById(containerId);
    this.routes = [];
    this.guard = null;
    window.addEventListener('hashchange', () => this.resolve());
  }

  register(path, renderer, init = null) {
    // Convert path pattern to regex, e.g. /papers/:id → /papers/([^/]+)
    const paramNames = [];
    const regexStr = path.replace(/:([^/]+)/g, (_match, name) => {
      paramNames.push(name);
      return '([^/]+)';
    });
    this.routes.push({
      path,
      regex: new RegExp(`^${regexStr}$`),
      paramNames,
      renderer,
      init
    });
    return this;
  }

  setGuard(guardFn) {
    this.guard = guardFn;
    return this;
  }

  resolve() {
    const rawHash = window.location.hash.slice(1) || '/';
    const hashPath = rawHash.split('?')[0] || '/';
    const normalized = hashPath.replace(/\/+$/, '') || '/';
    let matched = null;
    let params = {};

    if (typeof this.guard === 'function') {
      const redirect = this.guard(normalized);
      if (redirect && redirect !== normalized) {
        window.location.hash = `#${redirect}`;
        return;
      }
    }

    document.body.classList.toggle('auth-view', normalized === '/' || normalized === '/landing' || normalized === '/login');

    // Page-level cleanup hooks (if any)
    const cleanupFns = [
      window.__paperCleanup,
      window.__readerCleanup,
      window.__trackerCleanup,
      window.__topicQuickAddCleanup,
      window.__wordSelectorCleanup
    ];
    cleanupFns.forEach(fn => {
      if (typeof fn === 'function') {
        try { fn(); } catch (_e) {}
      }
    });

    for (const route of this.routes) {
      const m = normalized.match(route.regex);
      if (m) {
        matched = route;
        route.paramNames.forEach((name, i) => {
          params[name] = decodeURIComponent(m[i + 1]);
        });
        break;
      }
    }

    // Fallback to home
    if (!matched) {
      matched = this.routes.find(r => r.path === '/');
      params = {};
    }

    if (matched && this.container) {
      this.container.innerHTML = matched.renderer(params);
      if (matched.init) matched.init(params);
      this.updateNavLinks(normalized);
    }
  }

  updateNavLinks(currentHash) {
    document.querySelectorAll('.nav-link').forEach(link => {
      const route = link.dataset.route;
      // Exact match or prefix match for nested routes
      const isActive = route === currentHash ||
        (route !== '/' && currentHash.startsWith(route));
      link.classList.toggle('active', isActive);
    });
  }
}
