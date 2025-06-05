# 🚌 Bus Price Tracker Setup Guide

## Installation Steps

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Download ChromeDriver Manually
Since you've already done this, make sure `chromedriver.exe` is in your project root folder.

### 3. Update .env File
Add these variables to your `.env` file:
```env
BOT_TOKEN=your_telegram_bot_token
CHAT_ID=your_telegram_chat_id
USER_TAG=@your_username
TARGET_URL=https://www.bushikaku.net/search/niigata_tokyo/nagaoka_shinjuku/202506/time_division_type-night/
```

### 4. Create Required Folders
```bash
mkdir utils
mkdir scheduler
```

## Usage

### Run Individual Bots
```bash
# AI News Bot
python main.py ai

# Gold Price Bot
python main.py gold

# Bus Price Bot (one-time)
python main.py bus

# All bots
python main.py all
```

### Database Management
```bash
# View bus price database
python main.py db

# Or run database manager directly
python utils/bus_db_manager.py
```

### Automatic Monitoring
```bash
# Start continuous monitoring (checks 3x daily)
python main.py schedule

# Or run scheduler directly
python scheduler/bus_price_scheduler.py
```

### Interactive Mode
```bash
# Start interactive menu
python main.py
```

## How It Works

### 🔍 **Price Detection**
- Scrapes the bus booking website calendar
- Extracts prices from monthly view
- Finds lowest price for current week
- Stores all data in SQLite database

### 📊 **Change Detection**
- Compares new prices with historical data
- Calculates price changes and percentages
- Sends alerts only when prices change

### 🔔 **Notifications**
- **Regular Updates**: Shows weekly lowest price
- **Price Alerts**: Immediate notification when prices change
- **Trend Analysis**: Shows if prices are increasing/decreasing

### 🗄️ **Database Features**
- Stores daily prices and changes
- Tracks price history and trends
- Export data to JSON
- Automatic cleanup of old records

## Example Telegram Messages

### Regular Price Update
```
🚌 Bus Nagaoka → Shinjuku (14:30 05/06/2025)

💰 Giá thấp nhất tuần này: ¥4,000

📅 Giá tháng này:
  01/06: ¥4,200
  02/06: ¥4,000
  03/06: ¥4,500
  04/06: ¥4,100
  05/06: ¥4,000
```

### Price Change Alert
```
📉 Giá bus giảm!

📅 Ngày: 05/06/2025
💴 Giá cũ: ¥4,200
💰 Giá mới: ¥4,000
📊 Thay đổi: -200 (-4.8%)
```

## Troubleshooting

### Common Issues

1. **ChromeDriver not found**
   - Ensure `chromedriver.exe` is in project root
   - Check Chrome browser version matches ChromeDriver

2. **No prices found**
   - Website might have changed structure
   - Check if TARGET_URL is correct
   - Try running in non-headless mode for debugging

3. **Database errors**
   - Ensure write permissions in project folder
   - Database file will be created automatically

### Debug Mode
To debug the scraper:
```python
# In crawler_bus_price_complete.py, change:
options.add_argument("--headless")  # Comment this out
```

This will show the browser window so you can see what's happening.

## Scheduling Options

### 1. Manual Scheduling (Recommended)
```bash
python main.py schedule
```
Runs continuously, checks 3 times daily.

### 2. Cron Job (Linux/Mac)
```bash
# Add to crontab for 3 times daily
0 8,14,20 * * * cd /path/to/your/project && python main.py bus
```

### 3. Task Scheduler (Windows)
Create task to run `python main.py bus` at desired times.

## File Structure
```
├── crawler/
│   ├── crawler_bus_price_complete.py    # Main bus scraper
│   ├── crawl_ai_news.py                 # AI news bot
│   └── crawler_gold.py                  # Gold price bot
├── utils/
│   └── bus_db_manager.py                # Database management
├── scheduler/
│   └── bus_price_scheduler.py           # Automatic scheduling
├── services/
│   ├── telegram_bot.py                  # Telegram integration
│   └── ...
├── main.py                              # Main entry point
├── bus_prices.db                        # SQLite database (auto-created)
├── chromedriver.exe                     # ChromeDriver (manual download)
└── .env                                 # Environment variables
```

## Features Summary

✅ **Multi-website scraping** (Bus, Gold, AI News)  
✅ **Price change detection** with percentage calculations  
✅ **SQLite database** for historical data  
✅ **Automatic scheduling** with error handling  
✅ **Telegram notifications** with rich formatting  
✅ **Database management** tools  
✅ **Export capabilities** (JSON)  
✅ **Health monitoring** and error alerts  
✅ **Interactive command-line** interface  

The system is now ready to monitor bus prices and alert you to any changes!