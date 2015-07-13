import logging
import datetime
from logstash_formatter import LogstashFormatter
import logging as log

def init_log():
    current_time = datetime.datetime.now()
    logger = log.getLogger(__name__)
    logger.setLevel(log.INFO)
    handler = log.FileHandler('quota_watcher')
    handler.setLevel(log.INFO)
    # create a logging format
    #formatter = log.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    formatter = LogstashFormatter()
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger