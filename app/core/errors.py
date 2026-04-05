class AppError(Exception):
    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class ConfigurationError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=500)


class NotFoundError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=404)


class ExternalServiceError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=502)


class ValidationError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=400)
