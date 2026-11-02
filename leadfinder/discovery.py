import time
import requests

from .config import GOOGLE_PLACES_API_KEY
from .csv_utils import write_rows

PLACES_URL = "https://places.googleapis.com/v1/places:searchText"
FIELD_MASK = ",".join([
    "places.id",
    "places.displayName",
    "places.formattedAddress",
    "places.nationalPhoneNumber",
    "places.websiteUri",
    "places.rating",
    "places.userRatingCount",
    "places.primaryTypeDisplayName",
    "places.googleMapsUri",
])


def _search(query, page_size=20):
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GOOGLE_PLACES_API_KEY,
        "X-Goog-FieldMask": FIELD_MASK,
    }
    payload = {"textQuery": query, "pageSize": min(max(page_size, 1), 20)}
    response = requests.post(PLACES_URL, headers=headers, json=payload, timeout=30)
    if response.status_code >= 400:
        raise RuntimeError(f"Places API error {response.status_code}: {response.text[:500]}")
    return response.json().get("places", [])


def discover(industries, location, limit, output):
    if not GOOGLE_PLACES_API_KEY:
        raise SystemExit(
            "Missing GOOGLE_PLACES_API_KEY. Add it to .env or your environment. "
            "See README.md. You can still use 'audit' with your own CSV."
        )

    found = {}
    per_query = min(20, max(5, limit))
    for industry in industries:
        query = f"{industry} in {location}"
        print(f"Searching: {query}")
        try:
            places = _search(query, per_query)
        except Exception as exc:
            print(f"  Search failed: {exc}")
            continue

        for place in places:
            place_id = place.get("id")
            if not place_id:
                continue
            display = place.get("displayName") or {}
            found[place_id] = {
                "business_name": display.get("text", ""),
                "category": (place.get("primaryTypeDisplayName") or {}).get("text", industry),
                "address": place.get("formattedAddress", ""),
                "phone": place.get("nationalPhoneNumber", ""),
                "website": place.get("websiteUri", ""),
                "rating": place.get("rating", ""),
                "review_count": place.get("userRatingCount", ""),
                "place_id": place_id,
                "google_maps_url": place.get("googleMapsUri", ""),
                "search_query": query,
            }
        time.sleep(0.2)

    rows = list(found.values())[:limit]
    rows.sort(key=lambda r: (-(float(r["review_count"] or 0)), r["business_name"].lower()))
    write_rows(output, rows)
    print(f"Collected {len(rows)} unique businesses.")
    if len(rows) < limit:
        print("Note: Places Text Search is best-effort and may return fewer than the requested limit.")
