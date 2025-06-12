# services/gold_price_service.py - Fixed version
from services.service_registry import BaseService, ServiceConfig
import os


class GoldPriceService(BaseService):
    def get_config(self) -> ServiceConfig:
        return ServiceConfig(
            name="gold_price",
            description="Current gold prices in Vietnam",
            keywords=["gold", "vàng", "giá vàng", "vang", "gia vang", "sjc", "doji"],
            emoji="🪙",
            category="finance",
            requires_env=["BOT_TOKEN", "CHAT_ID"]
        )

    def execute(self) -> bool:
        try:
            # Try enhanced version first (returns 3 values)
            try:
                from crawler.crawler_gold import fetch_gold_prices, format_as_code_block, send_to_telegram

                result = fetch_gold_prices()

                # Handle both old (2 values) and new (3 values) return formats
                if len(result) == 3:
                    buy_trend, data, source_name = result
                    print(f"✅ Using enhanced version with source: {source_name}")
                else:
                    buy_trend, data = result
                    source_name = "Unknown"
                    print("✅ Using standard version")

                if data:
                    # Format and send gold data
                    if len(result) == 3:
                        # Enhanced version with source
                        send_to_telegram(format_as_code_block(data, source_name))
                    else:
                        # Standard version without source
                        send_to_telegram(format_as_code_block(data))

                    # Send trend message
                    user_tag = os.getenv('USER_TAG', '')
                    if buy_trend == 'increase':
                        send_to_telegram(f"Có nên mua vàng không má {user_tag} 🤔🤔🤔", parse_mode=None)
                    elif buy_trend == 'decrease':
                        send_to_telegram(f"✅ Mua vàng đi má {user_tag} 🧀🧀🧀", parse_mode=None)
                    else:
                        send_to_telegram(f"📊 Giá vàng cập nhật từ {source_name}", parse_mode=None)

                    print("✅ Gold price data sent successfully")
                    return True
                else:
                    print("❌ No gold data retrieved")
                    send_to_telegram("❌ Không thể lấy giá vàng từ tất cả các nguồn", parse_mode=None)
                    return False

            except ImportError:
                print("❌ Gold crawler module not found")
                return False

        except Exception as e:
            error_msg = f"❌ Gold price service error: {str(e)}"
            print(error_msg)

            # Send error notification to user
            try:
                from services.telegram_bot import send_to_telegram
                send_to_telegram(f"❌ Lỗi hệ thống gold bot: {str(e)[:100]}...", parse_mode=None)
            except:
                pass

            return False