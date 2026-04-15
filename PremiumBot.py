import asyncio, aiosqlite
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

# ПРОВЕРЬ ТОКЕН ПЕРЕД ЗАПУСКОМ!
BOT_TOKEN = "8241945653:AAFwDmguMaKys7vXAR4l7YNZ6Fwk5JeKnXg"
ADMIN_IDS = [103303270, 218946128]
DB_PATH = "/tmp/fheta_guard.db"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("CREATE TABLE IF NOT EXISTS triggers (keyword TEXT PRIMARY KEY, response TEXT, type TEXT)")
        await db.commit()

@dp.message(Command("start"), F.chat.type == "private")
async def start_cmd(message: types.Message):
    me = await bot.get_me()
    text = (
        "<tg-emoji emoji_id='5431343743113471043'>🛡</tg-emoji> <b>Fheta Total Security</b>\n"
        "—————————————————\n"
        f"Здравствуйте, {message.from_user.first_name}! <tg-emoji emoji_id='5431523326265715104'>✨</tg-emoji>\n\n"
        "Система защиты чата онлайн.\n\n"
        "<tg-emoji emoji_id='5431505330369571011'>⚙️</tg-emoji> <b>Статус:</b> Online"
    )
    kb = InlineKeyboardBuilder()
    kb.row(types.InlineKeyboardButton(text="➕ Добавить в группу", url=f"https://t.me/{me.username}?startgroup=true"))
    await message.answer(text, reply_markup=kb.as_markup(), parse_mode="HTML")

@dp.message(F.text.startswith(("+триггер", "+действие")), F.from_user.id.in_(ADMIN_IDS))
async def add_cmd(message: types.Message):
    try:
        is_rp = message.text.startswith("+действие")
        parts = message.text.replace("+действие" if is_rp else "+триггер", "").strip().split("|")
        word, action = parts[0].strip().lower(), parts[1].strip()
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("INSERT OR REPLACE INTO triggers VALUES (?, ?, ?)", (word, action, "rp" if is_rp else "text"))
            await db.commit()
        await message.answer("✅ Сохранено")
    except: pass

@dp.message(F.chat.type.in_({"group", "supergroup"}))
async def guard_hdl(message: types.Message):
    content = (message.text or message.caption or "").lower()
    if not content: return
    
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT keyword, response, type FROM triggers") as c:
            for key, res, t_type in await c.fetchall():
                # Логика удаления (полная зачистка)
                if res.lower() == "удалить" and key in content:
                    try:
                        if message.reply_to_message:
                            await bot.delete_message(message.chat.id, message.reply_to_message.message_id)
                        return await message.delete()
                    except: pass
                
                # РП и обычные триггеры
                if key == content:
                    if t_type == "rp" and message.reply_to_message:
                        u1, u2 = message.from_user.first_name, message.reply_to_message.from_user.first_name
                        return await message.answer(f"✨ <b>{u1}</b> {res} <b>{u2}</b>", parse_mode="HTML")
                    elif t_type == "text":
                        return await message.reply(res)

async def main():
    await init_db()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
