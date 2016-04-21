import logging
from logging.config import fileConfig
from control import Control
from data_store import DataStore
import data_store
import web



def start():
    setup_logging()
    logging.getLogger('pyro').info("started")
    db = DataStore(setup=True)
    db.apply_active_profile()
    settings = db.get_settings()
    settings['enabled'] = 0
    db.save_settings(settings)
    settings = db.get_settings()
    logging.getLogger('pyro').debug('starting with settings: %s'% settings)

    control = Control()
    control.start()


    print('starting web')
    web.start()


def setup_logging():
    fileConfig('conf/log.conf')
    logging.getLogger('pyro').log(logging.DEBUG, 'log setup complete')
