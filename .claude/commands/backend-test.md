Run the backend test suites.

```bash
just test-backend        # travel_common + core_api + ai_api
just test-core           # core_api only — needs PostgreSQL; creates <DB_NAME>_test and empties it per test
just test-ai             # ai_api only — no network, no API key (FakeProvider + MockTransport)
just test-common
```

A single file or test, from the package directory:

```bash
cd backend/services/core_api
uv run pytest tests/api/test_trips.py::test_other_users_trip_is_forbidden -v
```

Notes:

- Tests are async by default (`asyncio_mode = "auto"`) and use `--import-mode=importlib`; never import `tests.*` across packages.
- Test doubles for `ai_api` live in `ai_api/testing.py`.
