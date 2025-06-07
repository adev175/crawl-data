# crawler/crawler_gold_enhanced.py
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone
import os
import time
import random
from dotenv import load_dotenv
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

# Configuration
load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
TELEGRAM_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
TIMEOUT = 30


def create_enhanced_session():
    """Create session with better headers and retry logic"""
    session = requests.Session()

    # Rotating user agents
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    ]

    headers = {
        'User-Agent': random.choice(user_agents),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'vi-VN,vi;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Cache-Control': 'max-age=0',
        'Referer': 'https://www.google.com/'
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


def fetch_gold_prices():
    """Try multiple gold price sources"""
    sources = [
        {
            "name": "24h.com.vn",
            "url": "https://www.24h.com.vn/gia-vang-hom-nay-c425.html",
            "parser": parse_24h_gold
        },
        {
            "name": "CafeF",
            "url": "https://cafef.vn/gia-vang.chn",
            "parser": parse_cafef_gold
        },
        {
            "name": "DanTri",
            "url": "https://dantri.com.vn/kinh-doanh/gia-vang.htm",
            "parser": parse_dantri_gold
        }
    ]

    session = create_enhanced_session()

    for source in sources:
        try:
            print(f"Trying {source['name']}...")

            # Add random delay
            time.sleep(random.uniform(1, 3))

            response = session.get(source['url'], timeout=TIMEOUT)

            if response.status_code == 200:
                print(f"✅ Successfully connected to {source['name']}")

                # Try to parse the data
                try:
                    buy_trend, data = source['parser'](response.content)
                    if data:  # If we got valid data
                        print(f"✅ Successfully parsed data from {source['name']}")
                        return buy_trend, data, source['name']
                except Exception as parse_error:
                    print(f"❌ Failed to parse {source['name']}: {parse_error}")
                    continue
            else:
                print(f"❌ HTTP {response.status_code} from {source['name']}")

        except requests.exceptions.Timeout:
            print(f"⏰ Timeout connecting to {source['name']}")
        except requests.exceptions.RequestException as e:
            print(f"❌ Connection error to {source['name']}: {e}")
        except Exception as e:
            print(f"❌ Unexpected error with {source['name']}: {e}")

    return None, [], "None"


def parse_24h_gold(content):
    """Parse gold prices from 24h.com.vn"""
    soup = BeautifulSoup(content, 'html.parser')

    table = soup.find('div', {'class': 'cate-24h-gold-pri-table'})
    if not table:
        return None, []

    rows = table.find('table', {'class': 'gia-vang-search-data-table'})
    if not rows:
        return None, []

    data = []
    buy_trend = None

    for row in rows.find_all('tr'):
        cols = row.find_all('td')
        if len(cols) >= 3:
            try:
                # Extract price and trend data
                buy_price = cols[1].find('span', {'class': 'fixW'}).text.strip()
                buy_change_span = cols[1].find('span', {'class': ['colorGreen', 'colorRed']})

                if buy_change_span:
                    buy_change = buy_change_span.text.strip()
                    buy_symbol = "▲" if 'colorGreen' in buy_change_span.get('class', []) else "▼"

                    if buy_trend is None:
                        buy_trend = 'increase' if buy_symbol == "▲" else 'decrease'
                else:
                    buy_change = ""
                    buy_symbol = ""

                sell_price = cols[2].find('span', {'class': 'fixW'}).text.strip()
                sell_change_span = cols[2].find('span', {'class': ['colorGreen', 'colorRed']})

                if sell_change_span:
                    sell_change = sell_change_span.text.strip()
                    sell_symbol = "▲" if 'colorGreen' in sell_change_span.get('class', []) else "▼"
                else:
                    sell_change = ""
                    sell_symbol = ""

                # Format prices
                buy_price_full = f"{buy_price} {buy_symbol}{buy_change}"
                sell_price_full = f"{sell_price} {sell_symbol}{sell_change}"

                data.append([cols[0].text.strip(), buy_price_full, sell_price_full])

            except Exception as e:
                print(f"Error parsing row: {e}")
                continue

    return buy_trend, data


def parse_cafef_gold(content):
    """Parse gold prices from CafeF (fallback)"""
    # Simplified parser for backup source
    soup = BeautifulSoup(content, 'html.parser')

    # Look for any table with gold prices
    tables = soup.find_all('table')

    for table in tables:
        rows = table.find_all('tr')
        if len(rows) > 1:  # Has header and data
            data = []
            for row in rows[1:]:  # Skip header
                cols = row.find_all(['td', 'th'])
                if len(cols) >= 3:
                    data.append([
                        cols[0].text.strip()[:4],  # Gold type
                        cols[1].text.strip(),  # Buy price
                        cols[2].text.strip()  # Sell price
                    ])

            if data:
                return None, data  # No trend data from this source

    return None, []


def parse_dantri_gold(content):
    """Parse gold prices from DanTri (fallback)"""
    # Another simplified parser
    soup = BeautifulSoup(content, 'html.parser')

    # Look for price data
    price_elements = soup.find_all(string=lambda text: text and 'SJC' in text)

    if price_elements:
        # Simple fallback data
        return None, [["SJC", "N/A", "N/A"], ["Gold", "Check", "Source"]]

    return None, []


# Convert English day to Vietnamese (same as before)
def convert_day_to_vietnamese(day):
    return {
        "Monday": "Thứ Hai",
        "Tuesday": "Thứ Ba",
        "Wednesday": "Thứ Tư",
        "Thursday": "Thứ Năm",
        "Friday": "Thứ Sáu",
        "Saturday": "Thứ Bảy",
        "Sunday": "Chủ Nhật",
    }.get(day, day)


def format_as_code_block(data, source_name=""):
    """Format gold data with source info"""
    print("Formatting data as code block...")
    now = datetime.now(timezone.utc) + timedelta(hours=7)
    current_time = now.strftime("%H:%M:%S")
    current_day = convert_day_to_vietnamese(now.strftime("%A"))
    current_date = now.strftime("%d/%m/%Y")

    header = ["Loại", "Mua", "Bán"]
    line = "+------+--------------+--------------+"

    table = [
        f"{current_time} {current_day} {current_date}: Giá vàng! 📊",
        f"Nguồn: {source_name}" if source_name else "",
        "",
        line,
        f"| {header[0]:<4} | {header[1]:<12} | {header[2]:<12} |",
        line,
    ]

    for row in data:
        table.append(f"| {row[0][:4]:<4} | {row[1]:<12} | {row[2]:<12} |")
    table.append(line)

    print("Data formatted successfully.")
    return "```" + "\n".join(table) + "\n```"


def send_to_telegram(message, parse_mode="MarkdownV2"):
    """Send message to Telegram with enhanced error handling"""
    print("Sending message to Telegram...")
    try:
        session = create_enhanced_session()
        response = session.post(
            TELEGRAM_URL,
            data={
                'chat_id': CHAT_ID,
                'text': message,
                'parse_mode': parse_mode
            },
            timeout=TIMEOUT
        )
        if response.status_code != 200:
            print(f"Error sending message: {response.status_code}, {response.text}")
        else:
            print("Message sent successfully.")
    except requests.RequestException as e:
        print(f"Error sending message to Telegram: {e}")


def main():
    """Main function with enhanced error handling"""
    print("Starting enhanced gold price bot...")

    try:
        buy_trend, data, source_name = fetch_gold_prices()

        if data:
            send_to_telegram(format_as_code_block(data, source_name))
            user_tag = os.getenv('USER_TAG', '')

            if buy_trend == 'increase':
                send_to_telegram(f"Có nên mua vàng không má {user_tag} 🤔🤔🤔", parse_mode=None)
            elif buy_trend == 'decrease':
                send_to_telegram(f"✅ Mua vàng đi má {user_tag} 🧀🧀🧀", parse_mode=None)
            else:
                send_to_telegram(f"📊 Giá vàng cập nhật từ {source_name}", parse_mode=None)
        else:
            error_msg = "❌ Không thể lấy giá vàng từ tất cả các nguồn"
            send_to_telegram(error_msg, parse_mode=None)
            print(error_msg)

    except Exception as e:
        error_msg = f"❌ Lỗi hệ thống gold bot: {str(e)}"
        send_to_telegram(error_msg, parse_mode=None)
        print(error_msg)

    print("Enhanced gold price bot finished.")


if __name__ == "__main__":
    main()