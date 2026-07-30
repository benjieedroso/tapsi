"""Development-only email helpers.

The standard console backend prints MIME quoted-printable output. Long URLs are
soft-wrapped with a trailing ``=`` marker, which makes a copied reset URL look
invalid. This backend preserves the normal message output and also prints each
URL from the original message body on one unwrapped line.
"""

import re

from django.core.mail.backends.console import EmailBackend as ConsoleEmailBackend


class DevelopmentConsoleEmailBackend(ConsoleEmailBackend):
    def send_messages(self, email_messages):
        sent = super().send_messages(email_messages)
        for message in email_messages:
            for url in re.findall(r"https?://[^\s]+", message.body):
                self.stream.write(f"\nOpen this link in your browser:\n{url}\n")
        return sent
