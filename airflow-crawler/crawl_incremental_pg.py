import os, time, datetime as dt
import requests
from bs4 import BeautifulSoup
import psycopg2
from psycopg2.extras import execute_batch

BASE_URL = "https://tinnhiemmang.vn/danh-ba-ten-mien?title=&page="
TODAY = dt.date.today()
SLEEP = float(os.getenv("SLEEP", "0.5"))
EMPTY_STOP = 2
MAX_PAGE = int(os.getenv("MAX_PAGE", "2000"))

# Thông tin App DB
APP_DB_HOST = os.getenv("APP_DB_HOST", "fraud_alert_db")
APP_DB_PORT = os.getenv("APP_DB_PORT", "5432")
APP_DB_USER = os.getenv("APP_DB_USER", "fraud_user")
APP_DB_PASSWORD = os.getenv("APP_DB_PASSWORD", "fraud_password_123")
APP_DB_NAME = os.getenv("APP_DB_NAME", "fraud_alert")

APP_DB_DSN = f"postgresql://{APP_DB_USER}:{APP_DB_PASSWORD}@{APP_DB_HOST}:{APP_DB_PORT}/{APP_DB_NAME}"

def get_soup(url):
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser")

def parse_list_items(soup):
    """
    Parse domain + thông tin "Sở hữu bởi" từ layout mới của tinnhiemmang.vn

    Cấu trúc HTML hiện tại (t12/2025):
    <ul id="list-obj">
      <li class="item1">
        <div class="row">
          <div class="col-md-8 col-lg-5 obj">
            <div class="meta">
              <a class="sf-semibold webkit-box-1"><span>domain</span></a>
              <div class="date">Tín nhiệm mạng: ...</div>
              <a><label>Sở hữu bởi:</label> Tên tổ chức</a>
    """
    rows: list[tuple[str, str]] = []
    for item in soup.select("li.item1"):
        meta = item.select_one("div.meta")
        if not meta:
            continue

        # Domain nằm trong <a class="sf-semibold webkit-box-1"><span>domain</span></a>
        domain_tag = meta.select_one("a.sf-semibold.webkit-box-1 span")
        if not domain_tag:
            continue
        domain = (domain_tag.get_text(strip=True) or "").lower()
        if not domain:
            continue

        # Lấy "Sở hữu bởi"
        owner = ""
        for link in meta.select("a"):
            label = link.find("label")
            if label and "Sở hữu bởi" in label.get_text():
                label.extract()  # bỏ phần label để chỉ còn tên tổ chức
                owner = link.get_text(" ", strip=True)
                owner = owner.lstrip("- ").strip()
                break

        rows.append((domain, owner))
    return rows

def create_normalized_pattern(domain: str) -> str:
    """
    Tạo normalized_pattern từ domain đã clean sẵn
    Domain từ crawl đã sạch sẵn (ví dụ: tinnhiemmang.vn, dichvucong.quangninh.gov.vn)
    Chỉ cần thêm / ở cuối cho prefix match
    """
    if not domain:
        return ""
    # Domain từ crawl đã clean sẵn, chỉ cần strip và thêm / cho prefix match
    domain = domain.strip()
    if not domain:
        return ""
    # Tạo normalized_pattern: domain + "/" cho prefix match
    return f"{domain}/"

def crawl_once():
    page = 0
    empty = 0
    out = []
    while page <= MAX_PAGE:
        soup = get_soup(BASE_URL + str(page))
        items = parse_list_items(soup)
        if not items:
            empty += 1
            if empty >= EMPTY_STOP: break
        else:
            empty = 0
            out.extend(items)
        page += 1
        time.sleep(SLEEP)
    dedup = {}
    for d, c in out: dedup.setdefault(d, c or "")
    return [(d, dedup[d]) for d in dedup]

def upsert_to_app_db(rows):
    """
    Ghi TRỰC TIẾP vào App DB (bảng trusted_urls)
    Domain từ crawl đã clean sẵn, không cần clean thêm
    """
    if not rows: return 0
    
    try:
        conn = psycopg2.connect(APP_DB_DSN)
        conn.autocommit = True
        
        with conn.cursor() as cur:
            normalized_rows = []
            for domain, company in rows:
                # Domain từ crawl đã clean sẵn (ví dụ: tinnhiemmang.vn, dichvucong.quangninh.gov.vn)
                # Chỉ cần strip và kiểm tra không rỗng
                domain = domain.strip()
                if not domain:
                    continue
                
                # Tạo normalized_pattern: domain + "/" cho prefix match
                normalized_pattern = create_normalized_pattern(domain)
                if not normalized_pattern:
                    continue
                
                normalized_rows.append({
                    "normalized_pattern": normalized_pattern,
                    "match_type": "prefix",
                    "source": "airflow_crawler",
                    "description": company if company else None,
                    "raw_example": domain,  # Domain gốc từ crawl (đã clean sẵn, chỉ lower())
                    "is_active": True,
                })
            
            if not normalized_rows:
                print("Không có domain nào hợp lệ")
                return 0
            
            # Upsert vào trusted_urls
            sql = """
            INSERT INTO trusted_urls(
                normalized_pattern, match_type, source, description, 
                raw_example, is_active, created, updated
            )
            VALUES (%(normalized_pattern)s, %(match_type)s::whitelistmatchtype, 
                    %(source)s, %(description)s, %(raw_example)s, %(is_active)s, 
                    NOW(), NOW())
            ON CONFLICT (normalized_pattern, match_type) 
            DO UPDATE SET
                description = EXCLUDED.description,
                source = EXCLUDED.source,
                raw_example = EXCLUDED.raw_example,
                is_active = EXCLUDED.is_active,
                updated = NOW();
            """
            
            execute_batch(cur, sql, normalized_rows, page_size=500)
            print(f"✅ Đã upsert {len(normalized_rows)} domains vào App DB")
        
        conn.close()
        return len(normalized_rows)
    except Exception as e:
        print(f"❌ Lỗi kết nối App DB: {e}")
        print(f"DSN: {APP_DB_DSN.replace(APP_DB_PASSWORD, '***')}")
        raise

if __name__ == "__main__":
    print(f"🚀 Bắt đầu crawl tại {TODAY}")
    rows = crawl_once()
    print(f"📊 Tìm thấy {len(rows)} domains (sau dedup)")
    n = upsert_to_app_db(rows)
    print(f"✅ UPSERT {n} domains vào App DB tại {TODAY}")

