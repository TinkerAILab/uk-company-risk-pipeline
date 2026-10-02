import os
import json
import requests

api_key = os.getenv("CH_API_KEY")

company_number = "00445790"  # Tesco PLC
url = f"https://api.company-information.service.gov.uk/company/{company_number}"

response = requests.get(url, auth=(api_key, ""))

print("Status code:", response.status_code)
print(json.dumps(response.json(), indent=2))