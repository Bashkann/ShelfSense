"""Command-line interface for explicit preflight or import execution."""

import argparse
import json
from collections.abc import Sequence

from shelfsense.db.importer.report import ImportAborted
from shelfsense.db.importer.service import import_from_files, preflight_from_files


def main(argv: Sequence[str] | None = None) -> int:
    """Run importer CLI and print its structured report as JSON."""

    parser = argparse.ArgumentParser(description="Import one ShelfSense store")
    parser.add_argument("--store", default="data/store.json")
    parser.add_argument("--products", default="data/product_mapping.json")
    parser.add_argument("--store-name")
    parser.add_argument(
        "--preflight-only",
        action="store_true",
        help="Build and report the plan without writing to PostgreSQL",
    )
    args = parser.parse_args(argv)

    try:
        if args.preflight_only:
            report = preflight_from_files(
                args.store,
                args.products,
                store_name=args.store_name,
            ).report
        else:
            report = import_from_files(
                args.store,
                args.products,
                store_name=args.store_name,
            )
    except ImportAborted as error:
        print(json.dumps(error.report.as_dict(), ensure_ascii=False, indent=2))
        return 2
    print(json.dumps(report.as_dict(), ensure_ascii=False, indent=2))
    return 0
