import os
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

def get_pg_conn():
    """
    Use env vars or hardcode if you want.
    Example env vars:
      PGHOST, PGPORT, PGDATABASE, PGUSER, PGPASSWORD
    """
    return psycopg2.connect(
        host=os.getenv("PGHOST", "localhost"),
        port=int(os.getenv("PGPORT", "5432")),
        dbname=os.getenv("PGDATABASE", "postgres"),
        user=os.getenv("PGUSER", "postgres"),
        password=os.getenv("PGPASSWORD", "postgres"),
    )