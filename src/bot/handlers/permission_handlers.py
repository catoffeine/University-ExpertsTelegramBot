from aiogram import Bot

from bot.definitions import DEVELOPER_ID
from bot.sql.users import check_if_user_exists


async def permission_check(user_id: int, chat_id: int, bot: Bot, dev_command=False, is_start: bool=False):
    if not await check_if_user_exists(user_id):
        print("use does not exist")
        if not is_start:
            await bot.send_message(
                chat_id,
                text="Прежде чем использовать бот, необходимо сначала зарегестрироваться /start"
            )
        return False

    if dev_command and user_id != DEVELOPER_ID:
        await bot.send_message(
            chat_id,
            text="У вас нет прав не использование этой команды"
        )
        return False

    return True