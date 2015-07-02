import logging
import datetime

def init_log():
    current_time = datetime.datetime.now()
    logger = logging.getLogger('__name__')
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(current_time.isoformat()+'_quotawatcher.log')
    handler.setLevel(logging.INFO)
    # create a logging format
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger