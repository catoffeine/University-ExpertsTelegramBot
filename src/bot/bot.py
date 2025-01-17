import asyncio
import sys

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from bot.definitions import TELEGRAM_TOKEN, GIGACHAT_KEY
from bot.handlers import user_questionary, dev_commands, expert_register, ai_questions
from bot.sql.sql import db_init
from bot.sql.users import get_all_users

scheduler = AsyncIOScheduler()
bot = Bot(token=TELEGRAM_TOKEN)

async def send_daily_reminder():
    users = await get_all_users()
    for user in users:
        user_id = user["user_id"]
        chat_id = user["chat_id"]
        try:
            await bot.send_message(chat_id=chat_id, text="Здравствуй, напоминаную о себе!")
        except Exception as e:
            print(f"Error sending message to {user_id}: {e}")


# Запуск бота
async def launch_bot():

    dp = Dispatcher(storage=MemoryStorage())

    commands = [
        BotCommand(command="start", description="регистрация и приветствие"),
        BotCommand(command="profile", description="ваш текущий профиль"),
        BotCommand(command="clear", description="отчистить историю сообщений")
    ]
    await bot.set_my_commands(commands)

    db_init()

    dp.include_routers(
        user_questionary.router,
        dev_commands.router,
        expert_register.router,
        ai_questions.router
    )

    scheduler.add_job(send_daily_reminder, 'cron', hour=9, minute=0)
    scheduler.start()

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


def main():
    if TELEGRAM_TOKEN is None:
        print("Enivornment variable TELEGRAM_TOKEN is None, so quiting...")
        sys.exit(-1)

    if GIGACHAT_KEY is None:
        print("Enivornment variable GIGACHAT_KEY is None, so quiting...")
        sys.exit(-1)

    asyncio.run(launch_bot())
