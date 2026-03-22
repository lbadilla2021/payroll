"""
Email service. Uses Python's smtplib with TLS.
All emails use a minimal HTML template — extend with Jinja2 when needed.
"""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


def _send(to_email: str, subject: str, html_body: str) -> bool:
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{settings.EMAIL_FROM_NAME} <{settings.EMAIL_FROM}>"
        msg["To"] = to_email
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            if settings.SMTP_TLS:
                server.starttls()
            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(str(settings.EMAIL_FROM), to_email, msg.as_string())
        return True
    except Exception as exc:
        logger.error(f"Email send failed to {to_email}: {exc}")
        return False


def _base_template(content: str) -> str:
    return f"""
    <!DOCTYPE html><html><body style="font-family:system-ui,sans-serif;background:#f5f5f5;margin:0;padding:32px;">
    <div style="max-width:520px;margin:0 auto;background:#fff;border-radius:12px;padding:40px;box-shadow:0 2px 8px rgba(0,0,0,.08);">
        <div style="margin-bottom:32px;">
            <span style="font-weight:800;font-size:20px;color:#111;">{settings.APP_NAME}</span>
        </div>
        {content}
        <div style="margin-top:40px;padding-top:24px;border-top:1px solid #eee;font-size:12px;color:#999;">
            Este mensaje fue enviado automáticamente. No responder a este correo.
        </div>
    </div>
    </body></html>
    """


def send_password_reset_email(to_email: str, reset_link: str, user_name: str) -> bool:
    content = f"""
    <h2 style="margin:0 0 16px;font-size:22px;color:#111;">Restablecer contraseña</h2>
    <p style="color:#444;line-height:1.6;">Hola {user_name},</p>
    <p style="color:#444;line-height:1.6;">
        Recibimos una solicitud para restablecer tu contraseña. Haz clic en el botón a continuación:
    </p>
    <div style="text-align:center;margin:32px 0;">
        <a href="{reset_link}"
           style="background:#2563eb;color:#fff;text-decoration:none;padding:14px 28px;border-radius:8px;font-weight:600;display:inline-block;">
            Restablecer contraseña
        </a>
    </div>
    <p style="color:#666;font-size:13px;">Este enlace expira en {settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS} horas.</p>
    <p style="color:#666;font-size:13px;">Si no solicitaste este cambio, ignora este correo.</p>
    <p style="color:#999;font-size:12px;word-break:break-all;">O copia este enlace: {reset_link}</p>
    """
    return _send(to_email, f"Restablecer tu contraseña — {settings.APP_NAME}", _base_template(content))


def send_welcome_email(to_email: str, user_name: str, temp_password: Optional[str] = None) -> bool:
    pwd_section = ""
    if temp_password:
        pwd_section = f"""
        <p style="color:#444;line-height:1.6;">Tu contraseña temporal es: <code style="background:#f3f4f6;padding:2px 8px;border-radius:4px;font-size:14px;">{temp_password}</code></p>
        <p style="color:#e55;font-size:13px;"><strong>Deberás cambiarla al iniciar sesión por primera vez.</strong></p>
        """
    content = f"""
    <h2 style="margin:0 0 16px;font-size:22px;color:#111;">Bienvenido/a a {settings.APP_NAME}</h2>
    <p style="color:#444;line-height:1.6;">Hola {user_name},</p>
    <p style="color:#444;line-height:1.6;">Tu cuenta ha sido creada exitosamente.</p>
    {pwd_section}
    <div style="text-align:center;margin:32px 0;">
        <a href="{settings.FRONTEND_URL}"
           style="background:#2563eb;color:#fff;text-decoration:none;padding:14px 28px;border-radius:8px;font-weight:600;display:inline-block;">
            Acceder a la plataforma
        </a>
    </div>
    """
    return _send(to_email, f"Bienvenido/a a {settings.APP_NAME}", _base_template(content))


def send_invitation_email(
    to_email: str,
    invited_by_name: str,
    tenant_name: str,
    accept_link: str,
    role: str,
    expires_hours: int = 72,
) -> bool:
    role_labels = {"superadmin": "Superadmin", "admin": "Administrador", "viewer": "Colaborador"}
    role_label = role_labels.get(role, role.capitalize())

    content = f"""
    <h2 style="margin:0 0 16px;font-size:22px;color:#111;">Te han invitado a unirte</h2>
    <p style="color:#444;line-height:1.6;">
        <strong>{invited_by_name}</strong> te ha invitado a unirte a
        <strong>{tenant_name}</strong> en {settings.APP_NAME}
        como <strong>{role_label}</strong>.
    </p>
    <div style="text-align:center;margin:32px 0;">
        <a href="{accept_link}"
           style="background:#0ea5e9;color:#fff;text-decoration:none;padding:14px 32px;
                  border-radius:8px;font-weight:600;font-size:16px;display:inline-block;">
            Aceptar invitación
        </a>
    </div>
    <p style="color:#666;font-size:13px;text-align:center;">
        Este enlace expira en {expires_hours} horas.
    </p>
    <p style="color:#999;font-size:12px;text-align:center;">
        Si no esperabas esta invitación, puedes ignorar este correo.
    </p>
    <p style="color:#ccc;font-size:11px;word-break:break-all;text-align:center;">
        {accept_link}
    </p>
    """
    return _send(
        to_email,
        f"Invitación para unirte a {tenant_name} — {settings.APP_NAME}",
        _base_template(content),
    )
