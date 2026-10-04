import duckdb

SNAPSHOT_DATE = "2026-10-01"
RAW_PATH = f"data/raw/bulk/companies_{SNAPSHOT_DATE}.parquet"
CLEAN_PATH = f"data/clean/companies_clean_{SNAPSHOT_DATE}.parquet"

con = duckdb.connect()
con.execute("CREATE OR REPLACE MACRO to_date(s) AS try_strptime(s, '%d/%m/%Y')::DATE")

con.execute(f"""
    COPY (
        SELECT
            -- Identity
            companynumber AS company_number,
            companyname AS company_name,
            companycategory AS company_type,

            -- Status: keep the original, plus a tidy group
            companystatus AS status_raw,
            CASE
                WHEN upper(companystatus) = 'ACTIVE' THEN 'Active'
                WHEN upper(companystatus) LIKE '%STRIKE OFF%' THEN 'Proposal to strike off'
                WHEN upper(companystatus) LIKE '%LIQUIDATION%' THEN 'Liquidation'
                WHEN upper(companystatus) LIKE '%VOLUNTARY ARRANGEMENT%' THEN 'Voluntary arrangement'
                WHEN upper(companystatus) LIKE '%ADMINISTRAT%'
                  OR upper(companystatus) LIKE '%RECEIVER%' THEN 'Administration or receivership'
                ELSE 'Other'
            END AS status_group,

            -- Industry: split "47910 - Retail sale via..." into code and description
            nullif(regexp_extract(siccodesictext_1, '^(\\d+)', 1), '') AS sic_code,
            nullif(regexp_extract(siccodesictext_1, '^\\d+ - (.*)$', 1), '') AS sic_description,

            -- Location
            regaddressposttown AS post_town,
            upper(regaddresspostcode) AS postcode,
            nullif(regexp_extract(upper(regaddresspostcode), '^([A-Z]{{1,2}})', 1), '') AS postcode_area,

            -- Dates as real dates
            to_date(incorporationdate) AS incorporation_date,
            to_date(accountsnextduedate) AS accounts_next_due,
            to_date(accountslastmadeupdate) AS accounts_last_made_up,
            to_date(confstmtnextduedate) AS confirmation_next_due,
            accountsaccountcategory AS accounts_category,

            -- Derived risk signals
            round(date_diff('day', to_date(incorporationdate), DATE '{SNAPSHOT_DATE}') / 365.25, 1)
                AS company_age_years,
            coalesce(to_date(accountsnextduedate) < DATE '{SNAPSHOT_DATE}', false) AS accounts_overdue,
            coalesce(to_date(confstmtnextduedate) < DATE '{SNAPSHOT_DATE}', false) AS confirmation_overdue,
            coalesce(try_cast(mortgagesnummortoutstanding AS INTEGER), 0) AS charges_outstanding,

            DATE '{SNAPSHOT_DATE}' AS snapshot_date
        FROM '{RAW_PATH}'
    )
    TO '{CLEAN_PATH}' (FORMAT parquet)
""")

print(con.sql(f"SELECT COUNT(*) AS rows FROM '{CLEAN_PATH}'"))
print(con.sql(f"""
    SELECT status_group,
           COUNT(*) AS companies,
           COUNT(*) FILTER (WHERE accounts_overdue) AS accounts_overdue
    FROM '{CLEAN_PATH}'
    GROUP BY status_group
    ORDER BY companies DESC
"""))