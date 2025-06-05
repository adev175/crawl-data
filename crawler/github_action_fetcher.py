# crawler/github_actions_fetcher.py
# Enhanced fetcher for GitHub Actions environment

import requests
import time
import random
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter


def create_github_actions_session():
    """Create session optimized for GitHub Actions"""
    session = requests.Session()

    # Enhanced headers to bypass blocking
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Cache-Control': 'max-age=0'
    }

    session.headers.update(headers)

    # Retry strategy
    retry_strategy = Retry(
        total=5,
        status_forcelist=[429, 500, 502, 503, 504, 520, 522, 524],
        backoff_factor=2,
        raise_on_status=False
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    return session


def fetch_with_fallback(url, timeout=30, max_attempts=3):
    """Fetch URL with multiple attempts and fallbacks"""
    session = create_github_actions_session()

    for attempt in range(max_attempts):
        try:
            print(f"Attempt {attempt + 1}/{max_attempts} for {url}")

            # Random delay to avoid rate limiting
            if attempt > 0:
                delay = random.uniform(2, 5)
                print(f"Waiting {delay:.1f} seconds...")
                time.sleep(delay)

            response = session.get(url, timeout=timeout)

            if response.status_code == 200:
                print(f"✅ Successfully fetched {url}")
                return response
            else:
                print(f"❌ HTTP {response.status_code} for {url}")

        except requests.exceptions.ConnectTimeout:
            print(f"⏰ Connection timeout for {url} (attempt {attempt + 1})")
        except requests.exceptions.ReadTimeout:
            print(f"⏰ Read timeout for {url} (attempt {attempt + 1})")
        except requests.exceptions.RequestException as e:
            print(f"❌ Request error for {url}: {e}")
        except Exception as e:
            print(f"❌ Unexpected error for {url}: {e}")

    print(f"💀 All attempts failed for {url}")
    return None


# Enhanced gold price fetcher
def fetch_gold_prices_github_actions():
    """Enhanced gold price fetcher for GitHub Actions"""
    print("Fetching gold prices (GitHub Actions mode)...")

    url = "https://www.24h.com.vn/gia-vang-hom-nay-c425.html"

    # Try primary URL
    response = fetch_with_fallback(url, timeout=30, max_attempts=3)

    if not response:
        # Try alternative gold price sources
        alternative_sources = [
            "https://cafef.vn/gia-vang.chn",
            "https://vietcombank.com.vn/exchange-rate",
            # Add more backup sources
        ]

        for alt_url in alternative_sources:
            print(f"Trying alternative source: {alt_url}")
            response = fetch_with_fallback(alt_url, timeout=20, max_attempts=2)
            if response:
                print(f"✅ Using alternative source: {alt_url}")
                break

    if not response:
        return "Không thể kết nối đến các trang web giá vàng.", []

    # Continue with normal parsing...
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(response.content, 'html.parser')

    # ... rest of gold parsing logic
    return None, []  # Placeholder


# Enhanced bus price fetcher
def fetch_bus_prices_github_actions():
    """Enhanced bus price fetcher for GitHub Actions"""
    print("Fetching bus prices (GitHub Actions mode)...")

    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    import time

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    # Enhanced options for GitHub Actions
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-plugins")
    options.add_argument("--disable-images")  # Faster loading
    options.add_argument("--disable-javascript")  # If not needed
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

    try:
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(60)  # Longer timeout

        url = "https://www.bushikaku.net/search/niigata_tokyo/nagaoka_shinjuku/202506/time_division_type-night/"

        print(f"Loading bus website: {url}")
        driver.get(url)

        # Wait longer for page load
        time.sleep(15)

        # Rest of bus scraping logic...
        driver.quit()
        return True

    except Exception as e:
        print(f"Bus scraping error: {e}")
        return False