from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.main import app
from app.models import PasswordResetToken, Tenant, User
from app.security import generate_reset_token, hash_opaque_token, hash_password

engine = create_engine('sqlite:///./test_auth.db', connect_args={'check_same_thread': False})
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

    from app.database import get_db

    app.dependency_overrides = {get_db: override_get_db}

    db = TestingSessionLocal()
    t1 = Tenant(name='Tenant A', code='ta', is_active=True)
    t2 = Tenant(name='Tenant B', code='tb', is_active=True)
    db.add_all([t1, t2])
    db.flush()
    db.add_all(
        [
            User(tenant_id=t1.id, email_normalized='admin@a.com', full_name='Admin A', password_hash=hash_password('StrongPass1234'), is_tenant_admin=True, is_active=True),
            User(tenant_id=t2.id, email_normalized='admin@b.com', full_name='Admin B', password_hash=hash_password('StrongPass1234'), is_tenant_admin=True, is_active=True),
        ]
    )
    db.commit()
    db.close()


def _login(client, tenant='ta', email='admin@a.com', password='StrongPass1234'):
    return client.post('/api/auth/login', json={'tenant_code': tenant, 'email': email, 'password': password})


def test_login_ok():
    c = TestClient(app)
    assert _login(c).status_code == 200


def test_login_tenant_incorrecto():
    c = TestClient(app)
    assert _login(c, tenant='tb').status_code == 401


def test_login_password_incorrecta():
    c = TestClient(app)
    assert _login(c, password='bad').status_code == 401


def test_forgot_password_uniforme(monkeypatch):
    monkeypatch.setattr('app.main.send_password_reset_email', lambda *args, **kwargs: None)
    c = TestClient(app)
    a = c.post('/api/auth/forgot-password', json={'tenant_code': 'ta', 'email': 'admin@a.com'})
    b = c.post('/api/auth/forgot-password', json={'tenant_code': 'ta', 'email': 'ghost@a.com'})
    assert a.status_code == 200 and b.status_code == 200
    assert a.json()['message'] == b.json()['message']


def test_reset_token_expirado_y_reutilizado():
    c = TestClient(app)
    db = TestingSessionLocal()
    user = db.query(User).filter(User.email_normalized == 'admin@a.com').first()
    raw = generate_reset_token()
    db.add(PasswordResetToken(tenant_id=user.tenant_id, user_id=user.id, token_hash=hash_opaque_token(raw), expires_at=datetime.now(timezone.utc) - timedelta(minutes=1)))
    db.commit(); db.close()
    assert c.post('/api/auth/reset-password', json={'token': raw, 'new_password': 'AnotherStrongPass123', 'new_password_confirm': 'AnotherStrongPass123'}).status_code == 400

    db = TestingSessionLocal()
    user = db.query(User).filter(User.email_normalized == 'admin@a.com').first()
    raw2 = generate_reset_token()
    db.add(PasswordResetToken(tenant_id=user.tenant_id, user_id=user.id, token_hash=hash_opaque_token(raw2), expires_at=datetime.now(timezone.utc) + timedelta(minutes=5)))
    db.commit(); db.close()
    assert c.post('/api/auth/reset-password', json={'token': raw2, 'new_password': 'AnotherStrongPass123', 'new_password_confirm': 'AnotherStrongPass123'}).status_code == 200
    assert c.post('/api/auth/reset-password', json={'token': raw2, 'new_password': 'AnotherStrongPass123', 'new_password_confirm': 'AnotherStrongPass123'}).status_code == 400


def test_reset_token_tenant_distinto():
    c = TestClient(app)
    db = TestingSessionLocal()
    user_a = db.query(User).filter(User.email_normalized == 'admin@a.com').first()
    raw = generate_reset_token()
    db.add(PasswordResetToken(tenant_id=999, user_id=user_a.id, token_hash=hash_opaque_token(raw), expires_at=datetime.now(timezone.utc) + timedelta(minutes=5)))
    db.commit(); db.close()
    assert c.post('/api/auth/reset-password', json={'token': raw, 'new_password': 'AnotherStrongPass123', 'new_password_confirm': 'AnotherStrongPass123'}).status_code == 400


def test_refresh_rotativo_logout_logout_all():
    c = TestClient(app)
    login = _login(c)
    old_cookie = c.cookies.get('refresh_token')
    assert c.post('/api/auth/refresh').status_code == 200
    assert old_cookie != c.cookies.get('refresh_token')
    token = c.post('/api/auth/refresh').json()['access_token']
    assert c.post('/api/auth/logout', headers={'Authorization': f'Bearer {token}'}).status_code == 200
    assert c.get('/api/auth/me', headers={'Authorization': f'Bearer {token}'}).status_code == 401

    login2 = _login(c)
    token2 = login2.json()['access_token']
    assert c.post('/api/auth/logout-all', headers={'Authorization': f'Bearer {token2}'}).status_code == 200


def test_invalidacion_tras_reset_y_auth_version(monkeypatch):
    monkeypatch.setattr('app.main.send_password_reset_email', lambda *args, **kwargs: None)
    c = TestClient(app)
    login = _login(c)
    old_token = login.json()['access_token']

    c.post('/api/auth/forgot-password', json={'tenant_code': 'ta', 'email': 'admin@a.com'})
    db = TestingSessionLocal()
    prt = db.query(PasswordResetToken).order_by(PasswordResetToken.id.desc()).first()
    raw = generate_reset_token()
    prt.token_hash = hash_opaque_token(raw)
    db.commit(); db.close()

    assert c.post('/api/auth/reset-password', json={'token': raw, 'new_password': 'BrandNewStrongPass123', 'new_password_confirm': 'BrandNewStrongPass123'}).status_code == 200
    assert c.get('/api/auth/me', headers={'Authorization': f'Bearer {old_token}'}).status_code == 401


def test_cambio_password_autenticado():
    c = TestClient(app)
    login = _login(c)
    token = login.json()['access_token']
    assert c.post('/api/auth/change-password', headers={'Authorization': f'Bearer {token}'}, json={'current_password': 'StrongPass1234', 'new_password': 'ChangedStrongPass123', 'new_password_confirm': 'ChangedStrongPass123'}).status_code == 200


def test_me_con_sesion_invalida():
    c = TestClient(app)
    assert c.get('/api/auth/me', headers={'Authorization': 'Bearer token-invalido'}).status_code == 401


def test_cors_happy_path():
    c = TestClient(app)
    r = c.options('/api/auth/login', headers={'Origin': 'http://localhost:8080', 'Access-Control-Request-Method': 'POST'})
    assert r.status_code in (200, 204)
    assert r.headers.get('access-control-allow-origin') == 'http://localhost:8080'


def test_rate_limiting_login(monkeypatch):
    monkeypatch.setattr('app.config.settings.login_max_attempts', 1)
    c = TestClient(app)
    assert _login(c, password='bad').status_code == 401
    assert _login(c, password='bad').status_code == 429


def test_rate_limiting_forgot(monkeypatch):
    monkeypatch.setattr('app.config.settings.password_reset_requests_per_hour', 1)
    c = TestClient(app)
    assert c.post('/api/auth/forgot-password', json={'tenant_code': 'ta', 'email': 'admin@a.com'}).status_code == 200
    assert c.post('/api/auth/forgot-password', json={'tenant_code': 'ta', 'email': 'admin@a.com'}).status_code == 429
