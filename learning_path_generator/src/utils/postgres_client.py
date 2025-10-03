import json
import logging
import os
import time
import uuid
from contextlib import contextmanager
from typing import Dict, Iterable, List, Sequence

import psycopg2
from psycopg2 import pool
from psycopg2.extras import execute_values

logger = logging.getLogger(__name__)


class PostgresClient:
    def __init__(self) -> None:
        host = os.getenv("POSTGRES_HOST")
        database = os.getenv("POSTGRES_DB", "postgres")
        user = os.getenv("POSTGRES_USER", "postgres")
        password = os.getenv("POSTGRES_PASSWORD")
        port = int(os.getenv("POSTGRES_PORT", "5432"))
        if not host or not password:
            raise ValueError("POSTGRES_HOST and POSTGRES_PASSWORD environment variables are required")
        min_conn = int(os.getenv("POSTGRES_POOL_MIN", "1"))
        max_conn = int(os.getenv("POSTGRES_POOL_MAX", "5"))
        ssl_enabled = os.getenv("DB_SSL", "false").lower() == "true"
        connection_kwargs = {
            "host": host,
            "port": port,
            "dbname": database,
            "user": user,
            "password": password,
        }
        if ssl_enabled:
            connection_kwargs["sslmode"] = "verify-full"
            ca_path = os.getenv("DB_CA_PATH")
            if ca_path:
                connection_kwargs["sslrootcert"] = ca_path
        self._pool = pool.SimpleConnectionPool(min_conn, max_conn, **connection_kwargs)

    @contextmanager
    def connection(self):
        conn = self._pool.getconn()
        try:
            yield conn
        finally:
            self._pool.putconn(conn)

    def persist_learning_path(
        self,
        user_id: str,
        path_data: Dict[str, str],
        course_nodes: Sequence[Dict[str, str | int]],
    ) -> str:
        path_id = path_data.get("path_id", str(uuid.uuid4()))
        persisted_path_id = path_id
        with self.connection() as conn:
            start = time.time()
            try:
                conn.autocommit = False
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO user_learning_paths (path_id, user_id, name, description, status, target_hours_per_week)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        RETURNING path_id
                        """,
                        (
                            path_id,
                            user_id,
                            path_data.get("name"),
                            path_data.get("description"),
                            path_data.get("status", "active"),
                            path_data.get("target_hours_per_week", 5),
                        ),
                    )
                    persisted_path_id = cur.fetchone()[0]
                self._insert_course_progress(conn, user_id, persisted_path_id, course_nodes)
                conn.commit()
            except Exception as exc:  # noqa: BLE001
                conn.rollback()
                logger.error(json.dumps({"event": "postgres_persist_failed", "error": str(exc)}))
                raise
            finally:
                elapsed_ms = int((time.time() - start) * 1000)
                logger.info(
                    json.dumps(
                        {
                            "event": "path_persisted",
                            "path_id": persisted_path_id,
                            "courses_count": len(course_nodes),
                            "postgres_time_ms": elapsed_ms,
                        }
                    )
                )
            return persisted_path_id

    def _insert_course_progress(
        self,
        conn,
        user_id: str,
        path_id: str,
        course_nodes: Sequence[Dict[str, str | int]],
    ) -> None:
        payload = []
        for sequence_order, node in enumerate(course_nodes, start=1):
            progress_id = str(uuid.uuid4())
            payload.append(
                (
                    progress_id,
                    user_id,
                    path_id,
                    node.get("course_id"),
                    "not_started",
                    float(0.0),
                    sequence_order,
                )
            )
        with conn.cursor() as cur:
            execute_values(
                cur,
                """
                INSERT INTO course_progress (progress_id, user_id, path_id, mongodb_course_id, status, progress_percentage, sequence_order)
                VALUES %s
                ON CONFLICT (path_id, mongodb_course_id) DO NOTHING
                """,
                payload,
            )


_postgres_client: PostgresClient | None = None


def get_postgres_client() -> PostgresClient:
    global _postgres_client
    if _postgres_client is None:
        _postgres_client = PostgresClient()
    return _postgres_client
