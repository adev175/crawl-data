# services/btc_price_service.py - Example BTC Service
import requests
from services.service_registry import BaseService, ServiceConfig
from services.telegram_bot import send_to_telegram


class BTCPriceService(BaseService):
    def get_config(self) -> ServiceConfig:
        return ServiceConfig(
            name="btc_price",
            description="Current Bitcoin price and trends",
            keywords=["btc", "bitcoin", "crypto", "cryptocurrency", "giá bitcoin"],
            emoji="₿",
            category="finance",
            requires_env=["BOT_TOKEN", "CHAT_ID"]
        )

    def execute(self) -> bool:
        try:
            # Fetch BTC price from CoinGecko API
            response = requests.get(
                "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd,vnd&include_24hr_change=true",
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                btc_data = data['bitcoin']

                usd_price = btc_data['usd']
                vnd_price = btc_data['vnd']
                change_24h = btc_data['usd_24h_change']

                trend_emoji = "📈" if change_24h > 0 else "📉"

                message = f"""₿ **Bitcoin Price Update**

💵 **USD:** ${usd_price:,.2f}
🇻🇳 **VND:** ₫{vnd_price:,.0f}

{trend_emoji} **24h Change:** {change_24h:+.2f}%

🕐 Updated: {datetime.now().strftime('%H:%M %d/%m/%Y')}"""

                send_to_telegram(message, parse_mode="Markdown")
                return True

            return False

        except Exception as e:
            print(f"BTC price service error: {e}")
            return False


# services/notion_service.py - Example Notion Integration
import requests
from services.service_registry import BaseService, ServiceConfig
from services.telegram_bot import send_to_telegram


class NotionService(BaseService):
    def get_config(self) -> ServiceConfig:
        return ServiceConfig(
            name="notion",
            description="Query Notion knowledge base",
            keywords=["notion", "knowledge", "notes", "docs", "search", "kb"],
            emoji="📝",
            category="productivity",
            requires_env=["BOT_TOKEN", "CHAT_ID", "NOTION_TOKEN", "NOTION_DATABASE_ID"]
        )

    def execute(self) -> bool:
        try:
            import os

            notion_token = os.getenv('NOTION_TOKEN')
            database_id = os.getenv('NOTION_DATABASE_ID')

            headers = {
                'Authorization': f'Bearer {notion_token}',
                'Content-Type': 'application/json',
                'Notion-Version': '2022-06-28'
            }

            # Query recent pages
            response = requests.post(
                f'https://api.notion.com/v1/databases/{database_id}/query',
                headers=headers,
                json={
                    "sorts": [{"timestamp": "last_edited_time", "direction": "descending"}],
                    "page_size": 5
                },
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                pages = data.get('results', [])

                if pages:
                    message = "📝 **Recent Notion Updates:**\n\n"
                    for page in pages:
                        title = "Untitled"
                        if page.get('properties', {}).get('Name', {}).get('title'):
                            title = page['properties']['Name']['title'][0]['plain_text']

                        url = page.get('url', '')
                        last_edited = page.get('last_edited_time', '')[:10]

                        message += f"• [{title}]({url})\n  📅 {last_edited}\n\n"

                    send_to_telegram(message, parse_mode="Markdown")
                    return True

            return False

        except Exception as e:
            print(f"Notion service error: {e}")
            return False


# services/weather_service.py - Example Weather Service
import requests
from services.service_registry import BaseService, ServiceConfig
from services.telegram_bot import send_to_telegram


class WeatherService(BaseService):
    def get_config(self) -> ServiceConfig:
        return ServiceConfig(
            name="weather",
            description="Weather forecast for Nagaoka",
            keywords=["weather", "thời tiết", "forecast", "rain", "temperature"],
            emoji="🌤️",
            category="utility",
            requires_env=["BOT_TOKEN", "CHAT_ID", "OPENWEATHER_API_KEY"]
        )

    def execute(self) -> bool:
        try:
            import os

            api_key = os.getenv('OPENWEATHER_API_KEY')
            city = "Nagaoka,JP"

            response = requests.get(
                f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric",
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()

                temp = data['main']['temp']
                feels_like = data['main']['feels_like']
                humidity = data['main']['humidity']
                description = data['weather'][0]['description'].title()

                message = f"""🌤️ **Weather in Nagaoka**

🌡️ **Temperature:** {temp}°C (feels like {feels_like}°C)
💧 **Humidity:** {humidity}%
☁️ **Condition:** {description}

🕐 Updated: {datetime.now().strftime('%H:%M %d/%m/%Y')}"""

                send_to_telegram(message, parse_mode="Markdown")
                return True

            return False

        except Exception as e:
            print(f"Weather service error: {e}")
            return False


# services/github_service.py - Example GitHub Integration
import requests
from services.service_registry import BaseService, ServiceConfig
from services.telegram_bot import send_to_telegram


class GitHubService(BaseService):
    def get_config(self) -> ServiceConfig:
        return ServiceConfig(
            name="github",
            description="GitHub repository stats and recent commits",
            keywords=["github", "git", "repo", "commits", "code"],
            emoji="👨‍💻",
            category="developer",
            requires_env=["BOT_TOKEN", "CHAT_ID", "GITHUB_TOKEN", "GITHUB_REPO"]
        )

    def execute(self) -> bool:
        try:
            import os

            github_token = os.getenv('GITHUB_TOKEN')
            repo = os.getenv('GITHUB_REPO')  # format: "username/repo"

            headers = {
                'Authorization': f'token {github_token}',
                'Accept': 'application/vnd.github.v3+json'
            }

            # Get recent commits
            response = requests.get(
                f'https://api.github.com/repos/{repo}/commits',
                headers=headers,
                params={'per_page': 3},
                timeout=10
            )

            if response.status_code == 200:
                commits = response.json()

                message = f"👨‍💻 **Recent Commits in {repo}:**\n\n"

                for commit in commits:
                    sha = commit['sha'][:7]
                    message_text = commit['commit']['message'].split('\n')[0][:50]
                    author = commit['commit']['author']['name']
                    date = commit['commit']['author']['date'][:10]

                    message += f"• `{sha}` {message_text}\n"
                    message += f"  👤 {author} • 📅 {date}\n\n"

                send_to_telegram(message, parse_mode="Markdown")
                return True

            return False

        except Exception as e:
            print(f"GitHub service error: {e}")
            return False