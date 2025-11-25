import logging
import sys

def get_logger(name: str = None) -> logging.Logger:
    """Get a configured logger instance.
    
    Args:
        name: Logger name. If None, automatically determines from caller's module.
    
    Returns:
        Configured logger instance.
    """
    if name is None:
        import inspect
        frame = inspect.stack()[1]
        module = inspect.getmodule(frame[0])
        name = module.__name__ if module else __name__
    
    logger = logging.getLogger(name)
    
    # Configure handler if not already configured
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    
    return logger

# Backward compatibility wrapper
class Logging:
    def __init__(self) -> None:
        import inspect
        frame = inspect.stack()[1]
        module = inspect.getmodule(frame[0])
        name = module.__name__ if module else __name__
        self.logger = get_logger(name)

    def log_info(self, message: str) -> None:
        self.logger.info(message)

    def log_error(self, message: str) -> None:
        self.logger.error(message)
    
    def log_warning(self, message: str) -> None:
        self.logger.warning(message)