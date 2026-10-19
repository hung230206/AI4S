import hmac
import hashlib
from uuid import UUID
from fastapi import Depends, Request, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyCookie
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from sqlalchemy import select
from .config import settings
from .db import get_db
from .models import User, AuthSession, now


class ApiError(Exception):
    def __init__(self, code, message, status=409):
        self.code, self.message, self.status = code, message, status


signer = URLSafeTimedSerializer(settings.app_session_secret, salt="demo-session-v1")
bearer = HTTPBearer(auto_error=False)
cookie_auth = APIKeyCookie(name="baoan_session", auto_error=False)


def check_origin(request):
    allowed = (None, *settings.frontend_origins, str(request.base_url).rstrip("/"))
    if request.headers.get("origin") not in allowed or request.headers.get("sec-fetch-site") == "cross-site":
        raise ApiError("FORBIDDEN", "Origin is not allowed", 403)


def current_user(request: Request, credentials: HTTPAuthorizationCredentials | None = Depends(bearer), session_cookie: str | None = Depends(cookie_auth), csrf_token: str | None = Header(default=None, alias="X-CSRF-Token"), db=Depends(get_db, scope="function")):
    try:
        if credentials is not None:
            if not settings.demo_mode:
                raise ApiError("FORBIDDEN", "Demo sessions are disabled", 403)
            claims = signer.loads(credentials.credentials, max_age=3600)
            user = db.get(User, UUID(claims["sub"]))
            if not user or user.role != claims["role"] or user.email:
                raise ValueError()
            request.state.auth_mode = "demo"
            request.state.privacy_subject = hashlib.sha256(credentials.credentials.encode()).hexdigest() if claims.get("jti") else None
            return user
        token = session_cookie or ""
        session = db.scalar(select(AuthSession).where(AuthSession.token_hash == hashlib.sha256(token.encode()).hexdigest(), AuthSession.revoked == False, AuthSession.expires_at > now()))
        if not token or not session:
            raise ValueError()
        user = db.get(User, session.user_id)
        if not user or not user.email:
            raise ValueError()
        if request.method not in ("GET", "HEAD", "OPTIONS"):
            check_origin(request)
            csrf = csrf_token or ""
            if not hmac.compare_digest(csrf.encode(), session.csrf_token.encode()):
                raise ApiError("CSRF_INVALID", "Reload the page and retry", 403)
        request.state.account_session = session
        request.state.privacy_subject = session.token_hash
        request.state.auth_mode = "account"
        return user
    except (BadSignature, SignatureExpired, ValueError, KeyError, TypeError):
        raise ApiError("UNAUTHORIZED", "Sign in to continue", 401)


def student(user=Depends(current_user)):
    if user.role != "STUDENT":
        raise ApiError("FORBIDDEN", "Student session required", 403)
    return user


def operator(user=Depends(current_user)):
    if not settings.demo_mode or user.role != "OPERATOR":
        raise ApiError("FORBIDDEN", "Demo operator session required", 403)
    return user


def rag_admin(request: Request, user=Depends(current_user)):
    if not user.is_rag_admin or user.is_demo or not getattr(request.state, "account_session", None):
        raise ApiError("FORBIDDEN", "Chỉ tài khoản quản trị kho RAG được thao tác.", 403)
    return user


def lock_user(db, user):
    db.execute(select(User).where(User.id == user.id).with_for_update()).scalar_one()
