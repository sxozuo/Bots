import asyncio
import re
import aiosqlite
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

BOT_TOKEN = "8241945653:AAFwDmguMaKys7vXAR4l7YNZ6Fwk5JeKnXg"
ADMIN_IDS = [103303270, 218946128]
FORBIDDEN = r"(?i)(порно|porn|цп|cp|детское\s+видео|sell\s+stars|аккаунты\s+вк|tg\s+stars)"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

async def init_db():
    async with aiosqlite.connect("fheta_base.db") as db:
        await db.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value INTEGER)")
        await db.execute("CREATE TABLE IF NOT EXISTS triggers (keyword TEXT PRIMARY KEY, response TEXT, type TEXT)")
        await db.commit()

@dp.message(Command("start"), F.chat.type == "private")
async def start_cmd(message: types.Message):
    me = await bot.get_me()
    text = (
        "<tg-emoji emoji_id='5431343743113471043'>🛡</tg-emoji> <b>Fheta Manager</b>\n"
        "—————————————————\n"
        f"Здравствуйте, {message.from_user.first_name}! <tg-emoji emoji_id='5431523326265715104'>✨</tg-emoji>\n\n"
        "Управляйте триггерами и РП-командами прямо в чате.\n\n"
        "<tg-emoji emoji_id='5431505330369571011'>⚙️</tg-emoji> <b>Статус:</b> Активен"
    )
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="➕ Добавить в группу", url=f"https://t.me/{me.username}?startgroup=true"))
    await message.answer(text, reply_markup=builder.as_markup(), parse_mode="HTML")

@dp.message(F.text.startswith(("+триггер", "+действие")), F.from_user.id.in_(ADMIN_IDS))
async def add_cmd(message: types.Message):
    try:
        t_type = "rp" if message.text.startswith("+действие") else "text"
        cmd_name = "+действие" if t_type == "rp" else "+триггер"
        parts = message.text.replace(cmd_name, "").strip().split("|")
        async with aiosqlite.connect("fheta_base.db") as db:
            await db.execute("INSERT OR REPLACE INTO triggers VALUES (?, ?, ?)", (parts[0].strip().lower(), parts[1].strip(), t_type))
            await db.commit()
        await message.answer("<tg-emoji emoji_id='5431523326265715104'>✅</tg-emoji> Сохранено!")
    except: pass

@dp.message(F.text.startswith("-триггер"), F.from_user.id.in_(ADMIN_IDS))
async def del_trig(message: types.Message):
    key = message.text.replace("-триггер", "").strip().lower()
    async with aiosqlite.connect("fheta_base.db") as db:
        await db.execute("DELETE FROM triggers WHERE keyword = ?", (key,))
        await db.commit()
    await message.answer("<tg-emoji emoji_id='5431343743113471043'>🗑</tg-emoji> Удалено.")

@dp.message(F.chat.type.in_({"group", "supergroup"}))
async def hdl(message: types.Message):
    if not message.text: return
    low = message.text.lower()
    
    if re.search(FORBIDDEN, low):
        try: return await message.delete()
        except: pass

    async with aiosqlite.connect("fheta_base.db") as db:
        async with db.execute("SELECT response, type FROM triggers WHERE keyword = ?", (low,)) as c:
            r = await c.fetchone()
            if r:
                res_text, res_type = r[0], r[1]
                if res_text.lower() == "удалить":
                    try: await message.delete()
                    except: pass
                elif res_type == "rp" and message.reply_to_message:
                    u1 = message.from_user.first_name
                    u2 = message.reply_to_message.from_user.first_name
                    await message.answer(f"✨ <b>{u1}</b> {res_text} <b>{u2}</b>", parse_mode="HTML")
                elif res_type == "text":
                    ans = await message.reply(res_text)
                    await asyncio.sleep(30)
                    try: await ans.delete()
                    except: pass

async def main():
    await init_db()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
