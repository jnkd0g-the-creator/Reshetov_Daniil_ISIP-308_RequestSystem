class DomainError(Exception):
    def __init__(self, message, status=422, code="validation_error"):
        self.message = message
        self.status = status
        self.code = code
        super().__init__(message)


def not_found():
    return DomainError("Заявка не найдена или недоступна.", 404, "not_found")


def forbidden():
    return DomainError("Недостаточно прав для этого действия.", 403, "forbidden")
