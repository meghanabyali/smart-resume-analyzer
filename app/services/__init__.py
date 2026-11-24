"""Business logic for the Smart Resume Analyzer (independent of Flask routes)."""


class ResumeProcessingError(Exception):
    """An error whose message is safe to show to the end user."""

    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
