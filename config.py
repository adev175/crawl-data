import os
from dotenv import load_dotenv

# Load .env
ENV_PATH = "/secrets/.env"

# Kiểm tra nếu file tồn tại, thì load từ file đó, nếu không thì dùng load_dotenv() mặc định
if os.path.exists(ENV_PATH):
    load_dotenv(dotenv_path=ENV_PATH)
else:
    load_dotenv()

# Lấy các biến môi trường
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
USER_TAG = os.getenv("USER_TAG", "")

# Các hằng số / đường dẫn cố định
TELEGRAM_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage" if BOT_TOKEN else None
URL = "https://www.24h.com.vn/gia-vang-hom-nay-c425.html"
TIMEOUT = 15

# Safe logging - only show if variables are set, not their values
print("Environment variables status:")
print(f"BOT_TOKEN: {'✅ Set' if BOT_TOKEN else '❌ Missing'}")
print(f"CHAT_ID: {'✅ Set' if CHAT_ID else '❌ Missing'}")
print(f"USER_TAG: {'✅ Set' if USER_TAG else '❌ Missing'}")

# Check if running in GitHub Actions
if os.getenv('GITHUB_ACTIONS') == 'true':
    print("🐙 Running in GitHub Actions environment")
    if not BOT_TOKEN or not CHAT_ID:
        print("❌ Required secrets not found in GitHub Actions!")
        print("Make sure to set BOT_TOKEN and CHAT_ID in repository secrets.")
else:
    print("🏠 Running in local environment")