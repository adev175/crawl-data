# crawler/stable_bus_crawler.py
import os
import time
import sqlite3
import re
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from services.telegram_bot import send_to_telegram


class StableBusPriceTracker:
    def __init__(self):
        self.db_file = "bus_prices.db"
        self.init_database()

    def init_database(self):
        """Initialize SQLite database"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT UNIQUE NOT NULL,
                min_price INTEGER NOT NULL,
                prices_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS price_changes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                old_price INTEGER,
                new_price INTEGER NOT NULL,
                change_amount INTEGER NOT NULL,
                change_percentage REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()

    def setup_chrome_driver(self):
        """Setup Chrome driver with stable configuration"""
        print("Setting up Chrome driver with stable options...")

        options = Options()

        # Essential options for stability
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--headless=new")  # Use new headless mode

        # Window and display options
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--start-maximized")

        # Security and performance options
        options.add_argument("--disable-web-security")
        options.add_argument("--disable-features=VizDisplayCompositor")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-plugins")
        options.add_argument("--disable-images")
        options.add_argument("--disable-javascript")  # Only if not needed

        # User agent
        options.add_argument(
            "--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

        # Memory and process options
        options.add_argument("--memory-pressure-off")
        options.add_argument("--max_old_space_size=4096")

        # Disable logging
        options.add_argument("--disable-logging")
        options.add_argument("--log-level=3")

        # Additional stability options
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        # Prefs for better stability
        prefs = {
            "profile.default_content_setting_values": {
                "notifications": 2,
                "media_stream_mic": 2,
                "media_stream_camera": 2
            }
        }
        options.add_experimental_option("prefs", prefs)

        try:
            # Try multiple driver setup methods
            driver = None

            # Method 1: Use system Chrome
            try:
                service = Service()
                driver = webdriver.Chrome(service=service, options=options)
                print("✅ Using system Chrome")
            except Exception as e1:
                print(f"Method 1 failed: {e1}")

                # Method 2: Use local chromedriver
                try:
                    local_driver_path = "./chromedriver"
                    if not os.path.exists(local_driver_path):
                        local_driver_path = "./chromedriver.exe"

                    if os.path.exists(local_driver_path):
                        service = Service(local_driver_path)
                        driver = webdriver.Chrome(service=service, options=options)
                        print(f"✅ Using local driver: {local_driver_path}")
                    else:
                        raise Exception("Local chromedriver not found")

                except Exception as e2:
                    print(f"Method 2 failed: {e2}")

                    # Method 3: Use webdriver-manager
                    try:
                        from webdriver_manager.chrome import ChromeDriverManager
                        service = Service(ChromeDriverManager().install())
                        driver = webdriver.Chrome(service=service, options=options)
                        print("✅ Using webdriver-manager")
                    except Exception as e3:
                        print(f"Method 3 failed: {e3}")
                        raise Exception("All driver setup methods failed")

            # Configure driver settings
            if driver:
                driver.set_page_load_timeout(60)
                driver.implicitly_wait(10)

                # Test driver
                driver.execute_script("return navigator.userAgent")
                print("✅ Driver test successful")

                return driver

        except Exception as e:
            print(f"❌ Failed to setup Chrome driver: {e}")
            return None

    def fallback_price_fetch(self):
        """Fallback method using requests when Selenium fails"""
        print("🔄 Trying fallback method with requests...")

        try:
            import requests
            from bs4 import BeautifulSoup

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive'
            }

            url = os.getenv("TARGET_URL",
                            "https://www.bushikaku.net/search/niigata_tokyo/nagaoka_shinjuku/202506/time_division_type-night/")

            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Look for price patterns
            price_patterns = re.findall(r'(\d{1,2},?\d{3})円', response.text)
            prices = []

            for price_str in price_patterns:
                try:
                    price = int(price_str.replace(',', ''))
                    if 1000 <= price <= 50000:
                        prices.append(price)
                except ValueError:
                    continue

            if prices:
                today = datetime.now().strftime("%Y-%m-%d")
                min_price = min(prices)
                return {today: min_price}
            else:
                return {}

        except Exception as e:
            print(f"❌ Fallback method also failed: {e}")
            return {}

    def extract_prices_selenium(self, driver):
        """Extract prices using Selenium"""
        print("🔍 Extracting prices with Selenium...")

        url = os.getenv("TARGET_URL",
                        "https://www.bushikaku.net/search/niigata_tokyo/nagaoka_shinjuku/202506/time_division_type-night/")

        try:
            print(f"📄 Loading: {url}")
            driver.get(url)

            # Wait for page to load
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            # Additional wait for dynamic content
            time.sleep(10)

            print(f"📋 Page title: {driver.title}")

            # Try multiple extraction strategies
            prices_data = {}

            # Strategy 1: Look for calendar tables
            try:
                tables = driver.find_elements(By.TAG_NAME, "table")
                print(f"Found {len(tables)} tables")

                for table in tables:
                    rows = table.find_elements(By.TAG_NAME, "tr")
                    for row in rows:
                        cells = row.find_elements(By.TAG_NAME, "td")
                        if len(cells) >= 7:  # Calendar row
                            for cell in cells:
                                text = cell.text.strip()
                                if text:
                                    # Look for date and price
                                    date_match = re.search(r'^(\d{1,2})$', text.split('\n')[0])
                                    if date_match:
                                        day = int(date_match.group(1))
                                        price_matches = re.findall(r'(\d{1,2},?\d{3})', text)
                                        for price_str in price_matches:
                                            try:
                                                price = int(price_str.replace(',', ''))
                                                if 1000 <= price <= 50000:
                                                    date_str = f"2025-06-{day:02d}"
                                                    prices_data[date_str] = price
                                                    print(f"Found: {date_str} -> ¥{price}")
                                            except ValueError:
                                                continue
            except Exception as e:
                print(f"Strategy 1 error: {e}")

            # Strategy 2: Search page source directly
            if not prices_data:
                try:
                    page_source = driver.page_source
                    price_patterns = re.findall(r'(\d{1,2},?\d{3})円', page_source)

                    prices = []
                    for price_str in price_patterns:
                        try:
                            price = int(price_str.replace(',', ''))
                            if 1000 <= price <= 50000:
                                prices.append(price)
                        except ValueError:
                            continue

                    if prices:
                        today = datetime.now().strftime("%Y-%m-%d")
                        min_price = min(prices)
                        prices_data[today] = min_price
                        print(f"Strategy 2 found: {today} -> ¥{min_price}")

                except Exception as e:
                    print(f"Strategy 2 error: {e}")

            return prices_data

        except TimeoutException:
            print("❌ Page load timeout")
            return {}
        except WebDriverException as e:
            print(f"❌ WebDriver error: {e}")
            return {}
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return {}

    def save_to_database(self, prices_data):
        """Save prices to database and detect changes"""
        if not prices_data:
            return []

        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        changes_detected = []

        for date_str, price in prices_data.items():
            cursor.execute("SELECT min_price FROM daily_prices WHERE date = ?", (date_str,))
            existing = cursor.fetchone()

            if existing:
                old_price = existing[0]
                if old_price != price:
                    change_amount = price - old_price
                    change_percentage = (change_amount / old_price) * 100

                    cursor.execute('''
                        UPDATE daily_prices 
                        SET min_price = ?, updated_at = CURRENT_TIMESTAMP 
                        WHERE date = ?
                    ''', (price, date_str))

                    cursor.execute('''
                        INSERT INTO price_changes 
                        (date, old_price, new_price, change_amount, change_percentage)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (date_str, old_price, price, change_amount, change_percentage))

                    changes_detected.append({
                        'date': date_str,
                        'old_price': old_price,
                        'new_price': price,
                        'change_amount': change_amount,
                        'change_percentage': change_percentage
                    })
            else:
                import json
                cursor.execute('''
                    INSERT INTO daily_prices (date, min_price, prices_json)
                    VALUES (?, ?, ?)
                ''', (date_str, price, json.dumps({date_str: price})))

        conn.commit()
        conn.close()

        return changes_detected

    def get_lowest_price_this_week(self, prices_data):
        """Get the lowest price for this week"""
        if not prices_data:
            return None

        today = datetime.now()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)

        week_prices = []
        for date_str, price in prices_data.items():
            try:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                if week_start <= date_obj <= week_end:
                    week_prices.append(price)
            except ValueError:
                continue

        return min(week_prices) if week_prices else min(prices_data.values())

    def send_price_update(self, prices_data, changes_detected, lowest_week_price):
        """Send price update to Telegram (limited to 2 weeks)"""
        current_time = datetime.now().strftime("%H:%M %d/%m/%Y")

        if lowest_week_price:
            message = f"🚌 Bus Nagaoka → Shinjuku ({current_time})\n\n"
            message += f"💰 Giá thấp nhất tuần này: ¥{lowest_week_price:,}\n\n"

            if prices_data:
                message += "📅 Giá 2 tuần gần nhất:\n"
                # Sort dates and take only the most recent 14 entries
                sorted_dates = sorted(prices_data.items(), key=lambda x: x[0], reverse=True)[:14]
                for date_str, price in sorted_dates:
                    try:
                        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                        formatted_date = date_obj.strftime("%d/%m")
                        message += f"  {formatted_date}: ¥{price:,}\n"
                    except ValueError:
                        continue
        else:
            message = f"🚍 Không tìm thấy giá bus ({current_time})"

        send_to_telegram(message, parse_mode=None)

        # Send price change alerts
        if changes_detected:
            for change in changes_detected:
                date_obj = datetime.strptime(change['date'], "%Y-%m-%d")
                formatted_date = date_obj.strftime("%d/%m/%Y")

                if change['change_amount'] < 0:
                    emoji = "📉"
                    trend = "giảm"
                else:
                    emoji = "📈"
                    trend = "tăng"

                change_msg = f"{emoji} Giá bus {trend}!\n\n"
                change_msg += f"📅 Ngày: {formatted_date}\n"
                change_msg += f"💴 Giá cũ: ¥{change['old_price']:,}\n"
                change_msg += f"💰 Giá mới: ¥{change['new_price']:,}\n"
                change_msg += f"📊 Thay đổi: {change['change_amount']:+,} ({change['change_percentage']:+.1f}%)"

                send_to_telegram(change_msg, parse_mode=None)

    def run(self):
        """Main execution function with fallback support"""
        print("=== Starting Stable Bus Price Tracker ===")

        prices_data = {}

        # Try Selenium first
        driver = self.setup_chrome_driver()
        if driver:
            try:
                prices_data = self.extract_prices_selenium(driver)
            except Exception as e:
                print(f"❌ Selenium extraction failed: {e}")
            finally:
                try:
                    driver.quit()
                except:
                    pass

        # If Selenium failed, try fallback
        if not prices_data:
            print("🔄 Selenium failed, trying fallback method...")
            prices_data = self.fallback_price_fetch()

        # Process results
        if prices_data:
            print(f"✅ Found {len(prices_data)} price entries")

            lowest_week_price = self.get_lowest_price_this_week(prices_data)
            changes_detected = self.save_to_database(prices_data)
            self.send_price_update(prices_data, changes_detected, lowest_week_price)

            print("✅ Bus price tracking completed successfully")
            return True
        else:
            print("❌ No prices found with any method")
            send_to_telegram("🚍 Không tìm thấy giá bus. Website có thể đang bảo trì.", parse_mode=None)
            return False


def main():
    """Main function"""
    tracker = StableBusPriceTracker()
    return tracker.run()


if __name__ == "__main__":
    main()