import { login, register, isAuthed } from '../auth.js';

export function renderLoginPage() {
  return `
    <section class="auth-hero">
      <div class="auth-hero__bg"></div>
      <div class="auth-card">
        <div class="auth-card__brand">
          <div class="auth-card__logo">译</div>
          <div>
            <div class="auth-card__title">再译</div>
            <div class="auth-card__subtitle">华东政法大学涉外法治多模态学习平台</div>
          </div>
        </div>
        <div class="auth-card__tabs">
          <button class="auth-tab active" data-tab="login">登录</button>
          <button class="auth-tab" data-tab="register">注册</button>
        </div>
        <div class="auth-card__body">
          <div class="auth-pane active" data-pane="login">
            <div class="input-group">
              <label class="input-label">用户名</label>
              <input class="input-field" id="login-username" placeholder="请输入用户名" />
            </div>
            <div class="input-group">
              <label class="input-label">密码</label>
              <input type="password" class="input-field" id="login-password" placeholder="请输入密码" />
            </div>
            <button class="btn btn--primary btn--lg" id="btn-login" style="width:100%;">登录并进入</button>
          </div>
          <div class="auth-pane" data-pane="register">
            <div class="input-group">
              <label class="input-label">用户名</label>
              <input class="input-field" id="register-username" placeholder="请输入用户名" />
            </div>
            <div class="input-group">
              <label class="input-label">密码</label>
              <input type="password" class="input-field" id="register-password" placeholder="设置登录密码" />
            </div>
            <button class="btn btn--secondary btn--lg" id="btn-register" style="width:100%;">创建账号</button>
          </div>
        </div>
        <div class="auth-card__hint">
          首次使用请先注册账号。登录后可访问论文库、主题探索、翻译工作室等功能。
        </div>
        <div style="text-align:right;margin-top:12px;">
          <a href="/admin" target="_blank" style="font-size:0.75rem;color:var(--text-muted,#64748b);opacity:0.6;text-decoration:none;transition:opacity .2s;" onmouseover="this.style.opacity='1'" onmouseout="this.style.opacity='0.6'">🔧 开发者登录</a>
        </div>
      </div>
    </section>
  `;
}

export function initLoginPage() {
  if (isAuthed()) {
    window.location.hash = '#/home';
    return;
  }

  const tabs = Array.from(document.querySelectorAll('.auth-tab'));
  const panes = Array.from(document.querySelectorAll('.auth-pane'));
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => t.classList.remove('active'));
      panes.forEach(p => p.classList.remove('active'));
      tab.classList.add('active');
      const pane = panes.find(p => p.dataset.pane === tab.dataset.tab);
      if (pane) pane.classList.add('active');
    });
  });

  const loginBtn = document.getElementById('btn-login');
  loginBtn.addEventListener('click', async () => {
    const username = document.getElementById('login-username').value.trim();
    const password = document.getElementById('login-password').value;
    if (!username || !password) {
      window.showToast('请输入用户名和密码', 'warning');
      return;
    }
    loginBtn.disabled = true;
    loginBtn.textContent = '登录中...';
    try {
      await login(username, password);
      window.showToast('登录成功', 'success');
      window.location.hash = '#/home';
    } catch (err) {
      window.showToast(err.message || '登录失败', 'error');
    } finally {
      loginBtn.disabled = false;
      loginBtn.textContent = '登录并进入';
    }
  });

  const registerBtn = document.getElementById('btn-register');
  registerBtn.addEventListener('click', async () => {
    const username = document.getElementById('register-username').value.trim();
    const password = document.getElementById('register-password').value;
    if (!username || !password) {
      window.showToast('请输入用户名和密码', 'warning');
      return;
    }
    registerBtn.disabled = true;
    registerBtn.textContent = '创建中...';
    try {
      await register(username, password);
      window.showToast('注册成功，已自动登录', 'success');
      window.location.hash = '#/home';
    } catch (err) {
      window.showToast(err.message || '注册失败', 'error');
    } finally {
      registerBtn.disabled = false;
      registerBtn.textContent = '创建账号';
    }
  });
}
