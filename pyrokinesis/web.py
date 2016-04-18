from flask import Flask
from flask import render_template, request
import math
from data_store import DataStore
import json
import logging

app = Flask(__name__)

temp_range = 60


@app.route('/')
def index(name=None):
    db = DataStore()
    settings = db.get_settings()
    db.shutdown()
    min_temp = math.floor(settings['target_temp'] - temp_range/2)
    max_temp = math.ceil(settings['target_temp'] + temp_range/2)
    return render_template('index3.html', min_temp=min_temp, max_temp=max_temp, **settings)


@app.route('/history')
def history(name=None):
    db = DataStore()
    settings = db.get_settings()
    db.shutdown()
    tr = request.args.get('tr')
    if tr is None:
        tr = 8
    min_temp = math.floor(settings['target_temp'] - temp_range/2)
    max_temp = math.ceil(settings['target_temp'] + temp_range/2)
    return render_template('history.html', tr=tr, min_temp=min_temp, max_temp=max_temp, **settings)


@app.route('/temps/<idx>')
def temps(idx=0):
    db = DataStore()
    temps = db.get_temps(idx)
    db.shutdown()
    return temps


@app.route('/editprofiles', methods=['GET'])
def edit_profiles():
    return render_template('profiles.html')


@app.route('/profiles', methods=['GET', 'POST', 'DELETE'])
def profiles():
    db = DataStore()
    if request.method == 'POST':
        _profiles = request.get_json()
        for _profile in _profiles:
            if 'id' in _profile and _profile['id'] is not u'':
                logging.getLogger('pyro').debug('updating: %s' % _profile)
                db.save_profile(_profile)
            else:
                logging.getLogger('pyro').debug('adding: %s' % _profile)
                db.add_profile(_profile)
        db.shutdown()
        return 'ok'
    elif request.method == 'DELETE':
        _profile = request.get_json()
        logging.getLogger('pyro').debug('deleting: %s' % _profile)
        db.delete_profile(_profile['id'])
        db.shutdown()
        return 'ok'
    else:
        _profiles = db.get_profiles()
        db.shutdown()
        return json.dumps(_profiles)


@app.route('/settings', methods=['POST'])
def settings():
    _settings = request.get_json()
    db = DataStore()
    logging.getLogger('pyro').debug('Saving new settings: %s' % _settings)
    db.save_profile(_settings)
    db.set_active_profile(_settings['id'])
    db.apply_active_profile()
    db.save_settings(_settings)
    return 'ok'


def start():
    # app.debug = True
    app.run(host='0.0.0.0')


'''if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0')'''