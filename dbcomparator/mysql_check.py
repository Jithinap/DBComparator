from __future__ import annotations

import argparse
import json
from pathlib import Path

import mysql.connector


def load_test_data(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, list):
        raise ValueError("MySQL test data must be a JSON list")
    return data


def table_row_counts(host: str, username: str, password: str, database: str, tables: list[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    with mysql.connector.connect(host=host, user=username, password=password, database=database) as connection:
        with connection.cursor() as cursor:
            for table in tables:
                if not table.replace("_", "").replace(".", "").isalnum():
                    raise ValueError(f"Unsafe table identifier: {table}")
                cursor.execute(f"SELECT COUNT(*) FROM `{table.replace('`', '')}`")
                result = cursor.fetchone()
                counts[table] = int(result[0])
    return counts


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check configured MySQL table row counts")
    parser.add_argument("--config", type=Path, default=Path("testdata_for_mysql_scripting_db.json"))
    parser.add_argument("--fail-on-empty", action="store_true", help="Exit non-zero if a configured table is empty")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        test_data = load_test_data(args.config)
        failures: list[str] = []
        for record in test_data:
            tables = record["tablename"]
            if isinstance(tables, str):
                tables = [tables]
            counts = table_row_counts(
                record["hostname"],
                record["username"],
                record["password"],
                record.get("database", "scripting"),
                tables,
            )
            for table, count in counts.items():
                print(f"Table {table} contains {count} rows")
                if args.fail_on_empty and count == 0:
                    failures.append(table)
        if failures:
            print("Empty tables: " + ", ".join(failures))
            return 1
        return 0
    except (OSError, json.JSONDecodeError, KeyError, ValueError, mysql.connector.Error) as exc:
        print(f"Error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
