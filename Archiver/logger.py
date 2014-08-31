import logging
import logging.handlers
import datetime
import os

def make_logger(logger_name, file_name, log_path, level):
    _f = logging.Formatter('%(asctime)s - %(module)s - %(funcName)s - %(lineno)d - %(levelname)s - %(message)s',
        datefmt='%m/%d/%Y %H:%M:%S')
    date = datetime.datetime.now()
    _hm = logging.handlers.RotatingFileHandler(os.path.join(log_path,
        date.strftime('%Y-%m-%d_%H-%M-%S_') + file_name), maxBytes = 50000000, backupCount = 100)
    _hm.setFormatter(_f)
    _hm.setLevel(0)
    _l = logging.getLogger(logger_name)
    _l.setLevel(level)
    _l.addHandler(_hm)

    assert isinstance(_l, logging.Logger)
    return _l