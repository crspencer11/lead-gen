import os
from dotenv import load_dotenv

load_dotenv()

GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY", "").strip()
PAGESPEED_API_KEY = os.getenv("PAGESPEED_API_KEY", "").strip()

USER_AGENT = "LocalLeadFinder/0.1 (public website diagnostics)"
REQUEST_TIMEOUT = 15
