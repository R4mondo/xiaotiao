import os
import base64
from io import BytesIO
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
import docx
import openpyxl

from schemas_multimodal import MultimodalExtractResponse
from services.llm import call_claude_json, call_claude_vision_json

router = APIRouter(prefix="/multimodal", tags=["multimodal"])

def load_prompt(filename: str) -> str:
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompts", filename)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

@router.post("/extract", response_model=MultimodalExtractResponse)
async def extract_vocabulary(
    file: UploadFile = File(...),
    domain: str = Form("general")
):
    system_prompt = load_prompt("multimodal.txt")
    user_prompt = f"Domain focus: {domain}\n\nPlease analyze the provided content."

    # Read file content safely
    contents = await file.read()
    filename = file.filename.lower()
    
    # Text-based approaches
    extracted_text = ""
    
    if filename.endswith(".txt") or filename.endswith(".md"):
        extracted_text = contents.decode("utf-8")
        
    elif filename.endswith(".docx"):
        try:
            doc = docx.Document(BytesIO(contents))
            extracted_text = "\n".join([para.text for para in doc.paragraphs if para.text.strip() != ""])
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to parse Word document: {str(e)}")
            
    elif filename.endswith(".xlsx"):
        try:
            wb = openpyxl.load_workbook(BytesIO(contents), data_only=True)
            sheet = wb.active
            rows = []
            for row in sheet.iter_rows(values_only=True):
                non_empty = [str(cell) for cell in row if cell is not None]
                if non_empty:
                    rows.append(" | ".join(non_empty))
            extracted_text = "\n".join(rows)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to parse Excel document: {str(e)}")
            
    # Vision approach
    elif filename.endswith((".jpg", ".jpeg", ".png")):
        base64_image = base64.b64encode(contents).decode("utf-8")
        media_type = "image/jpeg" if filename.endswith(("jpg", "jpeg")) else "image/png"
        
        try:
            data = await call_claude_vision_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                base64_image=base64_image,
                media_type=media_type,
                max_tokens=4000
            )
            return MultimodalExtractResponse(**data)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Vision extraction failed: {str(e)}")
            
    else:
        raise HTTPException(status_code=400, detail="Unsupported file format. Please upload .txt, .md, .docx, .xlsx, .jpg or .png")

    # If it's pure text, cap it around 4000 chars to avoid prompt blast
    if extracted_text:
        truncated_text = extracted_text[:4000]
        user_prompt += f"\n\nSource Content:\n{truncated_text}"
        
        try:
            data = await call_claude_json(system_prompt, user_prompt, max_tokens=4000)
            return MultimodalExtractResponse(**data)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Text extraction failed: {str(e)}")
    
    raise HTTPException(status_code=400, detail="Document appears to be empty.")
