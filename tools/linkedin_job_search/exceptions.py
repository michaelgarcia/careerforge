"""Exception classes for the linkedin-job-search library."""


class LinkedInJobSearchError(Exception):
    """Base exception for the library."""


class LinkedInAPIError(LinkedInJobSearchError):
    """HTTP error from LinkedIn API."""

    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"HTTP {status_code}: {detail}")


class ParseError(LinkedInJobSearchError):
    """Failed to parse HTML/JSON response."""
