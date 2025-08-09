import os
from pathlib import Path


def _load_env_test():
    """Best-effort load of .env.test if python-dotenv is available."""
    try:
        from dotenv import load_dotenv  # type: ignore
    except Exception:
        return
    env_path = Path(__file__).resolve().parents[1] / ".env.test"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=False)


_load_env_test()

# Ensure runtime directory exists for sqlite file path, logs, etc.
Path("runtime").mkdir(parents=True, exist_ok=True)

# Set environment variables for tests (override if needed for compatibility)
os.environ["ENVIRONMENT"] = os.environ.get("ENVIRONMENT", "test")
# Provide DATABASE_URL in a JSON object format so Pydantic BaseSettings can parse
# the nested 'database' field correctly during import-time settings initialization.
os.environ["DATABASE_URL"] = (
    '{"database_url": "sqlite:///./runtime/test.db", '
    '"db_pool_size": 10, "db_max_overflow": 20, "db_pool_timeout": 30}'
)
# Provide SECURITY as JSON via the first env key in mapping (SECRET_KEY)
# so Pydantic can parse the nested SecuritySettings model during import.
os.environ["SECRET_KEY"] = (
    '{"secret_key": "test", '
    '"encryption_key": "0000000000000000000000000000000000000000000000000000000000000000", '
    '"jwt_secret_key": "test", "enable_https": false, "session_timeout": 3600}'
)
os.environ.setdefault(
    "ENCRYPTION_KEY",
    "0000000000000000000000000000000000000000000000000000000000000000",
)
os.environ.setdefault("JWT_SECRET_KEY", "test")
