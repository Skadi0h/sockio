import logging

from sockio.config import config


def make_logger(
    name: str,
) -> logging.Logger:
    level = getattr(logging, config.log_level.upper())
    logger = logging.getLogger(f'[sockio] {name}')
    logger.setLevel(level)
    logger.handlers.clear()
    
    handler = logging.StreamHandler()
    handler.setLevel(level)
    
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(name)s: %(message)s")
    handler.setFormatter(formatter)
    
    logger.addHandler(handler)
    return logger
