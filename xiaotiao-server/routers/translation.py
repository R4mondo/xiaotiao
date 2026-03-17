import os
from fastapi import APIRouter, HTTPException
from schemas import TranslationRequest, TranslationResponse
from services.prompt_engine import prompt_engine

router = APIRouter(prefix="/translation", tags=["翻译"])


@router.post(
    "/run",
    response_model=TranslationResponse,
    summary="文本翻译",
    description="对输入文本进行多风格翻译，支持直译、法律表达、简明表达。",
)
async def run_translation(req: TranslationRequest):
    if len(req.source_text) > 6000:
        raise HTTPException(status_code=422, detail="文本超过 5000 字符限制。")

    try:
        response = await prompt_engine.generate(
            template_name="translation.j2",
            response_model=TranslationResponse,
            max_tokens=4000,
            # 模板变量
            direction=req.direction,
            source_text=req.source_text,
            user_translation=req.user_translation or "",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"LLM 翻译失败：{e}"
        )

    return response
