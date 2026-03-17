import { fetchAPI } from './api.js';
import { authFetch } from './utils/http.js';

export function renderProgressPage() {
    return `
    <div class="page-container glass-panel" style="max-width: 1200px; margin: 40px auto; padding: 40px; border-radius: 24px;">
        <div style="display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 40px;">
            <div>
                 <div class="page-header__badge" style="margin-bottom: 12px; display: inline-flex; align-items: center; gap: 8px; padding: 6px 12px; background: var(--glass-bg); border-radius: 20px; font-size: 0.85rem; color: var(--text-secondary);">
                    <span class="nav-dot" style="background:#4ade80; width:8px; height:8px; border-radius:50%; display:inline-block;"></span>
                    模块 05 · 学习进度
                </div>
                <h1 class="vocab-page__title">学习数据洞察</h1>
                <p class="vocab-page__subtitle">基于间隔重复算法的记忆分析与未来复习任务预测。</p>
            </div>
            <button class="btn btn--secondary" onclick="window.__initProgressData()">
                <span class="material-symbols-rounded" style="font-size: 18px;">refresh</span>
                刷新数据
            </button>
        </div>

        <!-- KPI Row -->
        <div class="progress-stats-grid">
            <div class="stat-card stat-card--green" style="text-align: center;">
                <div class="stat-card__label">记忆留存率 (Retention)</div>
                <div style="position: relative; width: 120px; height: 120px; margin: 0 auto;">
                    <svg viewBox="0 0 36 36" style="width:100%; height:100%; transform: rotate(-90deg);">
                        <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="rgba(0,0,0,0.06)" stroke-width="3.5" />
                        <path id="retention-ring" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="#4ade80" stroke-width="3.5" stroke-dasharray="0, 100" style="transition: stroke-dasharray 1.5s ease-out;" />
                    </svg>
                    <div id="retention-text" style="position: absolute; top:50%; left:50%; transform:translate(-50%, -50%); color:var(--text-primary); font-size:1.5rem; font-weight:600;">0%</div>
                </div>
            </div>

            <div class="stat-card stat-card--accent" style="display: flex; flex-direction: column; justify-content: center; align-items: center;">
                <div class="stat-card__label">已掌握词汇 (Mastered)</div>
                <div id="stat-mastered" class="stat-card__value">0</div>
                <div style="color: var(--text-muted); font-size: 0.85rem; margin-top: 4px;">词库总计 <span id="stat-total">0</span> 个</div>
            </div>

            <div class="stat-card stat-card--warning" style="display: flex; flex-direction: column; justify-content: center; align-items: center;">
                <div class="stat-card__label">今日待复习 (Due)</div>
                <div id="stat-due" class="stat-card__value">0</div>
                <a href="#/vocab" style="color: var(--accent); font-size: 0.85rem; margin-top: 12px; text-decoration: none; display: flex; align-items: center; gap: 4px;">开始复习单词 <span class="material-symbols-rounded" style="font-size: 14px;">arrow_forward</span></a>
            </div>

            <div class="stat-card stat-card--accent" style="display: flex; flex-direction: column; justify-content: center; align-items: center;">
                <div class="stat-card__label">论文活跃 (近7天)</div>
                <div style="display:flex;gap:16px;margin-top:8px;">
                    <div style="text-align:center;">
                        <div id="stat-papers-imported" class="stat-card__value" style="font-size:1.6rem;">0</div>
                        <div style="color:var(--text-muted);font-size:0.8rem;">导入</div>
                    </div>
                    <div style="text-align:center;">
                        <div id="stat-papers-viewed" class="stat-card__value" style="font-size:1.6rem;">0</div>
                        <div style="color:var(--text-muted);font-size:0.8rem;">查阅</div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Forecast Chart -->
        <h3 style="color: var(--text-primary); font-size: 1.25rem; margin-bottom: 24px; font-weight: 500;">未来7日复习预测 (Forecast)</h3>
        <div class="glass-panel" style="padding: 32px;">
            <div id="forecast-chart" style="display: flex; align-items: flex-end; justify-content: space-between; height: 250px; gap: 16px;">
                <!-- Bars injected via JS -->
            </div>
            <div id="forecast-labels" style="display: flex; justify-content: space-between; gap: 16px; margin-top: 16px; color: var(--text-muted); font-size: 0.85rem; text-align: center;">
                <!-- Labels injected via JS -->
            </div>
        </div>
    </div>
    `;
}

export async function initProgressPage() {
    window.__initProgressData = async () => {
        try {
            const RAW_API_BASE = import.meta.env.VITE_API_BASE_URL || '';
            const API_BASE = RAW_API_BASE.replace(/\/api\/v1\/?$/, '');
            
            // Fetch stats
            const statsRes = await authFetch(`${API_BASE}/vocab/stats`);
            const stats = await statsRes.json();
            
            document.getElementById('stat-total').textContent = stats.total;
            document.getElementById('stat-mastered').textContent = stats.mastered;
            document.getElementById('stat-due').textContent = stats.need_review_today;
            
            // Calculate pseudo retention (mastered / active if active > 0)
            const retentionObj = document.getElementById('retention-text');
            const retentionRing = document.getElementById('retention-ring');
            
            let retentionPct = 0;
            if (stats.active > 0) {
                retentionPct = Math.round((stats.mastered / stats.active) * 100);
            }
            if (stats.total === 0) retentionPct = 0;
            
            retentionObj.textContent = `${retentionPct}%`;
            
            // Animate ring
            setTimeout(() => {
                retentionRing.style.strokeDasharray = `${retentionPct}, 100`;
            }, 100);

            // Fetch Forecast
            const forecastRes = await authFetch(`${API_BASE}/vocab/forecast`);
            const forecast = await forecastRes.json();

            // Fetch paper stats
            const paperStatsRes = await authFetch(`${API_BASE}/papers/stats`);
            const paperStats = await paperStatsRes.json();
            document.getElementById('stat-papers-imported').textContent = paperStats.imported_7d ?? 0;
            document.getElementById('stat-papers-viewed').textContent = paperStats.viewed_7d ?? 0;
            
            const chartContainer = document.getElementById('forecast-chart');
            const labelsContainer = document.getElementById('forecast-labels');
            
            const maxVal = Math.max(...forecast.map(f => f.count), 10); // Minimum scale of 10
            
            chartContainer.innerHTML = forecast.map((f, i) => {
                const heightPct = Math.max((f.count / maxVal) * 100, 2); // Min 2% height for visibility
                const color = i === 0 ? '#fbbf24' : 'var(--glass-bg-hover)';
                const hoverColor = i === 0 ? '#fcd34d' : 'var(--accent)';
                
                return `
                    <div style="flex: 1; display: flex; flex-direction: column; justify-content: flex-end; align-items: center; group">
                        <div style="color: var(--text-primary); font-size: 0.85rem; margin-bottom: 8px; opacity: ${f.count > 0 ? 1 : 0.5}; font-variant-numeric: tabular-nums;">
                            ${f.count}
                        </div>
                        <div style="width: 100%; max-width: 48px; background: ${color}; height: ${heightPct}%; border-radius: 6px 6px 0 0; transition: all 0.3s; cursor: pointer;"
                             onmouseover="this.style.background='${hoverColor}'"
                             onmouseout="this.style.background='${color}'">
                        </div>
                    </div>
                `;
            }).join('');
            
            labelsContainer.innerHTML = forecast.map((f, i) => {
                const isToday = i === 0;
                return `
                    <div style="flex: 1;">
                        <span style="${isToday ? 'color: var(--text-primary); font-weight: 600;' : ''}">${isToday ? '今日' : f.day_name}</span>
                    </div>
                `;
            }).join('');

        } catch (e) {
            console.error("Progress fetch error:", e);
        }
    };
    
    await window.__initProgressData();
}
