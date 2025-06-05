# Gold Price Crawler Bot

This project is a bot that fetches gold prices from a website and sends the data to a Telegram chat. It also provides recommendations based on the trend of gold prices.

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/quochuyyy1839/crawl-price-gold.git
    cd crawl-price-gold
    ```

2. Install the required dependencies:
    ```sh
    pip3 install -r requirements.txt
    ```

## Configuration

1. Create a `.env` file in the root directory of the project and add the following variables:
    ```sh
    BOT_TOKEN=your_telegram_bot_token
    CHAT_ID=your_telegram_chat_id
    USER_TAG=@your_telegram_username
    ```

2. Update the following configuration variables in `crawler-gold.py`:
    - `BOT_TOKEN`: Your Telegram bot token.
    - `CHAT_ID`: The chat ID where the bot will send messages.
    - `USER_TAG`: Your Telegram username.

## Usage

Run the bot:
```sh
python3 main.py
```
Or simple run:
```sh
python3 crawler-gold.py
```

The bot will fetch the gold prices, format the data, and send it to the specified Telegram chat. It will also send a recommendation message based on the trend of gold prices.

## License

This project is licensed under the MIT License.
