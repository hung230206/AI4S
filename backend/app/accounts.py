import hashlib
import secrets
from datetime import timedelta
from fastapi import APIRouter, Depends, Request, Response
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError
from pydantic import EmailStr, Field, field_validator
from sqlalchemy import select, text, update
from .config import settings
from .db import get_db
from .models import User, AuthSession, AuthThrottle, now
from .schemas import Strict
from .security import ApiError, current_user, check_origin
from .services import iso

router = APIRouter(prefix="/api/v1/auth", tags=["Accounts"])
hasher = PasswordHasher()
DUMMY_HASH = hasher.hash(secrets.token_urlsafe(24))


class Register(Strict):
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)
    display_name: str = Field(min_length=2, max_length=100)

    @field_validator("display_name")
    @classmethod
    def name(cls, value):
        value = value.strip()
        if len(value) < 2:
            raise ValueError("Display name is too short")
        return value


class Login(Strict):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class Profile(Strict):
    display_name: str = Field(min_length=2, max_length=100)


class PasswordChange(Strict):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=10, max_length=128)


def public_user(user):
    return {"id": str(user.id), "email": user.email, "display_name": user.display_name, "role": user.role, "is_demo": user.is_demo, "is_rag_admin": user.is_rag_admin, "created_at": iso(user.created_at)}


def throttle(db, request, subject, action, limit=10):
    ip = request.client.host if request.client else "local"
    key = hashlib.sha256(f"{action}:{ip}:{subject}".encode()).hexdigest()
    db.execute(text("SELECT pg_advisory_xact_lock(hashtext(:key))"), {"key": key})
    bucket = db.get(AuthThrottle, key)
    if not bucket:
        bucket = AuthThrottle(bucket=key, attempts=0, window_start=now())
        db.add(bucket)
    if bucket.window_start < now() - timedelta(minutes=15):
        bucket.attempts, bucket.window_start = 0, now()
    if bucket.attempts >= limit:
        raise ApiError("RATE_LIMITED", "Too many attempts; retry in 15 minutes", 429)
    bucket.attempts += 1
    db.flush()


def issue(db, user, response):
    token = secrets.token_urlsafe(48)
    session = AuthSession(user_id=user.id, token_hash=hashlib.sha256(token.encode()).hexdigest(), csrf_token=secrets.token_urlsafe(32), expires_at=now() + timedelta(hours=settings.session_hours))
    db.add(session)
    # Limit active sessions without keeping every old credential valid indefinitely.
    active = list(db.scalars(select(AuthSession).where(AuthSession.user_id == user.id, AuthSession.revoked == False).order_by(AuthSession.created_at.desc())))
    for old in active[4:]:
        old.revoked = True
    response.set_cookie("baoan_session", token, max_age=settings.session_hours * 3600, httponly=True, secure=settings.cookie_secure, samesite="lax", path="/api/v1")
    return {"user": public_user(user), "csrf_token": session.csrf_token, "expires_at": iso(session.expires_at)}


@router.post("/register")
def register(body: Register, request: Request, response: Response, db=Depends(get_db, scope="function")):
    check_origin(request)
    throttle(db, request, "registration", "register", limit=20)
    email = str(body.email).lower()
    if db.scalar(select(User.id).where(User.email == email)):
        db.commit()
        raise ApiError("EMAIL_EXISTS", "Email is already registered", 409)
    user = User(email=email, password_hash=hasher.hash(body.password), display_name=body.display_name, role="STUDENT", is_demo=False)
    db.add(user)
    db.flush()
    return issue(db, user, response)


@router.post("/login")
def login(body: Login, request: Request, response: Response, db=Depends(get_db, scope="function")):
    check_origin(request)
    email = str(body.email).lower()
    throttle(db, request, email, "login")
    throttle(db, request, "all-accounts", "login-ip")
    user = db.scalar(select(User).where(User.email == email))
    try:
        hasher.verify(user.password_hash if user and user.password_hash else DUMMY_HASH, body.password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        db.commit()  # Persist unsuccessful attempt counts without logging credentials.
        raise ApiError("INVALID_CREDENTIALS", "Email or password is incorrect", 401)
    if not user:
        db.commit()
        raise ApiError("INVALID_CREDENTIALS", "Email or password is incorrect", 401)
    if hasher.check_needs_rehash(user.password_hash):
        user.password_hash = hasher.hash(body.password)
    return issue(db, user, response)


@router.get("/session")
def session_info(request: Request, user=Depends(current_user)):
    session = getattr(request.state, "account_session", None)
    return {"user": public_user(user), "csrf_token": session.csrf_token if session else None, "expires_at": iso(session.expires_at) if session else None}


@router.post("/logout")
def logout(request: Request, response: Response, user=Depends(current_user), db=Depends(get_db, scope="function")):
    session = getattr(request.state, "account_session", None)
    if session:
        session.revoked = True
    from .privacy import permission, NOTICE_VERSION
    from .services import audit
    row = permission(db, request, user)
    if row and row.active:
        row.active = False; row.scopes = []; row.revision += 1; row.updated_at = now()
        audit(db, user, "AI_PERMISSION_REVOKED", notice_version=NOTICE_VERSION, revision=row.revision, scopes=[], reason="logout")
    response.delete_cookie("baoan_session", path="/api/v1")
    return {"signed_out": True}


@router.post("/profile")
def profile(body: Profile, user=Depends(current_user)):
    if not body.display_name.strip():
        raise ApiError("VALIDATION_ERROR", "Name is required", 422)
    user.display_name = body.display_name.strip()
    return {"user": public_user(user)}


@router.post("/logout-all")
def logout_all(request: Request, response: Response, user=Depends(current_user), db=Depends(get_db, scope="function")):
    if not getattr(request.state, "account_session", None):
        raise ApiError("FORBIDDEN", "Tài khoản sandbox không có phiên đăng nhập cá nhân.", 403)
    db.execute(update(AuthSession).where(AuthSession.user_id == user.id).values(revoked=True))
    response.delete_cookie("baoan_session", path="/api/v1")
    return {"signed_out_all": True}


@router.post("/password")
def password(body: PasswordChange, request: Request, response: Response, user=Depends(current_user), db=Depends(get_db, scope="function")):
    if not user.password_hash:
        raise ApiError("FORBIDDEN", "Demo account has no password", 403)
    throttle(db, request, str(user.id), "password")
    try:
        hasher.verify(user.password_hash, body.current_password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        db.commit()
        raise ApiError("INVALID_CREDENTIALS", "Current password is incorrect", 401)
    user.password_hash = hasher.hash(body.new_password)
    db.execute(update(AuthSession).where(AuthSession.user_id == user.id).values(revoked=True))
    response.delete_cookie("baoan_session", path="/api/v1")
    return {"password_changed": True, "sign_in_required": True}
