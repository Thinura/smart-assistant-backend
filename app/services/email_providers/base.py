from dataclasses import dataclass


@dataclass(frozen=True)
class EmailMessage:
    to_email: str
    subject: str
    body: str
    from_email: str
    from_name: str | None = None


@dataclass(frozen=True)
class EmailSendResult:
    success: bool
    provider_message_id: str | None = None
    error_message: str | None = None


class EmailProvider:
    def send(self, message: EmailMessage) -> EmailSendResult:
        raise NotImplementedError
