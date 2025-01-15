import asyncio

from aiogram import Router, Bot
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import Message
from gigachat import GigaChat

from bot.definitions import GIGACHAT_KEY
from bot.handlers.permission_handlers import permission_check
from bot.sql.keys import check_if_key_exists, add_key, get_all_keys, remove_key
from bot.sql.users import get_all_users, get_user_setting, get_user_table_setting, set_user_setting
from bot.utils.sql_utils import generate_key

router = Router()

@router.message(Command("cl"))
async def cl(message: Message, bot: Bot):
    if not await permission_check(message.from_user.id, message.chat.id, bot, dev_command=True):
        return

    await message.answer(
        "Команды: \n\n"
        "/get_key - получить ключ\n"
        "/keys - все доступные ключи на данный момент\n"
        "/remove_key key - удалить ключ\n"
        "/remove_all_keys - удалить все ключи\n"
        "/all_experts - получить всех текущих экспертов\n"
        "/forbid id - сделать эксперта обычным пользователем\n"
        "/balance - проверить остаток токенов на балансе"
    )

@router.message(Command("balance"))
async def balance(message: Message, bot: Bot):
    if not await permission_check(message.from_user.id, message.chat.id, bot, dev_command=True):
        return

    with GigaChat(credentials=GIGACHAT_KEY, verify_ssl_certs=False) as giga:
        remaining_balance = (await giga.aget_balance()).balance
        for balance in remaining_balance:
            if balance.usage == "GigaChat":
                await message.answer(f"Остаток токенов: {balance.value}")
                return


@router.message(Command("all_experts"))
async def all_experts(message: Message, bot: Bot):
    if not await permission_check(message.from_user.id, message.chat.id, bot, dev_command=True):
        return

    all_users = await get_all_users()
    experts = []
    for user in all_users:
        user_id = user["user_id"]
        is_expert = await get_user_setting(user_id, "is_expert")
        if is_expert:
            first_name = await get_user_setting(user_id, "name")
            last_name = await get_user_setting(user_id, "surname")
            username = await get_user_table_setting(user_id, "username")
            experts.append((user_id, first_name, last_name, username))

    if len(experts) == 0:
        await message.answer("Нет экспертов на текущий момент.")
    else:
        text = "Список экспертов:\n\n"
        for i, expert in enumerate(experts):
            text += f"{i + 1}: `{expert[0]}` - {expert[1]} {expert[2]} (@{expert[3]})\n"
        await message.answer(text=text, parse_mode=ParseMode.MARKDOWN)


@router.message(Command("forbid"))
async def forbid(message: Message, bot: Bot):
    if not await permission_check(message.from_user.id, message.chat.id, bot, dev_command=True):
        return

    text = message.text
    text = text.lstrip('/forbid').strip()
    args = text.split()

    if len(args) != 1:
        await message.answer("Количество аргументов должно быть равно 1")
        return

    user_id = args[0]
    if not user_id.isdigit():
        await message.answer("ID пользователя должно быть числом")
        return
    user_id = int(user_id)
    await set_user_setting(user_id, "is_expert", False)
    await message.answer(f"Пользователь {user_id} исключен из списка экспертов.")


@router.message(Command("get_key"))
async def get_key(message: Message, bot: Bot):
    if not await permission_check(message.from_user.id, message.chat.id, bot, dev_command=True):
        return

    key = generate_key()

    while await check_if_key_exists(key):
        key = generate_key()
        await asyncio.sleep(0.05)

    await add_key(key)

    text = f'Ключ для авторизации: `{key}`\n'

    await message.answer(text, parse_mode=ParseMode.MARKDOWN_V2)

@router.message(Command("keys"))
async def get_key(message: Message, bot: Bot):
    if not await permission_check(message.from_user.id, message.chat.id, bot, dev_command=True):
        return

    keys = await get_all_keys()
    if len(keys) == 0:
        text = "Нет доступных ключей на данный момент"
    else:
        text = "Все доступные ключи: \n\n"

        for key in keys:
            text += f"`{key}`\n"

    await message.answer(text, parse_mode=ParseMode.MARKDOWN_V2)

@router.message(Command("remove_key"))
async def delete_key(message: Message, bot: Bot):
    if not await permission_check(message.from_user.id, message.chat.id, bot, dev_command=True):
        return

    text = message.text
    text = text.lstrip('/remove_key').strip()
    args = text.split()

    if len(args) != 1:
        await message.answer("Количество аргументов должно быть равно 1")
        return

    key = args[0]
    if await check_if_key_exists(key):
        await remove_key(key)
        await message.answer("Ключ успешно удален.")
    else:
        await message.answer("Такого ключа не существует")

@router.message(Command("remove_all_keys"))
async def delete_all_keys(message: Message, bot: Bot):
    if not await permission_check(message.from_user.id, message.chat.id, bot, dev_command=True):
        return

    keys = await get_all_keys()
    for key in keys:
        await remove_key(key)

    await message.answer("Все ключи удалены")
