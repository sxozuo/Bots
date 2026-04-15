import asyncio
import re
import aiosqlite
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

BOT_TOKEN = "8241945653:AAFwDmguMaKys7vXAR4l7YNZ6Fwk5JeKnXg"
ADMIN_IDS = [103303270, 218946128]

FORBIDDEN_STUFF = r"(?i)(порно|porn|цп|cp|детское\s+видео|sell\s+stars|аккаунты\s+вк|tg\s+stars)"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

async def init_db():
    async with aiosqlite.connect("fheta_base.db") as db:
        await db.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, warns INTEGER DEFAULT 0)")
        await db.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value INTEGER)")
        await db.commit()

async def get_main_chat():
    async with aiosqlite.connect("fheta_base.db") as db:
        async with db.execute("SELECT value FROM settings WHERE key = 'main_chat_id'") as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None

@dp.message(Command("start"), F.chat.type == "private")
async def fheta_start(message: types.Message):
    start_text = (
        "<tg-emoji emoji_id='5431343743113471043'>🛡</tg-emoji> <b>Fheta Manager</b>\n"
        "—————————————————\n"
        f"Привет, {message.from_user.first_name}! <tg-emoji emoji_id='5431523326265715104'>✨</tg-emoji>\n\n"
        "Бот закреплен за чатом и работает в режиме мониторинга.\n\n"
        "<tg-emoji emoji_id='5431505330369571011'>⚙️</tg-emoji> <b>Статус:</b> Активен\n"
        "<tg-emoji emoji_id='5431523326265715104'>🔒</tg-emoji> <b>Доступ:</b> Приватный\n"
    )
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="💎 Профиль", callback_data="my_profile"),
                types.InlineKeyboardButton(text="🆘 Помощь", callback_data="help_info"))
    if message.from_user.id in ADMIN_IDS:
        builder.row(types.InlineKeyboardButton(text="🔧 Перепривязать чат", callback_data="rebind_chat"))
    await message.answer(start_text, reply_markup=builder.as_markup(), parse_mode="HTML")

@dp.callback_query(F.data == "rebind_chat")
async def rebind_info(callback: types.CallbackQuery):
    await callback.message.answer("Введите <code>!привязать</code> в нужной группе.")
    await callback.answer()

@dp.callback_query(F.data == "my_profile")
async def show_profile_callback(callback: types.CallbackQuery):
    async with aiosqlite.connect("fheta_base.db") as db:
        async with db.execute("SELECT warns FROM users WHERE user_id = ?", (callback.from_user.id,)) as cursor:
            row = await cursor.fetchone()
            warns = row[0] if row else 0
    await callback.message.answer(f"👤 <b>Профиль:</b> {callback.from_user.first_name}\n⚠️ Варны: {warns}/3")
    await callback.answer()

@dp.message(F.text == "!привязать", F.chat.type.in_({"group", "supergroup"}))
async def bind_chat_cmd(message: types.Message):
    if message.from_user.id not in ADMIN_IDS: return
    async with aiosqlite.connect("fheta_base.db") as db:
        await db.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('main_chat_id', ?)", (message.chat.id,))
        await db.commit()
    await message.answer(f"✅ Чат привязан!\nID: <code>{message.chat.id}</code>")

@dp.message(F.chat.type.in_({"group", "supergroup"}))
async def main_handler(message: types.Message):
    main_id = await get_main_chat()
    if message.chat.id != main_id: return
    if message.text and re.search(FORBIDDEN_STUFF, message.text):
        try:
            await message.delete()
            async with aiosqlite.connect("fheta_base.db") as db:
                await db.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (message.from_user.id,))
                await db.execute("UPDATE users SET warns = warns + 1 WHERE user_id = ?", (message.from_user.id,))
                await db.commit()
                cur = await db.execute("SELECT warns FROM users WHERE user_id = ?", (message.from_user.id,))
                w = (await cur.fetchone())[0]
            if w >= 3:
                await bot.ban_chat_member(message.chat.id, message.from_user.id)
                await message.answer(f"🚫 {message.from_user.first_name} забанен за нарушения.")
            else:
                await message.answer(f"⚠️ {message.from_user.first_name}, запрещенка удалена. Варны: {w}/3")
            return
        except: pass

    if not message.text: return
    cmd, uid = message.text.lower(), message.from_user.id
    if uid in ADMIN_IDS and message.reply_to_message:
        target = message.reply_to_message.from_user.id
        if cmd.startswith("!бан"): await bot.ban_chat_member(message.chat.id, target)
        elif cmd.startswith("!варн"):
            async with aiosqlite.connect("fheta_base.db") as db:
                await db.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (target,))
                await db.execute("UPDATE users SET warns = warns + 1 WHERE user_id = ?", (target,))
                await db.commit()
            await message.answer("⚠️ Варн выдан.")
        elif cmd.startswith("!разварн"):
            async with aiosqlite.connect("fheta_base.db") as db:
                await db.execute("UPDATE users SET warns = 0 WHERE user_id = ?", (target,))
                await db.commit()
            await message.answer("✅ Варны сняты.")

    if message.reply_to_message:
        t_name = message.reply_to_message.from_user.first_name
        if cmd.startswith("кусь"): await message.answer(f"🦷 {message.from_user.first_name} куснул {t_name}")
        elif cmd.startswith("обнять"): await message.answer(f"🫂 {message.from_user.first_name} обнял {t_name}")

async def main():
    await init_db()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
  
