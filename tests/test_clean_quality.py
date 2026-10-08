import duckdb
import pytest

SNAPSHOT_DATE = "2026-10-01"
RAW_PATH = f"data/raw/bulk/companies_{SNAPSHOT_DATE}.parquet"
CLEAN_PATH = f"data/clean/companies_clean_{SNAPSHOT_DATE}.parquet"

from pathlib import Path

if not Path(CLEAN_PATH).exists():
    pytest.skip("Snapshot data not available (it is not stored in Git)", allow_module_level=True)


@pytest.fixture(scope="module")
def con():
    """One database connection shared by all the tests below."""
    connection = duckdb.connect()
    connection.execute(f"CREATE VIEW clean AS SELECT * FROM '{CLEAN_PATH}'")
    connection.execute(f"CREATE VIEW raw AS SELECT * FROM '{RAW_PATH}'")
    yield connection
    connection.close()


def scalar(con, sql):
    """Run a query that returns a single number."""
    return con.sql(sql).fetchone()[0]


def test_row_count_matches_raw(con):
    assert scalar(con, "SELECT COUNT(*) FROM clean") == scalar(con, "SELECT COUNT(*) FROM raw")


def test_company_number_never_missing(con):
    missing = scalar(con, "SELECT COUNT(*) FROM clean WHERE company_number IS NULL OR trim(company_number) = ''")
    assert missing == 0


def test_company_number_unique(con):
    duplicates = scalar(con, """
        SELECT COUNT(*) FROM (
            SELECT company_number FROM clean
            GROUP BY company_number
            HAVING COUNT(*) > 1
        )
    """)
    assert duplicates == 0, f"{duplicates} company numbers appear more than once"


def test_company_number_is_8_characters(con):
    wrong_length = scalar(con, "SELECT COUNT(*) FROM clean WHERE length(company_number) <> 8")
    assert wrong_length == 0, f"{wrong_length} company numbers are not 8 characters"


def test_every_status_is_grouped(con):
    ungrouped = scalar(con, "SELECT COUNT(*) FROM clean WHERE status_group IS NULL OR status_group = 'Other'")
    assert ungrouped == 0


def test_no_incorporation_dates_in_future(con):
    future = scalar(con, f"SELECT COUNT(*) FROM clean WHERE incorporation_date > DATE '{SNAPSHOT_DATE}'")
    assert future == 0


def test_incorporation_date_mostly_present(con):
    missing_pct = scalar(con, """
        SELECT 100.0 * COUNT(*) FILTER (WHERE incorporation_date IS NULL) / COUNT(*)
        FROM clean
    """)
    assert missing_pct < 1, f"{missing_pct:.2f}% of companies have no incorporation date"


def test_charges_not_negative(con):
    negative = scalar(con, "SELECT COUNT(*) FROM clean WHERE charges_outstanding < 0")
    assert negative == 0