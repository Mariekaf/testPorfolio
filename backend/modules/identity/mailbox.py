"""Private development mailbox; never writes reset links to stdout."""
import os
from django.core.mail.backends.filebased import EmailBackend

class PrivateMailboxBackend(EmailBackend):
    def open(self):
        os.makedirs(self.file_path, mode=0o700, exist_ok=True)
        if os.name != "nt":
            os.chmod(self.file_path, 0o700)
        opened = super().open()
        if self.stream and os.name != "nt":
            os.fchmod(self.stream.fileno(), 0o600)
        return opened
