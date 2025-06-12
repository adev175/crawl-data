# crawler/crawler_gold_clean.py
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


def create_session():
    """Create session with headers and retry logic"""
    session = requests.Session()

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
        'Cache-Control': 'max-age=0',
        'Referer': 'https://www.google.com/'
    }

    session.headers.update(headers)

    # Retry strategy
    retry_strategy = Retry(
        total=3,
        status_forcelist=[429, 500, 502, 503, 504],
        backoff_factor=1,
        raise_on_status=False
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    return session


def fetch_gold_prices():
    """Fetch gold prices from 24h.com.vn"""
    url = "https://www.24h.com.vn/gia-vang-hom-nay-c425.html"
    session = create_session()

    try:
        print("Trying 24h.com.vn...")
        time.sleep(random.uniform(1, 2))

        response = session.get(url, timeout=TIMEOUT)

        if response.status_code == 200:
            print("✅ Successfully connected to 24h.com.vn")
            buy_trend, data = parse_24h_gold(response.content)

            if data:
                print("✅ Successfully parsed data from 24h.com.vn")
                return buy_trend, data
            else:
                print("❌ No data found")
                return None, []
        else:
            print(f"❌ HTTP {response.status_code} from 24h.com.vn")
            return None, []

    except requests.exceptions.Timeout:
        print("⏰ Timeout connecting to 24h.com.vn")
        return None, []
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
        return None, []
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None, []


def parse_24h_gold(content):
    """Parse gold prices from 24h.com.vn"""
    soup = BeautifulSoup(content, 'html.parser')

    table = soup.find('div', {'class': 'cate-24h-gold-pri-table'})
    if not table:
        print("❌ Could not find gold price table")
        return None, []

    rows = table.find('table', {'class': 'gia-vang-search-data-table'})
    if not rows:
        print("❌ Could not find price data table")
        return None, []

    data = []
    buy_trend = None

    for row in rows.find_all('tr'):
        cols = row.find_all('td')
        if len(cols) >= 3:
            try:
                # Get gold type
                gold_type = cols[0].text.strip()

                # Extract buy price and trend
                buy_price_elem = cols[1].find('span', {'class': 'fixW'})
                if not buy_price_elem:
                    continue

                buy_price = buy_price_elem.text.strip()
                buy_change_span = cols[1].find('span', {'class': ['colorGreen', 'colorRed']})

                if buy_change_span:
                    buy_change = buy_change_span.text.strip()
                    buy_symbol = "▲" if 'colorGreen' in buy_change_span.get('class', []) else "▼"

                    # Set overall trend from first row
                    if buy_trend is None:
                        buy_trend = 'increase' if buy_symbol == "▲" else 'decrease'

                    buy_price_full = f"{buy_price} {buy_symbol}{buy_change}"
                else:
                    buy_price_full = buy_price

                # Extract sell price and trend
                sell_price_elem = cols[2].find('span', {'class': 'fixW'})
                if not sell_price_elem:
                    continue

                sell_price = sell_price_elem.text.strip()
                sell_change_span = cols[2].find('span', {'class': ['colorGreen', 'colorRed']})

                if sell_change_span:
                    sell_change = sell_change_span.text.strip()
                    sell_symbol = "▲" if 'colorGreen' in sell_change_span.get('class', []) else "▼"
                    sell_price_full = f"{sell_price} {sell_symbol}{sell_change}"
                else:
                    sell_price_full = sell_price

                data.append([gold_type, buy_price_full, sell_price_full])

            except Exception as e:
                print(f"Error parsing row: {e}")
                continue

    return buy_trend, data


def convert_day_to_vietnamese(day):
    """Convert English day to Vietnamese"""
    return {
        "Monday": "Thứ Hai",
        "Tuesday": "Thứ Ba",
        "Wednesday": "Thứ Tư",
        "Thursday": "Thứ Năm",
        "Friday": "Thứ Sáu",
        "Saturday": "Thứ Bảy",
        "Sunday": "Chủ Nhật",
    }.get(day, day)


def format_as_code_block(data):
    """Format gold data as code block"""
    print("Formatting data as code block...")
    now = datetime.now(timezone.utc) + timedelta(hours=7)
    current_time = now.strftime("%H:%M:%S")
    current_day = convert_day_to_vietnamese(now.strftime("%A"))
    current_date = now.strftime("%d/%m/%Y")

    header = ["Loại", "Mua", "Bán"]
    line = "+------+--------------+--------------+"

    table = [
        f"{current_time} {current_day} {current_date}: Giá vàng! 📊",
        "Nguồn: 24h.com.vn",
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
    """Send message to Telegram"""
    print("Sending message to Telegram...")
    try:
        session = create_session()
        response = session.post(
            TELEGRAM_URL,
            data={
                'chat_id': CHAT_ID,
                'text': message,
                'parse_mode': parse_mode
            },
            timeout=TIMEOUT
        )

        if response.status_code == 200:
            print("Message sent successfully.")
        else:
            print(f"Error sending message: {response.status_code}, {response.text}")

    except requests.RequestException as e:
        print(f"Error sending message to Telegram: {e}")


def main():
    """Main function"""
    print("Starting gold price bot...")

    try:
        buy_trend, data = fetch_gold_prices()

        if data:
            # Send formatted table
            send_to_telegram(format_as_code_block(data))

            # Send trend message
            user_tag = os.getenv('USER_TAG', '')

            if buy_trend == 'increase':
                send_to_telegram(f"Có nên mua vàng không má {user_tag} 🤔🤔🤔", parse_mode=None)
            elif buy_trend == 'decrease':
                send_to_telegram(f"✅ Mua vàng đi má {user_tag} 🧀🧀🧀", parse_mode=None)
            else:
                send_to_telegram("📊 Giá vàng cập nhật từ 24h.com.vn", parse_mode=None)
        else:
            error_msg = "❌ Không thể lấy giá vàng từ 24h.com.vn"
            send_to_telegram(error_msg, parse_mode=None)
            print(error_msg)

    except Exception as e:
        error_msg = f"❌ Lỗi hệ thống gold bot: {str(e)}"
        send_to_telegram(error_msg, parse_mode=None)
        print(f"Gold bot error: {e}")

    print("Gold price bot finished.")


if __name__ == "__main__":
    main()