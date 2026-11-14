import asyncio
import logging
import os
import sqlite3
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiohttp import web

# Token Render muhit o'zgaruvchilaridan (Environment Variables) o'qiladi
TOKEN = os.getenv("BOT_TOKEN")

# O'zingizning Telegramdagi ID raqamingizni shu yerga yozasiz:
ADMIN_ID = 7617900973  # <--- Shu yerga o'z ID raqamingizni yozing

if not TOKEN:
    raise ValueError("Xatolik: BOT_TOKEN muhit o'zgaruvchisi topilmadi!")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- 1. MA'LUMOTLAR BAZASI (SQLite) ---
def db_start():
    conn = sqlite3.connect("movies.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS movies (
            id INTEGER PRIMARY KEY,
            movie_code TEXT UNIQUE,
            file_id TEXT,
            caption TEXT
        )
    """)
    # Agar jadval oldindan mavjud bo'lib, caption ustuni bo'lmasa xato bermasligi uchun
    try:
        cursor.execute("ALTER TABLE movies ADD COLUMN caption TEXT")
    except sqlite3.OperationalError:
        pass
        
    conn.commit()
    conn.close()

def add_movie(code, file_id, caption):
    conn = sqlite3.connect("movies.db")
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT OR REPLACE INTO movies (movie_code, file_id, caption) VALUES (?, ?, ?)", 
            (code, file_id, caption)
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"DB Xatolik: {e}")
        return False
    finally:
        conn.close()

def get_movie(code):
    conn = sqlite3.connect("movies.db")
    cursor = conn.cursor()
    cursor.execute("SELECT file_id, caption FROM movies WHERE movie_code = ?", (code,))
    movie = cursor.fetchone()
    conn.close()
    return movie if movie else (None, None)


# --- 2. FSM (Kino qo'shish holati) ---
class AddMovieState(StatesGroup):
    waiting_for_file = State()


# --- 3. BOT BUYRUQLARI ---
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer(
        "        "🎬 **Xush kelibsiz!** ✨\n\n"
        "🍿 *Eng sara va qiziqarli kinolar olamiga marhamat! Bizning bot orqali sevimli filmlaringizni bir soniyada topib olishingiz mumkin.*\n\n"
        "🔍 **Qanday foydalaniladi?**\n"
        "👉 Shunchaki kinoning maxsus **raqamli kodini** yuboring (masalan: `101` yoki `777`).\n\n"
        "⚡️ *Tezkor, qulay va reklamasiz! Maroqli hordiq tilaymiz!* 🎥🍿"
    )"
    )

# Admin uchun kino qo'shish buyrug'i: /add 101
@dp.message(Command("add"))
async def add_cmd(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ Kechirasiz, bu buyruq faqat admin uchun.")
        return

    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("⚠️ Noto'g'ri format! Foydalanish:\n`/add (raqam)`\nMasalan: `/add 101`")
        return

    movie_code = args[1].strip()
    
    await state.update_data(movie_code=movie_code)
    await message.answer(f"📥 `{movie_code}` raqami uchun **kinoni va uning tavsifini (caption)** birga yuboring:")
    await state.set_state(AddMovieState.waiting_for_file)

# Admin yuborgan video va uning tavsifini bazaga saqlash
@dp.message(AddMovieState.waiting_for_file, F.from_user.id == ADMIN_ID)
async def save_movie_file(message: types.Message, state: FSMContext):
    data = await state.get_data()
    movie_code = data.get("movie_code")

    if message.video:
        file_id = message.video.file_id
    elif message.document:
        file_id = message.document.file_id
    else:
        await message.answer("⚠️ Iltimos, video yoki hujjat (file) ko'rinishida yuboring!")
        return

    # Admin video bilan birga yozgan matnni (tavsifni) olamiz
    caption = message.caption if message.caption else ""

    success = add_movie(movie_code, file_id, caption)
    if success:
        await message.answer(f"✅ Muvaffaqiyatli saqlandi!\nKodi: `{movie_code}`")
    else:
        await message.answer("❌ Bazaga saqlashda xatolik yuz berdi.")

    await state.clear()

# Foydalanuvchi kod yuborganda kinoni va uning tavsifini chiqarish
@dp.message(F.text)
async def get_movie_handler(message: types.Message):
    code = message.text.strip()
    file_id, caption = get_movie(code)

    if file_id:
        # Agar admin tavsif yozgan bo'lsa o'shani chiqaramiz, bo'lmasa oddiy kodni yozamiz
        final_caption = caption if caption else f"🎬 Kino kodi: `{code}`"

        await message.answer_video(
            video=file_id, 
            caption=final_caption
        )
    else:
        await message.answer("🔍 Bunday kodli kino topilmadi. Iltimos, to'g'ri kod yuboring.")


# --- 4. RENDER UCHUN VEB-SERVER (Port ochish) ---
async def handle(request):
    return web.Response(text="Bot is running and alive!")

async def web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()


# --- 5. ASOSIY ISHGA TUSHIRISH ---
async def main():
    db_start()
    logging.basicConfig(level=logging.INFO)
    print("Bot va veb-server ishga tushdi...")
    
    await asyncio.gather(
        web_server(),
        dp.start_polling(bot)
    )

if __name__ == "__main__":
    asyncio.run(main())
    
