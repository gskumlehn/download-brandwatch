import os
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import pandas as pd
from typing import Generator, List
from bcr_api.bwproject import BWProject
from bcr_api.bwresources import BWQueries

load_dotenv()

USERNAME   = os.getenv("BW_EMAIL")
PASSWORD   = os.getenv("BW_PASSWORD")
PROJECT    = os.getenv("BW_PROJECT")
QUERY_NAME = os.getenv("BW_QUERY_NAME")

def get_project() -> BWProject:
    return BWProject(project=PROJECT, username=USERNAME, password=PASSWORD)


def iter_mentions_pages(name: str, startDate: str, endDate: str, pagesize: int = 5000) -> Generator[List[dict], None, None]:
    proj = get_project()
    queries = BWQueries(proj)
    for page in queries.iter_mentions(
        name=name,
        startDate=startDate,
        endDate=endDate,
        pagesize=pagesize,
        iter_by_page=True,
    ):
        yield page


def stream_csv_pages(name: str, start_iso: str, end_iso: str) -> Generator[str, None, None]:
    first = True
    for page in iter_mentions_pages(name=name, startDate=start_iso, endDate=end_iso, pagesize=5000):
        if not page:
            continue
        df = pd.json_normalize(page)
        csv_chunk = df.to_csv(index=False, header=first)
        first = False
        yield csv_chunk


if __name__ == "__main__":
    bw_date = os.getenv("BW_DATE")
    if bw_date:
        try:
            target_date = datetime.strptime(bw_date, "%Y-%m-%d").date()
            start_dt = datetime.combine(target_date, datetime.min.time()).replace(tzinfo=timezone.utc)
            end_dt = start_dt + timedelta(days=1)
        except ValueError:
            now_utc = datetime.now(timezone.utc).replace(microsecond=0)
            start_dt = now_utc - timedelta(minutes=30)
            end_dt = now_utc
    else:
        now_utc = datetime.now(timezone.utc).replace(microsecond=0)
        start_dt = now_utc - timedelta(minutes=30)
        end_dt = now_utc

    START_DATE = start_dt.isoformat().replace("+00:00", "Z")
    END_DATE = end_dt.isoformat().replace("+00:00", "Z")
    print(f"Downloading mentions from {START_DATE} to {END_DATE}")

    for chunk in stream_csv_pages(name=QUERY_NAME, start_iso=START_DATE, end_iso=END_DATE):
        print(f"Received chunk of size {len(chunk)}")
