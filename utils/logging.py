import logging

class Logging:
    def __init__(self) -> None:
        self.logger = self.get_logger()

    def get_logger(self) -> logging.Logger:
        """Returns the logger."""
        return logging.getLogger(__name__)

    def log_info(self, message: str) -> None:
        """Logs an info message."""
        self.logger.info(message)

    def log_error(self, message: str) -> None:
        """Logs an error message."""
        self.logger.error(message)