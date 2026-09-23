"""Database connection and initialization manager supporting Supabase PostgreSQL & SQLite."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, List, Optional, Dict
import aiosqlite
import asyncpg
from config import settings
from utils.logger import logger


class Database:
    """Unified Database Manager for Supabase PostgreSQL & SQLite."""

    def __init__(self):
        self.db_url = settings.DATABASE_URL or settings.SUPABASE_DB_URL or os.getenv("DATABASE_URL") or os.getenv("SUPABASE_DB_URL")
        self.db_path = settings.DATABASE_PATH
        self.is_postgres = bool(self.db_url and (self.db_url.startswith("postgres://") or self.db_url.startswith("postgresql://")))
        self.pool: Optional[asyncpg.Pool] = None
        
        self._schema_sqlite = Path(__file__).parent / "schema.sql"
        self._schema_pg = Path(__file__).parent / "schema_pg.sql"

    def _prepare_pg_url(self, url: str) -> str:
        """Normalizes postgres:// to postgresql:// for asyncpg."""
        if url.startswith("postgres://"):
            return "postgresql://" + url[len("postgres://"):]
        return url

    async def initialize(self) -> None:
        """Initializes database schema and connection pool."""
        if self.is_postgres:
            pg_url = self._prepare_pg_url(self.db_url)
            logger.info("Connecting to Supabase / PostgreSQL database...")
            try:
                # Create connection pool with SSL support for Supabase
                self.pool = await asyncpg.create_pool(
                    dsn=pg_url,
                    min_size=1,
                    max_size=10,
                    ssl="require",
                    timeout=30.0
                )
                
                # Run PostgreSQL schema
                schema_sql = self._schema_pg.read_text(encoding="utf-8")
                async with self.pool.acquire() as conn:
                    await conn.execute(schema_sql)
                logger.info("⚡ Connected to Supabase PostgreSQL & verified schema!")
            except Exception as e:
                logger.exception(f"Failed to connect to Supabase PostgreSQL: {e}. Falling back to SQLite...")
                self.is_postgres = False
                await self._init_sqlite()
        else:
            await self._init_sqlite()

    async def _init_sqlite(self) -> None:
        """Initializes local SQLite database."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        schema_sql = self._schema_sqlite.read_text(encoding="utf-8")
        async with aiosqlite.connect(self.db_path) as db:
            await db.executescript(schema_sql)
            await db.commit()
        logger.info(f"⚡ Local SQLite database initialized at {self.db_path}")

    def _format_query(self, query: str) -> str:
        """Translates ? placeholders to $1, $2, ... for PostgreSQL."""
        if not self.is_postgres:
            return query
        parts = query.split("?")
        if len(parts) <= 1:
            return query
        res = []
        for i, part in enumerate(parts[:-1]):
            res.append(part)
            res.append(f"${i + 1}")
        res.append(parts[-1])
        return "".join(res)

    async def execute(self, query: str, *args) -> None:
        """Executes an INSERT / UPDATE / DELETE statement."""
        if self.is_postgres and self.pool:
            pg_query = self._format_query(query)
            async with self.pool.acquire() as conn:
                await conn.execute(pg_query, *args)
        else:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(query, args)
                await db.commit()

    async def fetchrow(self, query: str, *args) -> Optional[Dict[str, Any]]:
        """Fetches a single row as a dictionary."""
        if self.is_postgres and self.pool:
            pg_query = self._format_query(query)
            async with self.pool.acquire() as conn:
                record = await conn.fetchrow(pg_query, *args)
                return dict(record) if record else None
        else:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute(query, args)
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def fetch(self, query: str, *args) -> List[Dict[str, Any]]:
        """Fetches multiple rows as a list of dictionaries."""
        if self.is_postgres and self.pool:
            pg_query = self._format_query(query)
            async with self.pool.acquire() as conn:
                records = await conn.fetch(pg_query, *args)
                return [dict(r) for r in records]
        else:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute(query, args)
                rows = await cursor.fetchall()
                return [dict(r) for r in rows]

    async def fetchval(self, query: str, *args) -> Any:
        """Fetches a single scalar value."""
        if self.is_postgres and self.pool:
            pg_query = self._format_query(query)
            async with self.pool.acquire() as conn:
                return await conn.fetchval(pg_query, *args)
        else:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(query, args)
                row = await cursor.fetchone()
                return row[0] if row else None

    async def close(self) -> None:
        """Closes connection pool if open."""
        if self.pool:
            await self.pool.close()
            logger.info("Database pool closed.")


db_manager = Database()
