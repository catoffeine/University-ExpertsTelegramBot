import json
import sqlite3

from bot import errors
from bot.definitions import DB_FILE, KEYS, BASE_KEY_CONFIG
from bot.utils.log_utils import get_main_logger
from bot.utils.sql_utils import convert_to_sqlite_string


async def add_key(key: str):
    main_logger = get_main_logger()
    main_logger.info(f'Adding key to database...')

    with sqlite3.connect(DB_FILE) as connection:
        cursor = connection.cursor()
        query = f'''
            INSERT INTO {KEYS} (key, settings) 
            VALUES (?, ?);
        '''
        try:
            cursor.execute(query, [key, json.dumps({})])
        except (sqlite3.OperationalError, sqlite3.IntegrityError) as exc:
            connection.rollback()
            main_logger.error('ERROR while adding new key')
            main_logger.error(repr(exc))
            raise errors.AddUserError from None
        except BaseException as be:
            main_logger.error(str(be))
            raise be


async def check_if_key_exists(key: str | int):
    with sqlite3.connect(DB_FILE) as connection:
        main_logger = get_main_logger()
        cursor = connection.cursor()
        if type(key) == int:
            query = f'''
                   SELECT 1 FROM {KEYS} WHERE id = {key}
            '''
        else:
            query = f'''
                   SELECT 1 FROM {KEYS} WHERE key = '{key}'
            '''

        try:
            cursor.execute(query)
        except BaseException as exc:
            main_logger.error('ERROR while checking key existing...')
            main_logger.error(repr(exc))
            raise errors.CheckKeyError from None

        response = cursor.fetchone()

        if response is None:
            return False

    return True


async def get_all_keys():
    with sqlite3.connect(DB_FILE) as connection:
        cursor = connection.cursor()
        query = f'''
            SELECT 
            key
            FROM {KEYS};
        '''
        try:
            cursor.execute(query)
        except (sqlite3.OperationalError, sqlite3.IntegrityError) as exc:
            main_logger = get_main_logger()
            connection.rollback()
            main_logger.error('ERROR while getting keys')
            main_logger.error(repr(exc))
            raise errors.GetKeysError from None
        except BaseException as be:
            main_logger = get_main_logger()
            main_logger.error(str(be))
            raise be
        key_list = [key[0] for key in cursor.fetchall()]

        return key_list


async def set_key_setting(key: str | int, name: str, value: [str | int | list]):
    if not await check_if_key_exists(key):
        return False

    with sqlite3.connect(DB_FILE) as connection:
        cursor = connection.cursor()
        if type(key) is str:
            where = f"WHERE key == '{key}';"
        else:
            where = f"WHERE id == {key};"

        if name in BASE_KEY_CONFIG.keys() and BASE_KEY_CONFIG[name] == value:
            # nothing to change, same as base config
            query = f'''
                UPDATE {KEYS}
                SET settings = JSON_REMOVE(settings, '$.{name}')
                {where}
            '''
        elif type(value) is str:
            query = f'''
                UPDATE {KEYS}
                SET settings = JSON_SET(settings, '$.{name}', "{value}")
                {where}
            '''
        elif type(value) is int or type(value) is float:
            query = f'''
                UPDATE {KEYS}
                SET settings = JSON_SET(settings, '$.{name}', {value})
                {where}
            '''
        elif type(value) is list:
            query = f'''
                UPDATE {KEYS}
                SET settings = JSON_SET(settings, '$.{name}', "{str(value)}")
                {where}
            '''
        else:
            query = f'''
                UPDATE {KEYS}
                SET settings = JSON_SET(settings, '$.{name}', '{convert_to_sqlite_string(value)}')
                {where}
            '''
        try:
            cursor.execute(query)
        except (sqlite3.OperationalError, sqlite3.IntegrityError) as exc:
            main_logger = get_main_logger()
            main_logger.error("An error occurred while setting key setting")
            main_logger.error(repr(exc))
            raise errors.SetSettingError from None
        except errors.SQLiteQueryError as exc:
            main_logger = get_main_logger()
            main_logger.error("Unhandled exception: ")
            main_logger.error(repr(exc))
            raise errors.SQLiteQueryError from None

    return True


async def get_key_setting(key: str, name: str):
    if not await check_if_key_exists(key):
        return None

    with sqlite3.connect(DB_FILE) as connection:
        main_logger = get_main_logger()
        cursor = connection.cursor()

        query = f'''
            SELECT JSON_EXTRACT(settings, '$.{name}') FROM {KEYS}
            WHERE key == '{key}';
        '''

        try:
            cursor.execute(query)
        except (sqlite3.OperationalError, sqlite3.IntegrityError) as exc:
            main_logger.error("An error occurred while getting key setting")
            main_logger.error(repr(exc))
            raise errors.GetSettingError from None
        except errors.SQLiteQueryError as exc:
            main_logger.error("Unhandled exception: ")
            main_logger.error(repr(exc))
            raise errors.SQLiteQueryError from None

        response = cursor.fetchone()
        main_logger.info(f'Getting user setting {name} response is {response}')
        if response[0] is None:
            if name in BASE_KEY_CONFIG:
                return BASE_KEY_CONFIG[name]
            return None

        return response[0]


async def remove_key(key: int | str):
    if not await check_if_key_exists(key):
        return False

    with sqlite3.connect(DB_FILE) as connection:
        cursor = connection.cursor()
        main_logger = get_main_logger()
        main_logger.info('removing the key...')
        if type(key) == str:
            main_logger.info('its type is str')
            query = f'''
                DELETE FROM {KEYS}
                WHERE key = '{key}';
            '''
        else:
            main_logger.info('its type is int (probably)')
            query = f'''
                DELETE FROM {KEYS}
                WHERE user_id = {key};
            '''

        try:
            cursor.execute(query)
        except BaseException as exc:
            main_logger.error('ERROR while deleting key...')
            main_logger.error(repr(exc))
            raise errors.SQLiteQueryError from None
        main_logger.info('query is done successfully')
    return True
