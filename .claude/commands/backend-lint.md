Lint and format the backend workspace with Ruff.

```bash
just lint        # ruff check + ruff format --check (and eslint for the frontend)
just format      # ruff format + ruff check --fix
```

Without `just`, from `backend/`:

```bash
uv run ruff check .
uv run ruff format .
```

Configuration lives in `backend/pyproject.toml` (`[tool.ruff]`: line length 88, target py312, rules E4/E7/E9/F, `alembic/` excluded) and applies to every workspace member.
