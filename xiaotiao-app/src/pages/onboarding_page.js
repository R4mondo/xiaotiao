// V2.0 Onboarding Page — 5-step profile setup for new users
import { fetchAPIGet, fetchAPI } from '../api.js';
import { getAuthUser, setAuth } from '../auth.js';

const STEPS = [
  {
    key: 'exam_type',
    title: '你的备考目标是？',
    subtitle: '选择你当前最主要的英语学习目标',
    icon: '🎯',
  },
  {
    key: 'subject_field',
    title: '你的学科领域是？',
    subtitle: '我们将为你推荐相关专业的学习材料',
    icon: '📚',
  },
  {
    key: 'specialty',
    title: '你的细分专业方向',
    subtitle: '进一步精确推荐',
    icon: '🔬',
  },
  {
    key: 'eng_level',
    title: '你的英语水平',
    subtitle: '用于智能调整文章难度和词汇推荐',
    icon: '📊',
  },
  {
    key: 'interest_tags',
    title: '选择你感兴趣的话题',
    subtitle: '可多选，帮助我们个性化推荐',
    icon: '🏷️',
  },
];

export function renderOnboardingPage() {
  return `
    <div class="onboarding">
      <div class="onboarding__card" id="onboarding-card">
        <div class="onboarding__header">
          <div class="onboarding__icon" id="onboarding-icon">🎯</div>
          <h1 class="onboarding__title" id="onboarding-title">欢迎来到再译!</h1>
          <p class="onboarding__subtitle" id="onboarding-subtitle">让我们先了解你，以便提供个性化的学习体验</p>
        </div>
        <div class="onboarding__body" id="onboarding-body">
          <div class="onboarding__loading">加载中...</div>
        </div>
        <div class="onboarding__footer">
          <div class="onboarding__progress">
            ${STEPS.map((_, i) => `<div class="onboarding__dot${i === 0 ? ' active' : ''}" data-step="${i}"></div>`).join('')}
          </div>
          <div class="onboarding__actions">
            <button class="btn btn--ghost" id="onboarding-back" style="display:none;">← 上一步</button>
            <button class="btn btn--ghost" id="onboarding-skip" style="opacity:0.6;font-size:0.85rem;">跳过</button>
            <button class="btn btn--primary" id="onboarding-next">下一步 →</button>
          </div>
        </div>
      </div>
    </div>
  `;
}

export function initOnboardingPage() {
  let currentStep = 0;
  let fieldConfig = null;
  const selections = {
    exam_type: null,
    subject_field: null,
    specialty: null,
    eng_level: null,
    interest_tags: [],
  };

  const body = document.getElementById('onboarding-body');
  const title = document.getElementById('onboarding-title');
  const subtitle = document.getElementById('onboarding-subtitle');
  const icon = document.getElementById('onboarding-icon');
  const nextBtn = document.getElementById('onboarding-next');
  const backBtn = document.getElementById('onboarding-back');
  const skipBtn = document.getElementById('onboarding-skip');

  // Fallback config in case API is unreachable
  const FALLBACK_CONFIG = {
    exam_types: [
      { id: 'kaoyan', label: '考研英语' },
      { id: 'cet4', label: '四级' },
      { id: 'cet6', label: '六级' },
      { id: 'ielts', label: '雅思' },
      { id: 'toefl', label: '托福' },
      { id: 'bar_exam', label: '法律英语/法考' },
      { id: 'other', label: '其他' },
    ],
    subject_fields: [
      { id: 'law', label: '法学' },
      { id: 'finance', label: '金融' },
      { id: 'cs', label: '计算机' },
      { id: 'medicine', label: '医学' },
      { id: 'engineering', label: '工程' },
      { id: 'humanities', label: '人文' },
      { id: 'other', label: '其他' },
    ],
    eng_levels: [
      { id: 'cet4', label: 'CET-4', description: '大学英语四级水平' },
      { id: 'cet6', label: 'CET-6', description: '大学英语六级水平' },
      { id: 'ielts5', label: '雅思 5-6 分', description: '中级英语水平' },
      { id: 'ielts7', label: '雅思 7+ 分', description: '高级英语水平' },
      { id: 'native', label: '接近母语', description: '可无障碍阅读学术文献' },
    ],
    interest_tags: [
      '区块链监管', '跨境金融', '国际仲裁', '知识产权',
      '数据隐私', '人工智能法律', '环境法', '国际贸易',
      '公司治理', '反垄断', '税法', '海商法',
      '劳动法', '消费者保护', '刑事司法', '人权法',
    ],
  };

  async function loadConfig() {
    try {
      fieldConfig = await fetchAPIGet('/config/fields');
      // Validate response has data
      if (!fieldConfig.exam_types || !fieldConfig.exam_types.length) {
        fieldConfig = FALLBACK_CONFIG;
      }
    } catch (e) {
      fieldConfig = FALLBACK_CONFIG;
    }
    renderStep(0);
  }

  function renderStep(stepIdx) {
    currentStep = stepIdx;
    const step = STEPS[stepIdx];

    icon.textContent = step.icon;
    title.textContent = step.title;
    subtitle.textContent = step.subtitle;

    // Update progress dots
    document.querySelectorAll('.onboarding__dot').forEach((dot, i) => {
      dot.classList.toggle('active', i === stepIdx);
      dot.classList.toggle('completed', i < stepIdx);
    });

    backBtn.style.display = stepIdx > 0 ? '' : 'none';
    nextBtn.textContent = stepIdx === STEPS.length - 1 ? '完成设置 ✓' : '下一步 →';

    let html = '';
    switch (step.key) {
      case 'exam_type':
        html = renderOptionGrid(fieldConfig.exam_types, 'exam_type', selections.exam_type);
        break;
      case 'subject_field':
        html = renderOptionGrid(fieldConfig.subject_fields, 'subject_field', selections.subject_field);
        break;
      case 'specialty':
        html = '<div class="onboarding__loading">加载专业方向...</div>';
        loadSpecialties();
        return;
      case 'eng_level':
        html = renderLevelCards(fieldConfig.eng_levels, selections.eng_level);
        break;
      case 'interest_tags':
        html = renderTagGrid(fieldConfig.interest_tags, selections.interest_tags);
        break;
    }
    body.innerHTML = html;
    bindSelectionEvents();
  }

  async function loadSpecialties() {
    const field = selections.subject_field || 'law';
    try {
      const data = await fetchAPIGet(`/config/specialties?field=${field}`);
      body.innerHTML = renderOptionGrid(data.specialties, 'specialty', selections.specialty);
    } catch (_e) {
      body.innerHTML = '<div class="onboarding__empty">暂无细分专业数据</div>';
    }
    bindSelectionEvents();
  }

  function renderOptionGrid(items, key, selected) {
    if (!items || !items.length) return '<div class="onboarding__empty">暂无选项</div>';
    return `<div class="onboarding__grid">
      ${items.map(it => `
        <button class="onboarding__option ${selected === it.id ? 'selected' : ''}"
          data-key="${key}" data-value="${it.id}">
          ${it.label}
        </button>
      `).join('')}
    </div>`;
  }

  function renderLevelCards(levels, selected) {
    if (!levels || !levels.length) return '';
    return `<div class="onboarding__levels">
      ${levels.map(l => `
        <button class="onboarding__level-card ${selected === l.id ? 'selected' : ''}"
          data-key="eng_level" data-value="${l.id}">
          <div class="onboarding__level-label">${l.label}</div>
          <div class="onboarding__level-desc">${l.description || ''}</div>
        </button>
      `).join('')}
    </div>`;
  }

  function renderTagGrid(tags, selected) {
    if (!tags || !tags.length) return '';
    return `<div class="onboarding__tags">
      ${tags.map(t => `
        <button class="onboarding__tag ${selected.includes(t) ? 'selected' : ''}"
          data-tag="${t}">
          ${t}
        </button>
      `).join('')}
    </div>`;
  }

  function bindSelectionEvents() {
    // Single-select options
    body.querySelectorAll('.onboarding__option, .onboarding__level-card').forEach(btn => {
      btn.addEventListener('click', () => {
        const key = btn.dataset.key;
        const value = btn.dataset.value;
        selections[key] = value;
        // Update UI
        btn.parentElement.querySelectorAll('.selected').forEach(el => el.classList.remove('selected'));
        btn.classList.add('selected');
      });
    });
    // Multi-select tags
    body.querySelectorAll('.onboarding__tag').forEach(btn => {
      btn.addEventListener('click', () => {
        const tag = btn.dataset.tag;
        const idx = selections.interest_tags.indexOf(tag);
        if (idx >= 0) {
          selections.interest_tags.splice(idx, 1);
          btn.classList.remove('selected');
        } else {
          selections.interest_tags.push(tag);
          btn.classList.add('selected');
        }
      });
    });
  }

  nextBtn.addEventListener('click', async () => {
    if (currentStep < STEPS.length - 1) {
      renderStep(currentStep + 1);
    } else {
      // Complete onboarding
      await saveProfile();
    }
  });

  backBtn.addEventListener('click', () => {
    if (currentStep > 0) renderStep(currentStep - 1);
  });

  skipBtn.addEventListener('click', async () => {
    selections.onboarding_completed = true;
    await saveProfile();
  });

  async function saveProfile() {
    nextBtn.disabled = true;
    nextBtn.textContent = '保存中...';
    try {
      const payload = { ...selections, onboarding_completed: true };
      await fetchAPI('/user/profile', payload, { method: 'PUT' });
      // Update local storage
      const user = getAuthUser();
      if (user) {
        user.onboarding_completed = true;
        setAuth(null, user);
      }
      // Store profile in localStorage for route guard
      localStorage.setItem('zaiyi_profile', JSON.stringify(payload));
      window.location.hash = '#/home';
    } catch (e) {
      if (window.showToast) window.showToast('保存失败: ' + e.message, 'error');
      nextBtn.disabled = false;
      nextBtn.textContent = '完成设置 ✓';
    }
  }

  loadConfig();
}
