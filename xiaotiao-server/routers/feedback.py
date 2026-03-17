"""
Feedback router — stores user feedback submissions from the frontend.
PRD §15: Data tracking event `feedback_submit`.
"""
import logging
from datetime import datetime

from fastapi import APIRouter, Request
from pydantic import BaseModel

logger = logging.getLogger("xiaotiao.feedback")

router = APIRouter(prefix="/feedback", tags=["反馈"])


class FeedbackRequest(BaseModel):
    module: str
    selection: str
    timestamp: str = ""


@router.post(
    "",
    summary="提交反馈",
    description="记录用户对模块结果的反馈（有帮助/需改进）。",
)
async def submit_feedback(body: FeedbackRequest, request: Request):
    user = getattr(request.state, "user", None)
    username = user["username"] if user else "anonymous"
    logger.info(
        "[feedback] user=%s module=%s selection=%s ts=%s",
        username,
        body.module,
        body.selection,
        body.timestamp or datetime.utcnow().isoformat(),
    )
    return {"ok": True}
