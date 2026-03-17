# 🚀 服务器更新指南

> 每次在本地修改代码后，按照以下流程将新版本部署到阿里云服务器。

## 服务器信息

| 项目 | 值 |
|------|------|
| 服务器 IP | `47.103.117.65` |
| 项目路径 | `/home/xiaotiao/` |
| 后端服务名 | `xiaotiao.service` |
| 后端端口 | `3000` |
| 虚拟环境 | `/home/xiaotiao/xiaotiao-server/venv/` |
| 前端构建目录 | `/home/xiaotiao/xiaotiao-app/dist/` |

---

## 第一步：本地提交并推送

```bash
cd /Users/zzzzy/Downloads/项目/xiaotiao-main
git add -A
git commit -m "描述你的改动"
git push origin main        # 推送到个人仓库
git push r4mondo main       # 推送到协作仓库
```

---

## 第二步：SSH 登录服务器

通过阿里云 Workbench 或本地终端 SSH 登录。

---

## 第三步：拉取并部署

### 快速一键更新（仅后端改动）

```bash
cd /home/xiaotiao
git pull origin main
cd xiaotiao-server
./venv/bin/pip install -r requirements.txt -q
sudo systemctl restart xiaotiao.service
```

### 包含前端改动时

```bash
cd /home/xiaotiao
git pull origin main

# 后端
cd xiaotiao-server
./venv/bin/pip install -r requirements.txt -q
sudo systemctl restart xiaotiao.service

# 前端
cd ../xiaotiao-app
npm run build
```

### 包含 Nginx 配置改动时

```bash
sudo cp /home/xiaotiao/deploy/nginx/xiaotiao.conf /etc/nginx/sites-available/xiaotiao.conf
sudo nginx -t && sudo systemctl reload nginx
```

---

## 第四步：验证

```bash
# 检查后端状态
sudo systemctl status xiaotiao.service --no-pager

# 健康检查
curl http://127.0.0.1:3000/health

# 管理后台（应返回 HTML）
curl -s http://127.0.0.1:3000/admin | head -c 100
```

浏览器访问：
- 前端主站：`http://47.103.117.65`
- 管理后台：`http://47.103.117.65/admin`

---

## 常见问题排查

### 后端启动失败 (502 Bad Gateway)

```bash
# 查看错误日志
sudo journalctl -u xiaotiao.service -n 30 --no-pager

# 如果是 "Start request repeated too quickly"
sudo systemctl reset-failed xiaotiao.service
sudo systemctl start xiaotiao.service
```

### 端口被占用

```bash
fuser -k -9 3000/tcp
sleep 2
sudo systemctl start xiaotiao.service
```

### 依赖版本冲突

```bash
cd /home/xiaotiao/xiaotiao-server
./venv/bin/pip install --upgrade anthropic httpx
sudo systemctl restart xiaotiao.service
```

### Git 拉取失败 (TLS 错误)

```bash
# 切换远程地址
git remote set-url origin https://github.com/zhuziyan-zzy/xiaotiao.git
git pull origin main
```

---

## ⚠️ 注意事项

1. **代码路径**：服务器代码在 `/home/xiaotiao/`，不是 `/root/xiaotiao/`
2. **虚拟环境**：服务器用的是 `venv`（不是 `.venv`）
3. **systemd 管理**：不要手动 `nohup python main.py`，用 `systemctl restart xiaotiao.service`
4. **管理后台密码**：`xiaotiao2026`（可通过 `.env` 中 `ADMIN_PASSWORD` 修改）
