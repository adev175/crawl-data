import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone
import os
from dotenv import load_dotenv

# Configuration
# Load environment variables from .env file
load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
TELEGRAM_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
URL = "https://www.24h.com.vn/gia-vang-hom-nay-c425.html"
TIMEOUT = 15

# Convert English day to Vietnamese
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

# Fetch gold prices
def fetch_gold_prices():
    print("Fetching gold prices...")
    try:
        response = requests.get(URL, timeout=TIMEOUT)
        response.raise_for_status()
        print("Successfully fetched data from website.")
        soup = BeautifulSoup(response.content, 'html.parser')

        table = soup.find('div', {'class': 'cate-24h-gold-pri-table'})
        if not table:
            print("No data table found.")
            return "Không tìm thấy dữ liệu giá vàng.", []

        rows = table.find('table', {'class': 'gia-vang-search-data-table'})
        if not rows:
            print("No rows found in the data table.")
            return "Không tìm thấy bảng giá vàng.", []

        data = []
        buy_trend = None  # Track if buy price is increasing or decreasing
        for row in rows.find_all('tr'):
            cols = row.find_all('td')
            if len(cols) >= 3:
                # Extract main price and change
                buy_price = cols[1].find('span', {'class': 'fixW'}).text.strip()
                buy_change_span = cols[1].find('span', {'class': ['colorGreen', 'colorRed']})
                buy_change = (buy_change_span.text.strip() if buy_change_span else "")
                buy_symbol = "▲" if 'colorGreen' in buy_change_span['class'] else "▼" if 'colorRed' in buy_change_span['class'] else ""

                sell_price = cols[2].find('span', {'class': 'fixW'}).text.strip()
                sell_change_span = cols[2].find('span', {'class': ['colorGreen', 'colorRed']})
                sell_change = (sell_change_span.text.strip() if sell_change_span else "")
                sell_symbol = "▲" if 'colorGreen' in sell_change_span['class'] else "▼" if 'colorRed' in sell_change_span['class'] else ""

                # Determine buy trend
                if buy_trend is None and buy_symbol:
                    buy_trend = 'increase' if buy_symbol == "▲" else 'decrease'

                # Combine price and change with symbol
                buy_price_full = f"{buy_price} {buy_symbol}{buy_change}"
                sell_price_full = f"{sell_price} {sell_symbol}{sell_change}"

                # Append results
                data.append([cols[0].text.strip(), buy_price_full, sell_price_full])

        print(f"Buy trend: {buy_trend}")
        print("Data fetched successfully.")
        return buy_trend, data
    except requests.RequestException as e:
        print(f"Error connecting to the website: {e}")
        return f"Lỗi khi kết nối đến trang web: {e}", []

# Format as code block
def format_as_code_block(data):
    print("Formatting data as code block...")
    now = datetime.now(timezone.utc) + timedelta(hours=7)
    current_time = now.strftime("%H:%M:%S")
    current_day = convert_day_to_vietnamese(now.strftime("%A"))
    current_date = now.strftime("%d/%m/%Y")

    header = ["Loại", "Mua", "Bán"]
    line = "+------+--------------+--------------+"

    table = [
        f"{current_time} {current_day} {current_date}: Giá vàng nè má ôi! 📉",
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

# Send message to Telegram
def send_to_telegram(message, parse_mode="MarkdownV2"):
    print("Sending message to Telegram...")
    try:
        response = requests.post(
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

if __name__ == "__main__":
    print("Starting gold price bot...")
    buy_trend, data = fetch_gold_prices()
    if data:
        send_to_telegram(format_as_code_block(data))
        user_tag = os.getenv('USER_TAG', '')
        if buy_trend == 'increase':
            send_to_telegram(f"Có nên mua vàng không má {user_tag} 🤔🤔🤔", parse_mode=None)
        elif buy_trend == 'decrease':
            send_to_telegram(f"✅ Mua vàng đi má {user_tag} 🧀🧀🧀", parse_mode=None)
    else:
        print(buy_trend)
    print("Gold price bot finished.")
