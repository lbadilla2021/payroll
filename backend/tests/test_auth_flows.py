from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.main import app, rate_windows
from app.models import PasswordResetToken, Tenant, User, UserSession
from app.security import hash_password


SQLALCHEMY_DATABASE_URL = 'sqlite:///./test_auth.db'
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={'check_same_thread': False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def setup_function():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    rate_windows.clear()
    app.dependency_overrides = {}
    from app.database import get_db

    app.dependency_overrides[get_db] = override_get_db

    db = TestingSessionLocal()
    t1 = Tenant(name='Tenant A', code='ta', is_active=True)
    t2 = Tenant(name='Tenant B', code='tb', is_active=True)
    db.add_all([t1, t2])
    db.flush()
    db.add_all(
        [
            User(email='admin@a.com', full_name='Admin A', password_hash=hash_password('StrongPass1234'), role='tenant_admin', tenant_id=t1.id, is_active=True),
            User(email='admin@b.com', full_name='Admin B', password_hash=hash_password('StrongPass1234'), role='tenant_admin', tenant_id=t2.id, is_active=True),
            User(email='superadmin@payroll.local', full_name='Super', password_hash=hash_password('StrongPass1234'), role='superadmin', tenant_id=None, is_active=True),
        ]
    )
    db.commit()
    db.close()


def test_login_and_tenant_isolation():
    c = TestClient(app)
    ok = c.post('/api/auth/login', json={'tenant_code': 'ta', 'email': 'admin@a.com', 'password': 'StrongPass1234'})
    assert ok.status_code == 200

    bad = c.post('/api/auth/login', json={'tenant_code': 'tb', 'email': 'admin@a.com', 'password': 'StrongPass1234'})
    assert bad.status_code == 401


def test_rate_limiting_login():
    c = TestClient(app)
    for _ in range(5):
        r = c.post('/api/auth/login', json={'tenant_code': 'ta', 'email': 'admin@a.com', 'password': 'bad'})
        assert r.status_code == 401
    blocked = c.post('/api/auth/login', json={'tenant_code': 'ta', 'email': 'admin@a.com', 'password': 'bad'})
    assert blocked.status_code == 429


def test_forgot_password_uniform_response():
    c = TestClient(app)
    a = c.post('/api/auth/forgot-password', json={'tenant_code': 'ta', 'email': 'admin@a.com'})
    b = c.post('/api/auth/forgot-password', json={'tenant_code': 'ta', 'email': 'ghost@a.com'})
    assert a.status_code == 200 and b.status_code == 200
    assert a.json()['message'] == b.json()['message']


def test_reset_password_single_use_and_session_invalidation():
    c = TestClient(app)
    login = c.post('/api/auth/login', json={'tenant_code': 'ta', 'email': 'admin@a.com', 'password': 'StrongPass1234'})
    assert login.status_code == 200

    db = TestingSessionLocal()
    user = db.query(User).filter(User.email == 'admin@a.com').first()
    from app.security import generate_reset_token, hash_opaque_token

    raw = generate_reset_token()
    db.add(PasswordResetToken(tenant_id=user.tenant_id, user_id=user.id, email=user.email, token_hash=hash_opaque_token(raw), expires_at=datetime.now(timezone.utc) + timedelta(minutes=10)))
    db.commit()
    db.close()

    reset = c.post('/api/auth/reset-password', json={'token': raw, 'new_password': 'AnotherStrongPass1234', 'new_password_confirm': 'AnotherStrongPass1234'})
    assert reset.status_code == 200

    reuse = c.post('/api/auth/reset-password', json={'token': raw, 'new_password': 'x'*13, 'new_password_confirm': 'x'*13})
    assert reuse.status_code == 400


def test_refresh_rotation():
    c = TestClient(app)
    login = c.post('/api/auth/login', json={'tenant_code': 'ta', 'email': 'admin@a.com', 'password': 'StrongPass1234'})
    assert login.status_code == 200
    old_cookie = c.cookies.get('refresh_token')
    refreshed = c.post('/api/auth/refresh')
    assert refreshed.status_code == 200
    new_cookie = c.cookies.get('refresh_token')
    assert old_cookie != new_cookie


def test_change_password():
    c = TestClient(app)
    login = c.post('/api/auth/login', json={'tenant_code': 'ta', 'email': 'admin@a.com', 'password': 'StrongPass1234'})
    token = login.json()['access_token']
    ch = c.post('/api/auth/change-password', headers={'Authorization': f'Bearer {token}'}, json={'current_password': 'StrongPass1234', 'new_password': 'ChangedPass12345', 'new_password_confirm': 'ChangedPass12345'})
    assert ch.status_code == 200

    relogin = c.post('/api/auth/login', json={'tenant_code': 'ta', 'email': 'admin@a.com', 'password': 'ChangedPass12345'})
    assert relogin.status_code == 200
