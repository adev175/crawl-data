# 🤖 Enhanced Telegram Bot Suite

Một hệ thống bot Telegram đa chức năng với kiến trúc service registry, hỗ trợ auto-discovery và extensible architecture.

## ✨ Tính năng chính

### 🔄 **Tự động hóa hoàn toàn**
- **AI News Bot** 🤖 - Tin tức AI mới nhất từ CNBC
- **Gold Price Bot** 🪙 - Giá vàng Việt Nam real-time
- **Bus Price Bot** 🚌 - Giá xe khách Nagaoka ↔ Shinjuku với database tracking
- **Interactive Chatbot** 💬 - Chatbot thông minh phản hồi commands

### 🏗️ **Kiến trúc linh hoạt**
- **Service Registry** - Auto-discovery services mới
- **Extensible** - Dễ dàng thêm services
- **Fallback Support** - Multiple fallback strategies
- **Database Integration** - SQLite tracking cho bus prices
- **GitHub Actions** - Tự động chạy 3 lần/ngày

## 📁 Cấu trúc Project

```
├── 🤖 Bot Core
│   ├── main.py                          # Entry point chính
│   ├── telegram_chatbot.py              # Interactive chatbot
│   ├── chatbot_manager.py               # Quản lý chatbot
│   └── config.py                        # Configuration
│
├── 🔧 Services (Extensible)
│   ├── service_registry.py              # Service discovery engine
│   ├── ai_news_service.py               # AI news service
│   ├── gold_price_service.py            # Gold price service  
│   ├── bus_price_service.py             # Bus price service
│   ├── btc_price_service.py             # Bitcoin service (example)
│   ├── telegram_bot.py                  # Telegram utilities
│   └── formatter.py                     # Message formatting
│
├── 🕷️ Crawlers
│   ├── crawl_ai_news.py                 # CNBC AI news crawler
│   ├── crawler_gold.py                  # Gold price crawler
│   ├── crawler_bus_price_complete.py    # Complete bus price tracker
│   ├── stable_bus_crawler.py            # Stable bus crawler
│   └── github_action_fetcher.py         # Enhanced GitHub Actions support
│
├── 🗄️ Database & Utils
│   ├── utils/
│   │   ├── bus_db_manager.py            # Bus price database manager
│   │   └── day_converter.py             # Vietnamese day converter
│   └── scheduler/
│       └── bus_price_scheduler.py       # Auto price monitoring
│
├── 🚀 Deployment
│   ├── .github/workflows/
│   │   └── telegram-bots.yml           # GitHub Actions workflow
│   ├── Dockerfile                       # Docker container
│   ├── cloudbuild.yaml                  # Google Cloud Build
│   └── requirements.txt                 # Dependencies
│
└── 📝 Documentation
    ├── README.md                        # This file
    └── README_BUS.md                    # Bus tracker detailed guide
```

## 🚀 Quick Start

### 1. Cài đặt Dependencies
```bash
git clone <your-repo>
cd telegram-bot-suite
pip install -r requirements.txt
```

### 2. Cấu hình Environment
```bash
cp .env.example .env
# Chỉnh sửa .env với thông tin của bạn
```

```env
BOT_TOKEN=your_telegram_bot_token
CHAT_ID=your_telegram_chat_id
USER_TAG=@your_username
TARGET_URL=https://www.bushikaku.net/search/...
```

### 3. Chạy Bot

#### **Single Command Mode**
```bash
python main.py ai        # AI news
python main.py gold      # Gold prices  
python main.py bus       # Bus prices
python main.py all       # All bots
```

#### **Interactive Chatbot Mode**
```bash
python main.py chatbot   # Start interactive chatbot
```

#### **Scheduled Mode**
```bash
python main.py schedule  # Auto monitoring
```

#### **Interactive Menu**
```bash
python main.py          # Sho