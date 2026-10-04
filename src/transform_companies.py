import json
from pathlib import Path

import pandas as pd
pd.set_option("display.max_columns", None)
pd.set_option("display.width", 200)

RAW_DIR = Path("data/raw/companies")
CLEAN_DIR = Path("data/clean")


def flatten_company(data):
    """Pick out the fields we need from one raw company record."""
    accounts = data.get("accounts", {})
    next_accounts = accounts.get("next_accounts", {})
    last_accounts = accounts.get("last_accounts", {})
    confirmation = data.get("confirmation_statement", {})
    address = data.get("registered_office_address", {})
    sic_codes = data.get("sic_codes", [])

    return {
        "company_number": data.get("company_number"),
        "company_name": data.get("company_name"),
        "company_status": data.get("company_status"),
        "company_type": data.get("type"),
        "date_of_creation": data.get("date_of_creation"),
        "sic_code": sic_codes[0] if sic_codes else None,
        "postcode": address.get("postal_code"),
        "locality": address.get("locality"),
        "last_accounts_made_up_to": last_accounts.get("made_up_to"),
        "accounts_overdue": next_accounts.get("overdue"),
        "confirmation_overdue": confirmation.get("overdue"),
        "has_insolvency_history": data.get("has_insolvency_history"),
        "has_charges": data.get("has_charges"),
    }


def main():
    records = []
    for path in sorted(RAW_DIR.glob("*.json")):
        data = json.loads(path.read_text())
        records.append(flatten_company(data))

    df = pd.DataFrame(records)

    # Turn text dates into real dates, then work out company age
    df["date_of_creation"] = pd.to_datetime(df["date_of_creation"])
    df["last_accounts_made_up_to"] = pd.to_datetime(df["last_accounts_made_up_to"])
    df["company_age_years"] = (
        (pd.Timestamp.today() - df["date_of_creation"]).dt.days / 365.25
    ).round(1)

    CLEAN_DIR.mkdir(parents=True, exist_ok=True)
    df.to_parquet(CLEAN_DIR / "companies.parquet", index=False)

    print(df.T)  # each company shown as a column, easier to read
    print(f"\nSaved {len(df)} companies to {CLEAN_DIR / 'companies.parquet'}")


if __name__ == "__main__":
    main()