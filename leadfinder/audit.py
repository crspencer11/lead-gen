import re
import time
from urllib.parse import urlparse, urljoin

import requests
from bs4 import BeautifulSoup

from .config import PAGESPEED_API_KEY, REQUEST_TIMEOUT, USER_AGENT
from .csv_utils import read_rows, write_rows

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": USER_AGENT})


def normalize_url(value):
    value = (value or "").strip()
    if not value:
        return ""
    if not re.match(r"^https?://", value, re.I):
        value = "https://" + value
    return value


def safe_get(url):
    try:
        return SESSION.get(url, timeout=REQUEST_TIMEOUT, allow_redirects=True)
    except requests.RequestException:
        return None


def _check_url(url):
    if not url:
        return {"website_status": "no_website", "final_url": "", "https": "", "page_title": "",
                "meta_description": "", "h1_count": "", "robots_txt": "", "sitemap_xml": "",
                "internal_links": "", "contact_form_detected": "", "audit_error": "No website URL"}

    response = safe_get(url)
    if response is None:
        return {"website_status": "request_failed", "final_url": "", "https": urlparse(url).scheme == "https",
                "page_title": "", "meta_description": "", "h1_count": "", "robots_txt": "",
                "sitemap_xml": "", "internal_links": "", "contact_form_detected": "",
                "audit_error": "Could not fetch homepage"}

    result = {
        "website_status": response.status_code,
        "final_url": response.url,
        "https": urlparse(response.url).scheme == "https",
        "page_title": "",
        "meta_description": "",
        "h1_count": "",
        "robots_txt": "",
        "sitemap_xml": "",
        "internal_links": "",
        "contact_form_detected": "",
        "audit_error": "",
    }

    content_type = response.headers.get("Content-Type", "")
    if "html" not in content_type.lower():
        result["audit_error"] = f"Non-HTML response: {content_type}"
        return result

    soup = BeautifulSoup(response.text, "html.parser")
    result["page_title"] = soup.title.get_text(" ", strip=True) if soup.title else ""
    description = soup.find("meta", attrs={"name": re.compile("^description$", re.I)})
    result["meta_description"] = description.get("content", "").strip() if description else ""
    result["h1_count"] = len(soup.find_all("h1"))

    base = response.url
    host = urlparse(base).netloc.lower()
    links = set()
    for a in soup.find_all("a", href=True):
        absolute = urljoin(base, a["href"])
        parsed = urlparse(absolute)
        if parsed.scheme in ("http", "https") and parsed.netloc.lower() == host:
            links.add(absolute.split("#")[0])
    result["internal_links"] = len(links)

    forms = soup.find_all("form")
    text_blob = soup.get_text(" ", strip=True).lower()
    has_contact_words = any(x in text_blob for x in ["request a quote", "get a quote", "contact us", "free estimate"])
    result["contact_form_detected"] = bool(forms) or has_contact_words

    origin = f"{urlparse(base).scheme}://{urlparse(base).netloc}"
    robots = safe_get(urljoin(origin, "/robots.txt"))
    sitemap = safe_get(urljoin(origin, "/sitemap.xml"))
    result["robots_txt"] = bool(robots is not None and robots.status_code == 200)
    result["sitemap_xml"] = bool(sitemap is not None and sitemap.status_code == 200)
    return result


def _pagespeed(url, strategy):
    endpoint = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
    params = {"url": url, "strategy": strategy, "category": ["PERFORMANCE", "SEO"]}
    if PAGESPEED_API_KEY:
        params["key"] = PAGESPEED_API_KEY
    try:
        response = requests.get(endpoint, params=params, timeout=90)
        if response.status_code >= 400:
            return "", f"PageSpeed HTTP {response.status_code}"
        data = response.json()
        categories = data.get("lighthouseResult", {}).get("categories", {})
        perf = categories.get("performance", {}).get("score")
        seo = categories.get("seo", {}).get("score")
        return (
            round(perf * 100) if perf is not None else "",
            round(seo * 100) if seo is not None else "",
        )
    except Exception as exc:
        return "", f"PageSpeed error: {str(exc)[:160]}"


def audit_csv(input_path, output_path, limit=0, run_pagespeed=True):
    rows = read_rows(input_path)
    if limit and limit > 0:
        rows = rows[:limit]

    if not rows:
        print("Input CSV contains no rows.")
        return

    output = []
    for index, row in enumerate(rows, start=1):
        name = row.get("business_name") or row.get("name") or "(unnamed business)"
        url = normalize_url(row.get("website") or row.get("website_url") or "")
        print(f"[{index}/{len(rows)}] Auditing {name} — {url or 'no website'}")

        checks = _check_url(url)
        row.update(checks)

        if url and run_pagespeed and checks.get("website_status") not in ("no_website", "request_failed"):
            mobile_perf, mobile_seo = _pagespeed(checks.get("final_url") or url, "mobile")
            time.sleep(1)
            desktop_perf, desktop_seo = _pagespeed(checks.get("final_url") or url, "desktop")
            row.update({
                "pagespeed_mobile_performance": mobile_perf,
                "pagespeed_mobile_seo": mobile_seo,
                "pagespeed_desktop_performance": desktop_perf,
                "pagespeed_desktop_seo": desktop_seo,
            })
            if isinstance(mobile_seo, str) and mobile_seo.startswith("PageSpeed"):
                row["pagespeed_error"] = mobile_seo
            elif isinstance(desktop_seo, str) and desktop_seo.startswith("PageSpeed"):
                row["pagespeed_error"] = desktop_seo
        else:
            row.update({
                "pagespeed_mobile_performance": "",
                "pagespeed_mobile_seo": "",
                "pagespeed_desktop_performance": "",
                "pagespeed_desktop_seo": "",
            })
        output.append(row)
        time.sleep(0.25)

    write_rows(output_path, output)
