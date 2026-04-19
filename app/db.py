import logging
import psycopg2
from psycopg2 import pool, OperationalError
from .config import DB_HOST, DB_NAME, DB_USER, DB_PASSWORD, DB_PORT

logger = logging.getLogger(__name__)

_pool: pool.ThreadedConnectionPool | None = None


def init_pool():
    global _pool
    _pool = pool.ThreadedConnectionPool(
        minconn=1,
        maxconn=10,
        host=DB_HOST,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        port=DB_PORT,
    )
    logger.info("DB connection pool initialised (%s/%s)", DB_HOST, DB_NAME)


def get_connection():
    if _pool is None:
        raise OperationalError("Connection pool not initialised. Call init_pool() first.")
    conn = _pool.getconn()
    try:
        yield conn
    finally:
        _pool.putconn(conn)
