// V2.0 Profile Settings Page — 画像设置中心 (Multi-Select Support)
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
      // Migrate legacy string values to arrays
      if (profile.subject_field && typeof profile.subject_field === 'string') {
        profile.subject_field = [profile.subject_field];
      }
      if (profile.specialty && typeof profile.specialty === 'string') {
        profile.specialty = [profile.specialty];
      }
      render();
    } catch (e) {
      container.innerHTML = `<div class="glass-panel" style="padding:24px;"><div class="result-empty"><div class="result-empty__icon">❌</div><div class="result-empty__text">加载失败：${e.message}</div></div></div>`;
    }
  }

  function render() {
    const examLabel = findLabel(fieldConfig.exam_types, profile.exam_type);
    const selectedFields = Array.isArray(profile.subject_field) ? profile.subject_field : (profile.subject_field ? [profile.subject_field] : []);
    const selectedSpecs = Array.isArray(profile.specialty) ? profile.specialty : (profile.specialty ? [profile.specialty] : []);
    const fieldLabels = selectedFields.map(id => findLabel(fieldConfig.subject_fields, id) || id).join('、') || '未设置';
    const specLabels = selectedSpecs.map(id => id).join('、') || '未设置';
    const levelLabel = findLabel(fieldConfig.eng_levels, profile.eng_level);
    const tags = (profile.interest_tags || []).join(', ') || '未设置';

    // Collect all specialties for selected fields
    const allSpecialties = [];
    selectedFields.forEach(fid => {
      const specs = fieldConfig._specialtiesCache?.[fid] || [];
      specs.forEach(s => {
        if (!allSpecialties.find(x => x.id === s.id)) allSpecialties.push(s);
      });
    });

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
          <div class="profile-card__label">📚 学科领域 <span style="font-size:.7rem;color:var(--text-muted);font-weight:normal">（可多选）</span></div>
          <div class="profile-card__value">${fieldLabels}</div>
          <div class="profile-tags" id="ps-subject-fields">
            ${(fieldConfig.subject_fields || []).map(f =>
              `<button class="onboarding__tag ${selectedFields.includes(f.id) ? 'selected' : ''}" data-field="${f.id}">${f.label}</button>`
            ).join('')}
          </div>
        </div>

        <div class="profile-card__section">
          <div class="profile-card__label">🔬 细分专业 <span style="font-size:.7rem;color:var(--text-muted);font-weight:normal">（可多选，根据学科自动加载）</span></div>
          <div class="profile-card__value">${specLabels}</div>
          <div class="profile-tags" id="ps-specialties">
            <span style="color:var(--text-muted);font-size:.8rem">请先选择学科领域...</span>
          </div>
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

    // Load specialties for selected fields
    loadSpecialtiesForFields(selectedFields);

    // Bind subject field tag click (multi-select)
    document.querySelectorAll('#ps-subject-fields .onboarding__tag').forEach(btn => {
      btn.addEventListener('click', () => {
        btn.classList.toggle('selected');
        const newFields = [];
        document.querySelectorAll('#ps-subject-fields .onboarding__tag.selected').forEach(b => {
          newFields.push(b.dataset.field);
        });
        loadSpecialtiesForFields(newFields);
      });
    });

    document.getElementById('ps-save').addEventListener('click', saveProfile);

    // Tag toggle for interest tags
    document.querySelectorAll('#ps-tags .onboarding__tag').forEach(btn => {
      btn.addEventListener('click', () => btn.classList.toggle('selected'));
    });
  }

  async function loadSpecialtiesForFields(fields) {
    const specContainer = document.getElementById('ps-specialties');
    if (!specContainer) return;
    if (!fields || fields.length === 0) {
      specContainer.innerHTML = '<span style="color:var(--text-muted);font-size:.8rem">请先选择学科领域...</span>';
      return;
    }

    // Initialize cache
    if (!fieldConfig._specialtiesCache) fieldConfig._specialtiesCache = {};

    // Load specialties for all selected fields
    const allSpecs = [];
    for (const field of fields) {
      if (!fieldConfig._specialtiesCache[field]) {
        try {
          const data = await fetchAPIGet(`/config/specialties?field=${field}`);
          fieldConfig._specialtiesCache[field] = data.specialties || [];
        } catch (_e) {
          fieldConfig._specialtiesCache[field] = [];
        }
      }
      const fieldLabel = findLabel(fieldConfig.subject_fields, field) || field;
      fieldConfig._specialtiesCache[field].forEach(s => {
        allSpecs.push({ ...s, fieldLabel });
      });
    }

    const selectedSpecs = Array.isArray(profile.specialty) ? profile.specialty : (profile.specialty ? [profile.specialty] : []);

    if (allSpecs.length === 0) {
      specContainer.innerHTML = '<span style="color:var(--text-muted);font-size:.8rem">该学科暂无细分专业</span>';
      return;
    }

    specContainer.innerHTML = allSpecs.map(s =>
      `<button class="onboarding__tag ${selectedSpecs.includes(s.id) ? 'selected' : ''}" data-spec="${s.id}" title="${s.fieldLabel}">${s.label}</button>`
    ).join('');

    // Bind specialty tag click (multi-select)
    specContainer.querySelectorAll('.onboarding__tag').forEach(btn => {
      btn.addEventListener('click', () => btn.classList.toggle('selected'));
    });
  }

  async function saveProfile() {
    const saveBtn = document.getElementById('ps-save');
    saveBtn.disabled = true;
    saveBtn.textContent = '保存中...';

    // Collect selected subject fields (multi)
    const selectedFields = [];
    document.querySelectorAll('#ps-subject-fields .onboarding__tag.selected').forEach(btn => {
      selectedFields.push(btn.dataset.field);
    });

    // Collect selected specialties (multi)
    const selectedSpecs = [];
    document.querySelectorAll('#ps-specialties .onboarding__tag.selected').forEach(btn => {
      selectedSpecs.push(btn.dataset.spec);
    });

    // Collect interest tags
    const selectedTags = [];
    document.querySelectorAll('#ps-tags .onboarding__tag.selected').forEach(btn => {
      selectedTags.push(btn.dataset.tag);
    });

    const updates = {
      exam_type: document.getElementById('ps-exam-type').value || undefined,
      subject_field: selectedFields.length ? selectedFields : undefined,
      specialty: selectedSpecs.length ? selectedSpecs : undefined,
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
