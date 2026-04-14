import os
from pathlib import Path
from tempfile import gettempdir

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool


def _resolve_database_url() -> str:
    raw_database_url = os.getenv("DATABASE_URL")
    if not raw_database_url:
        default_db_path = Path(gettempdir()) / "ai_interview_prep" / "ai_interview_prep.db"
        try:
            default_db_path.parent.mkdir(parents=True, exist_ok=True)
            return f"sqlite:///{default_db_path.as_posix()}"
        except OSError:
            return "sqlite:///:memory:"

    if raw_database_url.startswith("sqlite:///") and raw_database_url != "sqlite:///:memory:":
        sqlite_path = raw_database_url.replace("sqlite:///", "", 1)
        path_obj = Path(sqlite_path).expanduser()
        if not path_obj.is_absolute():
            path_obj = (Path.cwd() / path_obj).resolve()
        else:
            path_obj = path_obj.resolve()
        try:
            path_obj.parent.mkdir(parents=True, exist_ok=True)
            return f"sqlite:///{path_obj.as_posix()}"
        except OSError:
            fallback_path = Path(gettempdir()) / "ai_interview_prep" / "ai_interview_prep.db"
            try:
                fallback_path.parent.mkdir(parents=True, exist_ok=True)
                return f"sqlite:///{fallback_path.as_posix()}"
            except OSError:
                return "sqlite:///:memory:"

    return raw_database_url


DATABASE_URL = _resolve_database_url()

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine_kwargs = {"connect_args": connect_args, "pool_pre_ping": True}
if DATABASE_URL == "sqlite:///:memory:":
    engine_kwargs["poolclass"] = StaticPool

engine = create_engine(DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
