#!/usr/bin/env bash
# ========================================================
# 小挑 — 数据备份脚本
# ========================================================
# 用法: bash deploy/backup.sh
# 建议配置 crontab 每日自动执行:
#   0 3 * * * /home/deploy/xiaotiao-main/deploy/backup.sh >> /var/log/xiaotiao-backup.log 2>&1
# ========================================================
set -euo pipefail

# ---- 配置 ----
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SERVER_DIR="$PROJECT_ROOT/xiaotiao-server"
BACKUP_ROOT="${BACKUP_DIR:-/home/deploy/backups/xiaotiao}"
KEEP_DAYS="${BACKUP_KEEP_DAYS:-7}"
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
BACKUP_DIR_TODAY="$BACKUP_ROOT/$TIMESTAMP"

echo "[backup] 开始备份 — $TIMESTAMP"

mkdir -p "$BACKUP_DIR_TODAY"

# ---- 备份认证数据库 ----
if [ -f "$SERVER_DIR/db/auth.db" ]; then
    cp "$SERVER_DIR/db/auth.db" "$BACKUP_DIR_TODAY/auth.db"
    echo "  ✅ auth.db"
fi

# ---- 备份共享数据库 ----
if [ -f "$SERVER_DIR/db/xiaotiao.db" ]; then
    cp "$SERVER_DIR/db/xiaotiao.db" "$BACKUP_DIR_TODAY/xiaotiao.db"
    echo "  ✅ xiaotiao.db"
fi

# ---- 备份用户数据库 ----
if [ -d "$SERVER_DIR/db/users" ]; then
    cp -r "$SERVER_DIR/db/users" "$BACKUP_DIR_TODAY/users"
    echo "  ✅ db/users/"
fi

# ---- 备份上传文件 ----
if [ -d "$SERVER_DIR/uploads" ]; then
    cp -r "$SERVER_DIR/uploads" "$BACKUP_DIR_TODAY/uploads"
    echo "  ✅ uploads/"
fi

# ---- 备份 .env (密钥) ----
if [ -f "$SERVER_DIR/.env" ]; then
    cp "$SERVER_DIR/.env" "$BACKUP_DIR_TODAY/dot_env"
    echo "  ✅ .env"
fi

# ---- 压缩 ----
cd "$BACKUP_ROOT"
tar -czf "${TIMESTAMP}.tar.gz" "$TIMESTAMP" && rm -rf "$TIMESTAMP"
echo "  📦 已压缩: ${TIMESTAMP}.tar.gz"

# ---- 清理旧备份 ----
find "$BACKUP_ROOT" -name "*.tar.gz" -mtime +${KEEP_DAYS} -delete 2>/dev/null || true
echo "  🧹 已清理 ${KEEP_DAYS} 天前的旧备份"

BACKUP_SIZE=$(du -sh "$BACKUP_ROOT/${TIMESTAMP}.tar.gz" | cut -f1)
echo "[backup] 完成 — 大小: $BACKUP_SIZE"
