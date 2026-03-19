"""V2.0 User Profile & Config API endpoints."""
from fastapi import APIRouter, Request
from pydantic import BaseModel
from typing import Optional, List

from db.auth_db import get_user_profile, update_user_profile

router = APIRouter(tags=["用户画像"])


# ── Schemas ──────────────────────────────────

class ProfileUpdate(BaseModel):
    exam_type: Optional[str] = None
    subject_field: Optional[List[str]] = None
    specialty: Optional[List[str]] = None
    eng_level: Optional[str] = None
    interest_tags: Optional[List[str]] = None
    onboarding_completed: Optional[bool] = None


# ── Profile field options (static config) ────

EXAM_TYPES = [
    {"id": "kaoyan", "label": "考研英语"},
    {"id": "cet4", "label": "四级"},
    {"id": "cet6", "label": "六级"},
    {"id": "ielts", "label": "雅思"},
    {"id": "toefl", "label": "托福"},
    {"id": "bar_exam", "label": "法律英语/法考"},
    {"id": "other", "label": "其他"},
]

SUBJECT_FIELDS = [
    {"id": "law", "label": "法学"},
    {"id": "finance", "label": "金融"},
    {"id": "cs", "label": "计算机"},
    {"id": "medicine", "label": "医学"},
    {"id": "engineering", "label": "工程"},
    {"id": "humanities", "label": "人文"},
    {"id": "other", "label": "其他"},
]

SPECIALTIES = {
    "law": [
        {"id": "international-law", "label": "国际法"},
        {"id": "commercial-law", "label": "商法"},
        {"id": "constitutional-law", "label": "宪法学"},
        {"id": "criminal-law", "label": "刑法学"},
        {"id": "ip-law", "label": "知识产权法"},
        {"id": "financial-law", "label": "金融法"},
        {"id": "environmental-law", "label": "环境法"},
        {"id": "administrative-law", "label": "行政法"},
        {"id": "civil-law", "label": "民法"},
        {"id": "procedural-law", "label": "诉讼法"},
    ],
    "finance": [
        {"id": "accounting", "label": "会计"},
        {"id": "banking", "label": "银行"},
        {"id": "securities", "label": "证券"},
        {"id": "insurance", "label": "保险"},
        {"id": "fintech", "label": "金融科技"},
    ],
    "cs": [
        {"id": "ai", "label": "人工智能"},
        {"id": "cybersecurity", "label": "网络安全"},
        {"id": "data-science", "label": "数据科学"},
        {"id": "software-engineering", "label": "软件工程"},
    ],
    "medicine": [
        {"id": "clinical", "label": "临床医学"},
        {"id": "pharmacy", "label": "药学"},
        {"id": "public-health", "label": "公共卫生"},
    ],
    "engineering": [
        {"id": "civil-eng", "label": "土木工程"},
        {"id": "mechanical", "label": "机械工程"},
        {"id": "electrical", "label": "电气工程"},
    ],
    "humanities": [
        {"id": "philosophy", "label": "哲学"},
        {"id": "history", "label": "历史"},
        {"id": "literature", "label": "文学"},
        {"id": "politics", "label": "政治学"},
    ],
}

ENG_LEVELS = [
    {"id": "cet4", "label": "CET-4", "description": "大学英语四级水平"},
    {"id": "cet6", "label": "CET-6", "description": "大学英语六级水平"},
    {"id": "ielts5", "label": "雅思 5-6 分", "description": "中级英语水平"},
    {"id": "ielts7", "label": "雅思 7+ 分", "description": "高级英语水平"},
    {"id": "native", "label": "接近母语", "description": "可无障碍阅读学术文献"},
]

INTEREST_TAGS = [
    "区块链监管", "跨境金融", "国际仲裁", "知识产权",
    "数据隐私", "人工智能法律", "环境法", "国际贸易",
    "公司治理", "反垄断", "税法", "海商法",
    "劳动法", "消费者保护", "刑事司法", "人权法",
]


# ── Endpoints ────────────────────────────────

@router.get(
    "/user/profile",
    summary="获取用户画像",
    description="返回当前登录用户的画像数据（JSON 格式）。",
)
async def get_profile(request: Request):
    user = request.state.user
    profile = get_user_profile(user["id"])
    return {"profile": profile}


@router.put(
    "/user/profile",
    summary="更新用户画像",
    description="部分更新用户画像，仅传入需要修改的字段即可，其他字段保持不变。",
)
async def put_profile(request: Request, body: ProfileUpdate):
    user = request.state.user
    updates = body.model_dump(exclude_none=True)
    if not updates:
        profile = get_user_profile(user["id"])
        return {"profile": profile}
    profile = update_user_profile(user["id"], updates)
    return {"profile": profile}


@router.get(
    "/config/fields",
    summary="获取画像字段选项",
    description="返回所有画像字段的可选项（备考目标、学科、英语水平、兴趣标签等）。",
)
async def get_fields(request: Request):
    return {
        "exam_types": EXAM_TYPES,
        "subject_fields": SUBJECT_FIELDS,
        "eng_levels": ENG_LEVELS,
        "interest_tags": INTEREST_TAGS,
    }


@router.get(
    "/config/specialties",
    summary="获取细分专业列表",
    description="根据学科领域 ID 返回对应的细分专业列表。",
)
async def get_specialties(request: Request, field: str = "law"):
    items = SPECIALTIES.get(field, [])
    return {"field": field, "specialties": items}
