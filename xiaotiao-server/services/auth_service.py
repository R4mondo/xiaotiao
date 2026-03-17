import base64
import hashlib
import hmac
import os
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict

from fastapi import HTTPException, Request

from db.auth_db import (
    create_session,
    create_user,
    delete_session,
    get_user_by_id,
    get_user_by_token,
    get_user_by_username,
)

PASSWORD_ITERATIONS = int(os.getenv("AUTH_PASSWORD_ITERATIONS", "120000"))
SESSION_DAYS = int(os.getenv("AUTH_SESSION_DAYS", "7"))


def _encode_bytes(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")


def _decode_bytes(encoded: str) -> bytes:
    padded = encoded + "=" * (-len(encoded) % 4)
    return base64.urlsafe_b64decode(padded.encode("utf-8"))


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PASSWORD_ITERATIONS)
    return f"{PASSWORD_ITERATIONS}${_encode_bytes(salt)}${_encode_bytes(dk)}"


def verify_password(password: str, stored: str) -> bool:
    try:
        iterations_str, salt_b64, hash_b64 = stored.split("$", 2)
        iterations = int(iterations_str)
        salt = _decode_bytes(salt_b64)
        expected = _decode_bytes(hash_b64)
    except Exception:
        return False
    actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return hmac.compare_digest(actual, expected)


def register_user(username: str, password: str) -> Dict:
    if not username or not password:
        raise HTTPException(status_code=422, detail="用户名与密码不能为空。")
    if len(password) < 6:
        raise HTTPException(status_code=422, detail="密码长度至少为 6 位。")
    if len(username) < 2 or len(username) > 30:
        raise HTTPException(status_code=422, detail="用户名长度应在 2-30 个字符之间。")
    existing = get_user_by_username(username)
    if existing:
        raise HTTPException(status_code=409, detail="用户名已存在，请更换。")
    user_id = str(uuid.uuid4())
    password_hash = hash_password(password)
    return create_user(user_id, username, password_hash)


def authenticate_user(username: str, password: str) -> Optional[Dict]:
    user = get_user_by_username(username)
    if not user:
        return None
    if not verify_password(password, user.get("password_hash", "")):
        return None
    return user


def create_user_session(user_id: str) -> str:
    token = uuid.uuid4().hex
    expires_at = (datetime.now(timezone.utc) + timedelta(days=SESSION_DAYS)).isoformat()
    create_session(token, user_id, expires_at)
    return token


def logout_session(token: str) -> None:
    if token:
        delete_session(token)


def extract_token(request: Request) -> str:
    auth_header = request.headers.get("Authorization", "")
    if auth_header.lower().startswith("bearer "):
        return auth_header.split(" ", 1)[1].strip()
    xauth = request.headers.get("X-Auth-Token", "").strip()
    if xauth:
        return xauth
    # Fallback: query param token (for file download links)
    return request.query_params.get("token", "").strip()


def require_user(request: Request) -> Dict:
    token = extract_token(request)
    user = get_user_by_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="未登录或登录已失效。")
    return user


def get_user_from_token(token: str) -> Optional[Dict]:
    return get_user_by_token(token)


def get_safe_user(user_id: str) -> Optional[Dict]:
    return get_user_by_id(user_id)
