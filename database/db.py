"""Database connection and initialization manager for SQLite."""
from __future__ import annotations

import os
from pathlib import Path
import aiosqlite
from config import settings
from utils.logger import logger


class Database:
    def __init__(self, db_path: str = settings.DATABASE_PATH):
        self.db_path = db_path
        self._schema_file = Path(__file__).parent / "schema.sql"

    async def initialize(self) -> None:
        """Initializes database schema and tables."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        schema_sql = self._schema_file.read_text(encoding="utf-8")

        async with aiosqlite.connect(self.db_path) as db:
            await db.executescript(schema_sql)
            await db.commit()
            logger.info(f"Database initialized successfully at {self.db_path}")

    def get_connection(self) -> aiosqlite.Connection:
        """Returns a new connection context."""
        return aiosqlite.connect(self.db_path)


db_manager = Database()
