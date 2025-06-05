# crawler/crawler_bus_price.py
import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from services.telegram_bot import send_to_telegram
from datetime import datetime

path = "C:\chromedriver-win64\chromedriver-win64\chromedriver.exe" ###chrome driver path
def setup_driver():
    """Setup Chrome driver with proper options"""
    print("Setting up Chrome driver...")

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

    # Additional options for better stability
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    try:
        service = Service(executable_path=path)
        driver = webdriver.Chrome(service=service, options=options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        return driver
    except Exception as e:
        print(f"Error setting up driver: {e}")
        return None


def wait_for_page_load(driver, timeout=30):
    """Wait for page to fully load"""
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        return True
    except TimeoutException:
        print("Page load timeout")
        return False


def fetch_cheapest_bus_price():
    """Fetch the cheapest bus price from the website"""
    print("Starting bus price fetcher...")

    # Get URL from environment or use default
    URL = os.getenv("TARGET_URL",
                    "https://www.bushikaku.net/search/niigata_tokyo/nagaoka_shinjuku/20250605/time_division_type-night/")

    print(f"Target URL: {URL}")

    driver = setup_driver()
    if not driver:
        send_to_telegram("❌ Không thể khởi tạo Chrome driver", parse_mode=None)
        return

    try:
        print("Loading page...")
        driver.get(URL)

        # Wait for page to load
        if not wait_for_page_load(driver):
            send_to_telegram("❌ Trang web không tải được", parse_mode=None)
            return

        # Additional wait for dynamic content
        time.sleep(5)

        # Take screenshot for debugging (optional)
        # driver.save_screenshot("debug_screenshot.png")

        # Try multiple selector strategies
        prices = []
        selectors_to_try = [
            # Original selector
            {
                "container": "SearchLowestPriceCalendar_lowest-price-calendar__f8m0U",
                "buttons": "SearchLowestPriceCalendar_day_button_qHWJ2"
            },
            # Alternative selectors (in case class names changed)
            {
                "container": "[class*='lowest-price-calendar']",
                "buttons": "[class*='day_button']"
            },
            {
                "container": "[class*='calendar']",
                "buttons": "button[class*='day']"
            }
        ]

        calendar_found = False

        for selector_set in selectors_to_try:
            try:
                print(f"Trying selector: {selector_set['container']}")

                # Try to find calendar container
                if "class*=" in selector_set["container"]:
                    calendar = driver.find_element(By.CSS_SELECTOR, selector_set["container"])
                else:
                    calendar = driver.find_element(By.CLASS_NAME, selector_set["container"])

                print("Calendar container found!")
                calendar_found = True

                # Find price buttons
                if "class*=" in selector_set["buttons"]:
                    buttons = calendar.find_elements(By.CSS_SELECTOR, selector_set["buttons"])
                else:
                    buttons = calendar.find_elements(By.CLASS_NAME, selector_set["buttons"])

                print(f"Found {len(buttons)} price buttons")

                # Extract prices
                for i, btn in enumerate(buttons):
                    try:
                        price_text = btn.text.strip()
                        print(f"Button {i + 1} text: '{price_text}'")

                        # Clean price text and extract number
                        clean_price = price_text.replace("円", "").replace(",", "").replace("¥", "")

                        # Try to extract number from text
                        import re
                        numbers = re.findall(r'\d+', clean_price)
                        if numbers:
                            price = int(numbers[0])
                            if 1000 <= price <= 50000:  # Reasonable price range
                                prices.append(price)
                                print(f"Valid price found: ¥{price}")

                    except (ValueError, AttributeError) as e:
                        print(f"Error processing button {i + 1}: {e}")
                        continue

                if prices:
                    break  # Success, no need to try other selectors

            except (NoSuchElementException, TimeoutException) as e:
                print(f"Selector {selector_set['container']} not found: {e}")
                continue

        # If no calendar found, try alternative approach
        if not calendar_found:
            print("Calendar not found, trying alternative approach...")

            # Look for any elements containing price information
            price_elements = driver.find_elements(By.XPATH, "//*[contains(text(), '円') or contains(text(), '¥')]")
            print(f"Found {len(price_elements)} elements with price indicators")

            for elem in price_elements:
                try:
                    text = elem.text.strip()
                    print(f"Price element text: '{text}'")

                    # Extract numbers from text
                    import re
                    numbers = re.findall(r'\d+', text.replace(",", ""))
                    for num_str in numbers:
                        num = int(num_str)
                        if 1000 <= num <= 50000:
                            prices.append(num)
                            print(f"Alternative method found price: ¥{num}")

                except Exception as e:
                    continue

        # Process results
        if prices:
            min_price = min(prices)
            max_price = max(prices)
            avg_price = sum(prices) // len(prices)

            current_time = datetime.now().strftime("%H:%M %d/%m/%Y")

            message = f"""🚌 Bus Nagaoka → Shinjuku ({current_time})

Giá rẻ nhất: ¥{min_price:,}
Giá cao nhất: ¥{max_price:,}
Giá trung bình: ¥{avg_price:,}
Tổng {len(prices)} chuyến tìm thấy"""

            send_to_telegram(message, parse_mode=None)
            print(f"Success! Found {len(prices)} prices, cheapest: ¥{min_price}")

        else:
            # Send debug info
            page_title = driver.title
            page_source_preview = driver.page_source[:500] + "..." if len(
                driver.page_source) > 500 else driver.page_source

            error_message = f"""🚍 Không tìm thấy giá bus hôm nay

Debug info:
- Page title: {page_title}
- URL: {URL}
- Calendar found: {calendar_found}
- Page source preview: {page_source_preview}"""

            send_to_telegram(error_message, parse_mode=None)
            print("No prices found")

    except Exception as e:
        error_msg = f"❌ Lỗi không xác định: {str(e)}"
        send_to_telegram(error_msg, parse_mode=None)
        print(f"Unexpected error: {e}")

    finally:
        print("Closing driver...")
        driver.quit()


def test_bus_crawler():
    """Test function to debug the crawler"""
    print("=== Testing Bus Crawler ===")

    # Test with debug output
    driver = setup_driver()
    if not driver:
        print("Failed to setup driver")
        return

    try:
        URL = os.getenv("TARGET_URL",
                        "https://www.bushikaku.net/search/niigata_tokyo/nagaoka_shinjuku/20250605/time_division_type-night/")

        print(f"Loading: {URL}")
        driver.get(URL)

        time.sleep(10)  # Wait longer for debugging

        print(f"Page title: {driver.title}")
        print(f"Current URL: {driver.current_url}")

        # Save screenshot for manual inspection
        driver.save_screenshot("bus_page_debug.png")
        print("Screenshot saved as bus_page_debug.png")

        # Print page source (first 1000 chars)
        print("Page source preview:")
        print(driver.page_source[:1000])

        # Try to find any elements with price-like text
        all_elements = driver.find_elements(By.XPATH, "//*")
        price_like_elements = []

        for elem in all_elements:
            try:
                text = elem.text.strip()
                if "円" in text or "¥" in text or any(char.isdigit() for char in text):
                    price_like_elements.append(text)
            except:
                continue

        print(f"Found {len(price_like_elements)} elements with price-like text:")
        for text in price_like_elements[:10]:  # Show first 10
            print(f"  - {text}")

    except Exception as e:
        print(f"Test error: {e}")
    finally:
        driver.quit()


if __name__ == "__main__":
    # Uncomment the line below to run debug test
    # test_bus_crawler()

    # Normal execution
    fetch_cheapest_bus_price()