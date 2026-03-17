import { authFetch } from './utils/http.js';

// Real AI generation service — calls POST /...
const RAW_API_BASE = import.meta.env.VITE_API_BASE_URL || '';
const API_BASE = RAW_API_BASE.replace(/\/api\/v1\/?$/, '');

const TIMEOUTS = {
    defaultPost: 90000,
    defaultGet: 30000,
    llmHeavy: 120000,
};

function wait(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
}

async function requestJSON({ endpoint, method = 'POST', payload, timeoutMs, retries = 0, timeoutMessage = '请求超时，请重试' }) {
    const url = `${API_BASE}${endpoint}`;
    let lastError = null;

    for (let attempt = 0; attempt <= retries; attempt++) {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

        try {
            const response = await authFetch(url, {
                method,
                headers: method === 'GET' ? undefined : { 'Content-Type': 'application/json' },
                body: method === 'GET' ? undefined : JSON.stringify(payload),
                signal: controller.signal
            });

            clearTimeout(timeoutId);

            if (!response.ok) {
                let errorMsg = `HTTP Error ${response.status}`;
                try {
                    const errData = await response.json();
                    errorMsg = errData.detail || errorMsg;
                } catch (_e) {}
                throw new Error(errorMsg);
            }

            return await response.json();
        } catch (error) {
            clearTimeout(timeoutId);
            lastError = error;
            const isTimeout = error?.name === 'AbortError';
            const isLastAttempt = attempt === retries;

            if (!isLastAttempt) {
                // Small backoff before retry to absorb transient network/model latency.
                await wait(600 * (attempt + 1));
                continue;
            }

            if (isTimeout) {
                throw new Error(timeoutMessage);
            }
            throw new Error(error?.message || '请求失败，请检查网络连接或后端服务状态');
        }
    }

    throw new Error(lastError?.message || '请求失败，请稍后重试');
}

export async function fetchAPI(endpoint, payload, options = {}) {
    return await requestJSON({
        endpoint,
        method: 'POST',
        payload,
        timeoutMs: options.timeoutMs ?? TIMEOUTS.defaultPost,
        retries: options.retries ?? 1,
        timeoutMessage: options.timeoutMessage ?? '请求大语言模型超时，请重试'
    });
}

export async function fetchAPIGet(endpoint, options = {}) {
    return await requestJSON({
        endpoint,
        method: 'GET',
        timeoutMs: options.timeoutMs ?? TIMEOUTS.defaultGet,
        retries: options.retries ?? 0,
        timeoutMessage: options.timeoutMessage ?? '请求超时，请重试'
    });
}

export async function generateTopic(params) {
    const payload = {
        topics: [params.topic || ''],
        domains: params.domains || ['general'],
        level: params.level || 'intermediate',
        article_style_id: params.style || 'economist',
        article_length: params.length || 400,
        db_word_count: params.dbWords ?? 8,
        new_word_count: params.newWords ?? 5,
        target_range_id: 'cet6',
        db_words: []
    };

    return await fetchAPI('/topic/generate', payload, {
        timeoutMs: TIMEOUTS.llmHeavy,
        retries: 1,
        timeoutMessage: '生成超时（已自动重试），请重试或缩短文章长度'
    });
}

export async function analyzeArticle(params) {
    const payload = {
        source_text: params.source_text || '',
        analysis_mode: params.analysis_mode || 'plain',
        grounded: Boolean(params.grounded),
        top_k: params.top_k || 4
    };

    return await fetchAPI('/article/analyze', payload, {
        timeoutMs: TIMEOUTS.llmHeavy,
        retries: 1,
        timeoutMessage: '解读超时（已自动重试），请重试或缩短文本'
    });
}

export async function runTranslation(params) {
    const payload = {
        source_text: params.source_text || '',
        direction: params.direction || 'zh_to_en',
        style: ['literal', 'legal', 'plain'],
        user_translation: params.user_translation || ''
    };

    return await fetchAPI('/translation/run', payload, {
        timeoutMs: TIMEOUTS.llmHeavy,
        retries: 1,
        timeoutMessage: '翻译超时（已自动重试），请重试或缩短文本'
    });
}

export async function createVocabItem(payload) {
    return await fetchAPI('/vocab', {
        word: payload.word || '',
        definition_zh: payload.definition_zh || '',
        part_of_speech: payload.part_of_speech || '',
        domain: payload.domain || 'general',
        source: payload.source || 'topic_selection',
        example_sentence: payload.example_sentence || ''
    }, {
        timeoutMs: TIMEOUTS.defaultPost,
        retries: 0,
        timeoutMessage: '加入生词本超时，请重试'
    });
}

export async function getResearchGithubCases(limit = 20) {
    return await fetchAPIGet(`/research/github-cases?limit=${limit}`);
}

export async function refreshResearchGithubCases() {
    return await fetchAPI('/research/github-cases/refresh', {});
}

export async function getOrgUnits() {
    return await fetchAPIGet('/research/org-units');
}

export async function ingestGithubCasesToRag(limit = 30) {
    return await fetchAPI(`/research/rag/ingest/github-cases?limit=${limit}`, {});
}

export async function queryRag(payload) {
    return await fetchAPI('/research/rag/query', {
        query: payload.query || '',
        top_k: payload.top_k || 5
    });
}
