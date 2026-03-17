from datetime import datetime, timezone

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, UserSession
from app.security import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/api/auth/login')


def get_current_user(
    request: Request,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_error = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Sesión inválida')
    try:
        payload = decode_token(token)
        email = payload.get('sub')
        session_id = payload.get('sid')
        token_ver = int(payload.get('ver', -1))
        if not email or not session_id:
            raise credentials_error
    except Exception as exc:
        raise credentials_error from exc

    user = db.query(User).filter(User.email == email, User.is_active.is_(True)).first()
    if not user or user.auth_version != token_ver:
        raise credentials_error

    session = (
        db.query(UserSession)
        .filter(UserSession.session_id == session_id, UserSession.user_id == user.id, UserSession.revoked_at.is_(None))
        .first()
    )
    now = datetime.now(timezone.utc)
    if not session or session.expires_at.replace(tzinfo=timezone.utc) < now or session.absolute_expires_at.replace(tzinfo=timezone.utc) < now:
        raise credentials_error

    request.state.session_id = session.session_id
    return user


def require_superadmin(user: User = Depends(get_current_user)) -> User:
    if user.role != 'superadmin':
        raise HTTPException(status_code=403, detail='Superadmin access required')
    return user
