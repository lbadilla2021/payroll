CREATE TABLE IF NOT EXISTS tenants (
    id SERIAL PRIMARY KEY,
    name VARCHAR(120) NOT NULL UNIQUE,
    code VARCHAR(64) NOT NULL UNIQUE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER REFERENCES tenants(id) ON DELETE CASCADE,
    email_normalized VARCHAR(255) NOT NULL,
    full_name VARCHAR(150) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_superadmin BOOLEAN NOT NULL DEFAULT FALSE,
    is_tenant_admin BOOLEAN NOT NULL DEFAULT FALSE,
    auth_version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE users ADD COLUMN IF NOT EXISTS tenant_id INTEGER REFERENCES tenants(id) ON DELETE CASCADE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS email_normalized VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_superadmin BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_tenant_admin BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS auth_version INTEGER NOT NULL DEFAULT 1;
ALTER TABLE users ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW();

UPDATE users SET email_normalized = LOWER(email) WHERE email_normalized IS NULL AND EXISTS (
    SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='email'
);

ALTER TABLE users DROP CONSTRAINT IF EXISTS users_email_key;
DROP INDEX IF EXISTS uq_users_email;
CREATE UNIQUE INDEX IF NOT EXISTS uq_users_tenant_email_normalized ON users(tenant_id, email_normalized);
CREATE UNIQUE INDEX IF NOT EXISTS uq_users_global_email_normalized ON users(email_normalized) WHERE tenant_id IS NULL;
CREATE INDEX IF NOT EXISTS ix_users_email_normalized ON users(email_normalized);
CREATE INDEX IF NOT EXISTS ix_users_tenant_id ON users(tenant_id);

CREATE TABLE IF NOT EXISTS user_sessions (
    id VARCHAR(64) PRIMARY KEY,
    tenant_id INTEGER REFERENCES tenants(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    refresh_token_hash VARCHAR(128) NOT NULL,
    user_agent VARCHAR(512),
    ip_address VARCHAR(64),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    idle_expires_at TIMESTAMPTZ NOT NULL,
    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    revoked_at TIMESTAMPTZ,
    revoke_reason VARCHAR(128),
    rotated_from_session_id VARCHAR(64)
);
CREATE INDEX IF NOT EXISTS ix_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS ix_user_sessions_tenant_id ON user_sessions(tenant_id);
CREATE INDEX IF NOT EXISTS ix_user_sessions_refresh_hash ON user_sessions(refresh_token_hash);
CREATE INDEX IF NOT EXISTS ix_user_sessions_revoked_at ON user_sessions(revoked_at);
CREATE INDEX IF NOT EXISTS ix_user_sessions_expires_at ON user_sessions(expires_at);

CREATE TABLE IF NOT EXISTS password_reset_tokens (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER REFERENCES tenants(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(128) NOT NULL UNIQUE,
    expires_at TIMESTAMPTZ NOT NULL,
    used_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    requested_ip VARCHAR(64),
    requested_user_agent VARCHAR(512)
);
CREATE INDEX IF NOT EXISTS ix_password_reset_tokens_user_id ON password_reset_tokens(user_id);
CREATE INDEX IF NOT EXISTS ix_password_reset_tokens_tenant_id ON password_reset_tokens(tenant_id);
CREATE INDEX IF NOT EXISTS ix_password_reset_tokens_expires_at ON password_reset_tokens(expires_at);

CREATE TABLE IF NOT EXISTS auth_audit_logs (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER REFERENCES tenants(id) ON DELETE SET NULL,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    email_input VARCHAR(255),
    event_type VARCHAR(64) NOT NULL,
    outcome VARCHAR(32) NOT NULL,
    reason VARCHAR(255),
    ip_address VARCHAR(64),
    user_agent VARCHAR(512),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_auth_audit_logs_tenant_id ON auth_audit_logs(tenant_id);
CREATE INDEX IF NOT EXISTS ix_auth_audit_logs_user_id ON auth_audit_logs(user_id);
CREATE INDEX IF NOT EXISTS ix_auth_audit_logs_event_type ON auth_audit_logs(event_type);
CREATE INDEX IF NOT EXISTS ix_auth_audit_logs_created_at ON auth_audit_logs(created_at);


CREATE TABLE IF NOT EXISTS auth_rate_limit_buckets (
    key VARCHAR(255) PRIMARY KEY,
    count INTEGER NOT NULL DEFAULT 0,
    window_started_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_auth_rate_limit_updated_at ON auth_rate_limit_buckets(updated_at);
