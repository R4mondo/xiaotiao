#!/usr/bin/env bash
# ========================================================
# 小挑 — 一键部署/更新脚本
# ========================================================
# 用法: bash deploy/deploy.sh
# 在服务器项目根目录下执行，完成代码拉取、依赖安装、
# 前端构建、配置同步和服务重启。
# ========================================================
set -euo pipefail

# ---- 配置 ----
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SERVER_DIR="$PROJECT_ROOT/xiaotiao-server"
APP_DIR="$PROJECT_ROOT/xiaotiao-app"
VENV_DIR="$SERVER_DIR/.venv"
SERVICE_NAME="xiaotiao-server"

echo "=========================================="
echo "  小挑部署脚本"
echo "  $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="

# ---- 1. 拉取最新代码 ----
echo ""
echo "[1/6] 拉取最新代码..."
cd "$PROJECT_ROOT"
git pull --ff-only origin main || {
    echo "⚠️  git pull 失败，请手动解决冲突后重试"
    exit 1
}

# ---- 2. Python 虚拟环境 & 依赖 ----
echo ""
echo "[2/6] 安装/更新 Python 依赖..."
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
fi
"$VENV_DIR/bin/pip" install --upgrade pip -q
"$VENV_DIR/bin/pip" install -r "$SERVER_DIR/requirements.txt" -q

# ---- 3. 构建前端 ----
echo ""
echo "[3/6] 构建前端..."
cd "$APP_DIR"
npm install --production=false --silent 2>/dev/null || npm install --silent
# 同域反代下 API 使用相对路径，设置为空
VITE_API_BASE_URL="" npm run build

# ---- 4. 同步 Nginx 配置 ----
echo ""
echo "[4/6] 同步 Nginx 配置..."
NGINX_CONF="/etc/nginx/sites-available/xiaotiao.conf"
NGINX_ENABLED="/etc/nginx/sites-enabled/xiaotiao.conf"

if [ -f "$PROJECT_ROOT/deploy/nginx/xiaotiao.conf" ]; then
    sudo cp "$PROJECT_ROOT/deploy/nginx/xiaotiao.conf" "$NGINX_CONF"
    if [ ! -L "$NGINX_ENABLED" ]; then
        sudo ln -s "$NGINX_CONF" "$NGINX_ENABLED"
    fi
    # 删除默认配置（如果存在）
    sudo rm -f /etc/nginx/sites-enabled/default
    sudo nginx -t && sudo systemctl reload nginx
    echo "  ✅ Nginx 配置已更新并重载"
else
    echo "  ⚠️  未找到 Nginx 配置文件，跳过"
fi

# ---- 5. 同步 systemd 配置 & 重启后端 ----
echo ""
echo "[5/6] 重启后端服务..."
SYSTEMD_SRC="$PROJECT_ROOT/deploy/systemd/xiaotiao-server.service"
SYSTEMD_DEST="/etc/systemd/system/${SERVICE_NAME}.service"

if [ -f "$SYSTEMD_SRC" ]; then
    sudo cp "$SYSTEMD_SRC" "$SYSTEMD_DEST"
    sudo systemctl daemon-reload
    sudo systemctl enable "$SERVICE_NAME"
fi
sudo systemctl restart "$SERVICE_NAME"
echo "  ✅ 后端服务已重启"

# ---- 6. 健康检查 ----
echo ""
echo "[6/6] 健康检查..."
sleep 3
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:3000/health || echo "000")
if [ "$HTTP_CODE" = "200" ]; then
    echo "  ✅ 后端健康检查通过 (HTTP $HTTP_CODE)"
else
    echo "  ❌ 后端健康检查失败 (HTTP $HTTP_CODE)"
    echo "  查看日志: sudo journalctl -u $SERVICE_NAME -n 50 --no-pager"
    exit 1
fi

echo ""
echo "=========================================="
echo "  ✅ 部署完成！"
echo "=========================================="
