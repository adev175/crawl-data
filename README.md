# 🔧 How to Add New Services

## **Quick Start:**

1. **Create service file** in `services/` directory with `_service.py` suffix
2. **Inherit from BaseService** and implement required methods
3. **Restart chatbot** - auto-discovery will load your service

## **Service Template:**

```python
# services/your_new_service.py
from services.service_registry import BaseService, ServiceConfig
from services.telegram_bot import send_to_telegram
import requests
import os

class YourNewService(BaseService):
    def get_config(self) -> ServiceConfig:
        return ServiceConfig(
            name="your_service",
            description="What your service does", 
            keywords=["keyword1", "keyword2", "từ khóa"],
            emoji="🔥",
            category="your_category",  # finance, news, utility, etc.
            requires_env=["BOT_TOKEN", "CHAT_ID", "YOUR_API_KEY"]  # optional
        )
    
    def execute(self) -> bool:
        try:
            # Your service logic here
            
            # Example: Send result to Telegram
            send_to_telegram("🔥 Your service result!", parse_mode="Markdown")
            
            return True  # Success
            
        except Exception as e:
            print(f"Your service error: {e}")
            return False  # Failed
```

## **Real Examples:**

### **BTC Price Service:**
```python
# services/btc_service.py
import requests
from services.service_registry import BaseService, ServiceConfig
from services.telegram_bot import send_to_telegram

class BTCService(BaseService):
    def get_config(self) -> ServiceConfig:
        return ServiceConfig(
            name="btc",
            description="Bitcoin price and trends",
            keywords=["btc", "bitcoin", "crypto", "giá bitcoin"],
            emoji="₿",
            category="finance"
        )
    
    def execute(self) -> bool:
        try:
            response = requests.get(
                "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd,vnd&include_24hr_change=true"
            )
            
            data = response.json()['bitcoin']
            message = f"₿ **Bitcoin:** ${data['usd']:,.2f} (₫{data['vnd']:,.0f})\n📊 24h: {data['usd_24h_change']:+.2f}%"
            
            send_to_telegram(message, parse_mode="Markdown")
            return True
        except:
            return False
```

### **Notion Knowledge Base Service:**
```python
# services/notion_service.py
import requests
import os
from services.service_registry import BaseService, ServiceConfig
from services.telegram_bot import send_to_telegram

class NotionService(BaseService):
    def get_config(self) -> ServiceConfig:
        return ServiceConfig(
            name="notion",
            description="Search Notion knowledge base",
            keywords=["notion", "kb", "docs", "notes", "search"],
            emoji="📝",
            category="productivity",
            requires_env=["NOTION_TOKEN", "NOTION_DATABASE_ID"]
        )
    
    def execute(self) -> bool:
        try:
            headers = {
                'Authorization': f'Bearer {os.getenv("NOTION_TOKEN")}',
                'Notion-Version': '2022-06-28',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(
                f'https://api.notion.com/v1/databases/{os.getenv("NOTION_DATABASE_ID")}/query',
                headers=headers,
                json={"page_size": 5}
            )
            
            pages = response.json().get('results', [])
            
            if pages:
                message = "📝 **Recent Notion Pages:**\n\n"
                for page in pages:
                    title = page.get('properties', {}).get('Name', {}).get('title', [])
                    title_text = title[0]['plain_text'] if title else 'Untitled'
                    url = page.get('url', '')
                    message += f"• [{title_text}]({url})\n"
                
                send_to_telegram(message, parse_mode="Markdown")
                return True
            
            return False
        except:
            return False
```

### **Weather Service:**
```python
# services/weather_service.py
import requests
import os
from services.service_registry import BaseService, ServiceConfig
from services.telegram_bot import send_to_telegram

class WeatherService(BaseService):
    def get_config(self) -> ServiceConfig:
        return ServiceConfig(
            name="weather",
            description="Weather forecast for Nagaoka",
            keywords=["weather", "thời tiết", "forecast", "rain"],
            emoji="🌤️",
            category="utility",
            requires_env=["OPENWEATHER_API_KEY"]
        )
    
    def execute(self) -> bool:
        try:
            api_key = os.getenv('OPENWEATHER_API_KEY')
            response = requests.get(
                f"http://api.openweathermap.org/data/2.5/weather?q=Nagaoka,JP&appid={api_key}&units=metric"
            )
            
            data = response.json()
            temp = data['main']['temp']
            description = data['weather'][0]['description']
            
            message = f"🌤️ **Nagaoka Weather:**\n🌡️ {temp}°C, {description}"
            send_to_telegram(message, parse_mode="Markdown")
            return True
        except:
            return False
```

## **Categories:**
- **finance** - Financial data (stocks, crypto, gold)
- **news** - News and updates
- **transport** - Travel and transportation
- **utility** - General tools (weather, time, etc.)
- **productivity** - Work tools (Notion, GitHub, etc.)
- **developer** - Development tools
- **entertainment** - Fun stuff

## **Environment Variables:**
Add to your `.env` file:
```env
# Existing
BOT_TOKEN=your_telegram_bot_token
CHAT_ID=your_telegram_chat_id

# New services
NOTION_TOKEN=secret_...
NOTION_DATABASE_ID=...
OPENWEATHER_API_KEY=...
GITHUB_TOKEN=...
```

## **Testing Your Service:**

1. **Test manually:**
   ```python
   from services.your_service import YourService
   service = YourService()
   result = service.execute()
   print(f"Success: {result}")
   ```

2. **Test via chatbot:**
   - Start chatbot: `python telegram_chatbot.py`
   - Send keyword to Telegram
   - Check results

3. **Debug:**
   - Check console output
   - Verify environment variables
   - Test API endpoints separately

## **Tips:**

✅ **Use descriptive keywords** - Include both English and Vietnamese  
✅ **Handle errors gracefully** - Always return True/False  
✅ **Add helpful emojis** - Makes messages more engaging  
✅ **Keep responses concise** - Telegram has message limits  
✅ **Test thoroughly** - Check all edge cases  

❌ **Don't block execution** - Keep services fast  
❌ **Don't hardcode values** - Use environment variables  
❌ **Don't ignore errors** - Log and handle exceptions  

The system will automatically discover and load your service! 🚀