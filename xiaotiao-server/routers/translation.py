import os
from fastapi import APIRouter, HTTPException
from schemas import TranslationRequest, TranslationResponse
from services.llm import call_claude_json

router = APIRouter(prefix="/translation", tags=["翻译"])

def load_prompt(filename: str) -> str:
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompts", filename)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

@router.post(
    "/run",
    response_model=TranslationResponse,
    summary="文本翻译",
    description="对输入文本进行多风格翻译，支持直译、法律表达、简明表达。",
)
async def run_translation(req: TranslationRequest):
    if len(req.source_text) > 6000:
        raise HTTPException(status_code=422, detail="文本超过 5000 字符限制。")

    system_prompt = load_prompt("translation.txt")
    
    user_prompt = f"""
Direction: {req.direction}
Styles requested: {', '.join(req.style)}
User's explicit translation attempt: "{req.user_translation}"

Source Text:
{req.source_text}
    """

    data = await call_claude_json(system_prompt, user_prompt, max_tokens=4000)

    # Normalize legacy/variant model outputs into TranslationResponse schema.
    if isinstance(data, dict):
        if "variants" not in data:
            legacy_variants = []
            if data.get("literal_translation"):
                legacy_variants.append(
                    {"style": "literal", "label": "直译版", "text": data.get("literal_translation")}
                )
            if data.get("legal_translation"):
                legacy_variants.append(
                    {"style": "legal", "label": "法律表达版", "text": data.get("legal_translation")}
                )
            if data.get("plain_translation"):
                legacy_variants.append(
                    {"style": "plain", "label": "简明表达版", "text": data.get("plain_translation")}
                )
            data["variants"] = legacy_variants
        else:
            normalized_variants = []
            for v in data.get("variants") or []:
                if not isinstance(v, dict):
                    continue
                style = v.get("style") or ""
                label = v.get("label") or ""
                if style == "literal":
                    label = "直译版"
                elif style == "legal":
                    label = "法律表达版"
                elif style == "plain":
                    label = "简明表达版"
                normalized_variants.append(
                    {
                        "style": style or "plain",
                        "label": label or "简明表达版",
                        "text": v.get("text") or "",
                    }
                )
            if normalized_variants:
                data["variants"] = normalized_variants

        if "terms" not in data:
            data["terms"] = []
        if "notes" not in data:
            data["notes"] = []
        if "common_errors" not in data:
            data["common_errors"] = []
        if "confidence_hint" not in data:
            data["confidence_hint"] = "medium"

        critique = data.get("critique")
        if isinstance(critique, dict):
            if critique.get("score") is not None and not isinstance(critique.get("score"), str):
                critique["score"] = str(critique.get("score"))
            if "improvements" not in critique and isinstance(critique.get("errors"), list):
                improvements = []
                for e in critique["errors"]:
                    if not isinstance(e, dict):
                        continue
                    improvements.append(
                        {
                            "original": e.get("original", ""),
                            "suggested": e.get("suggested") or e.get("correction", ""),
                            "reason": e.get("reason", ""),
                        }
                    )
                critique["improvements"] = improvements
            if "improvements" not in critique:
                critique["improvements"] = []

    try:
        response = TranslationResponse(**data)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM 返回数据格式错误：{e}。原始数据：{data}")
