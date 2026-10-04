import duckdb

SNAPSHOT_DATE = "2026-10-01"
CSV_PATH = "data/raw/bulk/*.csv"
PARQUET_PATH = f"data/raw/bulk/companies_{SNAPSHOT_DATE}.parquet"

con = duckdb.connect()

# Read the CSV as text (no guessing types in the raw layer) and save as Parquet
con.execute(f"""
    COPY (
        SELECT * FROM read_csv('{CSV_PATH}', header = true, all_varchar = true, normalize_names = true)
    )
    TO '{PARQUET_PATH}' (FORMAT parquet)
""")

row_count = con.sql(f"SELECT COUNT(*) FROM '{PARQUET_PATH}'").fetchone()[0]
print(f"Rows: {row_count:,}")

print("\nColumns:")
for column in con.sql(f"DESCRIBE SELECT * FROM '{PARQUET_PATH}'").fetchall():
    print(column[0])