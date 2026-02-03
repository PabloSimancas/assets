"""
Quick diagnostic script to check if gold views exist
"""
import os
from sqlalchemy import create_engine, text, inspect

DATABASE_URL = os.environ.get("DATABASE_URL", "")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
inspector = inspect(engine)

print("=" * 60)
print("DATABASE DIAGNOSTIC")
print("=" * 60)

# Check Gold schema
print("\n### GOLD SCHEMA ###")
try:
    gold_tables = inspector.get_table_names(schema='gold')
    print(f"Tables in gold schema: {gold_tables}")
    
    # Check for views
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT table_name, table_type 
            FROM information_schema.tables 
            WHERE table_schema = 'gold'
        """))
        print("\nAll objects in gold schema:")
        for row in result:
            print(f"  - {row[0]} ({row[1]})")
except Exception as e:
    print(f"Error checking gold schema: {e}")

# Check Silver schema for session_timestamp column
print("\n### SILVER SCHEMA ###")
try:
    if 'hyperliquid_aggregated' in inspector.get_table_names(schema='silver'):
        columns = inspector.get_columns('hyperliquid_aggregated', schema='silver')
        column_names = [c['name'] for c in columns]
        print(f"Columns in silver.hyperliquid_aggregated:")
        for col in column_names:
            print(f"  - {col}")
        
        if 'session_timestamp' in column_names:
            print("\n✅ session_timestamp column EXISTS")
        else:
            print("\n❌ session_timestamp column MISSING")
    else:
        print("silver.hyperliquid_aggregated table doesn't exist")
except Exception as e:
    print(f"Error checking silver schema: {e}")

# Check Bronze schema
print("\n### BRONZE SCHEMA ###")
try:
    bronze_tables = inspector.get_table_names(schema='bronze')
    print(f"Tables in bronze schema: {bronze_tables}")
    
    if 'hyperliquid_positions' in bronze_tables:
        columns = inspector.get_columns('hyperliquid_positions', schema='bronze')
        column_names = [c['name'] for c in columns]
        if 'session_timestamp' in column_names:
            print("✅ bronze.hyperliquid_positions has session_timestamp")
        else:
            print("❌ bronze.hyperliquid_positions MISSING session_timestamp")
except Exception as e:
    print(f"Error checking bronze schema: {e}")

print("\n" + "=" * 60)
