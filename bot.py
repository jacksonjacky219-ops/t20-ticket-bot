import os
import asyncio
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from telegram.ext import ApplicationBuilder, CommandHandler

# 🔐 TOKEN from Railway Environment Variable
TOKEN = os.getenv("TOKEN")

MATCHES = {
    "Semi Final 2": {
        "seat_url": "https://in.bookmyshow.com/sports/icc-men-s-t20-world-cup-2026-semi-final-2/ET00474271/seat-layout/aerialcanvas/WSMI/10235"
    },
    "Final": {
        "seat_url": "https://in.bookmyshow.com/sports/icc-men-s-t20-world-cup-2026-final/ET00476187/seat-layout/aerialcanvas/SPSM/10116"
    }
}

SUBSCRIBERS = set()
LAST_AVAILABLE = {}

# 🔥 STEALTH CHROME DRIVER
def create_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )
    return driver


# 🔁 RETRY LOGIC
def check_seat_layout(url):
    for attempt in range(3):
        try:
            driver = create_driver()
            driver.get(url)
            time.sleep(6)

            page = driver.page_source.lower()

            layout_accessible = "block" in page

            prices = []
            if "₹2000" in page:
                prices.append("₹2000")
            if "₹3000" in page:
                prices.append("₹3000")
            if "₹3500" in page:
                prices.append("₹3500")
            if "₹4000" in page:
                prices.append("₹4000")

            driver.quit()

            return {
                "layout_accessible": layout_accessible,
                "prices": prices
            }

        except WebDriverException:
            print(f"Retry attempt {attempt+1}")
            time.sleep(4)

    return None


async def start(update, context):
    await update.message.reply_text(
        "🚀 Advanced Live Monitor Started\nUse /subscribe"
    )


async def subscribe(update, context):
    SUBSCRIBERS.add(update.effective_chat.id)
    await update.message.reply_text("✅ Subscribed for alerts")


async def unsubscribe(update, context):
    SUBSCRIBERS.discard(update.effective_chat.id)
    await update.message.reply_text("❌ Unsubscribed")


async def monitor(app):
    while True:
        print("\nChecking seat layouts...")

        for name, data in MATCHES.items():
            result = check_seat_layout(data["seat_url"])

            if result is None:
                continue

            previous = LAST_AVAILABLE.get(name)

            if previous != result:
                LAST_AVAILABLE[name] = result

                if result["layout_accessible"]:
                    price_list = (
                        ", ".join(result["prices"])
                        if result["prices"]
                        else "Detected"
                    )

                    message = f"""
🚨 SEAT LAYOUT LIVE 🚨

🏏 Match: {name}

💺 Seat Layout Accessible
💰 Price Blocks: {price_list}

🔗 Open Layout:
{data['seat_url']}
                    """

                    for user in SUBSCRIBERS:
                        await app.bot.send_message(
                            chat_id=user,
                            text=message
                        )

        await asyncio.sleep(30)


async def post_init(app):
    app.create_task(monitor(app))


def main():
    if not TOKEN:
        print("ERROR: TOKEN not found in environment variables")
        return

    app = ApplicationBuilder().token(TOKEN).post_init(post_init).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("subscribe", subscribe))
    app.add_handler(CommandHandler("unsubscribe", unsubscribe))

    print("🔥 Cloud Live Monitor Running (30s interval)")
    app.run_polling()


if __name__ == "__main__":
    main()
