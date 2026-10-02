import os
import json
import time
from pathlib import Path

import requests

API_KEY = os.getenv("CH_API_KEY")
BASE_URL = "https://api.company-information.service.gov.uk"
OUTPUT_DIR = Path("data/raw/companies")


def get_company(company_number, max_retries=3):
    """Fetch one company profile. Returns the data, or None if it fails."""
    url = f"{BASE_URL}/company/{company_number}"

    for attempt in range(1, max_retries + 1):
        response = requests.get(url, auth=(API_KEY, ""), timeout=10)

        if response.status_code == 200:
            return response.json()

        if response.status_code == 404:
            print(f"{company_number}: not found")
            return None

        if response.status_code == 429:
            wait = 60 * attempt
            print(f"{company_number}: rate limited, waiting {wait} seconds")
            time.sleep(wait)
            continue

        print(f"{company_number}: error {response.status_code}, attempt {attempt}")
        time.sleep(5)

    return None


def save_raw(company_number, data):
    """Save the API response exactly as received."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / f"{company_number}.json"
    path.write_text(json.dumps(data, indent=2))


def main():
    # A few large UK companies, plus one made-up number to test errors
    company_numbers = ["00445790", "00102498", "01833679", "99999999"]

    for number in company_numbers:
        data = get_company(number)
        if data:
            save_raw(number, data)
            print(f"{number}: saved {data.get('company_name')}")
        time.sleep(0.6)  # pause between calls to respect the API limit


if __name__ == "__main__":
    main()