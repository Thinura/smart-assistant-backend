from uuid import uuid4

from app.services.email_providers.base import (
    EmailMessage,
    EmailProvider,
    EmailSendResult,
)


class ConsoleEmailProvider(EmailProvider):
    def send(self, message: EmailMessage) -> EmailSendResult:
        print("\n--- LOCAL EMAIL SEND ---")
        print(f"From: {message.from_name or ''} <{message.from_email}>")
        print(f"To: {message.to_email}")
        print(f"Subject: {message.subject}")
        print("")
        print(message.body)
        print("--- END LOCAL EMAIL SEND ---\n")

        return EmailSendResult(
            success=True,
            provider_message_id=f"console-{uuid4()}",
        )
