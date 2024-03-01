import os
import logging

from logging.handlers import TimedRotatingFileHandler

#FILENAME = '/tmp/tango-tangosys/PyCATS/bl13/log.txt'
#FILENAME = '/tmp/tango-tangosys/PyCATS/bl06/log.txt'
FILENAME = '/tmp/tango-tangosys/PyCATS/log.txt'


def get_logger(name='root'):
    formatter = logging.Formatter(
        "%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        "%Y-%m-%d %H:%M:%S")
    chlr = logging.StreamHandler()
    chlr.setFormatter(formatter)
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(chlr)

    fhlr = TimedRotatingFileHandler(filename=FILENAME,
                                    when='midnight',
                                    backupCount=30)
    os.chmod(FILENAME, 0o666)
    fhlr.setFormatter(formatter)
    logger.addHandler(fhlr)

    return logger
