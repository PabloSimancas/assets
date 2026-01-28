
import pandas as pd
import os
from sqlalchemy import text
from src.infrastructure.database.session import engine

def import_csv_data():
    base_path = os.path.dirname(os.path.abspath(__file__))
    # assuming script is in src/scripts, so we go up two levels to root, then import_data
    # wait, container /app is root. Script in /app/src/scripts
    # files in /app/import_data
    
    csv_dir = "/app/import_data"
    main_file = os.path.join(csv_dir, "run_main.csv")
    details_file = os.path.join(csv_dir, "run_details.csv")

    if not os.path.exists(main_file) or not os.path.exists(details_file):
        print("CSV files not found in /app/import_data")
        return

    print("Reading CSVs...")
    # pandas read_csv handles quotes automatically
    df_main = pd.read_csv(main_file)
    df_details = pd.read_csv(details_file)

    print(f"Loaded {len(df_main)} main rows and {len(df_details)} detail rows.")

    with engine.begin() as conn:
        # Import Main
        # We want to preserve IDs to keep relationships valid. 
        # But we need to handle potential conflicts if IDs already exist?
        # The user said "run main have just 2 runs". Those likely have IDs 1 and 2 (or whatever serial gave them).
        # The CSV IDs seem to start at 9. So unlikely to conflict if serial started at 1.
        
        print("Importing run_main...")
        # Check max existing ID
        res = conn.execute(text("SELECT MAX(run_main_id) FROM crypto_forwards.run_main"))
        max_id = res.scalar() or 0
        print(f"Current max run_main_id: {max_id}")

        count_main = 0
        for _, row in df_main.iterrows():
            # Check if exists
            exists = conn.execute(
                text("SELECT 1 FROM crypto_forwards.run_main WHERE run_main_id = :id"),
                {"id": row["run_main_id"]}
            ).scalar()
            
            if not exists:
                conn.execute(
                    text("""
                        INSERT INTO crypto_forwards.run_main 
                        (run_main_id, asset, ran_at_utc, source, spot_price)
                        OVERRIDING SYSTEM VALUE
                        VALUES (:id, :asset, :ran_at, :source, :spot)
                    """),
                    {
                        "id": row["run_main_id"],
                        "asset": row["asset"],
                        "ran_at": row["ran_at_utc"],
                        "source": row["source"],
                        "spot": row["spot_price"]
                    }
                )
                count_main += 1
        
        print(f"Inserted {count_main} new runs.")

        print("Importing run_details...")
        count_details = 0
        for _, row in df_details.iterrows():
            # Check if main exists (referential integrity)
            main_exists = conn.execute(
                text("SELECT 1 FROM crypto_forwards.run_main WHERE run_main_id = :id"),
                {"id": row["run_main_id"]}
            ).scalar()

            if main_exists:
                # Check duplicate detail
                det_exists = conn.execute(
                    text("SELECT 1 FROM crypto_forwards.run_details WHERE detail_id = :id"),
                    {"id": row["detail_id"]}
                ).scalar()
                
                if not det_exists:
                    conn.execute(
                        text("""
                            INSERT INTO crypto_forwards.run_details
                            (detail_id, run_main_id, expiry_date, days_to_expiry, future_price, open_interest, spot_price, premium_pct, annualized_pct, curve, instrument_name)
                            OVERRIDING SYSTEM VALUE
                            VALUES (:did, :mid, :exp_date, :days, :fut, :oi, :spot, :prem, :ann, :curve, :inst)
                        """),
                        {
                            "did": row["detail_id"],
                            "mid": row["run_main_id"],
                            "exp_date": row["expiry_date"],
                            "days": row["days_to_expiry"],
                            "fut": row["future_price"],
                            "oi": row["open_interest"],
                            "spot": row["spot_price"],
                            "prem": row["premium_pct"],
                            "ann": row["annualized_pct"],
                            "curve": row["curve"],
                            "inst": row["instrument_name"]
                        }
                    )
                    count_details += 1
            else:
                 print(f"Skipping detail {row['detail_id']} because main {row['run_main_id']} missing.")

        print(f"Inserted {count_details} details.")

        # Update sequences
        print("Updating sequences...")
        conn.execute(text("SELECT setval('crypto_forwards.run_main_run_main_id_seq', (SELECT MAX(run_main_id) FROM crypto_forwards.run_main))"))
        conn.execute(text("SELECT setval('crypto_forwards.run_details_detail_id_seq', (SELECT MAX(detail_id) FROM crypto_forwards.run_details))"))
        
    print("Import complete.")

if __name__ == "__main__":
    import_csv_data()
