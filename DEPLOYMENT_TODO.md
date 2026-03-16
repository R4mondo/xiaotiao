# 云服务器部署待办清单（未完成项）

以下清单基于当前仓库内容梳理，项目仍以本地开发为主，缺少生产环境部署相关配置与流程。用于“上云”前的补齐与确认。

## 1) 部署形态与访问路径
- 明确部署方式：单机直装、Docker、还是 PaaS（如 Railway/Render）。
- 确定前后端访问路径：
  - 前端独立域名（如 `app.xxx.com`）+ 后端独立域名（如 `api.xxx.com`），或
  - 反向代理同域：`/` 前端静态，`/api` 后端服务。
- 根据以上决定调整：
  - 前端 `VITE_API_BASE_URL`（见 `xiaotiao-app/src/api.js`）。
  - 后端 CORS `allow_origins`（见 `xiaotiao-server/main.py`）。

## 2) 前端生产构建与静态托管
- 增加生产构建流程：
  - `npm install && npm run build` 生成 `dist/`。
- 选择并配置静态托管方式：
  - Nginx/Apache 静态目录，或对象存储 + CDN。
- 配置 SPA 路由回退（`index.html`）以支持 `#/` 或将路由改为 history 模式时的刷新回退。

## 3) 后端生产运行与进程管理
- 选择生产运行方式：
  - `uvicorn`/`gunicorn` 多进程（建议）。
- 补充服务启动脚本或 systemd 单元文件：
  - 自动启动、崩溃自启、日志持久化。
- 健康检查与探活：
  - `/health` 已存在，但需在负载均衡/监控中启用。

## 4) 反向代理与 HTTPS
- 配置 Nginx/Traefik 反向代理：
  - 反代后端 `:3000`。
  - 静态托管前端 `dist/`。
- 申请并配置 HTTPS（Let’s Encrypt/ACME）：
  - 自动续期证书。
  - 强制 HTTP → HTTPS。

## 5) 数据库与迁移
- 当前使用 SQLite（`DB_PATH`，默认 `./db/xiaotiao.db`）。
- 需保证服务器磁盘持久化与备份机制：
  - 定期备份 `db/` 与 `uploads/`。
- 启动时已执行 `db/migrations/*.sql`，但需确认生产环境权限与路径一致。

## 6) 文件存储与上传文件持久化
- 论文 PDF 上传路径：`xiaotiao-server/uploads/papers`。
- 上云必须保证该目录可写、可持久化（容器需挂载卷）。
- 需要明确存储策略：
  - 本地磁盘 or 对象存储（如 OSS/S3）。

## 7) 环境变量与密钥管理
- 后端 `.env` 需要安全管理（不要进仓库）：
  - `LLM_PROVIDER` / `QWEN_API_KEY` / `ANTHROPIC_API_KEY` 等。
  - `DB_PATH`（生产路径）。
  - `LLM_SSL_VERIFY`（如需关闭证书校验需评估风险）。
- 前端 `VITE_API_BASE_URL` 需在构建时注入。

## 8) 依赖与系统包确认
- 生产环境需安装 Python 依赖（`requirements.txt`）。
- `PyMuPDF` 在部分 Linux 环境需要额外系统库支持，需提前验证。
- Node 版本与 npm 镜像配置（如使用 `pnpm`/`npm`）。

## 9) 日志、监控与告警
- 日志落盘或输出到平台：
  - 访问日志、错误日志、LLM 调用耗时。
- 监控：
  - CPU/内存/磁盘、请求量、错误率、超时率。

## 10) 运行时安全
- CORS 生产域名白名单收敛（当前只允许 localhost）。
- 后端接口鉴权/限流策略（目前多数接口无鉴权）。
- 防止大文件上传与恶意调用（限制大小、频率）。

## 11) 发布流程与回滚
- 建立部署脚本或 CI/CD（GitHub Actions）。
- 版本管理与回滚机制：
  - 保留上一个可运行版本。

## 12) 生产验证清单
- 核心链路验证：
  - 前端能访问后端。
  - 论文导入、上传、解析、阅读与追踪正常。
- LLM 接口联通与超时策略验证。
- 上传 PDF、导出功能、PDF 阅读器渲染验证。

---

如你希望，我可以基于你选定的服务器环境（如阿里云/腾讯云 + Ubuntu + Nginx + systemd）补齐部署脚本与配置，并给出一步到位的上线流程。
