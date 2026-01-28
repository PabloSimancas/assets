import os
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

# ---------- your function get_data_BTC() is assumed to exist ----------
# It returns: main (dict), details (list[dict])



def save_to_db(main: dict, details: list[dict], conn):
    """
    Inserts 1 row in run_main and N rows in run_details in one transaction.
    Returns run_main_id.
    """
   
    with conn:
        with conn.cursor() as cur:
            # 1) insert main
            cur.execute(
                """
                INSERT INTO cryptodata.run_main (asset, ran_at_utc, source, spot_price)
                VALUES (%s, %s, %s, %s)
                RETURNING run_main_id
                """,
                (
                    main.get("asset"),
                    main.get("ran_at_utc"),
                    main.get("source"),
                    main.get("spot_price"),
                ),
            )
            run_main_id = cur.fetchone()[0]

            # 2) prepare rows
            # Build rows with run_main_id injected
            rows = [
                (run_main_id, *row)
                for row in details
            ]

            # 3) bulk insert details
            execute_values(
                cur,
                """
                INSERT INTO cryptodata.run_details
                (run_main_id, expiry_str, expiry_date, days_to_expiry, future_price, open_interest, spot_price,
                 premium_pct, annualized_pct, curve, instrument_name)
                VALUES %s
                """,
                rows,
                page_size=200
            )

            return run_main_id

def main_save_to_db(main: dict, details: list[tuple],conn):
    
    if not main:
        print("No data to save.")
        return
 
    try:
        run_id = save_to_db(main, details, conn)
        print(f"Saved run_main_id={run_id} with {len(details)} detail rows.")
    finally:
        conn.close()


