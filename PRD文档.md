# 小挑项目 产品需求文档（PRD）— 整合版

- 文档版本：`v3.0（现状版）`
- 文档日期：`2026-03-17`
- 产品阶段：`V1 MVP 已完成 + AInsight 合并已完成 → 打磨优化与云端上线阶段`
- 产品定位：`A+B（工具可用性优先的学习平台 → 智能语言与跨学科知识获取引擎）`
- 目标用户：`法学本科生/研究生 · 跨学科专业学习者`
- 来源文档：
  - `2026-03-13-小挑项目-v1-prd.md`（V1 MVP 基础需求）
  - `AI文章生成器PRD撰写.docx`（全栈平台深度设计）
  - `MERGE-STRATEGY.md`（AInsight 合并策略，已完成归档）

---

## 目录

1. [背景与问题定义](#1-背景与问题定义)
2. [战略愿景与执行摘要](#2-战略愿景与执行摘要)
3. [产品目标与成功标准](#3-产品目标与成功标准)
4. [用户画像与使用场景](#4-用户画像与使用场景)
5. [范围边界（Scope）](#5-范围边界scope)
6. [信息架构与页面结构](#6-信息架构与页面结构)
7. [系统架构与模块化信息流设计](#7-系统架构与模块化信息流设计)
8. [V1 详细功能需求（MVP 核心三模块）](#8-v1-详细功能需求mvp-核心三模块)
9. [数据云端化与用户个性化矩阵](#9-数据云端化与用户个性化矩阵)
10. [科学目标词滚动算法：基于记忆规律的重构](#10-科学目标词滚动算法基于记忆规律的重构)
11. [实时动态词汇与文本难度调节引擎](#11-实时动态词汇与文本难度调节引擎)
12. [沉浸式阅读发现图书馆体系](#12-沉浸式阅读发现图书馆体系)
13. [关键接口与类型（Public Interfaces）](#13-关键接口与类型public-interfaces)
14. [非功能需求（NFR）与系统表现](#14-非功能需求nfr与系统表现)
15. [数据埋点与分析需求](#15-数据埋点与分析需求)
16. [里程碑与发布计划](#16-里程碑与发布计划)
17. [测试与验收场景](#17-测试与验收场景)
18. [风险与应对](#18-风险与应对)
19. [V2+ 候选路线](#19-v2-候选路线)
20. [参考文献与引用](#20-参考文献与引用)

---

## 1. 背景与问题定义

### 1.1 核心痛点

当前法学生及跨学科专业学习者在涉外法治与专业英语学习中常见两类问题：

1. **缺少可持续接触的高质量英文法律学习材料**。
2. **现有翻译或大模型工具偏通用**，法律语境解释不足，难以形成"专业内容驱动的英语学习"闭环。

### 1.2 原型验证

本项目的前身——基于 Claude 提示词工程的本地化原型系统，已成功验证了核心理念的可行性。该原型系统能够基于用户的目标词汇表（如涵盖"通用词汇"与"会计·金融·审计专业词汇"的 Excel），结合社会热点（如 DeFi 金融监管），生成难度对标 C1-C2 级别的专业英语文章，并成功实现了**跨专业问题思考与语言训练的双重目标**。

然而，受限于本地化运行、手动提示词输入以及基于 Excel 的扁平化数据管理，该原型在以下方面存在固有瓶颈：
- 扩展性
- 算法科学性
- 多模态交互能力

### 1.3 V1 目标闭环

小挑项目 V1 的目标不是做全功能研究平台，而是先验证一个高频闭环：

> `Topic 选题 -> 英文内容学习 -> 术语理解 -> 翻译训练`

---

## 2. 战略愿景与执行摘要

> *来源：AI文章生成器PRD撰写.docx*

认知科学与第二语言习得（SLA）理论表明，当语言学习被置于具有高度相关性和真实应用价值的专业语境（**Comprehensible Input**）中时，其吸收效率将呈指数级增长。

新平台的**核心战略目标**包括：

| # | 战略目标 | 说明 |
|---|---------|------|
| 1 | **API 驱动与自动化** | 通过后端 API 接入主流 LLM，全面自动化原有 Claude 项目的生成流程，消除手动提示词复制粘贴的摩擦力 |
| 2 | **全维度个性化定制** | 允许用户在云端自定义兴趣图谱、选修学科框架及词汇库范围 |
| 3 | **数据资产云端化** | 构建高并发的云端关系型与向量数据库，实现学习数据的多端同步与持久化存储 |
| 4 | **输入输出模块化解耦** | 确保文本、音频、PDF 等任何形式的信息均可作为输入源，并能结构化输出文章、听力脚本、阅读理解等多种教学资产 |
| 5 | **记忆规律算法重构** | 引入基于艾宾浩斯遗忘曲线的科学间隔重复系统（SRS），彻底升级"遍历次数"的简单逻辑 |
| 6 | **实时难度动态调节** | 开发基于细粒度文本特征的提示词工程引擎，允许用户实时升降文本的词汇与句法难度 |
| 7 | **构建智能聚合阅读图书馆** | 深度融合 AInsight 等前沿项目的功能逻辑，结合 LingQ、Readlang 等沉浸式阅读软件的最佳实践 |

> 通过实现上述功能，平台将不再仅仅是一个"文章生成器"，而是演进为一个具有自适应能力、认知科学支撑的 **"全天候 AI 双语专业导师"**。

---

## 3. 产品目标与成功标准

### 3.1 业务目标（V1 MVP）

1. 让目标用户在一次访问内完成至少 **1 次完整学习任务**（生成/解读/翻译之一）。
2. 建立差异化心智：`涉外法治语境下的英语学习工具`。
3. 为 V2（Research Finder / Workspace / 全功能平台）沉淀真实使用数据和高频场景。

### 3.2 北极星指标与核心指标

- **北极星指标**：`有效学习任务完成次数/日`（定义：用户输入内容并查看结构化结果超过 30 秒）
- **核心指标**：
  - 任务完成率（按模块）
  - 首次价值到达时间 `TTFV`（首次打开到首次结果生成成功）
  - 单次会话学习深度（查看术语卡片数量、切换模块行为）
  - 用户反馈满意度（"结果是否有帮助"二值反馈）

### 3.3 V1 成功阈值（建议）

| 指标 | 目标值 |
|------|--------|
| Topic 生成成功率 | >= `95%` |
| Article 解读成功率 | >= `95%` |
| Translation 成功率 | >= `97%` |
| 中位 TTFV | <= `90 秒` |
| 首周"至少完成 1 次任务"用户占比 | >= `60%` |

---

## 4. 用户画像与使用场景

### 4.1 核心用户画像

- **法学本科生**：备课、课程论文、英文材料阅读基础较弱。
- **法学研究生**：需要快速理解英文文献、判例、条约片段并输出规范表达。
- **跨学科专业学习者**（V2 扩展）：金融、会计、审计等领域的双语专业人才。

### 4.2 核心场景

1. 用户想了解某涉外法治主题，但不知道从哪篇英文材料开始。
2. 用户拿到英文判例/条约段落，看懂字面但不理解法律含义。
3. 用户需要把中文法律论述翻成更地道、专业的英文表达（或反向翻译）。
4. **（V2）** 用户希望通过日常阅读专业资讯实现词汇的自然习得，而非死记硬背。

---

## 5. 范围边界（Scope）

### 5.1 V1 已完成（Delivered）

- ✅ `Topic Explorer`（主题生成学习内容）
- ✅ `Article Lab`（文章/段落 AI 解读）
- ✅ `Translation Studio`（法律翻译训练）
- ✅ `My Words 词汇系统`（CRUD + 多格式导入 + AI 提取 + 导出）
- ✅ `SRS 间隔重复算法`（SM-2 改良版，词汇轮动）
- ✅ `进度看板`（学习统计与 SRS 可视化）

### 5.2 AInsight 合并已完成（Delivered）

- ✅ `论文库`（URL 导入 + PDF 上传 + 状态管理）
- ✅ `论文详情页`（AI Insight 解读 + 对话问答）
- ✅ `PDF 阅读器`（PDF.js 渲染 + 划词工具栏）
- ✅ `主题追踪`（Tracker 创建 + 论文发现）
- ✅ `合集管理`（论文分组管理）

### 5.3 基础设施已完成（Delivered）

- ✅ 后端 FastAPI 框架 + SQLite 数据库
- ✅ 多 LLM 厂商支持（Qwen / Anthropic / OpenAI / Gemini）
- ✅ Jinja2 Prompt 模板引擎
- ✅ 用户认证系统（JWT）
- ✅ 管理后台（Admin Dashboard）
- ✅ 流式输出（SSE / Streaming）
- ✅ XSS 安全防护
- ✅ 部署基础设施（Nginx + systemd + CI/CD + 备份脚本）

### 5.4 V2+ 仍待实现（Pending）

- **多智能体协同管线**（Multi-Agent Orchestration Pipeline）
- **实时难度调节引擎**（CEFR 滑块 + Adaptation Agent）
- **RAG 检索增强生成** 与向量知识库
- 数据云端化（PostgreSQL 迁移）
- `Research Finder`（文献检索与学术图谱）
- `Workspace`（收藏夹、长期笔记、知识图谱）
- 班级/社群/排行榜等学习运营体系

---

## 6. 信息架构与页面结构

### 6.1 当前页面结构（已实现）

```text
Home /                          ← 首页（Hero + 模块入口）
├── Topic Explorer /topic       ← 主题探索（多主题 + 文章生成）
├── Article Lab /article        ← 文章解读（分段 AI 解析）
├── Translation Studio /trans   ← 翻译训练（三风格翻译）
├── 论文库 /papers              ← 论文管理（URL/PDF 导入 + 合集）
│   ├── 论文详情 /papers/:id    ← AI Insight + Chat 对话
│   └── PDF 阅读器 /papers/:id/read  ← PDF.js + 划词工具
├── 追踪 /tracker               ← 主题追踪（自动发现论文）
├── My Words /vocab             ← 词汇管理（CRUD + 导入导出）
├── 进度 /progress              ← SRS 看板 + 学习统计
├── 登录 /login                 ← 用户认证
└── 管理后台 /admin             ← 系统管理（需开发者密码）
```

### 6.2 远期规划页面结构（V2+ 演进）

```text
（在当前基础上新增）
├── Intelligent Reading Library  ← 沉浸式阅读图书馆
│   ├── Dynamic Discovery Feed   ← 动态信息库
│   ├── Interactive Reading Engine ← 交互阅读器（LingQ 风格）
│   └── Personal Import Tool     ← 个人藏书馆导入
├── User Profile                 ← 用户配置中心
│   ├── Interest Tags            ← 兴趣标签
│   ├── Academic Disciplines     ← 学科框架
│   └── CEFR Baseline            ← 难度基线
└── Research Finder              ← 文献检索与学术图谱
```

### 6.3 Home（首页）

- 明确三大入口与价值说明。
- 提供示例主题与示例输入，降低首用门槛。

### 6.4 导航原则

- 一级导航仅保留 3 个核心模块（V1）。
- 任一模块从输入到结果最多 2 步。
- 结果页提供"继续学习下一步"入口（例如从 Topic 跳转 Translation）。

---

## 7. 系统架构与模块化信息流设计

> *来源：AI文章生成器PRD撰写.docx — 第二章*

### 7.1 架构原则

为实现"任何形式的信息可输出、可输入"的目标，系统架构必须摒弃庞大且脆弱的单一提示词（Monolithic Prompt）模式。研究表明，在单一提示词中同时要求 LLM 执行事实检索、词汇嵌入、难度控制和题型生成，极易导致"对齐漂移"（Alignment Drift）和上下文污染。

因此，平台将采用**基于微服务与多智能体（Multi-Agent）协作的流水线架构**。

### 7.2 多智能体协作管线（Multi-Agent Orchestration Pipeline）

平台后端将利用 LangGraph 或 LlamaIndex 等编排框架，将内容生成拆解为多个独立、可观察且可干预的服务节点。

| 智能体/处理节点 | 核心职责 | 输入依赖 | 输出资产 |
|:---|:---|:---|:---|
| **Data Ingestion Agent** (数据摄入智能体) | 解析多模态输入源。无论是用户主动上传的 PDF/EPUB 文档、粘贴的网页 URL，还是系统自动抓取的新闻，均转化为标准化纯文本 | URL, PDF, EPUB, API 原始数据 | 结构化纯文本、元数据标签 |
| **Discovery Agent** (发现智能体) | 基于用户的"兴趣"与"选修学科"标签，主动调用搜索引擎 API 获取行业前沿资讯 | 用户画像标签 (如: 金融, 衍生品, 侵权法) | 前沿资讯的内容摘要与事实逻辑树 |
| **Curriculum Agent** (教务智能体) | 根据科学滚动算法（SRS），从云端词库中精确抽取本次生成必须涵盖的 15-20 个目标单词 | SRS 算法输出参数、用户词汇库 | 目标词汇阵列 (Target Vocabulary Array) |
| **Drafting Agent** (撰稿智能体) | 核心生成引擎。将 Discovery Agent 提取的专业事实与 Curriculum Agent 给定的目标词汇融合，生成约 400 词的主体文章 | 资讯事实树、目标词汇阵列、初始 CEFR 难度设定 | 包含目标词汇的专业科普/分析文章 |
| **Adaptation Agent** (调节智能体) | 负责难度微调。当用户拖动难度滑块时，在不改变原意和目标词汇的前提下，动态改写文本的句法和非目标词的词汇密度 | 主体文章、用户难度控制参数 | 难度适配后的最终文章文本 |
| **Pedagogical Agent** (教研智能体) | 依据最终文章生成配套训练模块，包括等长的听力脚本 (Listening Script) 以及 T/F/NG 阅读理解题 | 难度适配后的最终文章文本 | T/F/NG 测试题及解析、听力文稿 |

### 7.3 模块化输入与输出标准

**输入端**不局限于 AI 自行检索的话题。用户可以直接将教授的课件 PDF 拖入系统。Data Ingestion Agent 会将课件转化为知识库，随后 Drafting Agent 围绕该课件生成涵盖用户"待背单词"的复习文章。

**输出端**生成的内容不再是单一的 Markdown 文本，而是**结构化的 JSON 数据包**：

- `article_body`：用于渲染高亮可交互的阅读主视图
- `vocabulary_table`：渲染文章末尾的词汇清单（词性、中英文释义及语境例句）
- `listening_script` & `audio_url`：调用 TTS 服务生成的高保真音频及同步滚动字幕
- `assessment_drill`：渲染为交互式的表单，测试用户对文章逻辑及目标词汇的理解

---

## 8. V1 详细功能需求（MVP 核心三模块）

### 8.1 Topic Explorer

#### 8.1.1 用户故事

> 作为法学生，我希望输入一个涉外法治主题后，快速获得可读的英文学习材料和术语解释，以便马上进入学习状态。

#### 8.1.2 功能要求

1. **输入参数**：主题关键词、难度等级、专业方向标签。
2. **结果输出**至少包含：
   - 英文主题文章（结构化分段）
   - 关键词汇列表（英文术语 + 中文释义）
   - 核心法律概念说明（简短）
3. 用户可点击术语查看解释和例句。
4. 用户可一键"基于本文章进入翻译训练"。

#### 8.1.3 验收标准

- 输入有效 topic 后 **15 秒内**返回首屏结果。
- 每次生成至少包含 **8 个术语条目**。
- 术语解释可展开/收起，交互无明显卡顿。

---

### 8.2 Article Lab

#### 8.2.1 用户故事

> 作为法学生，我希望粘贴英文法律文本并获得分段解读和重点解释，以减少阅读障碍。

#### 8.2.2 功能要求

1. 支持两种输入方式：**粘贴文本**、**上传文本文件（`txt/md`）**。
2. 支持解读模式：
   - 基础解读（plain）
   - 法律重点解读（legal focus）
3. 输出至少包含：
   - 分段中文解释
   - 关键词术语提取
   - 关键句说明（为什么重要）
4. 支持针对单段重试与重新解释。

#### 8.2.3 验收标准

- **2000 英文词**以内文本可稳定解析。
- 每段均返回解释文本，段落失败需提示并允许重试。
- 关键句至少给出 **3 条**（若原文长度允许）。

---

### 8.3 Translation Studio

#### 8.3.1 用户故事

> 作为法学生，我希望对同一段文本拿到多种法律风格翻译，并看到改进建议，以提升写作表达质量。

#### 8.3.2 功能要求

1. 方向支持：`EN->ZH` 与 `ZH->EN`。
2. 输出至少包含三种结果：
   - 直译版（literal）
   - 法律表达版（legal）
   - 简明表达版（plain）
3. 提供"表达建议"与"常见错误提示"。
4. 支持对用户自译内容进行对照点评（可选输入）。

#### 8.3.3 验收标准

- 翻译结果默认在 **12 秒内**返回。
- 三种风格输出完整可见，且可复制。
- 用户输入为空或过长时给出明确错误提示。

---

## 9. 数据云端化与用户个性化矩阵

> *来源：AI文章生成器PRD撰写.docx — 第三章*

### 9.1 问题背景

原型系统极度依赖本地 Excel 文件，其中手动记录了总计 264 个词条（206 个通用词汇与 58 个专业词汇）的遍历次数与熟记状态。这种方式不仅存在数据丢失风险，且无法支持跨设备的实时状态更新及复杂的算法运算。

### 9.2 云端数据库架构（Cloud Database Schema）

平台将采用 **PostgreSQL** 作为核心关系型数据库。

#### 用户配置表 (user_profiles)

| 字段 | 说明 |
|------|------|
| `user_id` | 唯一标识符 |
| `interest_tags` | JSONB 格式，存储用户自定义的兴趣领域（如：宏观经济、人工智能、加密货币） |
| `academic_disciplines` | JSONB 格式，存储选修学科（如：Jurisprudence, Accounting, Computer Science） |
| `cefr_baseline` | 初始设定的阅读难度水平（A1 至 C2） |

#### 用户专属词汇状态表 (user_vocabulary_states)

此表直接替代原有的 Excel 表格，并为科学滚动算法提供数据支撑。

| 字段名称 | 数据类型 | 业务逻辑说明 |
|----------|----------|-------------|
| `state_id` | UUID | 状态记录唯一主键 |
| `user_id` | UUID | 关联用户 |
| `word` | VARCHAR | 目标单词（如 fiduciary, liquidity） |
| `domain` | VARCHAR | 词汇板块分类（如"通用词汇"、"会计·金融"） |
| `traversal_count` | INTEGER | 历史曝光次数。平滑迁移原 Excel 中的"遍历0次/1次"数据 |
| `is_mastered` | BOOLEAN | 是否已熟记。若为 True 则移出生成队列 |
| `ease_factor` (EF) | FLOAT | 记忆容易度因子。算法核心参数，初始值默认 2.5 |
| `interval` (I) | INTEGER | 下一次复习的间隔天数 |
| `next_review_date` | TIMESTAMP | 下一次应当被编入文章的具体日期 |

### 9.3 检索增强生成（RAG）与知识库

系统将引入**向量数据库**（如 Tencent Cloud Vector DB 或 Pinecone）来实现检索增强生成（RAG）。当用户保存了一篇文章后，该文章及其释义将被向量化存储。未来生成新文章时，系统可通过 RAG 调取用户过往阅读过的语境，让 AI 生成前后呼应的内容，极大增强上下文的连贯性与用户代入感。

---

## 10. 科学目标词滚动算法：基于记忆规律的重构

> *来源：AI文章生成器PRD撰写.docx — 第四章*

### 10.1 传统 SRS 与生成式语境 SRS 的范式转移

传统间隔重复系统（SRS，如 Anki / SuperMemo）运作逻辑：

> 展示孤立的单词卡片 → 用户回忆 → 用户手动评分 → 算法推迟下次展示时间

本平台的核心创新在于 **"隐性语境评估"**：用户不是在背卡片，而是在阅读包含目标词汇的定制文章，并通过完成文章后的 T/F/NG 阅读理解题来被动验证记忆。因此，算法必须从"显性反馈"重构为"基于评估的隐性反馈"。

### 10.2 基于改良 SM-2 / FSRS 的统计算法

在生成每一篇新文章时，**Curriculum Agent** 需要挑选 15-20 个单词。这批单词的选取基于以下科学优先级：

1. **复习池 (Review Pool)**：查询 `next_review_date <= 当前时间` 的词汇。这些是算法预测用户即将遗忘的单词。
2. **新词池 (New Pool)**：查询 `traversal_count = 0` 的词汇。
3. **缓冲池 (Buffer Pool)**：若复习池和新词池不足，调取 `traversal_count > 0` 且尚未熟记、但未到复习时间的词汇作为文章点缀。

#### 区间计算逻辑

采用改良版 **SuperMemo-2 (SM-2)** 算法基线，结合现代 **FSRS**（Free Spaced Repetition Scheduler）的平滑演进理念。每个单词都绑定两个核心变量：**间隔（Interval, I）** 与 **容易度因子（Ease Factor, EF）**。

- **初始遭遇**：新词首次被编入生成文章后，`I = 1 天`，`EF = 2.5`。
- **反馈捕获**：用户阅读文章后完成 T/F/NG 练习。系统在生成练习时，将部分目标词汇作为解题的关键信息点。
- **动态更新**：根据用户练习表现，隐式计算回忆质量（q），取值 0-5：
  - `q = 5`：一次性完全答对且用时较短
  - `q = 3`：答对，但曾查阅内置词典或耗时较长
  - `q < 3`：相关题目答错，表明核心语境未被理解
- 对于成功回忆（`q >= 3`）的词汇，更新 EF 与 I
- 若 `q < 3`（未掌握），`I` 重置为 1 天，强制编入明天的文章

### 10.3 算法的认知优势

这种生成式滚动算法解决了传统记忆法则的枯燥性。用户面对的不再是同一张重复 10 次的单词卡片，而是在 10 篇情节截然不同的全新文章中，在不同的句法结构下反复遭遇目标单词。这种 **"多重编码"（Multiple Encoding）** 极大增强了大脑神经突触的长期连接。

---

## 11. 实时动态词汇与文本难度调节引擎

> *来源：AI文章生成器PRD撰写.docx — 第五章*

### 11.1 问题

LLM 默认输出往往偏向母语者的复杂程度（接近 CEFR C2 级别），对初中级学习者造成认知过载。简单地要求 LLM"以简单英语重写"会导致专业信息流失或发生"对齐漂移"（Alignment Drift）。

### 11.2 难度的量化解构

文本难度拆解为可通过提示词精确控制的正交维度：

| 维度 | 定义 |
|------|------|
| **词汇密度 (Lexical Density)** | 非目标学术词汇在总词汇量中的占比 |
| **句法复杂度 (Syntactic Complexity)** | 从句嵌套深度、被动语态使用频率、平均句长 |
| **词元遗漏率 (Token Miss Rate, TMR)** | 模型输出中超出用户当前词库承受范围的不可理解词元比例 |

### 11.3 前端实时滑块交互与提示词链 (Prompt Chaining)

用户在前端阅读界面可以拖动一个 **"文本难度调节"滑块**（范围 1-10 级）。该交互启动一条严谨的提示词链。

**Adaptation Agent 执行逻辑**（"保持事实、替换包装"策略）：

1. **输入锁定**：锁定所有从 Curriculum Agent 获取的目标单词，这些词的难度不容妥协，必须原样保留。
2. **结构改写**：执行特定的 System Prompt 进行降级重构：
   - 保留 100% 的原有专业事实与逻辑链条
   - **句法规则**：将复合长句拆分为短结构单句，避免超过一层的嵌套定语从句
   - **词汇规则**：除核心目标词汇外，将进阶学术词汇替换为 CEFR A2-B1 级别的高频日常词汇
   - 严禁改变信息的主旨

> 通过上述机制,即使是高精尖文章，系统也能改写为语法平易近人的版本，完美烘托出必须学习的专业目标词，实现绝对意义上的"可理解输入" (Comprehensible Input)。

---

## 12. 沉浸式阅读发现图书馆体系

> *来源：AI文章生成器PRD撰写.docx — 第六章*

### 12.1 动态流式信息库 (Dynamic Discovery Feed)

- **AInsight 风格的信息聚合**：底层的 Discovery Agent 每日通过集成各种合法 API（如彭博社金融新闻、法学数据库、科技前沿 RSS），根据用户兴趣设定自动抓取最新资讯。
- **智能卡片呈现**：在 Dashboard 上，资讯转化为带有标题、标签及预期阅读时长的极简卡片。
- **生成劫持 (Generation Hijack)**：当用户点击卡片时，系统触发生成管线，拦截原始新闻内容，提取核心事实，并强行植入用户今日需要复习的目标单词，即时生成一篇全新的专属学习文章。

### 12.2 交互阅读器 (Interactive Reading Engine)

| 核心功能 | 交互设计与底层逻辑 |
|:---------|:-------------------|
| **色彩编码进度跟踪** | 借鉴 LingQ 的核心视觉模式。蓝色 = 未学习新词；黄色 = SRS 复习周期中的词汇；透明底色 = 已熟记（Mastered） |
| **即时上下文查词** | 点击蓝色生词时，系统抓取所在句子向 LLM 发送微查询，提供精确的语境翻译与词性解析。一键将该词加入新词池 |
| **富媒体同步生成** | 阅读器支持边听边读的高亮滚动功能。利用高质量 TTS API，使学术级长文具备播客体验 |
| **个人藏书馆导入** | 用户可通过浏览器插件或直传功能上传个人专业材料。系统智能提取文本，保留段落格式，并套用 SRS 色彩标记与查词逻辑 |

---

## 13. 关键接口与类型（Public Interfaces）

> 以下为 PRD 级接口契约，供前后端拆分开发任务使用。

### 13.1 Topic 内容生成

- **Endpoint**：`POST /api/v1/topic/generate`
- **Request**:
```json
{
  "topic": "international arbitration",
  "level": "intermediate",
  "domain_tags": ["international-law", "dispute-resolution"]
}
```
- **Response**:
```json
{
  "result_text": "Generated article content...",
  "terms": [
    {"term": "arbitration clause", "definition_zh": "仲裁条款"}
  ],
  "notes": ["Key concept explanation..."],
  "confidence_hint": "medium"
}
```

### 13.2 Article 解读

- **Endpoint**：`POST /api/v1/article/analyze`
- **Request**:
```json
{
  "source_text": "Input legal text...",
  "analysis_mode": "legal_focus",
  "target_lang": "zh"
}
```
- **Response**:
```json
{
  "result_text": "Paragraph-by-paragraph explanation...",
  "terms": [
    {"term": "jurisdiction", "definition_zh": "管辖权"}
  ],
  "notes": ["Why sentence #2 matters..."],
  "confidence_hint": "high"
}
```

### 13.3 Translation

- **Endpoint**：`POST /api/v1/translation/run`
- **Request**:
```json
{
  "source_text": "跨境数据治理规则仍处于快速演化阶段。",
  "direction": "zh_to_en",
  "style": ["literal", "legal", "plain"]
}
```
- **Response**:
```json
{
  "result_text": "Translation bundle...",
  "terms": [
    {"term": "cross-border data governance", "definition_zh": "跨境数据治理"}
  ],
  "notes": ["Prefer 'shall' only when normative force is required."],
  "confidence_hint": "medium"
}
```

---

## 14. 非功能需求（NFR）与系统表现

### 14.1 基础 NFR（V1）

1. **可用性**：核心接口月可用性目标 `>= 99.5%`。
2. **性能**：P95 响应时间目标 `< 15 秒`。
3. **安全与隐私**：
   - 用户输入默认不对外公开。
   - 日志脱敏（不记录完整原文正文，记录摘要与长度）。
4. **可观测性**：
   - 每个模块至少记录请求量、成功率、平均耗时、失败码分布。

### 14.2 性能指标与 API 成本控制（V2）

> *来源：AI文章生成器PRD撰写.docx — 第七章*

- **缓存与向量复用**：针对热门新闻事件，系统可生成多份含通用高频错词的基础版本文章并缓存。对词汇偏好相似的用户群体，优先投递缓存结果，减少重复生成成本。
- **分步流式输出 (Streaming Output)**：在等待文章生成过程中，UI 采取流式传输（Token Streaming）逐步渲染文字，消除等待焦虑。配套的听力与 T/F/NG 测试生成放入后台队列异步处理。

### 14.3 数据隐私与安全性（V2）

用户构建的专业词库、输入的业务材料涉及高度敏感数据。系统必须：
- 对存储在数据库和向量知识库中的用户元数据进行严格的**加密隔离（Tenant Isolation）**
- 前端设置明确的"混淆参数"，在提交用户文本至公共 LLM API 之前，自动**脱敏或过滤**可能导致隐私泄漏的敏感信息实体

---

## 15. 数据埋点与分析需求

### 15.1 事件定义（最小集）

| 事件名 | 说明 |
|--------|------|
| `home_enter` | 进入首页 |
| `module_enter` | 进入模块（含 module_name） |
| `task_submit` | 提交任务 |
| `task_success` | 任务成功 |
| `task_fail` | 任务失败 |
| `term_click` | 点击术语 |
| `copy_result` | 复制结果 |
| `feedback_submit` | 提交反馈 |

### 15.2 关键分析看板

1. **按模块漏斗**：进入 -> 提交 -> 成功 -> 反馈
2. **失败分析**：失败码分布与输入长度关联
3. **用户行为深度**：一次会话触发的模块数、术语点击数

---

## 16. 里程碑与发布计划

### 16.1 已完成里程碑

| 里程碑 | 状态 | 完成内容 |
|--------|------|------|
| `M1 内部可演示` | ✅ 已完成 | 三模块（Topic/Article/Translation）原型与 API 接口打通 |
| `M2 词汇系统上线` | ✅ 已完成 | My Words 数据库 CRUD + 多格式导入（Excel/Word/照片 OCR）+ AI 提取 |
| `M3 SRS + 进度` | ✅ 已完成 | SM-2 改良算法 + 词汇轮动 + 进度看板可视化 |
| `M4 AInsight 合并` | ✅ 已完成 | 论文库 + AI 解读 + PDF 阅读器 + 主题追踪 + 合集管理 |
| `M5 基础设施` | ✅ 已完成 | 认证系统 + 管理后台 + 流式输出 + XSS 防护 + 部署方案 |

### 16.2 当前阶段与下一步

| 阶段 | 状态 | 核心内容 |
|------|------|---------|
| **云端部署上线** | ⏳ 进行中 | 阿里云 ECS 部署、域名配置、生产验证 |
| 目标范围词表 | 📋 待开始 | CET-4/6、IELTS、TOEFL 内置词表 + 进度可视化 |
| 数据埋点落地 | 📋 待开始 | 完整事件追踪 + 分析看板 |
| 自动化测试 | 📋 待开始 | 核心 API + SRS 算法单元测试 |

### 16.3 V2+ 远期路线

| 阶段 | 核心交付 |
|------|---------|
| V2.1 | 多智能体管线 + PostgreSQL 迁移 |
| V2.2 | 实时难度调节引擎（CEFR 滑块 + Adaptation Agent）|
| V2.3 | 沉浸式阅读图书馆 + RAG 向量知识库 |
| V2.4 | Research Finder + Workspace |

---

## 17. 测试与验收场景

### 17.1 主流程验收

1. 用户在 **Topic Explorer** 输入主题并成功获得文章与术语。
2. 用户在 **Article Lab** 输入文本并成功获得分段解读。
3. 用户在 **Translation Studio** 输入文本并获得三种翻译风格。

### 17.2 异常流程验收

1. **空输入**：阻止提交并提示补全。
2. **超长输入**：提示截断或分段处理建议。
3. **服务超时**：返回友好错误并允许重试。

### 17.3 可用性验收

- 新用户可在 **3 分钟内**完成一次完整任务。
- 每个模块的输入控件与结果区域清晰可见，不依赖文档说明即可使用。

---

## 18. 风险与应对

| # | 风险 | 应对策略 |
|---|------|----------|
| 1 | 生成内容质量波动 | 增加结果重生成功能与风格约束模板 |
| 2 | 法律术语解释不稳定 | 维护高频术语白名单并优先覆盖 |
| 3 | 功能范围膨胀导致延期 | 严格冻结 V1 边界，V2 需求统一入池评估 |
| 4 | LLM "对齐漂移" | 多智能体管线拆解、提示词链约束、TMR 监控 |
| 5 | API 成本高昂 | 缓存与向量复用策略、合理的模型分级调用 |
| 6 | 用户敏感数据泄露 | Tenant Isolation 加密隔离、自动脱敏过滤 |

---

## 19. V2+ 候选路线

> 以下为产品远期演进方向。标注 ✅ 的已在当前版本提前实现。

- **Research Finder**：文献检索、关键作者、争议主题聚类
- **Workspace**：收藏、笔记、主题管理、学习档案
- **学习路径**：任务制/周计划/复习提醒
- **多智能体协同管线**：Data Ingestion → Discovery → Curriculum → Drafting → Adaptation → Pedagogical Agent
- ✅ ~~**科学间隔重复系统（SRS）**：改良 SM-2 算法~~ → 已在 `services/srs.py` 实现
- **实时难度调节引擎**：CEFR 难度滑块 + Prompt Chaining
- ✅ ~~**沉浸式阅读图书馆（部分）**：AInsight 级论文管理 + PDF 阅读器~~ → 已实现论文库 + PDF 阅读器 + AI 解读
- ✅ ~~**Prompt 模板工程**~~ → 已实现 Jinja2 模板引擎 + 管理后台在线编辑

---

## 20. 参考文献与引用

> *来源：AI文章生成器PRD撰写.docx*

1. [The Science of Language Learning: What Research Actually Says - DEV Community](https://dev.to/pocket_linguist/the-science-of-language-learning-what-research-actually-says-1a93)
2. [Ebbinghaus Forgetting Curve - Wranx Microlearning App](https://www.wranx.com/blog/what-is-the-ebbinghaus-forgetting-curve/)
3. [Spaced Repetition Algorithm: A Three-Day Journey from Novice to Expert - GitHub](https://github.com/open-spaced-repetition/fsrs4anki/wiki/spaced-repetition-algorithm:-a-three%E2%80%90day-journey-from-novice-to-expert)
4. [Controlling Difficulty of Generated Text for AI-Assisted Language Learning - arXiv](https://arxiv.org/html/2506.04072v1)
5. [AInsight - App Store](https://apps.apple.com/lc/app/ainsight/id6746957669)
6. [GenAI_Agents/README.md at main - GitHub](https://github.com/NirDiamant/GenAI_Agents/blob/main/README.md)
7. [Readlang: Learn a Language by Reading](https://readlang.com/)
8. [ReadLang Alternatives – Compare ReadLang, LingQ, and Lingo Champion](https://lingochampion.com/en-US/readlang-alternatives/)
9. [CEFR LLM Alignment Drift - Emergent Mind](https://www.emergentmind.com/topics/alignment-drift-in-cefr-prompted-llms)
10. [Building Modular and Scalable AI for Content Creation using LlamaIndex - ResearchGate](https://www.researchgate.net/publication/397380994_Building_Modular_and_Scalable_AI_for_Content_Creation_using_LlamaIndex)
11. [Prompt Chaining | Prompt Engineering Guide](https://www.promptingguide.ai/techniques/prompt_chaining)
12. [Spaced repetition algorithm from SuperMemo (SM-2) - Stack Overflow](https://stackoverflow.com/questions/49047159/spaced-repetition-algorithm-from-supermemo-sm-2)
13. [How can AI Agent integrate external knowledge sources with one click? - Tencent Cloud](https://www.tencentcloud.com/techpedia/126653)
14. [LLM Fine-Tuning: A Comprehensive Guide - UBIAI](https://ubiai.tools/llm-fine-tuning-guide/)
15. [Spaced repetition - Wikipedia](https://en.wikipedia.org/wiki/Spaced_repetition)
16. [Top 5 Spaced Repetition Algorithms Compared - Quizcat AI](https://www.quizcat.ai/blog/top-5-spaced-repetition-algorithms-compared)
17. [What spaced repetition algorithm does Anki use?](https://faqs.ankiweb.net/what-spaced-repetition-algorithm)
18. [What is prompt chaining? | IBM](https://www.ibm.com/think/topics/prompt-chaining)

---

> **文档结束** — 本文档整合自 `2026-03-13-小挑项目-v1-prd.md` 与 `AI文章生成器PRD撰写.docx`，版本 v3.0（现状版），更新日期 2026-03-17。
