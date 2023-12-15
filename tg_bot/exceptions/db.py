class DBException(Exception):
    def __init__(self, message: str):
        self.message_for_user = "Ошибка связанная с бд..."
        super().__init__(f"Db error." if not message else message)


class AlreadyHaveCurrentAccount(DBException):
    def __init__(self, account_login: str):
        self.message_for_user = f"У вас уже подключен аккаунт. ({account_login})"
        super().__init__(f"Already have current account.")
