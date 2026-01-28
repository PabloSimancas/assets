import csv
import os
from sqlalchemy import create_engine, text

# Get DB URL from env
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    # Fallback to local test DB or specific EasyPanel URL only if needed for testing
    print("DATABASE_URL is not set. Please set it to connect to the DB.")
    exit(1)

print(f"Connecting to DB...")
engine = create_engine(DATABASE_URL)

def import_csv(file_path, table_name, pk_column):
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        
    print(f"Importing {len(rows)} rows into {table_name}...")
    
    with engine.connect() as conn:
        success_count = 0
        error_count = 0
        for row in rows:
            # Clean up keys (remove BOM if any)
            clean_row = {k.strip(): v for k, v in row.items()}
            
            # Construct columns
            cols = ', '.join(f'"{k}"' for k in clean_row.keys())
            param_placeholders = ', '.join(f':{k}' for k in clean_row.keys())
            
            # We explicitly use OVERRIDING SYSTEM VALUE because these tables have IDENTITY columns
            sql = f"""
                INSERT INTO {table_name} ({cols}) 
                OVERRIDING SYSTEM VALUE 
                VALUES ({param_placeholders})
                ON CONFLICT ("{pk_column}") DO NOTHING;
            """
            
            try:
                conn.execute(text(sql), clean_row)
                success_count += 1
            except Exception as e:
                print(f"Error inserting row ID {clean_row.get(pk_column)}: {e}")
                error_count += 1
        
        conn.commit()
    print(f"Finished {table_name}. Success: {success_count}, Ignored/Errors: {error_count}")

# Adjust paths assuming script is run from /app/
# Run Main
import_csv("example_data/run_main.csv", "crypto_forwards.run_main", "run_main_id")

# Run Details
import_csv("example_data/run_details.csv", "crypto_forwards.run_details", "detail_id")

# Update sequences
# Since we manually inserted IDs, the sequences for the IDENTITY columns might be out of sync.
# We should reset them to the max value.
with engine.connect() as conn:
    print("Resetting sequences...")
    try:
        conn.execute(text("SELECT setval(pg_get_serial_sequence('crypto_forwards.run_main', 'run_main_id'), COALESCE(MAX(run_main_id), 1)) FROM crypto_forwards.run_main;"))
        conn.execute(text("SELECT setval(pg_get_serial_sequence('crypto_forwards.run_details', 'detail_id'), COALESCE(MAX(detail_id), 1)) FROM crypto_forwards.run_details;"))
        conn.commit()
        print("Sequences reset successfully.")
    except Exception as e:
        print(f"Error resetting sequences: {e}")
