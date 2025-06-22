import logging


def make_logger(
    name: str,
    level: int = logging.DEBUG
) -> logging.Logger:
    logger = logging.getLogger(f'[sockio] {name}')
    logger.setLevel(level)
    logger.handlers.clear()
    
    handler = logging.StreamHandler()
    handler.setLevel(level)
    
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(name)s: %(message)s")
    handler.setFormatter(formatter)
    
    logger.addHandler(handler)
    return logger
