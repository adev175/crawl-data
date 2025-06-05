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
TELEGRAM_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
URL = "https://www.24h.com.vn/gia-vang-hom-nay-c425.html"
TIMEOUT = 15

print("Loaded environment variables:")
for key, value in os.environ.items():
    print(f"{key}: {value}")