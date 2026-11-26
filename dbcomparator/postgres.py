from __future__ import annotations

import argparse
import os
from pathlib import Path

import psycopg2

from .comparison import row_diff, rows_to_json, write_json
from .vault import VaultError, vault_secret


COMPARISON_QUERIES = {
    "tables": ["SELECT table_schema, table_name FROM information_schema.tables WHERE table_type = 'BASE TABLE' AND table_schema NOT IN ('pg_catalog', 'information_schema') ORDER BY table_schema, table_name"],
    "table_columns": ["SELECT table_schema, table_name, column_name, data_type, is_nullable, column_default FROM information_schema.columns WHERE table_schema NOT IN ('pg_catalog', 'information_schema') ORDER BY table_schema, table_name, ordinal_position"],
    "indexes": ["SELECT schemaname AS table_schema, tablename AS table_name, indexname AS index_name, indexdef AS definition FROM pg_indexes WHERE schemaname NOT IN ('pg_catalog', 'information_schema') ORDER BY schemaname, tablename, indexname"],
    "functions": ["SELECT n.nspname AS function_schema, p.proname AS function_name, pg_get_function_result(p.oid) AS return_type FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace WHERE n.nspname NOT IN ('pg_catalog', 'information_schema') ORDER BY function_schema, function_name"],
    "roles": ["SELECT rolname, rolsuper, rolcreatedb, rolcanlogin, rolreplication FROM pg_roles ORDER BY rolname"],
}


def execute_query(dsn: str, queries: list[str]) -> list[dict]:
    rows: list[dict] = []
    with psycopg2.connect(dsn) as connection:
        with connection.cursor() as cursor:
            for query in queries:
                cursor.execute(query)
                fetched = cursor.fetchall()
                rows.extend(rows_to_json(fetched, cursor.description))
    return rows


def vault_postgres_dsn(secret_path: str, connection_key: str, *, environment: str | None = None, shard: str | None = None, version: str | None = None) -> str:
    secret = vault_secret(secret_path, version=version)
    record: dict = secret
    for key in (environment, shard, connection_key):
        if key:
            if not isinstance(record, dict) or key not in record:
                raise VaultError("Vault secret does not contain the requested PostgreSQL connection")
            record = record[key]

    try:
        host = record["host"]
        port = record.get("port", 5432)
        database = record["database"]
        username = record["username"]
        password = record["password"]
        return f"postgresql://{username}:{password}@{host}:{port}/{database}"
    except (KeyError, TypeError) as exc:
        raise VaultError("Vault PostgreSQL record requires host, database, username, and password") from exc


def write_comparison_reports(source_rows: list[dict], destination_rows: list[dict], label: str, output_dir: Path) -> Path:
    source_only, destination_only = row_diff(source_rows, destination_rows)
    report = output_dir / f"{label}_differences.txt"
    with report.open("w", encoding="utf-8") as handle:
        handle.write("Entries in source but not in destination:\n")
        for row in source_only:
            handle.write(f"{row}\n")
        handle.write("\nEntries in destination but not in source:\n")
        for row in destination_only:
            handle.write(f"{row}\n")
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Compare PostgreSQL metadata across two environments")
    parser.add_argument("--source-dsn", help="Source PostgreSQL DSN")
    parser.add_argument("--destination-dsn", help="Destination PostgreSQL DSN")
    parser.add_argument("--source-vault-path", help="Source Vault secret path")
    parser.add_argument("--destination-vault-path", help="Destination Vault secret path")
    parser.add_argument("--vault-environment", help="Optional Vault environment key")
    parser.add_argument("--vault-shard", help="Optional Vault shard key")
    parser.add_argument("--vault-connection-key", default="postgres", help="Vault connection record key")
    parser.add_argument("--vault-version", help="Vault KV secret version")
    parser.add_argument("--output-dir", type=Path, default=Path("output"), help="Directory for JSON snapshots and reports")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        source_dsn = args.source_dsn
        destination_dsn = args.destination_dsn

        if not source_dsn:
            if not args.source_vault_path:
                raise VaultError("Provide --source-dsn or --source-vault-path")
            source_dsn = vault_postgres_dsn(
                args.source_vault_path,
                args.vault_connection_key,
                environment=args.vault_environment,
                shard=args.vault_shard,
                version=args.vault_version,
            )

        if not destination_dsn:
            if not args.destination_vault_path:
                raise VaultError("Provide --destination-dsn or --destination-vault-path")
            destination_dsn = vault_postgres_dsn(
                args.destination_vault_path,
                args.vault_connection_key,
                environment=args.vault_environment,
                shard=args.vault_shard,
                version=args.vault_version,
            )

        args.output_dir.mkdir(parents=True, exist_ok=True)
        for label, queries in COMPARISON_QUERIES.items():
            source_rows = execute_query(source_dsn, queries)
            destination_rows = execute_query(destination_dsn, queries)
            write_json(args.output_dir / f"{label}_source.json", source_rows)
            write_json(args.output_dir / f"{label}_destination.json", destination_rows)
            report = write_comparison_reports(source_rows, destination_rows, label, args.output_dir)
            print(f"Wrote {report}")
        return 0
    except (VaultError, psycopg2.Error, ValueError) as exc:
        print(f"Error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
