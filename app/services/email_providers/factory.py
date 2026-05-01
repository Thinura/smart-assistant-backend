from app.core.config import get_settings
from app.services.email_providers.base import EmailProvider
from app.services.email_providers.console_provider import ConsoleEmailProvider
from app.services.email_providers.smtp_provider import SmtpEmailProvider


class EmailProviderFactory:
    @staticmethod
    def create() -> EmailProvider:
        settings = get_settings()
        provider = settings.email_provider.strip().lower()

        if provider == "console":
            return ConsoleEmailProvider()

        if provider == "smtp":
            return SmtpEmailProvider()

        raise ValueError(f"Unsupported EMAIL_PROVIDER: {settings.email_provider}")
