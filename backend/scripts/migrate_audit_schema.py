#!/usr/bin/env python3
"""
Audit Schema Migration Script

Creates the PostgreSQL database schema for the enterprise-grade audit trail system.

Usage:
    python scripts/migrate_audit_schema.py
    python scripts/migrate_audit_schema.py --verify

Environment Variables:
    DATABASE_URL: PostgreSQL connection string
"""

import asyncio
import argparse
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import asyncpg
except ImportError:
    print("Error: asyncpg is required. Install it with: pip install asyncpg")
    sys.exit(1)

from config import DATABASE_URL


async def read_schema_sql() -> str:
    """Read the schema SQL file."""
    schema_path = Path(__file__).parent.parent / "schema" / "audit_schema.sql"
    with open(schema_path) as f:
        return f.read()


async def migrate_schema(dry_run: bool = False) -> bool:
    """
    Run the audit schema migration.

    Args:
        dry_run: If True, print SQL without executing

    Returns:
        True if successful, False otherwise
    """
    if not DATABASE_URL:
        print("Error: DATABASE_URL environment variable is not set")
        print("Set it to your PostgreSQL connection string, e.g.:")
        print("  export DATABASE_URL=postgresql://user:password@localhost:5432/dbname")
        return False

    schema_sql = await read_schema_sql()

    if dry_run:
        print("=== DRY RUN - Would execute the following SQL ===")
        print(schema_sql)
        return True

    try:
        print("Connecting to database...")
        conn = await asyncpg.connect(DATABASE_URL)

        # Split SQL into individual statements
        # This is a simple split; for production consider using a proper SQL parser
        statements = [
            s.strip()
            for s in schema_sql.split(";")
            if s.strip() and not s.strip().startswith("--")
        ]

        print(f"Executing {len(statements)} SQL statements...")

        for i, statement in enumerate(statements, 1):
            try:
                await conn.execute(statement)
                print(f"  [{i}/{len(statements)}] ✓ Executed")
            except asyncpg.DuplicateTableError:
                print(f"  [{i}/{len(statements)}] ⊘ Table already exists (skipped)")
            except asyncpg.DuplicateObjectError:
                print(f"  [{i}/{len(statements)}] ⊘ Object already exists (skipped)")
            except Exception as e:
                print(f"  [{i}/{len(statements)}] ✗ Error: {e}")

        await conn.close()
        print("\n✓ Audit schema migration completed successfully!")

        # Print summary
        await print_summary()

        return True

    except Exception as e:
        print(f"\n✗ Migration failed: {e}")
        return False


async def verify_schema() -> bool:
    """
    Verify that the audit schema is properly installed.

    Returns:
        True if all tables exist, False otherwise
    """
    if not DATABASE_URL:
        print("Error: DATABASE_URL environment variable is not set")
        return False

    try:
        print("Connecting to database...")
        conn = await asyncpg.connect(DATABASE_URL)

        # Check for required tables
        required_tables = ["audit_logs", "media_assets", "conversation_audits"]
        required_indexes = [
            "idx_audit_logs_timestamp",
            "idx_audit_logs_event_type",
            "idx_media_assets_created_at",
            "idx_conversation_audits_thread_id",
        ]
        required_views = ["v_recent_activity", "v_errors", "v_media_summary"]

        print("\nChecking tables:")
        for table in required_tables:
            result = await conn.fetchval(
                "SELECT EXISTS (SELECT FROM information_schema.tables "
                "WHERE table_name = $1)",
                table,
            )
            status = "✓" if result else "✗"
            print(f"  {status} {table}")

        print("\nChecking indexes:")
        for index in required_indexes:
            result = await conn.fetchval(
                "SELECT EXISTS (SELECT FROM pg_indexes WHERE indexname = $1)",
                index,
            )
            status = "✓" if result else "✗"
            print(f"  {status} {index}")

        print("\nChecking views:")
        for view in required_views:
            result = await conn.fetchval(
                "SELECT EXISTS (SELECT FROM information_schema.views "
                "WHERE table_name = $1)",
                view,
            )
            status = "✓" if result else "✗"
            print(f"  {status} {view}")

        # Get table counts
        print("\nCurrent data counts:")
        for table in required_tables:
            count = await conn.fetchval(f"SELECT COUNT(*) FROM {table}")
            print(f"  • {table}: {count:,} rows")

        await conn.close()

        print("\n✓ Schema verification completed!")
        return True

    except Exception as e:
        print(f"\n✗ Verification failed: {e}")
        return False


async def print_summary():
    """Print a summary of the installed schema."""
    if not DATABASE_URL:
        return

    try:
        conn = await asyncpg.connect(DATABASE_URL)

        print("\n" + "=" * 50)
        print("AUDIT SCHEMA SUMMARY")
        print("=" * 50)

        # Get row counts
        audit_count = await conn.fetchval("SELECT COUNT(*) FROM audit_logs")
        media_count = await conn.fetchval("SELECT COUNT(*) FROM media_assets")
        conv_count = await conn.fetchval("SELECT COUNT(*) FROM conversation_audits")

        print("\nTable Row Counts:")
        print(f"  • audit_logs:           {audit_count:,}")
        print(f"  • media_assets:         {media_count:,}")
        print(f"  • conversation_audits:  {conv_count:,}")

        # Get event type breakdown
        event_types = await conn.fetch(
            """
            SELECT event_type, COUNT(*) as count
            FROM audit_logs
            GROUP BY event_type
            ORDER BY count DESC
            LIMIT 10
            """
        )

        if event_types:
            print("\nTop Event Types:")
            for row in event_types:
                print(f"  • {row['event_type']}: {row['count']:,}")

        # Get recent activity
        recent = await conn.fetchval(
            "SELECT COUNT(*) FROM audit_logs WHERE timestamp > NOW() - INTERVAL '24 hours'"
        )
        print(f"\nRecent Activity (24h): {recent:,} events")

        await conn.close()

    except Exception as e:
        print(f"Warning: Could not print summary: {e}")


async def drop_schema() -> bool:
    """
    Drop all audit schema objects.

    WARNING: This will delete all audit data!

    Returns:
        True if successful, False otherwise
    """
    if not DATABASE_URL:
        print("Error: DATABASE_URL environment variable is not set")
        return False

    confirm = input("WARNING: This will delete ALL audit data. Type 'yes' to confirm: ")
    if confirm.lower() != "yes":
        print("Aborted.")
        return False

    try:
        print("Connecting to database...")
        conn = await asyncpg.connect(DATABASE_URL)

        print("Dropping audit schema objects...")

        # Drop views
        for view in ["v_recent_activity", "v_errors", "v_media_summary"]:
            await conn.execute(f"DROP VIEW IF EXISTS {view} CASCADE")
            print(f"  ✓ Dropped view {view}")

        # Drop tables
        for table in ["conversation_audits", "media_assets", "audit_logs"]:
            await conn.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
            print(f"  ✓ Dropped table {table}")

        await conn.close()
        print("\n✓ Audit schema dropped successfully!")
        return True

    except Exception as e:
        print(f"\n✗ Drop failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Audit schema migration and verification"
    )
    parser.add_argument(
        "action",
        choices=["migrate", "verify", "drop", "dry-run"],
        nargs="?",
        default="migrate",
        help="Action to perform",
    )
    args = parser.parse_args()

    if args.action == "migrate":
        success = asyncio.run(migrate_schema())
        sys.exit(0 if success else 1)
    elif args.action == "verify":
        success = asyncio.run(verify_schema())
        sys.exit(0 if success else 1)
    elif args.action == "drop":
        success = asyncio.run(drop_schema())
        sys.exit(0 if success else 1)
    elif args.action == "dry-run":
        success = asyncio.run(migrate_schema(dry_run=True))
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
