import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


def _load_dotenv() -> None:
    base_dir = Path(__file__).resolve().parent.parent
    env_path = base_dir / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def _read_int(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default

    try:
        return int(raw_value)
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    app_name: str
    app_version: str
    app_description: str
    database_path: Path
    default_page_size: int
    max_page_size: int


@lru_cache
def get_settings() -> Settings:
    _load_dotenv()
    base_dir = Path(__file__).resolve().parent.parent
    raw_database_path = Path(os.getenv("DATABASE_PATH", "tickets.db"))
    database_path = (
        raw_database_path.resolve()
        if raw_database_path.is_absolute()
        else (base_dir / raw_database_path).resolve()
    )

    return Settings(
        app_name=os.getenv("APP_NAME", "Ticket Management API"),
        app_version=os.getenv("APP_VERSION", "1.1.0"),
        app_description=os.getenv(
            "APP_DESCRIPTION",
            "A production-ready FastAPI service for tracking support tickets.",
        ),
        database_path=database_path,
        default_page_size=max(1, _read_int("DEFAULT_PAGE_SIZE", 20)),
        max_page_size=max(1, _read_int("MAX_PAGE_SIZE", 100)),
    )
