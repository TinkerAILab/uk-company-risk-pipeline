import duckdb

PARQUET_PATH = "data/raw/bulk/companies_2026-10-01.parquet"
SNAPSHOT_DATE = "2026-10-01"

con = duckdb.connect()
con.execute(f"CREATE VIEW companies AS SELECT * FROM '{PARQUET_PATH}'")

print("\n1. Companies by status")
print(con.sql("""
    SELECT companystatus, COUNT(*) AS companies
    FROM companies
    GROUP BY companystatus
    ORDER BY companies DESC
"""))

print("\n2. Live companies by year of incorporation (since 2016)")
print(con.sql("""
    SELECT year(try_strptime(incorporationdate, '%d/%m/%Y')) AS year,
           COUNT(*) AS companies
    FROM companies
    WHERE year(try_strptime(incorporationdate, '%d/%m/%Y')) >= 2016
    GROUP BY year
    ORDER BY year
"""))

print("\n3. Top 10 industries for companies formed in 2026")
print(con.sql("""
    SELECT siccodesictext_1 AS industry, COUNT(*) AS new_companies
    FROM companies
    WHERE year(try_strptime(incorporationdate, '%d/%m/%Y')) = 2026
    GROUP BY industry
    ORDER BY new_companies DESC
    LIMIT 10
"""))

print("\n4. Active companies with overdue accounts")
print(con.sql(f"""
    SELECT
        COUNT(*) AS active_companies,
        COUNT(*) FILTER (
            WHERE try_strptime(accountsnextduedate, '%d/%m/%Y') < DATE '{SNAPSHOT_DATE}'
        ) AS accounts_overdue,
        ROUND(100.0 * accounts_overdue / active_companies, 1) AS pct_overdue
    FROM companies
    WHERE companystatus = 'Active'
"""))