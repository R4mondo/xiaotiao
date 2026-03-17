# 云服务器部署待办清单

以下清单基于当前仓库内容梳理，用于"上云"前的补齐与确认。

> **推荐部署架构**: 阿里云 ECS + Ubuntu + Nginx（同域反代）+ systemd
>
> **首次部署**: `sudo bash deploy/setup.sh` → 编辑配置 → `bash deploy/deploy.sh`
>
> **后续更新**: `bash deploy/deploy.sh`（一键拉取构建重启）

---

## 1) 部署形态与访问路径 ✅

- **方案**: Nginx 同域反向代理 — `/` 前端静态文件，后端路由直接反代到 `:3000`。
- **配置**: [`deploy/nginx/xiaotiao.conf`](deploy/nginx/xiaotiao.conf)
- 前端 `VITE_API_BASE_URL` 构建时设为空（相对路径），无需跨域。
- CORS 配置已支持环境变量 `CORS_ORIGINS`（见 `main.py`），同域模式下可设为 `*`。
- [ ] **待操作**: 将 `xiaotiao.conf` 中的 `YOUR_DOMAIN_OR_IP` 替换为实际域名/IP。

## 2) 前端生产构建与静态托管 ✅

- 构建命令: `VITE_API_BASE_URL="" npm run build` — 已集成到 `deploy/deploy.sh`。
- Nginx 静态托管: `root /home/deploy/xiaotiao-main/xiaotiao-app/dist;`
- SPA 路由回退: `try_files $uri $uri/ /index.html;`
- [ ] **待操作**: 调整 Nginx 配置中的 `root` 路径为实际部署路径。

## 3) 后端生产运行与进程管理 ✅

- **systemd 服务**: [`deploy/systemd/xiaotiao-server.service`](deploy/systemd/xiaotiao-server.service)
  - uvicorn 单 worker（SQLite 约束），崩溃自启（`Restart=on-failure`）。
  - 日志: `journalctl -u xiaotiao-server`
- `/health` 接口已存在，`deploy.sh` 部署后自动检查。
- [ ] **待操作**: 调整 service 文件中的路径为实际部署路径。

## 4) 反向代理与 HTTPS ✅

- Nginx 反代配置已包含在 `xiaotiao.conf`。
- HTTPS 模板已注释在配置文件底部，使用 Let's Encrypt:
  ```bash
  sudo apt install certbot python3-certbot-nginx
  sudo certbot --nginx -d YOUR_DOMAIN
  ```
- [ ] **待操作**: 如需 HTTPS，取消注释并运行 certbot。

## 5) 数据库与迁移 ✅

- SQLite（`auth.db` + 用户级 `db/users/*.db`），启动时自动执行 migration。
- **备份脚本**: [`deploy/backup.sh`](deploy/backup.sh) — 备份所有数据库与上传文件。
- [ ] **待操作**: 配置 crontab 定时备份:
  ```bash
  crontab -e
  0 3 * * * /home/deploy/xiaotiao-main/deploy/backup.sh >> /var/log/xiaotiao-backup.log 2>&1
  ```

## 6) 文件存储与上传文件持久化 ✅

- 论文 PDF 路径: `xiaotiao-server/uploads/papers`。
- `setup.sh` 自动创建目录，systemd 配置有 `ReadWritePaths` 权限。
- 备份脚本已覆盖 `uploads/` 目录。

## 7) 环境变量与密钥管理 ✅

- `.env` 已在 `.gitignore`，不会进入仓库。
- systemd 通过 `EnvironmentFile` 加载 `.env`。
- 前端 `VITE_API_BASE_URL` 在 `deploy.sh` 构建时注入。
- [ ] **待操作**: 在服务器创建 `.env` 文件:
  ```
  LLM_PROVIDER=qwen
  QWEN_API_KEY=your_key_here
  CORS_ORIGINS=*
  DB_PATH=./db/xiaotiao.db
  ```

## 8) 依赖与系统包确认 ✅

- `setup.sh` 自动安装 Python3、Node.js 20.x、Nginx。
- `deploy.sh` 自动创建 venv 并安装 `requirements.txt`。
- PyMuPDF 在 Ubuntu 上通常可直接 pip 安装；如遇问题需 `apt install libmupdf-dev`。

## 9) 日志、监控与告警 ⚠️

- 后端日志: `journalctl -u xiaotiao-server -f`
- Nginx 日志: `/var/log/nginx/access.log` `/var/log/nginx/error.log`
- [ ] **待操作（可选）**: 配置日志轮转、接入云监控告警。

## 10) 运行时安全 ✅

- CORS 已改为环境变量驱动，生产环境可精确控制。
- 后端有 auth_guard 中间件，非公开接口需鉴权。
- Nginx `client_max_body_size 50M` 限制上传大小。
- [ ] **待操作（建议）**: 添加 Nginx rate limiting 防止恶意调用。

## 11) 发布流程与回滚 ✅

- **部署脚本**: [`deploy/deploy.sh`](deploy/deploy.sh) — 一键 git pull + 依赖 + 构建 + 重启。
- **CI/CD**: [`.github/workflows/deploy.yml`](.github/workflows/deploy.yml) — push to main 自动部署。
  - [ ] **待操作**: 在 GitHub 仓库 Settings → Secrets 添加:
    - `SERVER_HOST` — 服务器公网 IP
    - `SERVER_USER` — 部署用户名（如 `deploy`）
    - `SERVER_SSH_KEY` — SSH 私钥
- **回滚**: `git revert` 或 `git checkout <commit>` 后重新运行 `deploy.sh`。

## 12) 生产验证清单 ⚠️

部署完成后逐项验证:

- [ ] 前端页面可通过公网 IP/域名访问
- [ ] 注册 → 登录 → 退出 → 重新登录
- [ ] 论文导入/上传/解析/阅读
- [ ] 生词本增删改查与导出
- [ ] 文章生成 / 翻译 / 解读（LLM 联通性）
- [ ] PDF 阅读器渲染正常
- [ ] `kill` 后端进程后 systemd 自动重启
- [ ] 备份脚本生成 tar.gz 文件

---

## 部署文件总览

| 文件 | 用途 |
|------|------|
| `deploy/setup.sh` | 首次服务器初始化（装包、建用户、装配置） |
| `deploy/deploy.sh` | 一键更新部署（拉代码、装依赖、构建、重启） |
| `deploy/backup.sh` | 数据备份（数据库 + 上传文件，支持 crontab） |
| `deploy/nginx/xiaotiao.conf` | Nginx 站点配置（反代 + 静态托管 + HTTPS 模板） |
| `deploy/systemd/xiaotiao-server.service` | 后端 systemd 服务（自启动、崩溃恢复、日志） |
| `.github/workflows/deploy.yml` | GitHub Actions 自动部署 |
