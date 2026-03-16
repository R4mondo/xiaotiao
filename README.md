# 小挑项目

本目录包含完整项目：
- 前端：`xiaotiao-app`（Vite SPA）
- 后端：`xiaotiao-server`（FastAPI）

## 本地开发

```bash
cd /Users/mac/学习/小挑/项目
./scripts/dev.sh
```

默认地址：
- Backend: `http://127.0.0.1:3000`
- Frontend: `http://127.0.0.1:5173`（端口占用时会自动切到 `5174`）

前端单独构建：

```bash
cd /Users/mac/学习/小挑/项目/xiaotiao-app
npm run build
```

## GitHub 协作流程

1. 从 `main` 拉新分支开发：
```bash
git checkout main
git pull
git checkout -b feat/xxx
```

2. 本地完成后提交并推送：
```bash
git add .
git commit -m "feat: xxx"
git push -u origin feat/xxx
```

3. 在 GitHub 发起 Pull Request（仓库已内置 PR/Issue 模板与 CI）。

详细规范见 `CONTRIBUTING.md`。

## GitHub 网页直接编辑（无需本地环境）

1. 打开仓库：`https://github.com/R4mondo/xiaotiao`
2. 进入要修改的文件，点击右上角铅笔（Edit this file）
3. 底部选择 `Create a new branch for this commit`
4. 点击 `Propose changes`
5. 点击 `Create pull request` 提交评审

适合改文案、配置、小范围代码；复杂改动建议走本地开发流程。

## 一键创建 GitHub 远程仓库

已提供脚本：

```bash
cd /Users/mac/学习/小挑/项目
./scripts/setup_github.sh <repo-name> [public|private]
```

示例：

```bash
./scripts/setup_github.sh xiaotiao private
```

脚本会自动使用 `gh` 创建仓库、绑定 `origin` 并推送 `main`。

如果本机未安装 `gh`，脚本会自动回退到手动模式并打印可直接复制的 `git remote add / git push` 命令。

## API Key / 模型配置

- 不配置 API Key 也能运行和构建（后端可回退到 Mock 输出）。
- 需要真实大模型时，在 `xiaotiao-server/.env` 配置。

Qwen（DashScope 兼容接口）示例：

```env
LLM_PROVIDER=qwen
QWEN_API_KEY=你的key
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
QWEN_MODEL=qwen-plus
QWEN_VISION_MODEL=qwen-vl-plus
LLM_FALLBACK_TO_MOCK=true
```

Anthropic 示例：

```env
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=你的key
ANTHROPIC_MODEL=claude-3-7-sonnet-20250219
```

OpenAI 示例：

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=你的key
OPENAI_MODEL=gpt-4o-mini
```

Gemini 示例：

```env
LLM_PROVIDER=gemini
GEMINI_API_KEY=你的key
GEMINI_MODEL=gemini-2.5-flash
```
