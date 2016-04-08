import time
from apscheduler.schedulers.background import BackgroundScheduler
import RPi.GPIO as GPIO
from sensor import Sensor
from data_store import DataStore
import logging

scheduler = BackgroundScheduler()

# GPIO pin to control heat
heat_source_pin = 23

print GPIO.VERSION
GPIO.setmode(GPIO.BCM)
GPIO.setup(heat_source_pin, GPIO.OUT)


def current_time():
    return int(round(time.time() * 1000))


def get_db():
    db = DataStore()
    return db


class Control:

    def __init__(self):
        logging.info('Control is starting...')
        self.heat_start = 0
        self.heat_end = 0
        self.sensor = Sensor()

    def start(self):
        scheduler.start()
        scheduler.add_job(self.track, 'interval', seconds=2)
        scheduler.add_job(self.control_power, 'interval', seconds=5)
        scheduler.print_jobs()

    def set_heat_source(self, switch):
        GPIO.output(heat_source_pin, switch)

    def heat_is_on(self):
        return GPIO.input(heat_source_pin)

    def burst_heat(self, heat_duration, cool_duration):
        print 'starting burst..'
        now = current_time()
        if self.heat_is_on():
            print 'heat is already on %s %s %s' % (now, self.heat_start, heat_duration)
            if now > self.heat_start + heat_duration:
                print 'turning it off'
                self.heat_source_off()
            else:
                print 'leaving it on'
        else:
            print 'heat is off %s %s %s' % (now, self.heat_end, cool_duration)
            if now > self.heat_end + cool_duration:
                print 'cool done period ended, turing heat on'
                self.heat_source_on()
            else:
                print 'still cooling down'

    def heat_source_on(self):
        self.heat_start = current_time()
        self.set_heat_source(True)

    def heat_source_off(self):
        self.heat_end = current_time()
        self.set_heat_source(False)

    def track(self):
        current_temp = self.sensor.get_temperature()
        try:
            db = get_db()
            db.add_temperature(current_temp)
            db.shutdown()
        except Exception as e:
            print e
            print e.message
        print current_temp

    def control_power(self):
        try:
            db = get_db()
            control_data = db.get_control_data()
            print 'using %s to control power' % control_data
            target_temp = control_data['target_temp']
            enabled = control_data['enabled']
            heat_source = control_data['heat_source']
            avg_temp = control_data['avg_temp']
            tolerance = control_data['tolerance']
            sample_size = control_data['sample_size']
            temp = control_data['temp']
            slope = control_data['slope']
            heat_duration = control_data['heat_duration']
            cool_duration = control_data['cool_duration']
            if avg_temp is None:
                avg_temp = 1
            if enabled is 0:
                self.heat_source_off()
                db.set_heat_source_status('off')
                print 'disabled turning off heat'
            else:
                if temp > target_temp:
                    if temp < target_temp + tolerance and slope < 0:
                        self.burst_heat(heat_duration, cool_duration)
                        db.set_heat_source_status('on')
                    else:
                        self.heat_source_off()
                        db.set_heat_source_status('off')
                else:
                    if temp > target_temp - tolerance and slope > 0:
                        self.heat_source_off()
                        db.set_heat_source_status('off')
                    else:
                        self.burst_heat(heat_duration, cool_duration)
                        db.set_heat_source_status('on')
            db.shutdown()
        except Exception as e:
            print e
            print e.message


