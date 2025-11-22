import logging

class Logging:
    def __init__(self, name: str) -> None:
        self.logger = logging.getLogger(name)

    def log_info(self, message: str) -> None:
        """Logs an info message."""
        self.logger.info(message)

    def log_error(self, message: str) -> None:
        """Logs an error message."""
        self.logger.error(message)