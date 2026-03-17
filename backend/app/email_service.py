import logging
import smtplib
from email.message import EmailMessage

from app.config import settings

logger = logging.getLogger(__name__)


def send_password_reset_email(to_email: str, tenant_name: str, reset_link: str, expiry_minutes: int) -> None:
    msg = EmailMessage()
    msg['Subject'] = 'Restablecimiento de contraseña - Payroll'
    msg['From'] = f"{settings.smtp_from_name} <{settings.smtp_from}>"
    msg['To'] = to_email

    text_body = (
        'Hola,\n\n'
        'Recibimos una solicitud para restablecer tu contraseña.\n'
        f'Tenant: {tenant_name}\n'
        f'Enlace de restablecimiento: {reset_link}\n\n'
        f'El enlace expira en {expiry_minutes} minutos y se puede usar solo una vez.\n'
        'Si no solicitaste este cambio, ignora este mensaje.\n'
    )
    html_body = f"""
    <html><body>
    <h2>Restablecimiento de contraseña</h2>
    <p>Recibimos una solicitud para restablecer tu contraseña.</p>
    <p><strong>Tenant:</strong> {tenant_name}</p>
    <p><a href=\"{reset_link}\">Restablecer contraseña</a></p>
    <p>Este enlace expira en {expiry_minutes} minutos y es de un solo uso.</p>
    <p>Si no solicitaste este cambio, ignora este correo.</p>
    </body></html>
    """
    msg.set_content(text_body)
    msg.add_alternative(html_body, subtype='html')

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
            if settings.smtp_use_tls:
                smtp.starttls()
            if settings.smtp_username:
                smtp.login(settings.smtp_username, settings.smtp_password)
            smtp.send_message(msg)
    except Exception:
        logger.exception('Error enviando correo de reset password a %s', to_email)
