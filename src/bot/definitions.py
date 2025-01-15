import os

TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN'] if 'TELEGRAM_TOKEN' in os.environ else None
GIGACHAT_KEY = os.environ['GIGACHAT_KEY'] if 'GIGACHAT_KEY' in os.environ else None
DEVELOPER_ID = int(os.environ['DEVELOPER_ID']) if 'DEVELOPER_ID' in os.environ else None
DEVELOPER_CHAT_ID = int(os.environ['DEVELOPER_CHAT_ID']) if 'DEVELOPER_CHAT_ID' in os.environ else None
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(f'{ROOT_DIR}/', 'logfiles/')
USERS = "users"
KEYS = "keys"
DB_FILE = os.path.join(ROOT_DIR, 'database.db')

BASE_USER_CONFIG = {
    'name': '',
    'surname': '',
    'is_expert': False,
    'history': []
}

BASE_KEY_CONFIG = {
}
