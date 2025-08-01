import psycopg2
from psycopg2 import OperationalError
from .config import DB_HOST, DB_NAME, DB_USER, DB_PASSWORD, DB_PORT

def get_connection():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT
        )
        print(f"Connected to DB: {DB_HOST}/{DB_NAME} as {DB_USER}")
        return conn
    except OperationalError as e:
        print(f"Error connecting to the database: {e}")
        # Optionally, raise the error again or return None
        raise

