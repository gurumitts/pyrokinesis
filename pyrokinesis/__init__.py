import sys
import logging
import logging.handlers
from control import Control
from data_store import DataStore
from apscheduler.schedulers.background import BackgroundScheduler

LOG_FORMAT = '%(asctime)-15s %(module)s %(funcName)s %(thread)d %(message)s'

scheduler = BackgroundScheduler()


def start():
    if len(sys.argv) > 1:




        print 'Loading DB'
        db = DataStore()
        db.save_settings({'enabled': False, 'target_temp': target_temp,
                          'sample_size': 20, 'tolerance': 5, 'heat_duration': 30000, 'cool_duration': 30000})
        db.shutdown()
        print 'DB load complete'
        get_sensor()
        print 'Sensor load complete'
        print 'Starting control with target temp = %s' % target_temp

        control = Control()
        scheduler.start()
        scheduler.add_job(control.track,'interval', seconds=2)
        scheduler.add_job(control.control_power, 'interval', seconds=5)
        scheduler.print_jobs()


def setup_logging(config):
    handler = logging.handlers.RotatingFileHandler(config.get('DEFAULT', 'log_file'),
                                                   maxBytes=1024*1024*100,
                                                   backupCount=5)
    formatter = logging.Formatter(LOG_FORMAT)
    handler.setFormatter(formatter)
    logger = logging.getLogger()
    logger.addHandler(handler)
    logger.setLevel(config.getint('DEFAULT', 'log_level'))

