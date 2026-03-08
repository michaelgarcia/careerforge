"""Parse LinkedIn job alert emails into SearchResult records."""

from __future__ import annotations

import email
import email.policy
import logging
import re
from datetime import datetime, timezone

from linkedin_job_search.models import SearchResult

logger = logging.getLogger(__name__)

# Regex to extract job ID from LinkedIn job view URLs
_JOB_URL_RE = re.compile(r"https://www\.linkedin\.com/comm/jobs/view/(\d+)/")

# Separator between job cards in the text/plain body
_CARD_SEPARATOR = "---"


def parse_alert_email(raw_bytes: bytes) -> list[SearchResult]:
    """Parse a raw RFC-5322 email into a list of :class:`SearchResult`.

    Args:
        raw_bytes: The complete email message as bytes (e.g. from IMAP FETCH
                   or reading a ``.eml`` file).

    Returns:
        List of parsed job records. May be empty if the email contains no
        recognisable job cards.
    """
    msg = email.message_from_bytes(raw_bytes, policy=email.policy.default)
    text_body = _extract_text_body(msg)
    if not text_body:
        logger.warning("No text/plain body found in email: %s", msg.get("Subject", "(no subject)"))
        return []

    return _parse_text_body(text_body)


def parse_eml_file(path: str) -> list[SearchResult]:
    """Convenience wrapper: read a ``.eml`` file from disk and parse it.

    Args:
        path: Filesystem path to the ``.eml`` file.

    Returns:
        List of parsed :class:`SearchResult` records.
    """
    with open(path, "rb") as f:
        return parse_alert_email(f.read())


def _extract_text_body(msg: email.message.EmailMessage) -> str | None:
    """Return the text/plain body from a (possibly multipart) email."""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                return part.get_content()
        return None
    if msg.get_content_type() == "text/plain":
        return msg.get_content()
    return None


def _parse_text_body(text: str) -> list[SearchResult]:
    """Split the text/plain body into job cards and parse each one.

    LinkedIn alert emails use a consistent text layout::

        Your job alert for <search> in <location>

        New jobs match your preferences.

        <Title>
        <Company>
        <Location>
        [optional badge lines: "This company is actively hiring", etc.]
        View job: <url>

        ---------------------------------------------------------

        ... next card ...

        See all jobs on LinkedIn: <url>

    We split on the ``---`` separator lines, then extract fields from each
    block.
    """
    results: list[SearchResult] = []
    now = datetime.now(timezone.utc)

    # Split into blocks on separator lines (any line that is mostly dashes)
    blocks = re.split(r"\r?\n-{3,}\r?\n", text)

    for block in blocks:
        result = _parse_card_block(block.strip(), now)
        if result is not None:
            results.append(result)

    return results


def _parse_card_block(block: str, collected_at: datetime) -> SearchResult | None:
    """Try to parse a single job card block into a SearchResult.

    Returns None if the block doesn't contain a valid job URL.
    """
    # Find the job URL — this is the anchor for a valid card
    url_match = _JOB_URL_RE.search(block)
    if url_match is None:
        return None

    job_id = url_match.group(1)

    # Build a clean job URL (strip tracking params)
    job_url = f"https://www.linkedin.com/jobs/view/{job_id}/"

    # Extract the "View job:" line and everything above it
    lines = block.splitlines()

    # Find the line index that starts with "View job:"
    view_idx: int | None = None
    for i, line in enumerate(lines):
        if line.strip().startswith("View job:"):
            view_idx = i
            break

    if view_idx is None:
        return None

    # Content lines are everything above "View job:", stripped of blanks
    content_lines = [ln.strip() for ln in lines[:view_idx] if ln.strip()]

    # Filter out known non-field lines
    _SKIP_PREFIXES = (
        "Your job alert",
        "New jobs match",
        "See all jobs",
    )
    _BADGE_PHRASES = {
        "this company is actively hiring",
        "fast growing",
        "apply with resume",
        "apply with resume & profile",
    }

    field_lines: list[str] = []
    for ln in content_lines:
        if any(ln.startswith(p) for p in _SKIP_PREFIXES):
            continue
        if ln.lower() in _BADGE_PHRASES:
            continue
        # Skip connection count lines like "1 connection"
        if re.match(r"^\d+ connections?$", ln):
            continue
        field_lines.append(ln)

    # Expected order: title, company, location (minimum 2 lines for a valid card)
    if len(field_lines) < 2:
        return None

    title = field_lines[0]
    company_name = field_lines[1]
    location = field_lines[2] if len(field_lines) >= 3 else ""

    return SearchResult(
        job_id=job_id,
        title=title,
        company_name=company_name,
        location=location,
        job_url=job_url,
        posted_time="",  # Not available in alert emails
        collected_at=collected_at,
    )
