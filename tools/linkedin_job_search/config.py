"""Configuration loader for email polling settings."""

from __future__ import annotations

import configparser
from dataclasses import dataclass
from pathlib import Path

_DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[3] / "config.ini"


@dataclass(frozen=True)
class EmailConfig:
    """IMAP connection and filtering settings."""

    host: str
    port: int
    username: str
    password: str
    folder: str = "INBOX"
    sender_filter: str = "jobalerts-noreply@linkedin.com"


def load_email_config(path: str | Path | None = None) -> EmailConfig:
    """Load email configuration from an INI file.

    Args:
        path: Path to the config file. Defaults to ``config.ini`` at the
              project root.

    Returns:
        Populated :class:`EmailConfig`.

    Raises:
        FileNotFoundError: If the config file does not exist.
        KeyError: If a required key is missing from the ``[email]`` section.
    """
    config_path = Path(path) if path else _DEFAULT_CONFIG_PATH

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    parser = configparser.ConfigParser()
    parser.read(config_path)

    section = parser["email"]

    return EmailConfig(
        host=section["host"],
        port=int(section.get("port", "993")),
        username=section["username"],
        password=section["password"],
        folder=section.get("folder", "INBOX"),
        sender_filter=section.get("sender_filter", "jobalerts-noreply@linkedin.com"),
    )
