import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

STREAM_URL = "https://stream.companieshouse.gov.uk/companies"
STREAM_KEY = os.getenv("CH_STREAM_KEY")
OUTPUT_DIR = Path("data/raw/stream")
STATE_FILE = Path("data/raw/stream/_last_timepoint.txt")


def read_last_timepoint():
    """Where did we stop last time? Lets the stream resume without gaps."""
    if STATE_FILE.exists():
        return STATE_FILE.read_text().strip()
    return None


def capture(minutes):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    started = datetime.now(timezone.utc)
    out_path = OUTPUT_DIR / f"companies_{started:%Y-%m-%dT%H%M}.jsonl"

    params = {}
    last_timepoint = read_last_timepoint()
    if last_timepoint:
        params["timepoint"] = last_timepoint
        print(f"Resuming from timepoint {last_timepoint}")

    stop_at = time.time() + minutes * 60
    count = 0

    with requests.get(STREAM_URL, auth=(STREAM_KEY, ""), params=params,
                      stream=True, timeout=(10, 90)) as response:
        response.raise_for_status()
        with out_path.open("w") as out:
            for line in response.iter_lines():
                if time.time() > stop_at:
                    break
                if not line:  # blank lines are heartbeats that keep the connection open
                    continue

                event = json.loads(line)
                out.write(json.dumps(event) + "\n")
                count += 1

                timepoint = event.get("event", {}).get("timepoint")
                if timepoint is not None:
                    STATE_FILE.write_text(str(timepoint))

                if count % 100 == 0:
                    print(f"{count} events captured")

    print(f"\nSaved {count} events to {out_path}")


if __name__ == "__main__":
    minutes = float(sys.argv[1]) if len(sys.argv) > 1 else 2
    capture(minutes)