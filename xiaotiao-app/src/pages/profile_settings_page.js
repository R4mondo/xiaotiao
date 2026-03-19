// V2.0 Profile Settings Page — 画像设置中心
import { fetchAPIGet, fetchAPI } from '../api.js';

export function renderProfileSettingsPage() {
  return `
    <div class="container">
      <div class="page-header">
        <div class="page-header__badge">
          <span class="nav-dot" style="background:var(--topic)"></span>
          用户设置
        </div>
        <h1 class="page-header__title">画像设置中心</h1>
        <p class="page-header__subtitle">
          管理你的学习偏好，系统将根据这些信息为你提供个性化推荐
        </p>
      </div>

      <div class="profile-settings" id="profile-settings">
        <div class="glass-panel" style="padding: 24px;">
          <div class="profile-loading">加载中...</div>
        </div>
      </div>
    </div>
  `;
}

export function initProfileSettingsPage() {
  const container = document.getElementById('profile-settings');
  let profile = {};
  let fieldConfig = {};

  async function load() {
    try {
      const [profileRes, configRes] = await Promise.all([
        fetchAPIGet('/user/profile'),
        fetchAPIGet('/config/fields'),
      ]);
      profile = profileRes.profile || {};
      fieldConfig = configRes;
      render();
    } catch (e) {
      container.innerHTML = `<div class="glass-panel" style="padding:24px;"><div class="result-empty"><div class="result-empty__icon">❌</div><div class="result-empty__text">加载失败：${e.message}</div></div></div>`;
    }
  }

  function render() {
    const examLabel = findLabel(fieldConfig.exam_types, profile.exam_type);
    const fieldLabel = findLabel(fieldConfig.subject_fields, profile.subject_field);
    const levelLabel = findLabel(fieldConfig.eng_levels, profile.eng_level);
    const tags = (profile.interest_tags || []).join(', ') || '未设置';

    container.innerHTML = `
      <div class="glass-panel profile-card" style="padding: 24px;">
        <div class="profile-card__section">
          <div class="profile-card__label">🎯 备考目标</div>
          <div class="profile-card__value">${examLabel || '未设置'}</div>
          <select class="form-select profile-select" id="ps-exam-type">
            <option value="">请选择...</option>
            ${(fieldConfig.exam_types || []).map(t =>
              `<option value="${t.id}" ${profile.exam_type === t.id ? 'selected' : ''}>${t.label}</option>`
            ).join('')}
          </select>
        </div>

        <div class="profile-card__section">
          <div class="profile-card__label">📚 学科领域</div>
          <div class="profile-card__value">${fieldLabel || '未设置'}</div>
          <select class="form-select profile-select" id="ps-subject-field">
            <option value="">请选择...</option>
            ${(fieldConfig.subject_fields || []).map(t =>
              `<option value="${t.id}" ${profile.subject_field === t.id ? 'selected' : ''}>${t.label}</option>`
            ).join('')}
          </select>
        </div>

        <div class="profile-card__section">
          <div class="profile-card__label">🔬 细分专业</div>
          <div class="profile-card__value">${profile.specialty || '未设置'}</div>
          <select class="form-select profile-select" id="ps-specialty">
            <option value="">加载中...</option>
          </select>
        </div>

        <div class="profile-card__section">
          <div class="profile-card__label">📊 英语水平</div>
          <div class="profile-card__value">${levelLabel || '未设置'}</div>
          <select class="form-select profile-select" id="ps-eng-level">
            <option value="">请选择...</option>
            ${(fieldConfig.eng_levels || []).map(l =>
              `<option value="${l.id}" ${profile.eng_level === l.id ? 'selected' : ''}>${l.label} — ${l.description || ''}</option>`
            ).join('')}
          </select>
        </div>

        <div class="profile-card__section">
          <div class="profile-card__label">🏷️ 兴趣标签</div>
          <div class="profile-card__value">${tags}</div>
          <div class="profile-tags" id="ps-tags">
            ${(fieldConfig.interest_tags || []).map(t =>
              `<button class="onboarding__tag ${(profile.interest_tags || []).includes(t) ? 'selected' : ''}" data-tag="${t}">${t}</button>`
            ).join('')}
          </div>
        </div>

        <div class="profile-card__actions">
          <button class="btn btn--primary" id="ps-save">💾 保存设置</button>
        </div>
      </div>
    `;

    // Load specialties
    loadSpecialties(profile.subject_field || 'law');

    // Bind events
    document.getElementById('ps-subject-field').addEventListener('change', (e) => {
      loadSpecialties(e.target.value);
    });

    document.getElementById('ps-save').addEventListener('click', saveProfile);

    // Tag toggle
    document.querySelectorAll('#ps-tags .onboarding__tag').forEach(btn => {
      btn.addEventListener('click', () => btn.classList.toggle('selected'));
    });
  }

  async function loadSpecialties(field) {
    const select = document.getElementById('ps-specialty');
    if (!select) return;
    try {
      const data = await fetchAPIGet(`/config/specialties?field=${field}`);
      select.innerHTML = `<option value="">请选择...</option>` +
        (data.specialties || []).map(s =>
          `<option value="${s.id}" ${profile.specialty === s.id ? 'selected' : ''}>${s.label}</option>`
        ).join('');
    } catch (_e) {
      select.innerHTML = '<option value="">暂无数据</option>';
    }
  }

  async function saveProfile() {
    const saveBtn = document.getElementById('ps-save');
    saveBtn.disabled = true;
    saveBtn.textContent = '保存中...';

    const selectedTags = [];
    document.querySelectorAll('#ps-tags .onboarding__tag.selected').forEach(btn => {
      selectedTags.push(btn.dataset.tag);
    });

    const updates = {
      exam_type: document.getElementById('ps-exam-type').value || undefined,
      subject_field: document.getElementById('ps-subject-field').value || undefined,
      specialty: document.getElementById('ps-specialty').value || undefined,
      eng_level: document.getElementById('ps-eng-level').value || undefined,
      interest_tags: selectedTags.length ? selectedTags : undefined,
    };

    // Remove undefined keys
    Object.keys(updates).forEach(k => { if (updates[k] === undefined) delete updates[k]; });

    try {
      const result = await fetchAPI('/user/profile', updates, { method: 'PUT' });
      profile = result.profile || profile;
      localStorage.setItem('zaiyi_profile', JSON.stringify(profile));
      if (window.showToast) window.showToast('画像设置已保存', 'success');
      render();
    } catch (e) {
      if (window.showToast) window.showToast('保存失败: ' + e.message, 'error');
    }

    saveBtn.disabled = false;
    saveBtn.textContent = '💾 保存设置';
  }

  function findLabel(items, id) {
    if (!items || !id) return null;
    const item = items.find(i => i.id === id);
    return item ? item.label : id;
  }

  load();
}
