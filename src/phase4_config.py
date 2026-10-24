"""Phase 4: database configuration and connection with clear error messages.

Credentials never live in code. They come from the standard PostgreSQL environment variables
(PGHOST, PGPORT, PGDATABASE, PGUSER, PGPASSWORD), optionally read from a `.env` file in the project root.
Variables already set in the environment always win over `.env`.
"""
from pathlib import Path
import os

import psycopg2

REQUIRED_VARS = ["PGHOST", "PGPORT", "PGDATABASE", "PGUSER"]


class DatabaseConfigError(RuntimeError):
    """The environment is not set up (missing variables, server unreachable, login refused).
    This is an ENVIRONMENT problem, not a failure of the pipeline itself."""


def find_project_root(start: Path | None = None) -> Path:
    start = (start or Path.cwd()).resolve()
    for folder in [start, *start.parents]:
        if (folder / "data" / "processed").is_dir() and (folder / "sql").is_dir():
            return folder
    here = Path(__file__).resolve().parents[1]
    if (here / "data" / "processed").is_dir():
        return here
    raise FileNotFoundError("Could not find the project root (a folder containing data/processed and sql).")


def load_dotenv(path: Path) -> list[str]:
    """Read KEY=VALUE lines from .env without overriding variables that are already set.
    Returns the names that were set from the file (values are never printed)."""
    loaded = []
    if not path.is_file():
        return loaded
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value
            loaded.append(key)
    return loaded


def describe_target(dbname: str | None = None) -> str:
    """Connection target without the password, for messages and logs."""
    return (f"postgresql://{os.environ.get('PGUSER', '?')}@{os.environ.get('PGHOST', '?')}:"
            f"{os.environ.get('PGPORT', '?')}/{dbname or os.environ.get('PGDATABASE', '?')}")


def connect(dbname: str | None = None, root: Path | None = None):
    """Open a psycopg2 connection using PG* variables (and .env). Raises DatabaseConfigError with a
    plain-language explanation when the environment is the problem."""
    load_dotenv((root or find_project_root()) / ".env")
    missing = [v for v in REQUIRED_VARS if not os.environ.get(v)]
    if missing:
        raise DatabaseConfigError(
            f"Missing database settings: {', '.join(missing)}. Copy .env.example to .env and fill it in, "
            "or set these environment variables. See sql/README.md.")
    target = describe_target(dbname)
    try:
        conn = psycopg2.connect(dbname=dbname or os.environ["PGDATABASE"], connect_timeout=10,
                                application_name="layoffs_phase4", client_encoding="UTF8")
    except psycopg2.OperationalError as exc:
        msg = str(exc).strip().splitlines()[0] if str(exc).strip() else repr(exc)
        if "password authentication failed" in msg or "no password supplied" in msg:
            hint = "The server refused the login: check PGUSER and PGPASSWORD."
        elif "does not exist" in msg:
            hint = "The server is running but this database does not exist: create it first (sql/README.md, step 2)."
        elif "Connection refused" in msg or "could not connect" in msg or "timeout" in msg.lower():
            hint = "No PostgreSQL server answered: is it installed and running, and are PGHOST/PGPORT right?"
        else:
            hint = "See the server message above."
        raise DatabaseConfigError(f"Could not connect to {target}. {hint}\nServer said: {msg}") from None
    return conn
