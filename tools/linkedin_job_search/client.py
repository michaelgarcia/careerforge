"""LinkedIn Job Search client with rate limiting and retry logic."""

from __future__ import annotations

import html as html_module
import logging
import time
from datetime import datetime, timezone

import httpx
from bs4 import BeautifulSoup

from linkedin_job_search.exceptions import LinkedInAPIError
from linkedin_job_search.models import (
    DatePosted,
    EnrichedJob,
    ExperienceLevel,
    GeoLocation,
    JobType,
    SearchResult,
    WorkModel,
)

logger = logging.getLogger(__name__)

_SEARCH_URL = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
_DETAIL_URL = "https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}"
_GEO_URL = "https://www.linkedin.com/jobs-guest/api/typeaheadHits"

# Retryable HTTP status codes
_RETRYABLE_STATUSES = {429} | set(range(500, 600))


class LinkedInJobSearch:
    """Client for searching LinkedIn jobs via the public Guest API."""

    def __init__(
        self,
        request_delay: float = 1.0,
        max_retries: int = 3,
        backoff_base: float = 2.0,
    ) -> None:
        """Initialise the client.

        Args:
            request_delay: Seconds to wait between consecutive HTTP requests.
            max_retries: Maximum number of retry attempts on retryable errors.
            backoff_base: Base for exponential backoff; sleep = backoff_base ** attempt.
        """
        self.request_delay = request_delay
        self.max_retries = max_retries
        self.backoff_base = backoff_base
        self._http = httpx.Client(
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
            },
            follow_redirects=True,
            timeout=30.0,
        )
        self._last_request_time: float = 0.0

    # ------------------------------------------------------------------
    # Public API (stubs — implemented in subsequent tasks)
    # ------------------------------------------------------------------

    def search(
        self,
        keywords: str | None = None,
        location: str | None = None,
        geo_id: str | None = None,
        experience_level: ExperienceLevel | list[ExperienceLevel] | None = None,
        job_type: JobType | list[JobType] | None = None,
        work_model: WorkModel | list[WorkModel] | None = None,
        date_posted: DatePosted | None = None,
        easy_apply: bool = False,
        enrich: bool = True,
        limit: int = 25,
    ) -> list[SearchResult | EnrichedJob]:
        """Search LinkedIn jobs with optional filters, pagination, and optional enrichment.

        Args:
            keywords: Free-text search keywords.
            location: Location name string.
            geo_id: LinkedIn numeric geoId for precise location filtering.
            experience_level: One or more ExperienceLevel enum values.
            job_type: One or more JobType enum values.
            work_model: One or more WorkModel enum values.
            date_posted: DatePosted enum value.
            easy_apply: If True, filter to Easy Apply jobs only.
            enrich: If True (default), fetch full details for each result.
            limit: Maximum number of records to return (default 25).

        Returns:
            List of SearchResult (enrich=False) or EnrichedJob (enrich=True) records.
        """
        base_params = self._build_search_params(
            keywords=keywords,
            location=location,
            geo_id=geo_id,
            experience_level=experience_level,
            job_type=job_type,
            work_model=work_model,
            date_posted=date_posted,
            easy_apply=easy_apply,
        )

        collected: list[SearchResult] = []
        start = 0

        logger.info("Starting search: keywords=%r location=%r limit=%d", keywords, location, limit)

        while len(collected) < limit:
            params = {**base_params, "start": start}
            response = self._request(_SEARCH_URL, params)
            page_results = self._parse_search_html(response.text)

            if not page_results:
                logger.info("No more results from LinkedIn (collected %d so far).", len(collected))
                break

            collected.extend(page_results)
            logger.info("Fetched page starting at %d — %d jobs collected so far.", start, len(collected))
            start += 25

        # Trim to exactly limit records
        collected = collected[:limit]
        logger.info("Search complete: %d jobs found.", len(collected))

        if not enrich:
            return collected

        # Enrich each result
        enriched: list[SearchResult | EnrichedJob] = []
        for i, result in enumerate(collected, 1):
            logger.info("Enriching job %d/%d  (id=%s) — %s", i, len(collected), result.job_id, result.title or "")
            try:
                detail_response = self._request(_DETAIL_URL.format(job_id=result.job_id))
                detail_fields = self._parse_detail_html(detail_response.text)
                enriched.append(
                    EnrichedJob(
                        **result.model_dump(),
                        **detail_fields,
                        enriched_at=datetime.now(timezone.utc),
                    )
                )
            except LinkedInAPIError as exc:
                logger.warning(
                    "Failed to enrich job %s: %d", result.job_id, exc.status_code
                )
                enriched.append(
                    EnrichedJob(
                        **result.model_dump(),
                        enriched_at=None,
                    )
                )

        logger.info("Enrichment complete: %d jobs enriched.", len(enriched))
        return enriched

    def enrich_jobs(
        self,
        jobs: list[SearchResult],
        limit: int | None = None,
    ) -> list[EnrichedJob]:
        """Enrich a list of SearchResult records with full job details.

        Args:
            jobs: List of SearchResult records to enrich.
            limit: If provided, only enrich the first `limit` records; the rest
                   are converted to EnrichedJob with enrichment fields as None.

        Returns:
            List of EnrichedJob records in the same order as the input.
        """
        to_enrich = jobs if limit is None else jobs[:limit]
        skip = [] if limit is None else jobs[limit:]

        enriched: list[EnrichedJob] = []

        for job in to_enrich:
            try:
                detail_response = self._request(_DETAIL_URL.format(job_id=job.job_id))
                detail_fields = self._parse_detail_html(detail_response.text)
                enriched.append(
                    EnrichedJob(
                        **job.model_dump(),
                        **detail_fields,
                        enriched_at=datetime.now(timezone.utc),
                    )
                )
            except LinkedInAPIError as exc:
                logger.warning("Failed to enrich job %s: %s", job.job_id, exc.status_code)
                enriched.append(EnrichedJob(**job.model_dump()))

        # Records beyond the limit are returned without enrichment fields
        for job in skip:
            enriched.append(EnrichedJob(**job.model_dump()))

        return enriched

    def resolve_geo_id(self, query: str) -> list[GeoLocation]:
        """Resolve a location name to LinkedIn geoId values.

        Args:
            query: Location name to search for.

        Returns:
            List of GeoLocation records matching the query, or empty list if none found.

        Raises:
            LinkedInAPIError: If all retries are exhausted.
        """
        response = self._request(
            _GEO_URL,
            params={
                "typeaheadType": "GEO",
                "geoTypes": "POPULATED_PLACE",
                "query": query,
            },
        )

        data = response.json()
        if not data:
            return []

        locations: list[GeoLocation] = []
        for item in data:
            # Try id.objectUrn first, then entityUrn at top level
            raw_urn = item.get("id", {}).get("objectUrn", "") or item.get("entityUrn", "")
            # Extract numeric part after the last colon
            geo_id = raw_urn.rsplit(":", 1)[-1] if ":" in raw_urn else raw_urn
            display_name = item.get("displayName", "")
            if geo_id and display_name:
                locations.append(GeoLocation(geo_id=geo_id, display_name=display_name))

        return locations

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_search_params(self, **filters) -> dict:
        """Convert filter kwargs to LinkedIn query parameter dict.

        Mapping:
            keywords        → "keywords"  (str)
            location        → "location"  (str)
            geo_id          → "geoId"     (str)
            experience_level→ "f_E"       (comma-separated int values)
            job_type        → "f_JT"      (comma-separated str values)
            work_model      → "f_WT"      (comma-separated int values)
            date_posted     → "f_TPR"     (single str value)
            easy_apply      → "f_AL"      ("true", only when True)

        None/unset filters are omitted from the result dict.
        """
        params: dict = {}

        # Simple string pass-throughs
        for key, param in (("keywords", "keywords"), ("location", "location"), ("geo_id", "geoId")):
            value = filters.get(key)
            if value is not None:
                params[param] = value

        # Multi-select enum filters: single value or list → comma-separated .value strings
        for key, param in (
            ("experience_level", "f_E"),
            ("job_type", "f_JT"),
            ("work_model", "f_WT"),
        ):
            value = filters.get(key)
            if value is not None:
                if isinstance(value, list):
                    params[param] = ",".join(str(v.value) for v in value)
                else:
                    params[param] = str(value.value)

        # date_posted: single enum value
        date_posted = filters.get("date_posted")
        if date_posted is not None:
            params["f_TPR"] = date_posted.value

        # easy_apply: only include when True
        easy_apply = filters.get("easy_apply")
        if easy_apply:
            params["f_AL"] = "true"

        return params

    def _parse_search_html(self, html: str) -> list[SearchResult]:
        """Parse search endpoint HTML and return a list of SearchResult."""
        soup = BeautifulSoup(html, "html.parser")
        results: list[SearchResult] = []

        # Job cards can be <li> or <div> with class "base-card" or "job-search-card"
        cards = soup.find_all(["li", "div"], class_=lambda c: c and (
            "base-card" in c or "job-search-card" in c
        ))

        for card in cards:
            # Extract job_id from data-entity-urn (e.g. "urn:li:jobPosting:3912345678")
            urn = card.get("data-entity-urn", "")
            if not urn or ":" not in urn:
                continue
            job_id = urn.rsplit(":", 1)[-1].strip()
            if not job_id:
                continue

            def _text(selector: str) -> str:
                el = card.find(class_=selector)
                if el is None:
                    return ""
                return html_module.unescape(el.get_text(strip=True))

            title = _text("base-search-card__title")
            company_name = _text("base-search-card__subtitle")
            location = _text("job-search-card__location")

            # job_url from <a class="base-card__full-link">
            link_el = card.find("a", class_="base-card__full-link")
            job_url = html_module.unescape(link_el.get("href", "").strip()) if link_el else ""

            # posted_time from <time> element
            time_el = card.find("time")
            posted_time = html_module.unescape(time_el.get_text(strip=True)) if time_el else ""

            results.append(
                SearchResult(
                    job_id=job_id,
                    title=title,
                    company_name=company_name,
                    location=location,
                    job_url=job_url,
                    posted_time=posted_time,
                    collected_at=datetime.now(timezone.utc),
                )
            )

        return results

    def _parse_detail_html(self, html: str) -> dict:
        """Parse detail endpoint HTML and return enrichment field dict."""
        soup = BeautifulSoup(html, "html.parser")

        def _clean(el) -> str | None:
            if el is None:
                return None
            return html_module.unescape(el.get_text(strip=True)) or None

        # full_description: try .description__text first, then .show-more-less-html__markup
        desc_el = soup.find(class_="description__text") or soup.find(class_="show-more-less-html__markup")
        full_description = _clean(desc_el)

        # Criteria list: ul.description__job-criteria-list
        seniority_level: str | None = None
        employment_type: str | None = None
        job_function: str | None = None
        industries: str | None = None

        criteria_list = soup.find("ul", class_="description__job-criteria-list")
        if criteria_list:
            for li in criteria_list.find_all("li"):
                header_el = li.find("h3")
                value_el = li.find("span")
                if not header_el or not value_el:
                    continue
                header = header_el.get_text(strip=True)
                value = html_module.unescape(value_el.get_text(strip=True))
                if header == "Seniority level":
                    seniority_level = value or None
                elif header == "Employment type":
                    employment_type = value or None
                elif header == "Job function":
                    job_function = value or None
                elif header == "Industries":
                    industries = value or None

        # salary_info: try .salary selector, then look for text containing "$"
        salary_el = soup.find(class_="salary") or soup.find(class_="compensation")
        if salary_el is None:
            # Search all text nodes for salary patterns
            for el in soup.find_all(string=lambda t: t and "$" in t):
                parent = el.parent
                if parent and parent.name not in ("script", "style"):
                    salary_el = parent
                    break
        salary_info = _clean(salary_el)

        return {
            "full_description": full_description,
            "seniority_level": seniority_level,
            "employment_type": employment_type,
            "job_function": job_function,
            "industries": industries,
            "salary_info": salary_info,
        }

    def _wait(self) -> None:
        """Sleep until at least `request_delay` seconds have passed since the last request."""
        elapsed = time.monotonic() - self._last_request_time
        remaining = self.request_delay - elapsed
        if remaining > 0:
            time.sleep(remaining)

    def _request(self, url: str, params: dict | None = None) -> httpx.Response:
        """Send a GET request with rate limiting and exponential backoff retry.

        Retryable status codes: 429 and 5xx.
        Non-retryable 4xx (except 429): raises LinkedInAPIError immediately.
        After max_retries exhausted: raises LinkedInAPIError with last status.

        Args:
            url: The URL to request.
            params: Optional query parameters.

        Returns:
            The successful httpx.Response.

        Raises:
            LinkedInAPIError: On non-retryable HTTP errors or exhausted retries.
        """
        last_response: httpx.Response | None = None

        for attempt in range(self.max_retries + 1):
            self._wait()
            try:
                response = self._http.get(url, params=params)
            finally:
                self._last_request_time = time.monotonic()

            if response.status_code < 400:
                # Success
                return response

            if response.status_code in _RETRYABLE_STATUSES:
                last_response = response
                if attempt < self.max_retries:
                    sleep_time = self.backoff_base ** (attempt + 1)
                    logger.warning(
                        "Retryable HTTP %d from %s — retrying in %.1fs (attempt %d/%d)",
                        response.status_code,
                        url,
                        sleep_time,
                        attempt + 1,
                        self.max_retries,
                    )
                    time.sleep(sleep_time)
                    continue
                # Retries exhausted
                raise LinkedInAPIError(
                    status_code=response.status_code,
                    detail=response.text,
                )
            else:
                # Non-retryable 4xx (except 429 which is in _RETRYABLE_STATUSES)
                raise LinkedInAPIError(
                    status_code=response.status_code,
                    detail=response.text,
                )

        # Should not reach here, but guard just in case
        assert last_response is not None
        raise LinkedInAPIError(
            status_code=last_response.status_code,
            detail=last_response.text,
        )

    def __enter__(self) -> "LinkedInJobSearch":
        return self

    def __exit__(self, *args) -> None:
        self._http.close()

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._http.close()
