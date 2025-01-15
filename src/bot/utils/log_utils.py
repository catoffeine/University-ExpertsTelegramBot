import logging
import os
from tokenize import endpats

from bot.definitions import (
    LOG_DIR,
    DEVELOPER_CHAT_ID,
)

from datetime import datetime, date


from pytz import timezone

from bot.utils.wrappers import bad_request_ignore


if not os.path.isdir(LOG_DIR):
    os.mkdir(LOG_DIR)

loggers = {}

LOGS_SEND = True

timezone = timezone('Europe/Moscow')
last_time_logs = 0


def setup_logger(name, log_file, level=logging.INFO, _format=None):
    """To set up as many loggers as you want"""
    _format = _format or '[%(levelname)s %(asctime)s %(filename)s:%(lineno)s - %(funcName)20s()] %(message)s'
    formatter = logging.Formatter(_format)
    handler = logging.FileHandler(log_file, encoding='utf-8')
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger


async def clear_logs(days=5):
    folders_names = os.listdir(LOG_DIR)
    current_time = datetime.now().timestamp()
    for folder in folders_names:
        file_names = os.listdir(os.path.join(LOG_DIR, folder))

        files_to_delete = []
        for file in file_names:
            time = int(file.split('_')[1].rstrip('.log'))
            if current_time - time > days * 24 * 60 * 60:
                files_to_delete.append(file)
        main_logger = get_main_logger()
        main_logger.info(f'Logfiles to delete: {repr(files_to_delete)}')
        for i in range(0, len(files_to_delete)):
            os.remove(os.path.join(LOG_DIR, folder, files_to_delete[i]))


def add_logger(name: str, folder_name=None, level=None, clear=False) -> logging.Logger:
    folder_name = folder_name or name

    full_name = name + folder_name
    if full_name in loggers.keys():
        return loggers[full_name]

    name += '.log'

    level = level or logging.DEBUG

    if not os.path.isdir(LOG_DIR + folder_name):
        os.mkdir(LOG_DIR + folder_name)

    if clear:
        if os.path.isdir(os.path.join(LOG_DIR, folder_name)):
            file = os.path.join(LOG_DIR, folder_name, name)
            if os.path.isfile(file):
                os.remove(file)

    loggers[full_name] = setup_logger(name, LOG_DIR + f'{folder_name}/{name}', level)
    return loggers[full_name]


def _get_timed_name(_id: int):
    today = date.today()
    time = int(datetime(today.year, today.month, today.day, 0, 0, tzinfo=timezone).timestamp())
    return str(_id) + "_" + str(time)


@bad_request_ignore
async def send_logs(user_id: int, bot, user_name: str = None):
    if not LOGS_SEND:
        return
    global last_time_logs
    tmp_time = last_time_logs
    last_time_logs = datetime.now().timestamp()

    if datetime.now().timestamp() - tmp_time < 1000:
        return

    folder_name = str(user_id)
    file = os.path.join(LOG_DIR, folder_name, _get_timed_name(user_id)) + '.log'
    user_name = user_name or 'anonymous_data'
    current_date = datetime.now(tz=timezone).strftime('%d-%m-%Y_%H-%M-%S')
    if os.path.isfile(file):
        await bot.send_message(
            chat_id=DEVELOPER_CHAT_ID,
            text=f'Some errors occurred from @{user_name}\n'
                 f'Date: {current_date}'
        )
        await bot.send_document(
            chat_id=DEVELOPER_CHAT_ID,
            document=file,
            filename=f'{user_name}_{current_date}.log'
        )
    else:
        await bot.send_message(
            chat_id=DEVELOPER_CHAT_ID,
            text=f'Some errors occurred from @{user_name}\n'
                 f'Date: {current_date}\n'
                 f'There are no log files on the system'
        )


def get_timed_logger(logger_name: str, wipe_logs: bool = False):
    today = date.today()
    time = int(datetime(today.year, today.month, today.day, 0, 0, tzinfo=timezone).timestamp())
    return add_logger(str(logger_name) + '_' + str(time), str(logger_name), clear=wipe_logs)


def get_user_logger(user_id: int, wipe_logs: bool = False):
    return get_timed_logger(str(user_id), wipe_logs)


def get_main_logger():
    return get_timed_logger('main', True)


# main_logger = get_timed_logger('main', True)
