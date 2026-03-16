// Enhanced hash-based router for SPA — supports dynamic routes like /papers/:id
export class Router {
  constructor(containerId) {
    this.container = document.getElementById(containerId);
    this.routes = [];
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

  resolve() {
    const hash = window.location.hash.slice(1) || '/';
    let matched = null;
    let params = {};

    for (const route of this.routes) {
      const m = hash.match(route.regex);
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
      this.updateNavLinks(hash);
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
