"""Team Members API — public endpoint + admin management."""
import json
import os
import uuid
import shutil
from fastapi import APIRouter, Request, UploadFile, File, Form
from fastapi.responses import JSONResponse

router = APIRouter(tags=["团队管理"])

TEAM_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "team_members.json")
TEAM_UPLOADS_DIR = os.path.join(os.path.dirname(__file__), "..", "uploads", "team")

os.makedirs(TEAM_UPLOADS_DIR, exist_ok=True)


def _load_members() -> list:
    try:
        with open(TEAM_DATA_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _save_members(members: list):
    with open(TEAM_DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(members, f, indent=2, ensure_ascii=False)


# ── Public endpoint (no auth required) ──

@router.get("/api/team-members", summary="获取已审核的团队成员列表")
async def get_team_members():
    """Public endpoint — returns only approved members."""
    members = _load_members()
    approved = [m for m in members if m.get("approved", False)]
    # Don't expose internal fields
    public = []
    for m in approved:
        public.append({
            "id": m.get("id"),
            "name": m.get("name", ""),
            "role": m.get("role", ""),
            "bio": m.get("bio", ""),
            "avatar_url": m.get("avatar_url", ""),
            "order": m.get("order", 99),
        })
    public.sort(key=lambda x: x.get("order", 99))
    return {"members": public}


# ── Admin endpoints (auth checked by admin router) ──

@router.get("/api/admin/team-members", summary="管理员获取所有团队成员")
async def admin_get_team_members(request: Request):
    members = _load_members()
    return {"members": members}


@router.post("/api/admin/team-members", summary="添加团队成员")
async def admin_add_member(request: Request):
    body = await request.json()
    member = {
        "id": str(uuid.uuid4())[:8],
        "name": body.get("name", ""),
        "role": body.get("role", ""),
        "bio": body.get("bio", ""),
        "avatar_url": body.get("avatar_url", ""),
        "order": body.get("order", 99),
        "approved": False,
    }
    members = _load_members()
    members.append(member)
    _save_members(members)
    return {"ok": True, "member": member}


@router.put("/api/admin/team-members/{member_id}", summary="更新团队成员")
async def admin_update_member(member_id: str, request: Request):
    body = await request.json()
    members = _load_members()
    for m in members:
        if m.get("id") == member_id:
            for key in ["name", "role", "bio", "avatar_url", "order", "approved"]:
                if key in body:
                    m[key] = body[key]
            _save_members(members)
            return {"ok": True, "member": m}
    return JSONResponse({"error": "成员不存在"}, status_code=404)


@router.delete("/api/admin/team-members/{member_id}", summary="删除团队成员")
async def admin_delete_member(member_id: str):
    members = _load_members()
    members = [m for m in members if m.get("id") != member_id]
    _save_members(members)
    return {"ok": True}


@router.post("/api/admin/team-members/{member_id}/avatar", summary="上传成员头像")
async def admin_upload_avatar(member_id: str, file: UploadFile = File(...)):
    ext = os.path.splitext(file.filename or "img.png")[1] or ".png"
    filename = f"{member_id}{ext}"
    filepath = os.path.join(TEAM_UPLOADS_DIR, filename)
    with open(filepath, "wb") as f:
        shutil.copyfileobj(file.file, f)

    avatar_url = f"/uploads/team/{filename}"

    # Update member record
    members = _load_members()
    for m in members:
        if m.get("id") == member_id:
            m["avatar_url"] = avatar_url
            break
    _save_members(members)

    return {"ok": True, "avatar_url": avatar_url}
