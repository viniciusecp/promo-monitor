from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

engine = create_engine(
    settings.database_url,
    echo=settings.debug,
    connect_args={"check_same_thread": False},
)


@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


SessionLocal = sessionmaker(bind=engine, class_=Session, expire_on_commit=False)


# Colunas adicionadas após a criação inicial das tabelas. Como o projeto não usa
# Alembic e `create_all` não altera tabelas existentes, aplicamos um ADD COLUMN
# idempotente no startup para bancos SQLite já existentes.
_COLUMN_MIGRATIONS: dict[str, dict[str, str]] = {
    "product_interests": {"limiar_match": "FLOAT"},
    "promotion_matches": {
        "matched_keyword": "TEXT",
        "llm_motivo": "TEXT",
        "llm_aprovado": "BOOLEAN DEFAULT 1",
    },
}


def ensure_columns() -> None:
    from sqlalchemy import text

    with engine.begin() as conn:
        for table, columns in _COLUMN_MIGRATIONS.items():
            existing = {
                row[1] for row in conn.execute(text(f"PRAGMA table_info({table})"))
            }
            for name, ddl_type in columns.items():
                if name not in existing:
                    conn.execute(
                        text(f"ALTER TABLE {table} ADD COLUMN {name} {ddl_type}")
                    )


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
