"""IMAP email source for fetching LinkedIn job alert emails."""

from __future__ import annotations

import email as email_stdlib
import imaplib
import logging

from linkedin_job_search.config import EmailConfig
from linkedin_job_search.email_parser import parse_alert_email
from linkedin_job_search.models import SearchResult

logger = logging.getLogger(__name__)


class IMAPSource:
    """Connect to an IMAP mailbox and fetch LinkedIn job alert emails.

    Usage::

        from linkedin_job_search.config import load_email_config

        cfg = load_email_config()
        with IMAPSource(cfg) as source:
            jobs = source.fetch_new_jobs(mark_read=True)
    """

    def __init__(self, config: EmailConfig) -> None:
        self._config = config
        self._conn: imaplib.IMAP4_SSL | None = None

    # -- context manager ---------------------------------------------------

    def __enter__(self) -> "IMAPSource":
        self.connect()
        return self

    def __exit__(self, *args) -> None:
        self.disconnect()

    # -- connection --------------------------------------------------------

    def connect(self) -> None:
        """Open an IMAP4-SSL connection and authenticate."""
        cfg = self._config
        logger.info("Connecting to %s:%d as %s", cfg.host, cfg.port, cfg.username)
        self._conn = imaplib.IMAP4_SSL(cfg.host, cfg.port)
        self._conn.login(cfg.username, cfg.password)
        logger.info("Authenticated successfully.")

    def disconnect(self) -> None:
        """Close the IMAP connection gracefully."""
        if self._conn is not None:
            try:
                self._conn.close()
            except imaplib.IMAP4.error:
                pass
            try:
                self._conn.logout()
            except imaplib.IMAP4.error:
                pass
            self._conn = None

    # -- fetching ----------------------------------------------------------

    def fetch_new_jobs(self, mark_read: bool = True) -> list[SearchResult]:
        """Fetch unread LinkedIn alert emails and parse them into jobs.

        Args:
            mark_read: If True, mark processed emails as SEEN so they are
                       not fetched again on the next run.

        Returns:
            Flat list of :class:`SearchResult` from all unread alert emails.
        """
        assert self._conn is not None, "Call connect() or use as context manager first."

        cfg = self._config
        self._conn.select(cfg.folder)

        # Search for unread emails from the LinkedIn alerts sender
        search_criteria = f'(UNSEEN FROM "{cfg.sender_filter}")'
        status, data = self._conn.search(None, search_criteria)

        if status != "OK" or not data or not data[0]:
            logger.info("No unread alert emails found.")
            return []

        msg_ids = data[0].split()
        logger.info("Found %d unread alert email(s).", len(msg_ids))

        all_jobs: list[SearchResult] = []

        for msg_id in msg_ids:
            status, msg_data = self._conn.fetch(msg_id, "(RFC822)")
            if status != "OK" or not msg_data or not msg_data[0]:
                logger.warning("Failed to fetch message %s", msg_id)
                continue

            raw_bytes = msg_data[0][1]
            if not isinstance(raw_bytes, bytes):
                logger.warning("Unexpected payload type for message %s", msg_id)
                continue

            # Extract subject for logging
            msg = email_stdlib.message_from_bytes(raw_bytes)
            subject = msg.get("Subject", "(no subject)")
            logger.info("Processing: %s", subject)

            jobs = parse_alert_email(raw_bytes)
            logger.info("  → %d job(s) parsed.", len(jobs))
            all_jobs.extend(jobs)

            if mark_read:
                self._conn.store(msg_id, "+FLAGS", "\\Seen")

        logger.info("Total: %d job(s) from %d email(s).", len(all_jobs), len(msg_ids))
        return all_jobs
