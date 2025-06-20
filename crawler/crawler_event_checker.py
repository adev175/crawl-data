# crawler/event_checker_crawler.py
import time
import random
import re
from datetime import datetime, timedelta, timezone
from utils.day_converter import convert_day_to_vietnamese
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

# Base URL for Event Checker
BASE_URL = "https://event-checker.info/"


def setup_chrome_driver():
    """Setup Chrome driver optimized for Japanese websites"""
    print("Setting up Chrome driver...")

    options = Options()

    # Essential options
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    # Japanese-optimized options
    options.add_argument("--lang=ja-JP")
    options.add_argument("--accept-lang=ja-JP,ja,en-US,en")

    # Performance options
    options.add_argument("--disable-images")
    options.add_argument("--disable-javascript")  # Most content should be static
    options.add_argument("--disable-plugins")
    options.add_argument("--disable-extensions")

    # User agent
    options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    # Additional stability options
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    try:
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(60)
        driver.implicitly_wait(10)

        print("✅ Chrome driver setup successful")
        return driver

    except Exception as e:
        print(f"❌ Failed to setup Chrome driver: {e}")
        return None


def fetch_events(max_events=10):
    """Fetch events using Selenium"""
    print(f"Fetching events from {BASE_URL}...")

    driver = setup_chrome_driver()
    if not driver:
        return []

    try:
        # Add random delay
        time.sleep(random.uniform(1, 3))

        print(f"Loading page: {BASE_URL}")
        driver.get(BASE_URL)

        # Wait for page to load
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        print("✅ Page loaded successfully")

        # Additional wait for dynamic content
        time.sleep(5)

        # Get page source and parse
        page_source = driver.page_source
        print(f"Page source length: {len(page_source)}")

        # Parse events directly from page source
        events = parse_events_from_source(page_source)

        return events[:max_events]

    except TimeoutException:
        print("❌ Page load timeout")
        return []
    except WebDriverException as e:
        print(f"❌ WebDriver error: {e}")
        return []
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return []
    finally:
        try:
            driver.quit()
        except:
            pass


def parse_events_from_source(page_source):
    """Parse events directly from page source text"""
    events = []

    try:
        print("Parsing events from page source...")

        # Method 1: Look for 今週のイベント section
        weekly_events_found = False

        # Find the section containing 今週のイベント
        if '今週のイベント' in page_source:
            print("✅ Found 今週のイベント section")
            weekly_events_found = True

            # Extract the section around 今週のイベント
            start_pos = page_source.find('今週のイベント')

            # Get a reasonable chunk of text after the heading (next 2000 chars)
            section_text = page_source[start_pos:start_pos + 2000]

            print(f"Section text sample: {section_text[:300]}")

            # Parse the bullet point events: ・6/18 マック 恐竜バーガーズ
            event_lines = re.findall(r'・([^・\n<>]+)', section_text)

            print(f"Found {len(event_lines)} event lines")

            for line in event_lines:
                line = line.strip()
                if len(line) > 5:  # Skip very short lines

                    # Extract date and title: "6/18 マック 恐竜バーガーズ"
                    date_match = re.match(r'^([0-9]+/[0-9]+(?:-[0-9]+/[0-9]+)?)\s+(.+)$', line)

                    if date_match:
                        date_part = date_match.group(1)
                        title_part = date_match.group(2).strip()

                        # Clean title from HTML entities
                        title_part = clean_html_entities(title_part)

                        event = {
                            'title': title_part,
                            'link': BASE_URL,
                            'date': date_part,
                            'summary': f"今週のイベント: {line}"
                        }

                        events.append(event)
                        print(f"✅ Extracted: {event['title']}")
                    else:
                        # If doesn't match date pattern, still add it
                        title = clean_html_entities(line.strip())
                        if len(title) > 3:
                            event = {
                                'title': title,
                                'link': BASE_URL,
                                'date': '',
                                'summary': f"今週のイベント: {line}"
                            }
                            events.append(event)
                            print(f"✅ Extracted (no date): {event['title']}")

        # Method 2: If no 今週のイベント found, look for bullet patterns anywhere
        if not weekly_events_found:
            print("📝 今週のイベント section not found, looking for bullet patterns...")

            # Find all bullet point lines in the entire page
            event_lines = re.findall(r'・([^・\n<>]+)', page_source)

            print(f"Found {len(event_lines)} total bullet point lines")

            # Filter and process lines that look like events
            for line in event_lines:
                line = line.strip()

                # Basic filtering for event-like content
                if (len(line) > 10 and
                        re.search(r'[0-9]+/[0-9]+', line) and  # Has date pattern
                        not any(skip in line for skip in ['メニュー', 'ホーム', 'サイト', 'ページ'])):

                    date_match = re.match(r'^([0-9]+/[0-9]+(?:-[0-9]+/[0-9]+)?)\s+(.+)$', line)

                    if date_match:
                        date_part = date_match.group(1)
                        title_part = clean_html_entities(date_match.group(2).strip())

                        event = {
                            'title': title_part,
                            'link': BASE_URL,
                            'date': date_part,
                            'summary': line
                        }

                        events.append(event)
                        print(f"✅ Extracted: {event['title']}")

        # Remove duplicates
        seen_titles = set()
        unique_events = []

        for event in events:
            title = event['title'].strip()
            if title not in seen_titles and len(title) > 2:
                unique_events.append(event)
                seen_titles.add(title)

        print(f"✅ Found {len(unique_events)} unique events")
        return unique_events

    except Exception as e:
        print(f"❌ Error parsing events: {e}")
        import traceback
        traceback.print_exc()
        return []


def clean_html_entities(text):
    """Clean HTML entities and unwanted characters"""
    if not text:
        return ""

    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)

    # Common HTML entities
    html_entities = {
        '&amp;': '&',
        '&lt;': '<',
        '&gt;': '>',
        '&quot;': '"',
        '&#39;': "'",
        '&nbsp;': ' ',
        '&yen;': '¥'
    }

    for entity, replacement in html_entities.items():
        text = text.replace(entity, replacement)

    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text.strip())

    return text


def format_events(events):
    """Format events for Telegram message"""
    print("Formatting events for Telegram...")

    # Get current time in JST (Japan Standard Time)
    now = datetime.now(timezone.utc) + timedelta(hours=9)
    current_time = now.strftime("%H:%M:%S")
    current_day = convert_day_to_vietnamese(now.strftime("%A"))
    current_date = now.strftime("%d/%m/%Y")

    message_lines = [
        f"{current_time} {current_day} {current_date}: イベント情報 🎪",
        ""
    ]

    for idx, event in enumerate(events, 1):
        # Format: number + markdown link
        if event['link']:
            title_line = f"{idx}. [{event['title']}]({event['link']})"
        else:
            title_line = f"{idx}. {event['title']}"

        message_lines.append(title_line)

        # Add date if available
        if event.get('date'):
            message_lines.append(f"    📅 {event['date']}")

        # Add summary if available and different from title
        if event.get('summary') and event['summary'] != event['title']:
            summary = event['summary']
            if len(summary) > 100:
                summary = summary[:97] + "..."
            message_lines.append(f"    📝 {summary}")

        message_lines.append("")  # Empty line between events

    print("Events formatted successfully.")
    return "\n".join(message_lines).strip()


def main():
    """Main function for testing"""
    print("Testing Event Checker with Selenium...")
    print("=" * 50)

    events = fetch_events(8)

    if events:
        print(f"\n✅ Found {len(events)} events:")
        for i, event in enumerate(events, 1):
            print(f"\n{i}. {event['title']}")
            print(f"   Date: {event.get('date', 'N/A')}")
            print(f"   Link: {event.get('link', 'N/A')}")
            if event.get('summary'):
                print(f"   Summary: {event['summary'][:80]}...")

        print("\n" + "=" * 50)
        print("Formatted Telegram message:")
        print("=" * 50)
        formatted = format_events(events)
        print(formatted)
    else:
        print("❌ No events found")


if __name__ == "__main__":
    main()