"""Data models and filter enums for LinkedIn job search."""

from datetime import datetime
from enum import Enum, IntEnum

from pydantic import BaseModel


class ExperienceLevel(IntEnum):
    """LinkedIn experience level filter values."""

    INTERNSHIP = 1
    ENTRY_LEVEL = 2
    ASSOCIATE = 3
    MID_SENIOR = 4
    DIRECTOR = 5
    EXECUTIVE = 6


class JobType(str, Enum):
    """LinkedIn job type filter values."""

    FULL_TIME = "F"
    PART_TIME = "P"
    CONTRACT = "C"
    TEMPORARY = "T"
    VOLUNTEER = "V"
    INTERNSHIP = "I"
    OTHER = "O"


class WorkModel(IntEnum):
    """LinkedIn work model filter values."""

    ON_SITE = 1
    REMOTE = 2
    HYBRID = 3


class DatePosted(str, Enum):
    """LinkedIn date posted filter values."""

    PAST_24H = "r86400"
    PAST_WEEK = "r604800"
    PAST_MONTH = "r2592000"
    ANY_TIME = ""


class SearchResult(BaseModel):
    """Minimal job record from the search endpoint."""

    job_id: str
    title: str
    company_name: str
    location: str
    job_url: str
    posted_time: str
    collected_at: datetime


class EnrichedJob(SearchResult):
    """Search result augmented with full job details."""

    full_description: str | None = None
    seniority_level: str | None = None
    employment_type: str | None = None
    job_function: str | None = None
    industries: str | None = None
    salary_info: str | None = None
    enriched_at: datetime | None = None


class GeoLocation(BaseModel):
    """LinkedIn geographic location with geoId."""

    geo_id: str
    display_name: str
