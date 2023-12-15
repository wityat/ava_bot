class NoAccountIdInContextData(Exception):
    def __init__(self):
        self.message_for_user = "Нет account_id в данных контекста (Забыл установить нужный аккаунт в хендлер)"
        super().__init__(f"No account_id in context data")
