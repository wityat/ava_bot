class KeException(Exception):
    def __init__(self, message: str, message_for_user: str):
        self.message = message
        self.message_for_user = message_for_user if message_for_user else "Ошибка в КЕ."
        # super().__init__(message)


class KeAuthException(KeException):
    def __init__(self, message: str, message_for_user: str):
        self.message_for_user = (
            message_for_user
            if message_for_user
            else "Ошибка во время аутентификации в КЕ."
        )
        super().__init__(message, self.message_for_user)


class LoginIncorrect(KeAuthException):
    def __init__(self, login: str):
        self.login = login
        self.message_for_user = "Неверный формат логина."
        super().__init__(
            f"Login '{login}' does not match login regexp expression.",
            self.message_for_user,
        )


class CannotGetAccessToken(KeAuthException):
    def __init__(self, response: str):
        self.message_for_user = "Неверная пара логин/пароль."
        super().__init__(
            f"Incorrect login/password pair.\n Response: {response}",
            self.message_for_user,
        )


class CheckAccessTokenError(KeAuthException):
    def __init__(self):
        self.message_for_user = "Ошибка во время проверки токена."
        super().__init__(f"Error while checking token.", self.message_for_user)
