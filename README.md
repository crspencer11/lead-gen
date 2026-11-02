# Local Lead Finder

A small, deterministic Python CLI for discovering local businesses and running basic website checks.

- No AI, LLM, inference, or agent framework.
- Google Places API (New) is optional and requires your own API key.
- Website audits use ordinary HTTP requests and HTML parsing.
- Google PageSpeed Insights is optional; it can run without an API key at low usage, but a key is recommended.
- Exports a CSV you can open in Excel or Google Sheets.

## 1. Requirements

- Python 3.10+
- A Google Maps Platform API key with Places API (New) enabled if you want automated discovery.
- Optional PageSpeed Insights API key.

## 2. Install

```bash
cd local_lead_finder
python -m venv .venv

# macOS / Linux
source .venv/bin/activate

# Windows PowerShell
# .venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

## 3. Configure API keys

Copy `.env.example` to `.env` and add your keys:

```bash
cp .env.example .env
```

Or set environment variables directly:

```bash
export GOOGLE_PLACES_API_KEY="your-key"
export PAGESPEED_API_KEY="your-key"
```

On Windows PowerShell:

```powershell
$env:GOOGLE_PLACES_API_KEY="your-key"
$env:PAGESPEED_API_KEY="your-key"
```

Enable **Places API (New)** in Google Cloud and configure billing/API restrictions. The project requests only a small set of fields, but Google Places API usage is billable. Check current pricing before running large searches.

## 4. Discover businesses

```bash
python main.py discover --industry plumber --location "Thousand Oaks, CA" --limit 40
```

Multiple categories can be supplied:

```bash
python main.py discover \
  --industry plumber \
  --industry electrician \
  --industry "HVAC contractor" \
  --location "Thousand Oaks, CA" \
  --limit 60
```

The script runs one Places Text Search per industry/location combination. The API may return fewer results than requested, and a search is not guaranteed to enumerate every business in an area.

Results are written to `data/prospects.csv`.

## 5. Audit businesses already in a CSV

You can also skip Places discovery and audit a CSV you created yourself. Required column: `website`. Optional columns include `business_name`, `phone`, `address`, `rating`, `review_count`, and `place_id`.

```bash
python main.py audit --input data/my_prospects.csv
```

Or audit the latest discovered list:

```bash
python main.py audit --input data/prospects.csv
```

Audit results are written to `data/audited_prospects.csv`.

## 6. Run PageSpeed checks

PageSpeed checks are enabled by default. To skip them:

```bash
python main.py audit --input data/prospects.csv --no-pagespeed
```

To run only a small number while testing:

```bash
python main.py audit --input data/prospects.csv --limit 10
```

PageSpeed requests can take a while. The tool runs mobile and desktop tests sequentially and pauses briefly between requests.

## 7. Output fields

The audit CSV includes:
- Business name, category, address, phone, website, rating, review count, Place ID
- Website HTTP status, final URL, HTTPS, page title, meta description, H1 count
- `robots.txt` and `sitemap.xml` availability
- Number of internal links and detected contact forms
- Mobile and desktop PageSpeed performance scores (when available)
- Audit errors, if any

These are screening indicators, not a complete SEO audit. A PageSpeed score is not a Google ranking, and public checks cannot reveal actual organic traffic, conversions, Search Console indexing diagnostics, or keyword rankings reliably.

## Data / API terms

Use official APIs and respect their terms, rate limits, and attribution requirements. Google Maps Platform content has storage, display, and usage restrictions; review the current Places API policies before retaining, redistributing, or using Places data outside permitted purposes. Place IDs have separate storage treatment. This tool is for your own prospect research, not bulk republication or resale of Google Maps data.

The crawler makes a single homepage request per site plus optional robots/sitemap checks. Only audit public websites you are permitted to access. It does not bypass logins, CAPTCHAs, or access controls.

## Commands

```bash
python main.py discover --help
python main.py audit --help
```
