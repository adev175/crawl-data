# crawler/event_checker_crawler.py
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

        # Handle encoding issues properly
        response.encoding = 'utf-8'

        soup = BeautifulSoup(response.content, 'html.parser', from_encoding='utf-8')
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
    """Parse events from the webpage - Extract all titles like AI news bot"""
    events = []

    try:
        # Method 1: Look for specific title classes (like the h2 you found)
        title_selectors = [
            'h2.entry-card-title',
            'h2[class*="entry-card-title"]',
            'h2[class*="card-title"]',
            '.entry-card-title',
            'h1, h2, h3',  # Fallback to all headings
        ]

        found_titles = False

        for selector in title_selectors:
            title_elements = soup.select(selector)
            if title_elements:
                print(f"✅ Found {len(title_elements)} titles with selector: {selector}")
                found_titles = True

                for element in title_elements:
                    title_text = clean_text(element.get_text())

                    if title_text and len(title_text) > 5:
                        # Look for parent element that might have a link
                        link_elem = element.find_parent('a') or element.find('a')
                        if not link_elem:
                            # Look for sibling or nearby elements with links
                            parent = element.find_parent(['article', 'div'])
                            if parent:
                                link_elem = parent.find('a', href=True)

                        event_link = BASE_URL
                        if link_elem and link_elem.get('href'):
                            href = link_elem.get('href')
                            event_link = urljoin(BASE_URL, href) if not href.startswith('http') else href

                        event = {
                            'title': title_text,
                            'link': event_link,
                            'date': '',
                            'summary': ''
                        }

                        # Look for date in title or surrounding elements
                        date_match = re.search(r'([0-9]+月[0-9]+日)', title_text)
                        if date_match:
                            event['date'] = date_match.group(1)

                        # Try to get summary from nearby elements
                        parent = element.find_parent(['article', 'div'])
                        if parent:
                            # Look for description elements
                            desc_elem = parent.find(['p', 'div'],
                                                    class_=re.compile(r'excerpt|summary|content|desc', re.I))
                            if desc_elem:
                                summary_text = clean_text(desc_elem.get_text())
                                if summary_text and len(summary_text) > 10:
                                    event['summary'] = summary_text[:150] + "..." if len(
                                        summary_text) > 150 else summary_text

                        events.append(event)
                        print(f"✅ Extracted: {event['title'][:50]}...")

                break  # Stop after finding titles with first successful selector

        # Method 2: If no structured titles found, look for all links as fallback
        if not found_titles:
            print("📝 No structured titles found, trying link extraction...")
            links = soup.find_all('a', href=True)
            print(f"Found {len(links)} total links")

            for link in links:
                link_text = clean_text(link.get_text())
                href = link.get('href')

                # Take any substantial link text (no keyword filtering)
                if link_text and len(link_text) > 10 and href:
                    event = {
                        'title': link_text,
                        'link': urljoin(BASE_URL, href) if not href.startswith('http') else href,
                        'date': '',
                        'summary': ''
                    }

                    # Look for date in link text
                    date_match = re.search(r'([0-9]+月[0-9]+日)', link_text)
                    if date_match:
                        event['date'] = date_match.group(1)

                    events.append(event)
                    print(f"✅ Link extracted: {event['title'][:50]}...")

        # Remove duplicates and clean up
        seen_titles = set()
        unique_events = []

        for event in events:
            title = event['title'].strip()

            # Skip navigation/menu items and duplicates
            if (title not in seen_titles and
                    len(title) > 5 and
                    not any(skip in title.lower() for skip in [
                        'ホーム', 'メニュー', 'home', 'menu', 'search', '検索',
                        'about', 'contact', 'privacy', 'サイト', 'ページ'
                    ])):
                unique_events.append(event)
                seen_titles.add(title)

        print(f"✅ Found {len(unique_events)} unique events")
        return unique_events

    except Exception as e:
        print(f"❌ Error parsing events: {e}")
        import traceback
        traceback.print_exc()
        return []


# Remove the complex extraction functions and keep it simple
def clean_text(text):
    """Clean and normalize text - simplified version"""
    if not text:
        return ""

    # Remove extra whitespace and newlines
    text = re.sub(r'\s+', ' ', text.strip())

    # Remove common unwanted phrases
    unwanted_phrases = [
        'Read more', 'Continue reading', '続きを読む', 'もっと見る', 'HOME', 'Menu'
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
    """Format events for Telegram message - simplified like AI news bot"""
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
        # Simple format like AI news: number + markdown link
        if event['link']:
            title_line = f"{idx}. [{event['title']}]({event['link']})"
        else:
            title_line = f"{idx}. {event['title']}"

        message_lines.append(title_line)

        # Add date if available (keep Japanese format)
        if event.get('date'):
            message_lines.append(f"    📅 {event['date']}")

        # Add summary if available
        if event.get('summary'):
            summary = event['summary']
            if len(summary) > 100:
                summary = summary[:97] + "..."
            message_lines.append(f"    📝 {summary}")

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