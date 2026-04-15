import asyncio, aiosqlite
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

BOT_TOKEN = "8241945653:AAFwDmguMaKys7vXAR4l7YNZ6Fwk5JeKnXg"
ADMIN_IDS = [103303270, 218946128]
DB_PATH = "/tmp/fheta_total_guard.db"

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
        "Режим полной зачистки активен. Удаляю триггеры и любые медиа-реплаи на них."
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
        await message.answer(f"<tg-emoji emoji_id='5431523326265715104'>✅</tg-emoji> Фильтр <b>{word}</b> добавлен.")
    except: pass

@dp.message(F.chat.type.in_({"group", "supergroup"}))
async def security_hdl(message: types.Message):
    # 1. ПРОВЕРКА НА ТРИГГЕРЫ (ТЕКСТ ИЛИ ПОДПИСЬ)
    content = (message.text or message.caption or "").lower()
    
    async with aiosqlite.connect(DB_PATH) as db:
        # Ищем все запрещенные слова
        async with db.execute("SELECT keyword FROM triggers WHERE response = 'удалить'") as c:
            bad_words = [row[0] for row in await c.fetchall()]

    # Проверка текущего сообщения
    for word in bad_words:
        if word in content:
            try:
                # Если это медиа-ответ на запрещенку, удаляем и оригинал
                if message.reply_to_message:
                    await bot.delete_message(message.chat.id, message.reply_to_message.message_id)
                await message.delete()
                return
            except: pass

    # 2. ПРОВЕРКА РЕПЛАЕВ (ЕСЛИ КТО-ТО ОТВЕТИЛ МЕДИА НА ТРИГГЕР)
    if message.reply_to_message and (message.photo or message.video or message.animation or message.document):
        reply_content = (message.reply_to_message.text or message.reply_to_message.caption or "").lower()
        for word in bad_words:
            if word in reply_content:
                try:
                    # Удаляем и медиа-ответ, и само слово, на которое ответили
                    await bot.delete_message(message.chat.id, message.reply_to_message.message_id)
                    await message.delete()
                    return
                except: pass

    # 3. ОБРАБОТКА РП И ОБЫЧНЫХ ОТВЕТОВ (ТОЧНОЕ СОВПАДЕНИЕ)
    if content:
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT response, type FROM triggers WHERE keyword = ?", (content,)) as c:
                row = await c.fetchone()
                if row:
                    res, t_type = row[0], row[1]
                    if t_type == "rp" and message.reply_to_message:
                        u1, u2 = message.from_user.first_name, message.reply_to_message.from_user.first_name
                        return await message.answer(f"✨ <b>{u1}</b> {res} <b>{u2}</b>", parse_mode="HTML")
                    if t_type == "text" and res.lower() != "удалить":
                        await message.reply(res)

async def main():
    await init_db()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
