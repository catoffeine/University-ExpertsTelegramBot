class SQLiteQueryError(BaseException):
    pass


class SetSettingError(SQLiteQueryError):
    pass


class AddUserError(SQLiteQueryError):
    pass


class GetSettingError(SQLiteQueryError):
    pass


class CheckUserError(SQLiteQueryError):
    pass


class GetUsersError(SQLiteQueryError):
    pass


class CheckKeyError(SQLiteQueryError):
    pass


class GetKeysError(SQLiteQueryError):
    pass