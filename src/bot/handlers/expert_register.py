from aiogram import Router, Bot
from aiogram.filters import Command
from aiogram.types import Message

from bot.handlers.permission_handlers import permission_check
from bot.sql.keys import check_if_key_exists, remove_key
from bot.sql.users import set_user_setting

router = Router()

@router.message(Command("auth"))
async def auth(message: Message, bot: Bot):
    if not await permission_check(message.from_user.id, message.chat.id, bot):
        return

    text = message.text
    text = text.lstrip('/auth').strip()
    args = text.split()

    if len(args) != 1:
        await message.answer("Ключ не обнаружен\nИспользование команды: /auth ключ")
        return

    key = args[0]
    if await check_if_key_exists(key):
        await set_user_setting(message.from_user.id, "is_expert", True)
        await remove_key(key)
        await message.answer("Вы зарегистрированы в качестве эксперта!")
    else:
        await message.answer("Неверный ключ доступа.")

