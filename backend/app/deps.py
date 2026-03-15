from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.security import decode_token


oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/api/auth/login')


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Could not validate credentials',
    )

    try:
        payload = decode_token(token)
        email = payload.get('sub')
        if not email:
            raise credentials_error
    except ValueError as exc:
        raise credentials_error from exc

    user = db.query(User).filter(User.email == email, User.is_active.is_(True)).first()
    if not user:
        raise credentials_error
    return user


def require_superadmin(user: User = Depends(get_current_user)) -> User:
    if user.role != 'superadmin':
        raise HTTPException(status_code=403, detail='Superadmin access required')
    return user
