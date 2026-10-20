import os
import pymysql
import pymysql.cursors
from contextlib import contextmanager
from config import Config

def get_connection():
    """Returns a direct raw PyMySQL connection with utf8mb4 and DictCursor."""
    return pymysql.connect(
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        user=Config.DB_USER,
        password=Config.DB_PASS,
        database=Config.DB_NAME,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False
    )

@contextmanager
def get_db_connection():
    """Context manager for raw database connection.
    Automatically commits on normal exit and rolls back on exception.
    Always closes the connection.
    """
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

@contextmanager
def get_db_cursor(commit=False):
    """Context manager yielding a DictCursor.
    Usage:
        with get_db_cursor(commit=True) as cursor:
            cursor.execute("UPDATE ... WHERE id = %s", (user_id,))
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            yield cursor
        if commit:
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def query_db(query, args=(), one=False):
    """Executes a parameterized SELECT query and returns dict or list of dicts.
    Strict Rule: All queries MUST be parameterized to prevent SQL injection.
    """
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, args)
            result = cursor.fetchall()
            return (result[0] if result else None) if one else result

def execute_db(query, args=(), lastrowid=False):
    """Executes a parameterized INSERT/UPDATE/DELETE query, commits transaction.
    Returns:
        lastrowid (int) if lastrowid=True, else affected row count (int).
    """
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, args)
            if lastrowid:
                return cursor.lastrowid
            return cursor.rowcount

def execute_many(query, args_list):
    """Executes a parameterized query across multiple tuples of args."""
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.executemany(query, args_list)
            return cursor.rowcount
