from transform_companies import flatten_company

SAMPLE = {
    "company_number": "12345678",
    "company_name": "EXAMPLE TRADING LTD",
    "company_status": "active",
    "type": "ltd",
    "date_of_creation": "2020-03-15",
    "sic_codes": ["47910", "62020"],
    "registered_office_address": {"postal_code": "AB1 2CD", "locality": "London"},
    "accounts": {
        "next_accounts": {"overdue": True},
        "last_accounts": {"made_up_to": "2024-03-31"},
    },
    "confirmation_statement": {"overdue": False},
    "has_insolvency_history": False,
    "has_charges": True,
}


def test_flatten_picks_out_the_right_fields():
    row = flatten_company(SAMPLE)
    assert row["company_number"] == "12345678"
    assert row["sic_code"] == "47910"  # only the first industry code
    assert row["postcode"] == "AB1 2CD"
    assert row["accounts_overdue"] is True
    assert row["confirmation_overdue"] is False


def test_flatten_handles_missing_fields():
    row = flatten_company({"company_number": "00000001"})
    assert row["company_name"] is None
    assert row["sic_code"] is None
    assert row["accounts_overdue"] is None