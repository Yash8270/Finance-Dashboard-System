import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from dotenv import load_dotenv

load_dotenv()

# --- Read individual credentials from .env ---
HOST     = os.getenv("HOST")
PORT     = os.getenv("DB_PORT", "4000")
USER     = os.getenv("DB_USER")
PASSWORD = os.getenv("PASSWORD")
DATABASE = os.getenv("DATABASE")

# --- Build connection URL for TiDB Cloud (MySQL-compatible) ---
DATABASE_URL = (
    f"mysql+pymysql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DATABASE}"
)

# --- TiDB Cloud requires SSL ---
connect_args = {
    "ssl": {
        "ca": None          # TiDB public CA is trusted by default via PyMySQL
    }
}

engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args=connect_args,

    # --- Connection Pool Settings for TiDB Cloud ---

    # Ping the connection before using it — if it's dead, get a fresh one
    # This is the primary fix for "MySQL server has gone away"
    pool_pre_ping=True,

    # Recycle connections older than 30 minutes
    # TiDB Cloud free tier closes idle connections around 30-60 minutes
    pool_recycle=1800,

    # Max connections kept open in the pool
    pool_size=5,

    # Extra connections allowed beyond pool_size under heavy load
    max_overflow=10,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()