import os
from fastapi import APIRouter, HTTPException
from schemas import TranslationRequest, TranslationResponse
from services.llm import call_claude_json

router = APIRouter(prefix="/translation", tags=["translation"])

def load_prompt(filename: str) -> str:
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompts", filename)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

@router.post("/run", response_model=TranslationResponse)
async def run_translation(req: TranslationRequest):
    if len(req.source_text) > 6000:
        raise HTTPException(status_code=422, detail="Text exceeds 5000 characters limit.")

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
                    {"style": "literal", "label": "直译版 Literal", "text": data.get("literal_translation")}
                )
            if data.get("legal_translation"):
                legacy_variants.append(
                    {"style": "legal", "label": "法律表达版 Legal", "text": data.get("legal_translation")}
                )
            if data.get("plain_translation"):
                legacy_variants.append(
                    {"style": "plain", "label": "简明表达版 Plain", "text": data.get("plain_translation")}
                )
            data["variants"] = legacy_variants

        if "terms" not in data:
            data["terms"] = []
        if "notes" not in data:
            data["notes"] = []
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

    try:
        response = TranslationResponse(**data)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM returned malformed data: {e}. Raw data: {data}")
