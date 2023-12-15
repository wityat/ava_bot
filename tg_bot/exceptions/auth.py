class AuthException(Exception):
    def __init__(
        self, message: str = None, promo_value: str = None, message_for_user: str = None
    ):
        self.promo_value = promo_value
        self.message_for_user = (
            message_for_user if message_for_user else "Ошибка во время аутентификации."
        )
        super().__init__(message)


class PromoIncorrect(AuthException):
    def __init__(self, promo_value: str):
        self.promo_value = promo_value
        self.message_for_user = "Неверный формат промокода."
        super().__init__(
            f"Promo '{promo_value}' does not match promo regexp expression.",
            self.promo_value,
            self.message_for_user,
        )


class PromoNotFound(AuthException):
    def __init__(self, promo_value: str):
        self.promo_value = promo_value
        self.message_for_user = "Такой промокод не был найден в нашей базе."
        super().__init__(
            f"Promo '{promo_value}' was not found in db.",
            self.promo_value,
            self.message_for_user,
        )


class PromoAlreadyUsed(AuthException):
    def __init__(self, promo_value: str):
        self.promo_value = promo_value
        self.message_for_user = (
            "Такой промокод уже был использован другим пользователем."
        )
        super().__init__(
            f"Promo '{promo_value}' was already used by another user.",
            self.promo_value,
            self.message_for_user,
        )
