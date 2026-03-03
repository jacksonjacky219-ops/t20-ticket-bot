import os
import asyncio
from telegram.ext import ApplicationBuilder, CommandHandler
from playwright.async_api import async_playwright

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
LAST_STATUS = {}


async def start(update, context):
    await update.message.reply_text("🚀 Cloud Monitor Started\nUse /subscribe")


async def subscribe(update, context):
    SUBSCRIBERS.add(update.effective_chat.id)
    await update.message.reply_text("✅ Subscribed for alerts")


async def unsubscribe(update, context):
    SUBSCRIBERS.discard(update.effective_chat.id)
    await update.message.reply_text("❌ Unsubscribed")


async def check_seat_layout(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        await page.goto(url, timeout=60000)
        await page.wait_for_timeout(5000)

        content = await page.content()
        await browser.close()

        text = content.lower()

        layout_accessible = "block" in text

        prices = []
        if "₹2000" in text:
            prices.append("₹2000")
        if "₹3000" in text:
            prices.append("₹3000")
        if "₹3500" in text:
            prices.append("₹3500")
        if "₹4000" in text:
            prices.append("₹4000")

        return {
            "layout_accessible": layout_accessible,
            "prices": prices
        }


async def monitor(app):
    while True:
        print("Checking seat layouts...")

        for name, data in MATCHES.items():
            try:
                result = await check_seat_layout(data["seat_url"])
                previous = LAST_STATUS.get(name)

                if previous != result:
                    LAST_STATUS[name] = result

                    if result["layout_accessible"]:
                        price_list = ", ".join(result["prices"]) if result["prices"] else "Detected"

                        message = f"""
🚨 SEAT LAYOUT LIVE 🚨

🏏 Match: {name}

💺 Layout Accessible
💰 Prices: {price_list}

🔗 Book Here:
{data['seat_url']}
                        """

                        for user in SUBSCRIBERS:
                            await app.bot.send_message(chat_id=user, text=message)

            except Exception as e:
                print("Error:", e)

        await asyncio.sleep(30)


async def post_init(app):
    app.create_task(monitor(app))


def main():
    if not TOKEN:
        print("TOKEN missing")
        return

    app = ApplicationBuilder().token(TOKEN).post_init(post_init).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("subscribe", subscribe))
    app.add_handler(CommandHandler("unsubscribe", unsubscribe))

    print("🔥 Playwright Cloud Monitor Running")
    app.run_polling()


if __name__ == "__main__":
    main()
