#!/usr/bin/env bash
# ========================================================
# 小挑 — 首次服务器初始化脚本
# ========================================================
# 适用于: Ubuntu 22.04+ / Debian 12+ 阿里云 ECS
# 用法: 以 root 身份运行
#   sudo bash deploy/setup.sh
# ========================================================
set -euo pipefail

DEPLOY_USER="${DEPLOY_USER:-deploy}"
PROJECT_DIR="/home/$DEPLOY_USER/xiaotiao-main"
NODE_MAJOR=20

echo "=========================================="
echo "  小挑 — 服务器初始化"
echo "  $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="

# ---- 1. 系统包更新 ----
echo ""
echo "[1/7] 更新系统包..."
apt-get update -qq
apt-get upgrade -y -qq

# ---- 2. 安装基础依赖 ----
echo ""
echo "[2/7] 安装基础依赖..."
apt-get install -y -qq \
    python3 python3-venv python3-pip \
    nginx curl git \
    build-essential libffi-dev

# ---- 3. 安装 Node.js ----
echo ""
echo "[3/7] 安装 Node.js ${NODE_MAJOR}.x..."
if ! command -v node &>/dev/null || [[ $(node -v | cut -d'.' -f1 | tr -d 'v') -lt $NODE_MAJOR ]]; then
    curl -fsSL https://deb.nodesource.com/setup_${NODE_MAJOR}.x | bash -
    apt-get install -y -qq nodejs
fi
echo "  Node: $(node -v), npm: $(npm -v)"

# ---- 4. 创建部署用户 ----
echo ""
echo "[4/7] 配置部署用户..."
if ! id "$DEPLOY_USER" &>/dev/null; then
    useradd -m -s /bin/bash "$DEPLOY_USER"
    echo "  创建用户: $DEPLOY_USER"
fi

# ---- 5. 克隆/配置项目 ----
echo ""
echo "[5/7] 项目目录配置..."
if [ ! -d "$PROJECT_DIR" ]; then
    echo "  ⚠️  请先将项目代码放到 $PROJECT_DIR"
    echo "  示例: git clone <repo-url> $PROJECT_DIR"
    echo "  然后重新运行此脚本"
else
    # 确保目录属主正确
    chown -R "$DEPLOY_USER:$DEPLOY_USER" "$PROJECT_DIR"

    # 创建必要子目录
    su - "$DEPLOY_USER" -c "mkdir -p $PROJECT_DIR/xiaotiao-server/db/users"
    su - "$DEPLOY_USER" -c "mkdir -p $PROJECT_DIR/xiaotiao-server/uploads/papers"
    echo "  ✅ 目录结构已就绪"
fi

# ---- 6. Python 虚拟环境 ----
echo ""
echo "[6/7] 设置 Python 虚拟环境..."
if [ -d "$PROJECT_DIR/xiaotiao-server" ]; then
    su - "$DEPLOY_USER" -c "
        cd $PROJECT_DIR/xiaotiao-server
        python3 -m venv .venv
        .venv/bin/pip install --upgrade pip -q
        .venv/bin/pip install -r requirements.txt -q
    "
    echo "  ✅ Python 依赖已安装"

    # 检查 .env
    if [ ! -f "$PROJECT_DIR/xiaotiao-server/.env" ]; then
        echo ""
        echo "  ⚠️  请创建 $PROJECT_DIR/xiaotiao-server/.env 文件，包含以下变量:"
        echo "  ---"
        echo "  LLM_PROVIDER=qwen"
        echo "  QWEN_API_KEY=your_key_here"
        echo "  CORS_ORIGINS=*"
        echo "  DB_PATH=./db/xiaotiao.db"
        echo "  ---"
    fi
fi

# ---- 7. 安装 systemd & Nginx 配置 ----
echo ""
echo "[7/7] 安装服务配置..."
if [ -d "$PROJECT_DIR/deploy" ]; then
    # systemd
    if [ -f "$PROJECT_DIR/deploy/systemd/xiaotiao-server.service" ]; then
        cp "$PROJECT_DIR/deploy/systemd/xiaotiao-server.service" /etc/systemd/system/
        systemctl daemon-reload
        systemctl enable xiaotiao-server
        echo "  ✅ systemd 服务已安装并启用"
    fi

    # Nginx
    if [ -f "$PROJECT_DIR/deploy/nginx/xiaotiao.conf" ]; then
        cp "$PROJECT_DIR/deploy/nginx/xiaotiao.conf" /etc/nginx/sites-available/
        ln -sf /etc/nginx/sites-available/xiaotiao.conf /etc/nginx/sites-enabled/
        rm -f /etc/nginx/sites-enabled/default
        echo "  ✅ Nginx 配置已安装"
        echo "  ⚠️  请编辑 /etc/nginx/sites-available/xiaotiao.conf"
        echo "     将 YOUR_DOMAIN_OR_IP 替换为实际域名或公网 IP"
    fi
fi

# ---- 创建备份目录 ----
mkdir -p /home/$DEPLOY_USER/backups/xiaotiao
chown -R "$DEPLOY_USER:$DEPLOY_USER" /home/$DEPLOY_USER/backups

echo ""
echo "=========================================="
echo "  ✅ 初始化完成！"
echo ""
echo "  后续步骤:"
echo "  1. 编辑 Nginx 配置中的域名/IP"
echo "  2. 创建 .env 文件 (如果还没有)"
echo "  3. 运行 bash deploy/deploy.sh 完成部署"
echo "  4. (可选) 配置 HTTPS:"
echo "     sudo apt install certbot python3-certbot-nginx"
echo "     sudo certbot --nginx -d YOUR_DOMAIN"
echo "  5. (可选) 配置定时备份:"
echo "     crontab -e"
echo "     0 3 * * * $PROJECT_DIR/deploy/backup.sh"
echo "=========================================="
