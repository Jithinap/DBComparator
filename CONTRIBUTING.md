# Contributing

Thank you for helping improve DBComparator.

## Development Setup

```bash
python -m pip install -e ".[all,dev]"
pytest
```

## Guidelines

- Never commit passwords, Vault tokens, private endpoints, or generated comparison output.
- Keep database-specific scripts configurable rather than hard-coded.
- Prefer read-only queries unless a change explicitly requires otherwise.
- Add tests for parsing, diff logic, configuration handling, and error paths.
- Avoid printing credentials or authentication tokens.
- Use environment variables or prompt-independent configuration for secrets.
- Update the README when adding commands or changing arguments.

## Pull Requests

1. Create a topic branch.
2. Add or update tests.
3. Run `pytest` and, where possible, test against disposable database instances.
4. Describe the problem, implementation, security implications, and sample output.
5. Open an issue first for major architecture or breaking changes.
