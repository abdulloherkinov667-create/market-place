import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command 

logging.basicConfig(level=logging.INFO)

TOKEN = "8664343682:AAF1kA0nwrIeLZjwUsbV97Za_J1Ry90sGBc"
ADMIN_IDS = [6411347321, 8327989068]

bot = Bot(token=TOKEN)
dp = Dispatcher()
waiting_for_support = set()

@dp.message(CommandStart())
async def start_handler(message: types.Message):
    if message.from_user.id in ADMIN_IDS:
        await message.answer("Salom admin! Qo'llab-quvvatlash bo'limiga xush kelibsiz.")
    else:
        await message.answer(f"""
                        Qo'llab-quvvatlash bo'limiga xush kelibsiz!
                        Iltimos, muammoingizni yoki savolingizni yozib yuboring.
                        Yuborilsa, sizga tasdiq xabari yuboriladi.
                        """)


@dp.message()
async def support_message_handler(message: types.Message):
    # Faqat matnli xabarlarni tekshiramiz
    if message.from_user.id in waiting_for_support:
        if not message.text:
            await message.answer("Iltimos, murojaatingizni matn ko'rinishida yozing.")
            return

        text = message.text.strip()
        waiting_for_support.discard(message.from_user.id)

        # Barcha adminga xabar yuborish
        for admin_id in ADMIN_IDS:
            try:
                username = f"@{message.from_user.username}" if message.from_user.username else "mavjud emas"
                await bot.send_message(
                    admin_id,
                    f"📩 **Yangi support murojaati:**\n\n"
                    f"👤 Foydalanuvchi: {message.from_user.full_name}\n"
                    f"🔗 Username: {username}\n"
                    f"🆔 ID: {message.from_user.id}\n"
                    f"📝 Matn: {text}"
                )
            except Exception as e:
                logging.error(f"Admin {admin_id} ga yuborishda xatolik: {e}")

        # Foydalanuvchiga tasdiqlash xabari
        await message.answer("❗️ Sizning murojaatingiz qabul qilindi. Tez orada javob beramiz.")

async def main():
    print("Bot ishlamoqda...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Bot to'xtatildi")