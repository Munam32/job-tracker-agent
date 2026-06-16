"""
scraper.py — Job listing scraper
Supports: LinkedIn, Indeed, Rozee.pk, and arbitrary job URLs.

Note: LinkedIn and Indeed actively block scrapers.
This uses public/unauthenticated endpoints where possible.
For best results, use the direct 'url' mode with a job posting link.
"""

import time
import requests
from bs4 import BeautifulSoup
from typing import Optional
from urllib.parse import quote_plus

from config import SCRAPE_DELAY, SCRAPE_MAX_RESULTS, USER_AGENT


class JobScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": USER_AGENT,
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        })

    # ──────────────────────────────────────────
    # Router
    # ──────────────────────────────────────────

    def scrape(self, source: str, keyword: str, location: str) -> list[dict]:
        """Route to the correct scraper by source name."""
        handlers = {
            "linkedin": self._scrape_linkedin,
            "indeed":   self._scrape_indeed,
            "rozee":    self._scrape_rozee,
        }
        fn = handlers.get(source)
        if not fn:
            raise ValueError(f"Unknown source: {source}")
        return fn(keyword, location)

    def scrape_url(self, url: str) -> list[dict]:
        """Scrape a single job posting URL."""
        try:
            resp = self._get(url)
            if not resp:
                return []

            soup = BeautifulSoup(resp.text, "html.parser")
            job  = self._extract_generic(soup, url)
            return [job] if job else []
        except Exception as e:
            print(f"[scraper] URL scrape failed: {e}")
            return []

    # ──────────────────────────────────────────
    # Source-specific scrapers
    # ──────────────────────────────────────────

    def _scrape_linkedin(self, keyword: str, location: str) -> list[dict]:
        """
        Scrape LinkedIn public job search (no login required for search results).
        """
        url = (
            "https://www.linkedin.com/jobs/search/"
            f"?keywords={quote_plus(keyword)}"
            f"&location={quote_plus(location)}"
            "&f_TPR=r86400"   # last 24 hours
            "&position=1&pageNum=0"
        )

        resp = self._get(url)
        if not resp:
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        cards = soup.select("div.base-card")[:SCRAPE_MAX_RESULTS]

        jobs = []
        for card in cards:
            try:
                title   = card.select_one("h3.base-search-card__title")
                company = card.select_one("h4.base-search-card__subtitle")
                loc     = card.select_one("span.job-search-card__location")
                link    = card.select_one("a.base-card__full-link")

                job = {
                    "title":       title.get_text(strip=True)   if title   else "",
                    "company":     company.get_text(strip=True) if company else "",
                    "location":    loc.get_text(strip=True)     if loc     else location,
                    "url":         link["href"].split("?")[0]   if link    else "",
                    "description": "",
                    "salary":      "",
                    "status":      "Saved",
                    "date_applied": "",
                }

                # Optionally fetch description from individual posting
                if job["url"]:
                    job["description"] = self._fetch_linkedin_description(job["url"])
                    time.sleep(SCRAPE_DELAY)

                jobs.append(job)
            except Exception:
                continue

        return jobs

    def _fetch_linkedin_description(self, url: str) -> str:
        resp = self._get(url)
        if not resp:
            return ""
        soup = BeautifulSoup(resp.text, "html.parser")
        desc = soup.select_one("div.description__text") or \
               soup.select_one("div.show-more-less-html__markup")
        return desc.get_text(separator="\n", strip=True)[:3000] if desc else ""

    def _scrape_indeed(self, keyword: str, location: str) -> list[dict]:
        """
        Scrape Indeed Pakistan job listings.
        """
        url = (
            f"https://pk.indeed.com/jobs"
            f"?q={quote_plus(keyword)}"
            f"&l={quote_plus(location)}"
        )

        resp = self._get(url)
        if not resp:
            return []

        soup  = BeautifulSoup(resp.text, "html.parser")
        cards = soup.select("div.job_seen_beacon, div[data-testid='slider_item']")[:SCRAPE_MAX_RESULTS]

        jobs = []
        for card in cards:
            try:
                title   = card.select_one("h2.jobTitle span, h2.jobTitle a")
                company = card.select_one("span.companyName, [data-testid='company-name']")
                loc     = card.select_one("div.companyLocation, [data-testid='text-location']")
                salary  = card.select_one("div.salary-snippet-container, [data-testid='attribute_snippet_testid']")
                link    = card.select_one("a[data-jk], h2.jobTitle a")

                job_url = ""
                if link and link.get("data-jk"):
                    job_url = f"https://pk.indeed.com/viewjob?jk={link['data-jk']}"
                elif link and link.get("href"):
                    job_url = "https://pk.indeed.com" + link["href"]

                jobs.append({
                    "title":       title.get_text(strip=True)   if title   else "",
                    "company":     company.get_text(strip=True) if company else "",
                    "location":    loc.get_text(strip=True)     if loc     else location,
                    "salary":      salary.get_text(strip=True)  if salary  else "",
                    "url":         job_url,
                    "description": "",
                    "status":      "Saved",
                    "date_applied": "",
                })
                time.sleep(SCRAPE_DELAY)
            except Exception:
                continue

        return jobs

    def _scrape_rozee(self, keyword: str, location: str) -> list[dict]:
        """
        Scrape Rozee.pk (Pakistan's largest job board).
        """
        url = (
            f"https://www.rozee.pk/job/jsearch/q/{quote_plus(keyword)}"
        )

        resp = self._get(url)
        if not resp:
            return []

        soup  = BeautifulSoup(resp.text, "html.parser")
        cards = soup.select("div.job-listing, li.job")[:SCRAPE_MAX_RESULTS]

        jobs = []
        for card in cards:
            try:
                title   = card.select_one("h3 a, .title a")
                company = card.select_one(".company-name, .org a")
                loc     = card.select_one(".location, .loc")
                link    = card.select_one("h3 a, .title a")

                job_url = link["href"] if link and link.get("href") else ""
                if job_url and not job_url.startswith("http"):
                    job_url = "https://www.rozee.pk" + job_url

                jobs.append({
                    "title":       title.get_text(strip=True)   if title   else "",
                    "company":     company.get_text(strip=True) if company else "",
                    "location":    loc.get_text(strip=True)     if loc     else location,
                    "salary":      "",
                    "url":         job_url,
                    "description": "",
                    "status":      "Saved",
                    "date_applied": "",
                })
                time.sleep(SCRAPE_DELAY)
            except Exception:
                continue

        return jobs

    # ──────────────────────────────────────────
    # Generic URL scraper (fallback)
    # ──────────────────────────────────────────

    def _extract_generic(self, soup: BeautifulSoup, url: str) -> Optional[dict]:
        """Best-effort extraction from an arbitrary job posting page."""
        # Try common patterns
        title = (
            soup.select_one("h1")
            or soup.select_one("title")
        )
        company_tag = (
            soup.select_one("[class*='company']")
            or soup.select_one("[class*='employer']")
            or soup.select_one("[class*='org']")
        )
        location_tag = (
            soup.select_one("[class*='location']")
            or soup.select_one("[class*='city']")
        )

        # Get the bulk of the page text as the description
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        description = soup.get_text(separator="\n", strip=True)[:5000]

        return {
            "title":       title.get_text(strip=True)       if title       else "Unknown Role",
            "company":     company_tag.get_text(strip=True) if company_tag else "",
            "location":    location_tag.get_text(strip=True) if location_tag else "",
            "salary":      "",
            "url":         url,
            "description": description,
            "status":      "Saved",
            "date_applied": "",
        }

    # ──────────────────────────────────────────
    # HTTP helper
    # ──────────────────────────────────────────

    def _get(self, url: str, retries: int = 2) -> Optional[requests.Response]:
        for attempt in range(retries + 1):
            try:
                resp = self.session.get(url, timeout=10)
                if resp.status_code == 200:
                    return resp
                if resp.status_code in (429, 503):
                    time.sleep(SCRAPE_DELAY * 3)
            except requests.RequestException as e:
                if attempt == retries:
                    print(f"[scraper] Request failed: {e}")
                time.sleep(SCRAPE_DELAY)
        return None
