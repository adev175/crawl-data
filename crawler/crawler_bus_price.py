# bus_price.py
import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from services.telegram_bot import send_to_telegram

def fetch_cheapest_bus_price():
    print("Fetching cheapest bus price...")
    URL = os.getenv("TARGET_URL", "https://www.bushikaku.net/search/niigata_tokyo/nagaoka_shinjuku/20250605/time_division_type-night/")

    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    time.sleep(2)
    driver.get(URL)
    time.sleep(5)

    prices = []
    try:
        calendar = driver.find_element(By.CLASS_NAME, "SearchLowestPriceCalendar_lowest-price-calendar__f8m0U")
        buttons = calendar.find_elements(By.CLASS_NAME, "SearchLowestPriceCalendar_day_button_qHWJ2")
        for btn in buttons:
            price_text = btn.text.strip().replace("円", "").replace(",", "")
            if price_text.isdigit():
                prices.append(int(price_text))
    except Exception as e:
        send_to_telegram(f"❌ Lỗi khi lấy giá bus: {e}", parse_mode=None)
        return
    finally:
        driver.quit()

    if prices:
        min_price = min(prices)
        send_to_telegram(f"🚌 Giá rẻ nhất từ Nagaoka → Shinjuku hôm nay: ¥{min_price}")
    else:
        send_to_telegram("🚍 Không tìm thấy giá bus hôm nay.")

if __name__ == "__main__":
    fetch_cheapest_bus_price()
