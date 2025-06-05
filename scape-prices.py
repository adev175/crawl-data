import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
URL = os.getenv("TARGET_URL")

def send_telegram_message(message):
    if not BOT_TOKEN or not CHAT_ID:
        print("Telegram bot token or chat ID is missing.")
        return
    endpoint = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.get(endpoint, params={"chat_id": CHAT_ID, "text": message})

def fetch_cheapest_prices():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    driver.get(URL)
    time.sleep(5)  # Let page render

    prices = []
    try:
        calendar = driver.find_element(By.CLASS_NAME, "SearchLowestPriceCalendar_lowest-price-calendar__f8m0U")
        buttons = calendar.find_elements(By.CLASS_NAME, "SearchLowestPriceCalendar_day_button_qHWJ2")
        for btn in buttons:
            price_text = btn.text.strip().replace("円", "").replace(",", "")
            if price_text.isdigit():
                prices.append(int(price_text))
    except Exception as e:
        send_telegram_message(f"Error: {e}")
    finally:
        driver.quit()

    if prices:
        lowest = min(prices)
        print(f"Cheapest: ¥{lowest}")
        send_telegram_message(f"🚍 Cheapest Nagaoka → Shinjuku bus: ¥{lowest}")
    else:
        print("No prices found.")

if __name__ == "__main__":
    fetch_cheapest_prices()
