import argparse
from pathlib import Path

from leadfinder.discovery import discover
from leadfinder.audit import audit_csv


def main():
    parser = argparse.ArgumentParser(
        description="Discover local businesses and run basic website checks."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    discover_parser = subparsers.add_parser("discover", help="Find businesses using Google Places API (New).")
    discover_parser.add_argument("--industry", action="append", required=True,
                                 help="Industry/search phrase. Repeat to search multiple categories.")
    discover_parser.add_argument("--location", required=True, help='Location, e.g. "Thousand Oaks, CA"')
    discover_parser.add_argument("--limit", type=int, default=40, help="Maximum total results to collect (best effort).")
    discover_parser.add_argument("--output", default="data/prospects.csv", help="Output CSV path.")

    audit_parser = subparsers.add_parser("audit", help="Run basic website checks on a CSV.")
    audit_parser.add_argument("--input", required=True, help="Input CSV with a website column.")
    audit_parser.add_argument("--output", default="data/audited_prospects.csv", help="Output CSV path.")
    audit_parser.add_argument("--limit", type=int, default=0, help="Only audit the first N rows; 0 means all.")
    audit_parser.add_argument("--no-pagespeed", action="store_true", help="Skip PageSpeed Insights checks.")

    args = parser.parse_args()

    if args.command == "discover":
        discover(args.industry, args.location, args.limit, args.output)
    elif args.command == "audit":
        audit_csv(args.input, args.output, args.limit, not args.no_pagespeed)


if __name__ == "__main__":
    main()
