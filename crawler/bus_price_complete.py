# crawler/crawler_bus_price_complete.py
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
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from services.telegram_bot import send_to_telegram


class BusPriceTracker:
    def __init__(self):
        self.db_file = "bus_prices.db"
        self.init_database()

    def init_database(self):
        """Initialize SQLite database"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        # Create table for daily prices
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

        # Create table for price changes
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
        print("Database initialized successfully")

    def setup_driver(self):
        """Setup Chrome driver"""
        print("Setting up Chrome driver...")

        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

        try:
            # Use manually downloaded chromedriver
            driver_path = "./chromedriver.exe"  # Adjust path as needed
            if os.path.exists(driver_path):
                service = Service(driver_path)
                driver = webdriver.Chrome(service=service, options=options)
            else:
                driver = webdriver.Chrome(options=options)

            return driver
        except Exception as e:
            print(f"Error setting up driver: {e}")
            return None

    def extract_prices_from_calendar(self, driver):
        """Extract prices from the monthly calendar"""
        print("Looking for price calendar...")

        prices_data = {}

        try:
            # Wait for page to load completely
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            time.sleep(5)

            # Look for calendar table with multiple strategies
            calendar_selectors = [
                "table",
                "[class*='calendar']",
                "[class*='lowest']",
                ".calendar",
                "tbody"
            ]

            calendar_found = False
            for selector in calendar_selectors:
                try:
                    calendar_elements = driver.find_elements(By.CSS_SELECTOR, selector)

                    for calendar in calendar_elements:
                        # Look for rows with date and price information
                        rows = calendar.find_elements(By.TAG_NAME, "tr")

                        for row in rows:
                            cells = row.find_elements(By.TAG_NAME, "td")
                            if len(cells) >= 7:  # Weekly calendar row
                                for i, cell in enumerate(cells):
                                    cell_text = cell.text.strip()

                                    # Look for date and price pattern
                                    if cell_text:
                                        # Extract date (look for numbers 1-31)
                                        date_match = re.search(r'^(\d{1,2})$', cell_text.split('\n')[0])
                                        if date_match:
                                            day = int(date_match.group(1))

                                            # Look for price in the cell (format: numbers followed by 円 or ¥)
                                            price_matches = re.findall(r'(\d{1,2},?\d{3})(?:円|¥)', cell_text)
                                            if price_matches:
                                                try:
                                                    price = int(price_matches[0].replace(',', ''))
                                                    if 1000 <= price <= 50000:  # Reasonable price range
                                                        # Generate full date (current month)
                                                        current_date = datetime.now()
                                                        date_str = f"2025-06-{day:02d}"  # June 2025
                                                        prices_data[date_str] = price
                                                        print(f"Found price: {date_str} -> ¥{price}")
                                                        calendar_found = True
                                                except ValueError:
                                                    continue

                    if calendar_found:
                        break

                except Exception as e:
                    print(f"Error with selector {selector}: {e}")
                    continue

            # Alternative: Look for any price patterns in the entire page
            if not prices_data:
                print("Calendar method failed, trying alternative approach...")
                page_source = driver.page_source

                # Look for price patterns
                price_patterns = re.findall(r'(\d{1,2},?\d{3})円', page_source)
                current_prices = []

                for price_str in price_patterns:
                    try:
                        price = int(price_str.replace(',', ''))
                        if 1000 <= price <= 50000:
                            current_prices.append(price)
                    except ValueError:
                        continue

                if current_prices:
                    # Use today's date
                    today = datetime.now().strftime("%Y-%m-%d")
                    min_price = min(current_prices)
                    prices_data[today] = min_price
                    print(f"Alternative method found: {today} -> ¥{min_price}")

            return prices_data

        except Exception as e:
            print(f"Error extracting prices: {e}")
            return {}

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

    def save_to_database(self, prices_data):
        """Save prices to database and detect changes"""
        if not prices_data:
            return None

        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        changes_detected = []

        for date_str, price in prices_data.items():
            # Check if this date already exists
            cursor.execute("SELECT min_price FROM daily_prices WHERE date = ?", (date_str,))
            existing = cursor.fetchone()

            if existing:
                old_price = existing[0]
                if old_price != price:
                    # Price changed
                    change_amount = price - old_price
                    change_percentage = (change_amount / old_price) * 100

                    # Update existing record
                    cursor.execute('''
                        UPDATE daily_prices 
                        SET min_price = ?, updated_at = CURRENT_TIMESTAMP 
                        WHERE date = ?
                    ''', (price, date_str))

                    # Record the change
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
                # New record
                import json
                cursor.execute('''
                    INSERT INTO daily_prices (date, min_price, prices_json)
                    VALUES (?, ?, ?)
                ''', (date_str, price, json.dumps({date_str: price})))

        conn.commit()
        conn.close()

        return changes_detected

    def get_recent_prices(self, days=7):
        """Get recent prices from database"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT date, min_price FROM daily_prices 
            ORDER BY date DESC LIMIT ?
        ''', (days,))

        results = cursor.fetchall()
        conn.close()

        return {date: price for date, price in results}

    def send_price_update(self, prices_data, changes_detected, lowest_week_price):
        """Send price update to Telegram (limited to 2 weeks)"""
        current_time = datetime.now().strftime("%H:%M %d/%m/%Y")

        # Basic price report
        if lowest_week_price:
            message = f"🚌 Bus Nagaoka → Shinjuku ({current_time})\n\n"
            message += f"💰 Giá thấp nhất tuần này: ¥{lowest_week_price:,}\n\n"

            # Show only 2 weeks (14 days) of prices
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

        # Send price change alerts (unchanged)
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
        """Main execution function"""
        print("=== Starting Bus Price Tracker ===")

        driver = self.setup_driver()
        if not driver:
            send_to_telegram("❌ Không thể khởi tạo trình duyệt", parse_mode=None)
            return

        try:
            # Navigate to the page
            url = os.getenv("TARGET_URL",
                            "https://www.bushikaku.net/search/niigata_tokyo/nagaoka_shinjuku/202506/time_division_type-night/")

            print(f"Loading: {url}")
            driver.get(url)

            # Wait for page to load
            time.sleep(10)

            # Extract prices
            prices_data = self.extract_prices_from_calendar(driver)

            if prices_data:
                print(f"Found {len(prices_data)} price entries")

                # Get lowest price this week
                lowest_week_price = self.get_lowest_price_this_week(prices_data)

                # Save to database and detect changes
                changes_detected = self.save_to_database(prices_data)

                # Send updates
                self.send_price_update(prices_data, changes_detected, lowest_week_price)

                print("✅ Bus price tracking completed successfully")
            else:
                print("❌ No prices found")
                send_to_telegram("🚍 Không tìm thấy giá bus hôm nay", parse_mode=None)

        except Exception as e:
            error_msg = f"❌ Lỗi hệ thống: {str(e)}"
            send_to_telegram(error_msg, parse_mode=None)
            print(f"Error: {e}")

        finally:
            driver.quit()


def main():
    """Main function"""
    tracker = BusPriceTracker()
    tracker.run()


if __name__ == "__main__":
    main()