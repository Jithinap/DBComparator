# DBComparator

DBComparator is an open-source Python toolkit for comparing database environments and identifying configuration drift across Oracle, PostgreSQL, and MySQL.

## Why This Project Exists

Database releases and environment promotions can cause databases that are expected to be the same to drift apart. A missing table, changed index, extra role, different constraint, or new database object can be difficult to detect manually, especially across multiple environments and shards.

DBComparator helps solve that problem by:

- Running a consistent set of read-only metadata queries against two databases.
- Exporting the query results as JSON snapshots.
- Comparing the snapshots and generating a readable difference report.
- Helping teams verify environments before, during, or after a deployment.
- Covering multiple database platforms through focused, command-line utilities.

## What You Can Compare

| Database | Area |
|---|---|
| Oracle configuration database | PLSQL objects, tables, constraints, constrained columns, and database links |
| Oracle transaction database | PLSQL objects, tables, constraints, constrained columns, and database links |
| Oracle data warehouse | PLSQL objects, tables, constraints, constrained columns, and database links |
| PostgreSQL | Tables, columns, indexes, functions, database objects, users, roles, ownership, and permissions |
| MySQL | Row counts for tables listed in a test configuration |

The tools are intended for **diagnosis and comparison**. They do not modify database schemas or data.

## Repository Structure

```text
DBComparator/
├── dbcomparator/
│   ├── comparison.py
│   ├── mysql_check.py
│   ├── oracle.py
│   ├── postgres.py
│   └── vault.py
├── tests/
├── CONTRIBUTING.md
├── LICENSE
├── pyproject.toml
└── requirements.txt
```

## Requirements

- Python 3.9 or newer
- Network access to the databases being compared
- Database credentials with permission to run read-only metadata queries
- Database-specific Python drivers

Install dependencies for all supported platforms:

```bash
python -m pip install -e ".[all,dev]"
```

Install only the drivers needed for a platform:

```bash
python -m pip install -e ".[postgres]"
python -m pip install -e ".[oracle]"
python -m pip install -e ".[mysql]"
```

## Security and Configuration

Never commit passwords, Vault tokens, database connection strings, private hostnames, or generated reports containing sensitive metadata.

For Vault authentication, set a token:

```bash
export VAULT_ADDR='https://vault.example.com:8200'
export VAULT_TOKEN='replace-me'
```

Alternatively, configure the Vault authentication mount and credentials:

```bash
export VAULT_ADDR='https://vault.example.com:8200'
export VAULT_AUTH_PATH='auth/userpass/login'
export VAULT_USERNAME='your-username'
export VAULT_PASSWORD='replace-me'
```

A direct database DSN can be used without Vault. Vault mode accepts generic environment, shard, and connection keys, so users control the secret layout rather than an organization-specific schema.

## Quick Start with Installed Commands

### PostgreSQL

Use direct DSNs:

```bash
dbcompare-postgres \
  --source-dsn "postgresql://user:password@source-host:5432/database" \
  --destination-dsn "postgresql://user:password@destination-host:5432/database" \
  --output-dir output/postgres
```

Or configure Vault secrets. Each source or destination secret can use an environment, shard, and connection-key hierarchy:

```bash
dbcompare-postgres \
  --source-vault-path "secret/data/postgres/source" \
  --destination-vault-path "secret/data/postgres/destination" \
  --vault-environment production \
  --vault-shard shard-a \
  --vault-connection-key postgres \
  --output-dir output/postgres
```

### Oracle

```bash
dbcompare-oracle \
  --source-dsn "user/password@source-host:1521/service" \
  --destination-dsn "user/password@destination-host:1521/service" \
  --output-dir output/oracle
```

Vault-backed sharded databases:

```bash
dbcompare-oracle \
  --source-vault-path "secret/data/oracle/source" \
  --destination-vault-path "secret/data/oracle/destination" \
  --vault-environment production \
  --vault-shard shard-a \
  --vault-connection-key oracle \
  --output-dir output/oracle
```

### MySQL

```bash
cp testdata_for_mysql_scripting_db.example.json testdata_for_mysql_scripting_db.json
# Edit the copy; never commit it if it contains credentials.
dbcompare-mysql --config testdata_for_mysql_scripting_db.json
```

Use `--fail-on-empty` to return a failing exit code when a configured table is empty.

## Generated Output

Comparators write JSON snapshots and text reports to the selected `--output-dir`.

Typical output includes:

- `<check>_source.json` — source database query data.
- `<check>_destination.json` — destination database query data.
- `<check>_differences.txt` — entries found in one database but not the other.

Run comparisons against disposable or authorized test databases first, and review reports before using them in a deployment decision.

## Known Limitations

- Vault secret schemas are configurable but must be consistent between source and destination.
- Oracle and PostgreSQL queries use broad metadata catalogs and may need tuning for a specific schema ownership model.
- Database differences are compared by complete normalized row values.
- Integration tests for live database engines are not included.
- The MySQL check requires a readable JSON configuration file.

## Contributing

Contributions are welcome. Useful areas include:

- Generalizing scripts so they support configurable database and Vault endpoints.
- Replacing hard-coded environments and internal infrastructure names with example configuration.
- Adding cross-platform setup instructions and dependency management.
- Adding unit tests and mocked database connections.
- Improving consistent JSON output and difference reporting.
- Supporting additional comparison categories or database platforms.
- Replacing duplicate Oracle logic with reusable modules.
- Documenting environment-specific setup in public, sanitized examples.

Before submitting a pull request:

1. Create a topic branch.
2. Keep organization-specific credentials and names out of the change.
3. Add or update tests where practical.
4. Run the affected script against a safe test database.
5. Describe the problem, implementation, and sample output in the pull request.

Please open an issue before large refactors or changes that may affect existing workflows.

## License

This project is licensed under the [MIT License](LICENSE).
