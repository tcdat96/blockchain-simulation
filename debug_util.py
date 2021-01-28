
'''
debug_util.py 
'''

import logging

def configure_logging(filename, level=logging.DEBUG):
    logging.basicConfig(filename=filename, level=level)
    handler = logging.FileHandler(filename, 'w', 'utf-8')
    logging.getLogger().addHandler(handler)

def setup_logger(name, log_file, level=logging.INFO):
    """To setup as many loggers as you want"""

    handler = logging.FileHandler(log_file)        
    
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger