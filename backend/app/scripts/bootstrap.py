#!/usr/bin/env python3
"""
Bootstrap script: creates the initial superadmin account.
Run ONCE after first migration:
  python -m app.scripts.bootstrap
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.core.config import settings
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.models import User


def bootstrap():
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.role == "superadmin").first()
        if existing:
            print(f"[bootstrap] Superadmin already exists: {existing.email}")
            return

        user = User(
            email=settings.FIRST_SUPERADMIN_EMAIL,
            first_name="Platform",
            last_name="Admin",
            password_hash=hash_password(settings.FIRST_SUPERADMIN_PASSWORD),
            role="superadmin",
            is_active=True,
            email_verified=True,
            force_password_change=True,  # force change on first login
        )
        db.add(user)
        db.commit()
        print(f"[bootstrap] Superadmin created: {settings.FIRST_SUPERADMIN_EMAIL}")
        print(f"[bootstrap] IMPORTANT: Change the default password immediately after first login.")
    finally:
        db.close()


if __name__ == "__main__":
    bootstrap()
