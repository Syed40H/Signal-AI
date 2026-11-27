"""Sends the digest email through Resend."""

import resend

from app.digest.build import DigestEmail


def send_digest(digest: DigestEmail, api_key: str, sender: str, recipient: str) -> str:
    """Sends the email and returns Resend's id for it. Raises if sending fails."""
    resend.api_key = api_key
    email = resend.Emails.send(
        {
            "from": sender,
            "to": [recipient],
            "subject": digest.subject,
            "html": digest.html,
            "text": digest.text,
        }
    )
    return email["id"]
