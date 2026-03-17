import smtplib
from email.message import EmailMessage

from app.config import settings


def send_password_reset_email(to_email: str, tenant_code: str | None, reset_link: str) -> None:
    msg = EmailMessage()
    msg['Subject'] = 'Restablecimiento de contraseña - Payroll'
    msg['From'] = f"{settings.smtp_from_name} <{settings.smtp_from}>"
    msg['To'] = to_email
    context = f'Tenant: {tenant_code}\n' if tenant_code else ''
    msg.set_content(
        'Hola,\n\n'
        'Recibimos una solicitud para restablecer tu contraseña. '
        'Si no fuiste tú, puedes ignorar este correo.\n\n'
        f'{context}'
        f'Enlace seguro: {reset_link}\n\n'
        f'Este enlace expira en {settings.password_reset_token_minutes} minutos y es de un solo uso.\n\n'
        'Equipo de Seguridad Payroll'
    )

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
        if settings.smtp_use_tls:
            smtp.starttls()
        if settings.smtp_username:
            smtp.login(settings.smtp_username, settings.smtp_password)
        smtp.send_message(msg)
