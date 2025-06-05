
# 🤖 Telegram Bot: AI News, Gold Prices, and Bus Fares

This is a multifunctional **Telegram bot** built with Python. It automates fetching and sending updates about:

- 📰 Latest AI news from CNBC
- 🪙 Real-time gold price data in Vietnam
- 🚌 Cheapest bus fares from Nagaoka to Shinjuku

You can run this bot using **Docker** _or_ locally with **Anaconda**. It supports `.env` configuration, modular services, and integrates easily with Telegram.

---

## ⚙️ Environment Variables (.env)

Before running, create a `.env` file with the following variables:

```env
BOT_TOKEN=your_telegram_bot_token
CHAT_ID=your_telegram_chat_id
USER_TAG=@your_username  # Optional tag for mentions
GEMINI_API_KEY=your_google_gemini_key
TARGET_URL=https://www.bushikaku.net/search/niigata_tokyo/nagaoka_shinjuku/20250605/time_division_type-night/
```

---

## 🚀 Quick Start with Docker

0. Start the Docker Desktop application to ensure Docker is running.

1. Build the image:

```bash
docker build -t telegram-news-bot .
```

2. Run the container:

```bash
docker run --env-file .env telegram-news-bot
```

All dependencies, including Chrome and ChromeDriver, are handled in the Dockerfile.

---

## 🧪 Local Setup with Anaconda (Recommended for Development)

1. Clone the repository and navigate into the folder:

```bash
git clone <your-repo-url>
cd telegram-news-bot
```

2. Create and activate environment (single line):

```bash
conda create -n bot_env python=3.10 -y && conda activate bot_env && pip install -r requirements.txt
```

3. Run the bot:

```bash
python main.py
```

---

## 📁 Project Structure

```
.
├── main.py                      # Entry point to run all bots
├── crawl_ai_news.py             # AI news fetcher and formatter
├── crawler_gold.py              # Gold price fetcher and notifier
├── bus_price.py                 # Bus fare fetcher using Selenium
├── services/
│   ├── fetcher.py               # AI news scraper from CNBC
│   ├── formatter.py             # Markdown formatting for Telegram
│   ├── telegram_bot.py          # Message sending abstraction
├── utils/
│   └── ai_summarizer.py         # Gemini/OpenAI summarizer (optional)
├── config.py                    # Loads .env configuration
├── .env                         # Your environment variables (not committed)
├── requirements.txt             # All dependencies
└── Dockerfile                   # Full setup for Chrome + Python
```

---

## 📄 License

This project is MIT licensed. Feel free to use and modify for personal or educational purposes.
