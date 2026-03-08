"""LinkedIn Job Search - Search LinkedIn jobs via the public Guest API."""

# Public API — imports filled as modules are created.
from linkedin_job_search.models import (
    ExperienceLevel,
    JobType,
    WorkModel,
    DatePosted,
    SearchResult,
    EnrichedJob,
    GeoLocation,
)
from linkedin_job_search.client import LinkedInJobSearch
from linkedin_job_search.storage import JSONLStore
from linkedin_job_search.config import EmailConfig, load_email_config
from linkedin_job_search.email_parser import parse_alert_email, parse_eml_file
from linkedin_job_search.email_source import IMAPSource
from linkedin_job_search.exceptions import (
    LinkedInJobSearchError,
    LinkedInAPIError,
    ParseError,
)

__all__ = [
    "ExperienceLevel",
    "JobType",
    "WorkModel",
    "DatePosted",
    "SearchResult",
    "EnrichedJob",
    "GeoLocation",
    "LinkedInJobSearch",
    "JSONLStore",
    "EmailConfig",
    "load_email_config",
    "parse_alert_email",
    "parse_eml_file",
    "IMAPSource",
    "LinkedInJobSearchError",
    "LinkedInAPIError",
    "ParseError",
]
