from __future__ import annotations

import argparse
from pathlib import Path

import oracledb

from .comparison import row_diff, rows_to_json, write_json
from .vault import VaultError, vault_secret


DEFAULT_QUERIES = {
    "tables": ["SELECT owner, table_name FROM all_tables ORDER BY owner, table_name"],
    "constraints": ["SELECT owner, table_name, constraint_name, constraint_type FROM all_constraints ORDER BY owner, table_name, constraint_name"],
    "constraint_columns": ["SELECT owner, table_name, constraint_name, column_name FROM all_cons_columns ORDER BY owner, table_name, constraint_name, column_name"],
    "database_links": ["SELECT owner, db_link, username FROM all_db_links ORDER BY owner, db_link"],
}


def execute_query(dsn: str, queries: list[str]) -> list[dict]:
    rows: list[dict] = []
    with oracledb.connect(dsn) as connection:
        with connection.cursor() as cursor:
            for query in queries:
                cursor.execute(query)
                fetched = cursor.fetchall()
                rows.extend(rows_to_json(fetched, cursor.description))
    return rows


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Compare Oracle metadata across two environments")
    parser.add_argument("--source-dsn", help="Source Oracle DSN")
    parser.add_argument("--destination-dsn", help="Destination Oracle DSN")
    parser.add_argument("--source-vault-path", help="Source Vault secret path")
    parser.add_argument("--destination-vault-path", help="Destination Vault secret path")
    parser.add_argument("--vault-environment", help="Optional Vault environment key")
    parser.add_argument("--vault-shard", help="Optional Vault shard key")
    parser.add_argument("--vault-connection-key", default="oracle", help="Vault connection record key")
    parser.add_argument("--vault-version", help="Vault KV secret version")
    parser.add_argument("--output-dir", type=Path, default=Path("output"), help="Directory for JSON snapshots and reports")
    return parser


def _vault_oracle_dsn(secret_path: str, connection_key: str, *, environment: str | None = None, shard: str | None = None, version: str | None = None) -> str:
    secret = vault_secret(secret_path, version=version)
    record: dict = secret
    for key in (environment, shard, connection_key):
        if key:
            if not isinstance(record, dict) or key not in record:
                raise VaultError("Vault secret does not contain the requested Oracle connection")
            record = record[key]

    try:
        return f"{record['username']}/{record['password']}@{record['host']}:{record.get('port', 1521)}/{record['service_name']}"
    except (KeyError, TypeError) as exc:
        raise VaultError("Vault Oracle record requires host, service_name, username, and password") from exc


def write_report(source_rows: list[dict], destination_rows: list[dict], label: str, output_dir: Path) -> Path:
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


def main() -> int:
    args = build_parser().parse_args()
    try:
        source_dsn = args.source_dsn
        destination_dsn = args.destination_dsn

        if not source_dsn:
            if not args.source_vault_path:
                raise VaultError("Provide --source-dsn or --source-vault-path")
            source_dsn = _vault_oracle_dsn(
                args.source_vault_path,
                args.vault_connection_key,
                environment=args.vault_environment,
                shard=args.vault_shard,
                version=args.vault_version,
            )

        if not destination_dsn:
            if not args.destination_vault_path:
                raise VaultError("Provide --destination-dsn or --destination-vault-path")
            destination_dsn = _vault_oracle_dsn(
                args.destination_vault_path,
                args.vault_connection_key,
                environment=args.vault_environment,
                shard=args.vault_shard,
                version=args.vault_version,
            )

        args.output_dir.mkdir(parents=True, exist_ok=True)
        for label, queries in DEFAULT_QUERIES.items():
            source_rows = execute_query(source_dsn, queries)
            destination_rows = execute_query(destination_dsn, queries)
            write_json(args.output_dir / f"{label}_source.json", source_rows)
            write_json(args.output_dir / f"{label}_destination.json", destination_rows)
            report = write_report(source_rows, destination_rows, label, args.output_dir)
            print(f"Wrote {report}")
        return 0
    except (VaultError, oracledb.Error, ValueError) as exc:
        print(f"Error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
