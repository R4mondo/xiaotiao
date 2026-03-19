import os
from fastapi import APIRouter, HTTPException, Request
from schemas import TranslationRequest, TranslationResponse
from services.prompt_engine import prompt_engine
from db.auth_db import get_user_profile

router = APIRouter(prefix="/translation", tags=["翻译"])


@router.post(
    "/run",
    response_model=TranslationResponse,
    summary="文本翻译",
    description="对输入文本进行多风格翻译，支持直译、法律表达、简明表达。",
)
async def run_translation(req: TranslationRequest, request: Request):
    if len(req.source_text) > 5000:
        raise HTTPException(status_code=422, detail="文本超过 5000 字符限制。")

    # V2.0: 读取用户画像，注入专业方向到翻译提示词
    user_profile = {}
    try:
        user_profile = get_user_profile(request.state.user["id"])
    except Exception:
        pass

    try:
        response = await prompt_engine.generate(
            template_name="translation.j2",
            response_model=TranslationResponse,
            max_tokens=4000,
            feature_id="translation",
            # 模板变量
            direction=req.direction,
            source_text=req.source_text,
            user_translation=req.user_translation or "",
            # V2.0: 用户画像注入
            user_specialty=user_profile.get("specialty", ""),
            user_subject_field=user_profile.get("subject_field", ""),
        )
    except Exception as e:
        import logging
        logging.getLogger("xiaotiao").error("Translation error: %s", e)
        raise HTTPException(
            status_code=500, detail="AI 翻译失败，请稍后重试。"
        )

    return response
