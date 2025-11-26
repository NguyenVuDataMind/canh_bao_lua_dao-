import os
import datetime as dt
import time
import requests
from bs4 import BeautifulSoup
import psycopg2
from psycopg2.extras import execute_batch

BASE_API = "https://tinnhiemmang.vn/filterObj"
TOKEN = "K25yWvL6YCA4ZecPjFA5jgEWMvSrjoMFM4zVQmY5"   # Token từ Network
TODAY = dt.date.today()

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "*/*",
    "X-Requested-With": "XMLHttpRequest"
}

def fetch_page(page: int):
    """Gọi API filterObj"""
    params = {
        "_token": TOKEN,
        "name_obj": "",
        "type": "web",
        "page": page
    }
    r = requests.get(BASE_API, params=params, headers=HEADERS, timeout=20)
    r.raise_for_status()
    return r.text


def parse_items(html_text):
    """Parse HTML từ API để lấy domain + công ty"""
    soup = BeautifulSoup(html_text, "html.parser")
    items = []

    for li in soup.select("li"):
        # Lấy domain
        a = li.select_one("a")
        if not a:
            continue

        domain = a.get_text(strip=True)

        # Lấy công ty
        info_block = li.get_text(" ", strip=True)
        company = ""
        if "Sở hữu bởi:" in info_block:
            company = info_block.split("Sở hữu bởi:")[1].strip()

        items.append((domain, company))
    return items


def crawl_all():
    """Crawl tất cả page đến khi hết dữ liệu"""
    page = 1
    result = []

    while True:
        print(f"🔎 Crawl page {page} ...")
        html = fetch_page(page)
        items = parse_items(html)

        if not items:
            print("⛔ Hết dữ liệu, dừng crawl.")
            break

        print(f"   → {len(items)} domain")
        result.extend(items)
        page += 1
        time.sleep(0.5)

    # dedup
    dedup = {}
    for d, c in result:
        dedup[d] = c or ""

    return [(d, dedup[d]) for d in dedup]


def upsert_rows(rows):
    if not rows:
        return 0

    PG_DSN = os.getenv("PG_DSN")
    conn = psycopg2.connect(PG_DSN)
    conn.autocommit = True

    with conn.cursor() as cur:
        # Ghi vào bảng white_listurl (đã được tạo bởi migration)
        # Sử dụng domain làm unique constraint, nếu domain đã tồn tại thì update
        sql = """
        INSERT INTO white_listurl(domain, company, first_seen, last_seen, source)
        VALUES (%s, NULLIF(%s,''), %s, %s, 'tinnhiemmang')
        ON CONFLICT (domain)
        DO UPDATE SET
            company = COALESCE(EXCLUDED.company, white_listurl.company),
            last_seen = EXCLUDED.last_seen,
            source = COALESCE(white_listurl.source, 'tinnhiemmang');
        """

        execute_batch(cur, sql, [(d, c, TODAY, TODAY) for d, c in rows], 500)

    conn.close()
    return len(rows)


if __name__ == "__main__":
    print(f"🚀 Bắt đầu crawl tại {TODAY}")
    rows = crawl_all()
    print(f"📊 Tổng: {len(rows)} domain sau dedup")

    n = upsert_rows(rows)
    print(f"✅ Đã upsert {n} domain vào DB")
