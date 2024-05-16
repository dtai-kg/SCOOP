import logging

def create_logger(logFile, logLevel):
    # create logger
    logger = logging.getLogger(__name__)
    logger.propagate = False
    logger.handlers.clear()
    # logger.setLevel(logging.DEBUG)

    # create formatter
    fmt = "%(asctime)-15s %(levelname)s %(filename)s %(lineno)d %(process)d %(message)s"
    datefmt = "%a %d %b %Y %H:%M:%S"
    formatter = logging.Formatter(fmt, datefmt)

    # create file handler
    logger.handlers.pop() if logger.handlers else None
    if not logger.handlers:
        fh = logging.FileHandler(logFile)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    if logLevel == "DEBUG":
        logger.setLevel(logging.DEBUG)
    elif logLevel == "INFO":
        logger.setLevel(logging.INFO)
    elif logLevel == "WARNING":
        logger.setLevel(logging.WARNING)
    elif logLevel == "ERROR":
        logger.setLevel(logging.ERROR)
    elif logLevel == "CRITICAL":
        logger.setLevel(logging.CRITICAL)

    return logger
