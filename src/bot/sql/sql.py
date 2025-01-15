import asyncio
import sqlite3

from bot import errors
from bot.definitions import USERS, DB_FILE, KEYS
from bot.utils.log_utils import get_main_logger


def db_drop(table: str = None, db_file: str = DB_FILE):
    main_logger = get_main_logger()
    main_logger.info("_____DB_DROP START_____")
    with sqlite3.connect(db_file) as connection:
        cursor = connection.cursor()
        if table is None:
            main_logger.info("table is None, dropping all existing tables")
            query = f'''
                PRAGMA foreign_keys = OFF;
                DROP TABLE IF EXISTS {USERS};
                DROP TABLE IF EXISTS {KEYS};
                PRAGMA foreign_keys = ON;
            '''
        else:
            main_logger.info(f"table is {table}, dropping...")
            query = f'''
                PRAGMA foreign_keys = OFF;
                DROP TABLE IF EXISTS {table};
                PRAGMA foreign_keys = ON;
            '''
        try:
            cursor.executescript(query)
            main_logger.info("dropping successful")

        except sqlite3.IntegrityError as exc:
            connection.rollback()
            main_logger.error("Integrity error while dropping tables:")
            main_logger.error(repr(exc))
            main_logger.info("_____DB_DROP END_____\n")
            raise errors.SQLiteQueryError from None
        except BaseException as be:
            main_logger.error("error while dropping tables:")
            main_logger.error(repr(be))
            main_logger.info("_____DB_DROP END_____\n")
            raise be

    main_logger.info("_____DB_DROP END_____\n")


def db_init(table: str = None, db_file: str = DB_FILE):
    main_logger = get_main_logger()
    main_logger.info("_____DB_INIT START_____")
    main_logger.info('Initializing SQLite Databases')
    with sqlite3.connect(db_file) as connection:
        cursor = connection.cursor()
        if table is None:
            main_logger.info("table is none, so initializing all possible databases (if not exists already)")
            queries = [
                f'''
                BEGIN;
                CREATE TABLE IF NOT EXISTS {USERS} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER UNIQUE,
                    chat_id INTEGER,
                    username TEXT,
                    registration_time REAL,
                    settings JSON
                );
                ''',
                f'''
                BEGIN;
                CREATE TABLE IF NOT EXISTS {KEYS} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT,
                    settings JSON
                );
                '''
            ]
        elif table == USERS:
            main_logger.info(f"table is {USERS}, so initializing this table")
            queries = [
                f'''
                BEGIN;
                CREATE TABLE IF NOT EXISTS {USERS} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER UNIQUE,
                    chat_id INTEGER,
                    username TEXT,
                    registration_time REAL,
                    settings JSON
                );
                '''
            ]
        elif table == KEYS:
            main_logger.info(f"table is {KEYS}, so initializing this table")
            queries = [
                f'''
                BEGIN;
                CREATE TABLE IF NOT EXISTS {KEYS} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT,
                    settings JSON
                );
                '''
            ]

        main_logger.info('trying to make queries...')
        try:
            for query in queries:
                cursor.executescript(query)
        except sqlite3.IntegrityError as exc:
            connection.rollback()
            main_logger.error('integrity ERROR while creating databases')
            main_logger.error(repr(exc))
            main_logger.info("_____DB_INIT END_____\n")
            raise errors.SQLiteQueryError from None
        except BaseException as be:
            main_logger.error(str(be))
            main_logger.info("_____DB_INIT END_____\n")
            raise be

        main_logger.info('Queries are done successfully')
        main_logger.info("_____DB_INIT END_____\n")


async def main():
    db_drop()


if __name__ == '__main__':
    asyncio.run(main())
