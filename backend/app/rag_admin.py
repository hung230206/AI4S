"""Server-only account provisioning. No public registration can request admin rights."""
import argparse
import json
from pathlib import Path
import secrets
from pydantic import TypeAdapter, EmailStr
from sqlalchemy import select, text
from .accounts import hasher
from .config import settings, ROOT
from .db import SessionLocal
from .models import User
from .security import ApiError
from .services import audit


def provision(db, email, password):
    email = str(TypeAdapter(EmailStr).validate_python(email)).lower()
    if len(password) < 16: raise ValueError("Administrator passwords require at least 16 characters")
    db.execute(text("SELECT pg_advisory_xact_lock(hashtext('rag-admin-provision'))"))
    user = db.scalar(select(User).where(User.email == email))
    if user:
        if not user.is_rag_admin: raise ApiError("ADMIN_ACCOUNT_EXISTS", "Email is already a regular account; server operator review required", 409)
        return user  # Never reset credentials or re-promote on every deployment.
    user = User(email=email, password_hash=hasher.hash(password), display_name="RAG Test Admin", role="STUDENT", is_demo=False, is_rag_admin=True)
    db.add(user); db.flush()
    audit(db, "SYSTEM", "RAG_ADMIN_PROVISIONED", user_id=str(user.id))
    return user


def provision_configured(db):
    if settings.rag_admin_email and settings.rag_admin_password.get_secret_value():
        provision(db, settings.rag_admin_email, settings.rag_admin_password.get_secret_value())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--email", default="admin.rag@example.com")
    parser.add_argument("--credentials-file", type=Path, default=ROOT / ".local/rag-admin-test.json")
    args = parser.parse_args()
    target = args.credentials_file.resolve()
    if not target.is_relative_to((ROOT / ".local").resolve()): raise SystemExit("Credentials must stay in the ignored .local directory")
    if target.exists(): raise SystemExit("Credential file already exists; no account/password was changed")
    password = secrets.token_urlsafe(24)
    with SessionLocal.begin() as db: provision(db, args.email, password)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps({"email": args.email, "password": password, "login_path": "/admin/rag", "notice": "Private test credentials. Never commit or publish this file."}, indent=2) + "\n", encoding="utf-8")
    print("Administrator created; private credentials saved to " + str(target))


if __name__ == "__main__": main()
