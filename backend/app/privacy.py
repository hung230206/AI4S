"""Fail-closed permission gate for optional external AI. No prompt content in audit."""
from datetime import timedelta
from typing import Literal
from fastapi import APIRouter, Depends, Request
from pydantic import Field
from sqlalchemy import select
from .config import settings
from .db import get_db
from .models import AiPermission, now
from .schemas import Strict
from .security import ApiError, student, lock_user
from .services import audit, iso

router = APIRouter(prefix="/api/v1/privacy", tags=["Privacy permissions"])
NOTICE_VERSION = "assistant-privacy-2026-10-19-v3"
# Purpose presets are defined by the server, never arbitrary client permissions.
PRESETS = {"QUESTION_ONLY": [], "SAMPLE_ASSISTANT": ["history", "documents"],
           "ACCOUNT_ASSISTANT": ["history", "documents", "finance", "insurance"]}


class PermissionInput(Strict):
    revision: int = Field(ge=0)
    notice_version: str
    enabled: bool
    preset: Literal["QUESTION_ONLY", "SAMPLE_ASSISTANT", "ACCOUNT_ASSISTANT"] | None = None


def permission(db, request, user):
    return db.scalar(select(AiPermission).where(AiPermission.subject == request.state.privacy_subject, AiPermission.user_id == user.id))


def valid(row):
    return bool(row and row.active and row.notice_version == NOTICE_VERSION and row.expires_at > now() and row.data_mode == settings.gemini_data_mode)


def out(row):
    active = valid(row)
    return {"enabled": active, "revision": row.revision if row else 0, "notice_version": NOTICE_VERSION,
            "scopes": row.scopes if active else [], "data_mode": settings.gemini_data_mode,
            "granted_at": iso(row.granted_at) if row and row.granted_at else None,
            "expires_at": iso(row.expires_at) if row else None,
            "allowed_scopes": ["history", "documents", *(["finance", "insurance"] if settings.gemini_data_mode == "PAID_PRIVATE" else [])]}


@router.get("/ai-permission")
def get_permission(request: Request, user=Depends(student), db=Depends(get_db, scope="function")):
    return out(permission(db, request, user))


@router.post("/ai-permission")
def set_permission(body: PermissionInput, request: Request, user=Depends(student), db=Depends(get_db, scope="function")):
    if not request.state.privacy_subject:
        raise ApiError("AI_REAUTH_REQUIRED", "Phiên sandbox cũ chưa hỗ trợ quyền riêng tư. Tải lại trang để mở phiên mới.", 403)
    lock_user(db, user)
    row = permission(db, request, user)
    if body.revision != (row.revision if row else 0):
        raise ApiError("PRIVACY_CHANGED", "Quyền đã thay đổi ở tab khác. Tải lại cài đặt quyền riêng tư.", 409)
    if body.enabled:
        if body.notice_version != NOTICE_VERSION or body.preset is None:
            raise ApiError("AI_CONSENT_REQUIRED", "Hãy đọc điều khoản và chọn Đồng ý trước khi sử dụng trợ lý.", 403)
        if settings.gemini_data_mode == "DEMO_ONLY" and body.preset == "ACCOUNT_ASSISTANT":
            raise ApiError("AI_SCOPE_UNAVAILABLE", "Trợ lý hiện không gửi dữ liệu tài chính hoặc hợp đồng cá nhân tới dịch vụ AI bên ngoài.", 403)
    if row is None:
        row = AiPermission(subject=request.state.privacy_subject, user_id=user.id, revision=0)
        db.add(row)
    row.revision += 1
    row.notice_version = NOTICE_VERSION
    row.active = body.enabled
    row.scopes = PRESETS[body.preset].copy() if body.enabled else []
    row.data_mode = settings.gemini_data_mode
    row.updated_at = now()
    row.granted_at = now() if body.enabled else None
    session = getattr(request.state, "account_session", None)
    row.expires_at = min(now() + timedelta(hours=1), session.expires_at) if session else now() + timedelta(hours=1)
    audit(db, user, "AI_PERMISSION_GRANTED" if body.enabled else "AI_PERMISSION_REVOKED",
          notice_version=NOTICE_VERSION, revision=row.revision, scopes=row.scopes, data_mode=row.data_mode)
    db.flush()
    return out(row)


def require_permission(db, request, user, revision):
    row = permission(db, request, user)
    if not valid(row) or revision != row.revision:
        raise ApiError("AI_CONSENT_REQUIRED", "Sự đồng ý sử dụng trợ lý chưa được cấp, đã hết hạn hoặc vừa thay đổi. Hãy mở lại trợ lý để đọc và đồng ý điều khoản.", 403)
    return row
