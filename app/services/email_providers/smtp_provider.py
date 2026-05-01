import smtplib
from email.message import EmailMessage as PythonEmailMessage
from email.utils import formataddr
from uuid import uuid4

from app.core.config import get_settings
from app.services.email_providers.base import (
    EmailMessage,
    EmailProvider,
    EmailSendResult,
)


class SmtpEmailProvider(EmailProvider):
    def send(self, message: EmailMessage) -> EmailSendResult:
        settings = get_settings()

        if not settings.smtp_host:
            return EmailSendResult(
                success=False,
                error_message="SMTP_HOST is required when EMAIL_PROVIDER=smtp",
            )

        if not settings.smtp_username:
            return EmailSendResult(
                success=False,
                error_message="SMTP_USERNAME is required when EMAIL_PROVIDER=smtp",
            )

        if not settings.smtp_password:
            return EmailSendResult(
                success=False,
                error_message="SMTP_PASSWORD is required when EMAIL_PROVIDER=smtp",
            )

        email = PythonEmailMessage()
        email["From"] = formataddr((message.from_name or "", message.from_email))
        email["To"] = message.to_email
        email["Subject"] = message.subject
        email.set_content(message.body)

        try:
            with smtplib.SMTP(
                host=settings.smtp_host,
                port=settings.smtp_port,
                timeout=settings.smtp_timeout_seconds,
            ) as smtp:
                if settings.smtp_use_tls:
                    smtp.starttls()

                smtp.login(settings.smtp_username, settings.smtp_password)
                smtp.send_message(email)

            return EmailSendResult(
                success=True,
                provider_message_id=f"smtp-{uuid4()}",
            )

        except Exception as exc:
            return EmailSendResult(
                success=False,
                error_message=str(exc),
            )
