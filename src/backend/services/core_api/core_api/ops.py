"""One-off operations on the core table: `python -m core_api.ops <command>`.

Without `DYNAMODB_ENDPOINT_URL` they target the AWS `CORE_TABLE` with the shell's
credentials. Nothing in the running service imports this module.
"""

import argparse
import asyncio
import sys

from travel_common.exceptions import DomainError

from core_api.config import get_settings
from core_api.infrastructure.dynamo.backfill import (
    BackfillResult,
    backfill_trip_index,
    open_core_table,
)


async def _backfill_with_own_table(*, dry_run: bool) -> BackfillResult:
    table = await open_core_table(get_settings())
    return await backfill_trip_index(table, dry_run=dry_run)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m core_api.ops",
        description="One-off operations on the core table.",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    backfill = commands.add_parser(
        "backfill-trip-index",
        help="write GSI2PK/GSI2SK on trips saved before the admin index",
    )
    backfill.add_argument(
        "--dry-run",
        action="store_true",
        help="count the trips that would be stamped; write nothing",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Exit 0 with the summary on stdout; exit 1 with the reason on stderr."""
    namespace = build_parser().parse_args(argv)
    try:
        result = asyncio.run(_backfill_with_own_table(dry_run=namespace.dry_run))
    except DomainError as exc:
        print(f"error: {exc.message}", file=sys.stderr)
        return 1
    print(result.summary(dry_run=namespace.dry_run))
    return 0


if __name__ == "__main__":
    sys.exit(main())
