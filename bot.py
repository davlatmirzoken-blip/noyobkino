import os
import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message

# Render muhitidan BOT_TOKEN ni o'qiydi
TOKEN = os.getenv("BOT_TOKEN")

# KINOLARNI QO'SHA OLADIGAN 2 TA ADMINNING TELEGRAM ID'SI
ADMIN_IDS = [9050771937, 7617900973]  # <--- O'zingizning ID raqamlaringizni yozing!

MOVIES_DB = {}

dp = Dispatcher()

@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.answer(
        "🎬 Kino botga xush kelibsiz!\n"
        "Menga kinoning **kodini** yuboring (masalan: `1`, `2`), va men sizga o'sha kinoni topib beraman."
    )

@dp.message(F.video)
async def save_movie_handler(message: Message, bot: Bot) -> None:
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ Sizda kino qo'shish huquqi yo'q!")
        return

    video_file_id = message.video.file_id
    movie_code = str(len(MOVIES_DB) + 1)
    
    MOVIES_DB[movie_code] = video_file_id

    await message.answer(
        f"✅ Kino muvaffaqiyatli bazaga qo'shildi!\n"
        f"📌 **Kino kodi:** `{movie_code}`\n\n"
        f"Foydalanuvchilar shu kodni yuborishsa, ushbu kino chiqadi."
    )

@dp.message(F.text)
async def get_movie_handler(message: Message) -> None:
    code = message.text.strip()

    if code in MOVIES_DB:
        video_id = MOVIES_DB[code]
        await message.answer_video(
            video=video_id,
            caption=f"🎥 Siz so'ragan kino (Kodi: {code})"
        )
    else:
        if message.from_user.id not in ADMIN_IDS:
            await message.answer("❌ Bunday kodli kino topilmadi.")
        else:
            await message.answer("ℹ️ Yangi kino qo'shish uchun shunchaki **video yuboring**.")

async def main() -> None:
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
