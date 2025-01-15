from aiogram import exceptions


def bad_request_ignore(f):
    async def wrapper(*args, **kwargs):
        try:
            return await f(*args, **kwargs)
        except exceptions.TelegramBadRequest:
            pass
    return wrapper
