# crawler/crawler_event_checker.py
import requests
from bs4 import BeautifulSoup
import re
import json
from datetime import datetime, timedelta, timezone
from utils.day_converter import convert_day_to_vietnamese
from urllib.parse import urljoin, urlparse
import time
import random

# Base URL for Event Checker
BASE_URL = "https://event-checker.info/"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "ja,en-US;q=0.7,en;q=0.3",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}


def create_session():
    """Create session with retry logic"""
    session = requests.Session()
    session.headers.update(headers)

    from urllib3.util.retry import Retry
    from requests.adapters import HTTPAdapter

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


def fetch_events(max_events=10):
    """Fetch events from イイベントチェッカー"""
    print(f"Fetching events from {BASE_URL}...")

    session = create_session()

    try:
        # Add random delay to avoid being blocked
        time.sleep(random.uniform(1, 2))

        response = session.get(BASE_URL, timeout=30)
        response.raise_for_status()

        print(f"✅ Successfully connected to Event Checker (status: {response.status_code})")

        soup = BeautifulSoup(response.content, 'html.parser')
        events = parse_events(soup)

        # Limit number of events
        return events[:max_events]

    except requests.exceptions.Timeout:
        print("❌ Timeout connecting to Event Checker")
        return try_fallback_sources()
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
        return try_fallback_sources()
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return []


def parse_events(soup):
    """Parse events from the webpage"""
    events = []

    try:
        # Method 1: Look for event list containers
        event_containers = soup.find_all(['div', 'article', 'section'],
                                         class_=re.compile(r'event|item|post|entry', re.I))

        if not event_containers:
            # Method 2: Look for common event structures
            event_containers = soup.find_all(['div', 'li'],
                                             attrs={'class': re.compile(r'.*')})[:20]

        print(f"Found {len(event_containers)} potential event containers")

        for container in event_containers:
            event = extract_event_info(container)
            if event and event['title'] and event['link']:
                events.append(event)
                print(f"✅ Extracted event: {event['title'][:50]}...")

        # Remove duplicates based on title
        seen_titles = set()
        unique_events = []
        for event in events:
            if event['title'] not in seen_titles:
                unique_events.append(event)
                seen_titles.add(event['title'])

        print(f"✅ Found {len(unique_events)} unique events")
        return unique_events

    except Exception as e:
        print(f"❌ Error parsing events: {e}")
        return []


def extract_event_info(container):
    """Extract event information from a container element"""
    try:
        event = {
            'title': '',
            'date': '',
            'time': '',
            'link': '',
            'description': '',
            'location': ''
        }

        # Extract title
        title_elem = container.find(['h1', 'h2', 'h3', 'h4', 'a'],
                                    class_=re.compile(r'title|name|event', re.I))
        if not title_elem:
            title_elem = container.find('a')
        if not title_elem:
            title_elem = container.find(['h1', 'h2', 'h3', 'h4'])

        if title_elem:
            event['title'] = clean_text(title_elem.get_text())

        # Extract link
        link_elem = container.find('a', href=True)
        if link_elem:
            href = link_elem.get('href')
            if href:
                if href.startswith('http'):
                    event['link'] = href
                else:
                    event['link'] = urljoin(BASE_URL, href)

        # Extract date and time information
        date_patterns = [
            r'(\d{4})[年/-](\d{1,2})[月/-](\d{1,2})[日]?',  # 2024年12月25日 or 2024/12/25
            r'(\d{1,2})[月/-](\d{1,2})[日]?',  # 12月25日 or 12/25
            r'(\d{1,2})/(\d{1,2})',  # 12/25
        ]

        time_patterns = [
            r'(\d{1,2}):(\d{2})',  # 14:30
            r'(\d{1,2})時(\d{2})?分?',  # 14時30分 or 14時
        ]

        # Search for date/time in text content
        text_content = container.get_text()

        for pattern in date_patterns:
            match = re.search(pattern, text_content)
            if match:
                if len(match.groups()) == 3:  # Full date with year
                    event['date'] = f"{match.group(1)}/{match.group(2):>02}/{match.group(3):>02}"
                elif len(match.groups()) == 2:  # Month/day only
                    current_year = datetime.now().year
                    event['date'] = f"{current_year}/{match.group(1):>02}/{match.group(2):>02}"
                break

        for pattern in time_patterns:
            match = re.search(pattern, text_content)
            if match:
                if len(match.groups()) == 2 and match.group(2):
                    event['time'] = f"{match.group(1):>02}:{match.group(2):>02}"
                else:
                    event['time'] = f"{match.group(1):>02}:00"
                break

        # Extract description (first few sentences)
        desc_elem = container.find(['p', 'div'],
                                   class_=re.compile(r'desc|summary|content', re.I))
        if desc_elem:
            event['description'] = clean_text(desc_elem.get_text())[:200]

        # Only return if we have essential information
        if event['title'] and len(event['title']) > 3:
            return event

        return None

    except Exception as e:
        print(f"❌ Error extracting event info: {e}")
        return None


def clean_text(text):
    """Clean and normalize text"""
    if not text:
        return ""

    # Remove extra whitespace and newlines
    text = re.sub(r'\s+', ' ', text.strip())

    # Remove common unwanted phrases
    unwanted_phrases = [
        'Read more', 'Continue reading', '続きを読む', 'もっと見る'
    ]

    for phrase in unwanted_phrases:
        text = text.replace(phrase, '')

    return text.strip()


def try_fallback_sources():
    """Try alternative methods or cached data"""
    print("🔄 Trying fallback methods...")

    # Could implement RSS feed parsing or cached data here
    # For now, return empty list
    return []


def format_events(events):
    """Format events for Telegram message"""
    print("Formatting events for Telegram...")

    # Get current time in JST (Japan Standard Time)
    now = datetime.now(timezone.utc) + timedelta(hours=9)
    current_time = now.strftime("%H:%M:%S")
    current_day = convert_day_to_vietnamese(now.strftime("%A"))
    current_date = now.strftime("%d/%m/%Y")

    message_lines = [
        f"{current_time} {current_day} {current_date}: Sự kiện mới từ Event Checker 🎪",
        ""
    ]

    for idx, event in enumerate(events, 1):
        # Format title with link
        if event['link']:
            title_line = f"{idx}. [{event['title']}]({event['link']})"
        else:
            title_line = f"{idx}. {event['title']}"

        message_lines.append(title_line)

        # Add date and time if available
        if event['date'] or event['time']:
            datetime_info = []
            if event['date']:
                datetime_info.append(f"📅 {event['date']}")
            if event['time']:
                datetime_info.append(f"🕒 {event['time']}")

            if datetime_info:
                message_lines.append(f"    {' '.join(datetime_info)}")

        # Add description if available
        if event['description']:
            desc = event['description']
            if len(desc) > 100:
                desc = desc[:97] + "..."
            message_lines.append(f"    📝 {desc}")

        # Add location if available
        if event['location']:
            message_lines.append(f"    📍 {event['location']}")

        message_lines.append("")  # Empty line between events

    print("Events formatted successfully.")
    return "\n".join(message_lines).strip()


def main():
    """Main function for testing"""
    print("Testing Event Checker crawler...")

    events = fetch_events(5)

    if events:
        print(f"\n✅ Found {len(events)} events:")
        for i, event in enumerate(events, 1):
            print(f"\n{i}. {event['title']}")
            print(f"   Date: {event.get('date', 'N/A')}")
            print(f"   Time: {event.get('time', 'N/A')}")
            print(f"   Link: {event.get('link', 'N/A')}")
            if event.get('description'):
                print(f"   Description: {event['description'][:100]}...")

        print("\n" + "=" * 50)
        print("Formatted message:")
        print("=" * 50)
        formatted = format_events(events)
        print(formatted)
    else:
        print("❌ No events found")


if __name__ == "__main__":
    main()