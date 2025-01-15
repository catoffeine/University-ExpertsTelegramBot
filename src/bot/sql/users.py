import json
import sqlite3
from datetime import datetime

from bot import errors
from bot.definitions import USERS, DB_FILE
from bot.definitions import BASE_USER_CONFIG
from bot.utils.log_utils import get_main_logger, get_user_logger
from bot.utils.sql_utils import convert_to_sqlite_string


async def check_if_user_exists(user: str | int):
    with sqlite3.connect(DB_FILE) as connection:
        main_logger = get_main_logger()
        cursor = connection.cursor()
        if type(user) == str:
            query = f'''
                SELECT 1 FROM {USERS} WHERE username = '{user}';
            '''
        else:
            query = f'''
                SELECT 1 FROM {USERS} WHERE user_id = {user};
            '''

        try:
            cursor.execute(query)
        except BaseException as exc:
            main_logger.error('ERROR while checking user existing...')
            main_logger.error(repr(exc))
            raise errors.CheckUserError

        response = cursor.fetchone()
        # main_logger.info(f'Checking if user {user} exists... response is {response}')

        if response is None:
            return False

    return True


async def get_all_users():
    main_logger = get_main_logger()
    main_logger.info("_____GET_ALL_USERS START_____")
    with sqlite3.connect(DB_FILE) as connection:
        cursor = connection.cursor()
        query = f'''
            SELECT 
            user_id, chat_id, username
            FROM {USERS};
        '''
        try:
            cursor.execute(query)
        except (sqlite3.OperationalError, sqlite3.IntegrityError) as exc:
            connection.rollback()
            main_logger.error('error while getting all users')
            main_logger.error(repr(exc))
            main_logger.info("_____GET_ALL_USERS END_____\n")
            raise errors.GetUsersError from None
        except BaseException as be:
            main_logger.error(repr(be))
            main_logger.info("_____GET_ALL_USERS END_____\n")
            raise BaseException from None
        users_list = []
        for user in cursor.fetchall():
            users_list.append(
                {
                    'user_id': user[0],
                    'chat_id': user[1],
                    'username': user[2]
                }
            )
        main_logger.info("_____GET_ALL_USERS END_____\n")
        return users_list


async def remove_user(user: int | str):
    if not await check_if_user_exists(user):
        return False

    with sqlite3.connect(DB_FILE) as connection:
        cursor = connection.cursor()
        if type(user) == str:
            query = f'''
                DELETE FROM {USERS}
                WHERE username = '{user}';
            '''
        else:
            query = f'''
                DELETE FROM {USERS}
                WHERE user_id = {user};
            '''

        try:
            cursor.execute(query)
        except BaseException as exc:
            main_logger = get_main_logger()
            main_logger.error('ERROR while removing user...')
            main_logger.error(repr(exc))
            raise errors.SQLiteQueryError from None
    return True


async def set_user_setting(user: int, name: str, value: [str | int | float | list | dict | bool]):
    logger = get_user_logger(user)
    logger.info("_____SET_USER_SETTING START_____")
    logger.info(f"changing setting <{name}>")
    with sqlite3.connect(DB_FILE) as connection:
        cursor = connection.cursor()
        if type(user) == str:
            where = f"WHERE username == '{user}';"
        else:
            where = f"WHERE user_id == {user};"

        base_user_config = BASE_USER_CONFIG
        in_execution = False
        if name in base_user_config.keys() and base_user_config[name] == value:
            # nothing to change, same as base config
            query = f'''
                UPDATE {USERS}
                SET settings = JSON_REMOVE(settings, '$.{name}')
                {where}
            '''
        elif type(value) is str:
            query = f'''
                UPDATE {USERS}
                SET settings = JSON_SET(settings, '$.{name}', "{value}")
                {where}
            '''
        elif type(value) is int or type(value) is float:
            query = f'''
                UPDATE {USERS}
                SET settings = JSON_SET(settings, '$.{name}', {value})
                {where}
            '''
        elif type(value) is list:
            query = f'''
                UPDATE {USERS}
                SET settings = JSON_SET(settings, '$.{name}', "{str(value)}")
                {where}
            '''
        else:
            in_execution = True
            query = f'''
                UPDATE {USERS}
                SET settings = JSON_SET(settings, '$.{name}', ?)
                {where}
            '''
        try:
            if in_execution:
                cursor.execute(query, [value])
            else:
                cursor.execute(query)

        except (sqlite3.OperationalError, sqlite3.IntegrityError) as exc:
            logger.error("An error occurred while setting new user setting")
            logger.error(repr(exc))
            logger.info("_____SET_USER_SETTING END_____\n")
            raise errors.SetSettingError from None
        except errors.SQLiteQueryError as exc:
            logger.error("Unhandled exception: ")
            logger.error(repr(exc))
            logger.info("_____SET_USER_SETTING END_____\n")
            raise errors.SQLiteQueryError from None
    logger.info("changed successfully")
    logger.info("_____SET_USER_SETTING END_____\n")


async def get_user_setting(user: int, name: str):
    logger = get_user_logger(user)
    logger.info("_____GET_USER_SETTING START_____")
    logger.info(f"getting setting <{name}>")

    if not await check_if_user_exists(user):
        logger.error("user does not exist error")
        logger.info("_____GET_USER_SETTING END_____\n")
        raise errors.CheckUserError("User doesn't exist")

    with sqlite3.connect(DB_FILE) as connection:
        cursor = connection.cursor()
        if type(user) == str:
            query = f'''
                SELECT JSON_EXTRACT(settings, '$.{name}') FROM {USERS}
                WHERE username == '{user}';
            '''
        else:
            query = f'''
                SELECT JSON_EXTRACT(settings, '$.{name}') FROM {USERS}
                WHERE user_id == {user};
            '''
        try:
            cursor.execute(query)
        except (sqlite3.OperationalError, sqlite3.IntegrityError) as exc:
            logger.error("An error occurred while setting new user setting")
            logger.error(repr(exc))
            raise errors.GetSettingError from None
        except errors.SQLiteQueryError as exc:
            logger.error("Unhandled exception: ")
            logger.error(repr(exc))
            raise errors.SQLiteQueryError from None

        response = cursor.fetchone()
        logger.info(f'Getting user setting {name} response is {response}')
        if response[0] is None:
            # if name in BASE_USER_CONFIG:
            #     logger.info("name is in BASE_USER_CONFIG, so returning it")
            #     logger.info("_____GET_USER_SETTING END_____\n")
            #     return BASE_USER_CONFIG[name]
            # logger.info("name is not in BASE_USER_CONFIG, so returning None")
            # logger.info("_____GET_USER_SETTING END_____\n")
            return BASE_USER_CONFIG[name]

        logger.info("_____GET_USER_SETTING END_____\n")
        return response[0]


async def delete_user_setting(user: int, name: str):
    logger = get_user_logger(user)
    logger.info("_____DELETE_USER_SETTING START_____")
    logger.info(f"deleting setting <{name}>")

    with sqlite3.connect(DB_FILE) as connection:
        cursor = connection.cursor()
        if type(user) is str:
            query = f'''
                UPDATE {USERS}
                SET settings = JSON_REMOVE(settings, '$.{name}')
                WHERE username == '{user}';
            '''
        else:
            query = f'''
               UPDATE {USERS}
               SET settings = JSON_REMOVE(settings, '$.{name}')
               WHERE user_id == {user};
            '''
        try:
            cursor.execute(query)
        except (sqlite3.OperationalError, sqlite3.IntegrityError) as exc:
            logger.error("An error occurred while deleting new user setting")
            logger.error(repr(exc))
            logger.info("_____DELETE_USER_SETTING END_____\n")
            raise errors.SetSettingError from None
        except errors.SQLiteQueryError as exc:
            logger.error("Unhandled exception: ")
            logger.error(repr(exc))
            logger.info("_____DELETE_USER_SETTING END_____\n")
            raise errors.SQLiteQueryError from None

        logger.info("_____DELETE_USER_SETTING END_____\n")


async def get_user_table_setting(user: int | str, setting: str):
    logger = get_user_logger(user)
    logger.info("_____GET_USER_TABLE_SETTING START_____")
    logger.info(f"getting setting <{setting}>")
    if not await check_if_user_exists(user):
        raise errors.CheckUserError("User doesn't exist")

    with sqlite3.connect(DB_FILE) as connection:
        cursor = connection.cursor()
        if type(user) == str:
            query = f'''
                   SELECT {setting} FROM {USERS} WHERE username = '{user}';
               '''
        else:
            query = f'''
                   SELECT {setting} FROM {USERS} WHERE user_id = {user};
               '''

        try:
            cursor.execute(query)
        except BaseException as exc:
            logger.info("_____GET_USER_TABLE_SETTING END_____\n")
            raise errors.GetSettingError

        response = cursor.fetchone()
        logger.info(f"table setting got successfully, response is {response}")
        # logger.info(f'Getting user setting {setting} response is {response}')

        logger.info("_____GET_USER_TABLE_SETTING END_____\n")
        return response[0]


async def set_user_table_setting(user: int | str, setting: str, new_value: str | int | bytes | list):
    logger = get_user_logger(user)
    logger.info("____SET_USER_TABLE_SETTING START_____")
    logger.info(f"setting setting <{setting}>")
    with sqlite3.connect(DB_FILE) as connection:
        cursor = connection.cursor()
        if type(user) == str:
            where = f"WHERE username == '{user}';"
        else:
            where = f"WHERE user_id == {user};"
        if type(new_value) is bytes:
            query = f'''
                    UPDATE {USERS}
                    SET {setting} = '{memoryview(new_value)}'
                    {where}
               '''
        elif type(new_value) is str:
            query = f'''
                    UPDATE {USERS}
                    SET {setting} = '{new_value}'
                    {where}
               '''
        elif type(new_value) is int:
            query = f'''
                    UPDATE {USERS}
                    SET {setting} = {new_value}
                    {where}
               '''
        else:
            value_str = convert_to_sqlite_string(new_value)
            query = f'''
                    UPDATE {USERS}
                    SET {setting} = '{value_str}'
                    {where}
               '''

        try:
            cursor.execute(query)
        except BaseException as exc:
            logger.error(f'ERROR while setting {setting} with new value {new_value}...')
            logger.error(repr(exc))
            logger.info("____SET_USER_TABLE_SETTING END_____\n")
            raise errors.SetSettingError

        logger.info("changed successfully")
        logger.info("____SET_USER_TABLE_SETTING END_____\n")



async def add_user(user_id: int, chat_id: int, user_name=None):
    main_logger = get_main_logger()
    main_logger.info("_____ADD_USER START_____")
    main_logger.info(f'Adding user <{user_name}> to database...')

    user_name = user_name or "no_user_name"
    registration_time = datetime.now().timestamp()

    with sqlite3.connect(DB_FILE) as connection:
        cursor = connection.cursor()
        query = f'''
            INSERT INTO {USERS} (user_id, chat_id, username, registration_time, settings) 
            VALUES ({user_id}, {chat_id}, '@{user_name}', ?, ?);
        '''
        try:
            cursor.execute(query, [registration_time, json.dumps({})])
        except (sqlite3.OperationalError, sqlite3.IntegrityError) as exc:
            connection.rollback()

            main_logger.error('Integrity or Operational ERROR while adding new user')
            main_logger.error(repr(exc))
            main_logger.info("_____ADD_USER END_____\n")
            raise errors.AddUserError from None
        except BaseException as be:
            main_logger.error(str(be))
            main_logger.info("_____ADD_USER END_____\n")
            raise be

    main_logger.info("_____ADD_USER END_____\n")
