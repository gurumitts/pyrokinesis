import time
from apscheduler.schedulers.background import BackgroundScheduler
import RPi.GPIO as GPIO
from sensor import Sensor
from data_store import DataStore
import logging

scheduler = BackgroundScheduler()

# GPIO pin to control heat
heat_source_pin = 23

program_led = 21
program_button = 2
ready_led = 16

print GPIO.VERSION
GPIO.cleanup()
GPIO.setmode(GPIO.BCM)
GPIO.setup(heat_source_pin, GPIO.OUT)
GPIO.setup(program_button, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(program_led, GPIO.OUT)
GPIO.setup(ready_led, GPIO.OUT)


def current_time():
    return int(round(time.time() * 1000))


def get_db():
    db = DataStore()
    return db


class Control:

    def __init__(self):
        logging.getLogger('pyro').info('Control is starting...')
        self.heat_start = 0
        self.heat_end = 0
        self.sensor = Sensor()
        self.turn_led_off(ready_led)

    def start(self):
        while not self.sensor.ready():
            self.sensor.initialize()
            self.flash_led(program_led, 1, 5)

        self.turn_led_on(ready_led)
        GPIO.add_event_detect(program_button, GPIO.FALLING, callback=self.toggle_program, bouncetime=5000)
        scheduler.start()
        scheduler.add_job(self.track, 'interval', seconds=2)
        scheduler.add_job(self.control_power, 'interval', seconds=5)
        scheduler.print_jobs()

    def toggle_program(self, channel):
        db = get_db()
        enabled = db.get_enabled()
        logging.getLogger('pyro').info('Program was: %s' % enabled)
        if enabled == 'true':
            logging.getLogger('pyro').info('Program will be set to : false')
            db.set_enabled(False)
            self.turn_led_off(program_led)
        else:
            db.set_enabled(True)
            self.turn_led_on(program_led)
        enabled = db.get_enabled()
        logging.getLogger('pyro').info('Program is: %s' % enabled)
        db.shutdown()

    def turn_led_on(self, led):
        GPIO.output(led, 1)

    def turn_led_off(self, led):
        GPIO.output(led, 0)

    def flash_led(self, led, on_duration, num_times):
        count = 0
        while count < num_times:
            self.turn_led_on(led)
            time.sleep(on_duration)
            self.turn_led_off(led)
            time.sleep(.5)
            count += 1

    def set_heat_source(self, switch):
        GPIO.output(heat_source_pin, switch)

    def heat_is_on(self):
        return GPIO.input(heat_source_pin)

    def burst_heat(self, heat_duration, cool_duration):
        logging.getLogger('pyro').debug('starting burst..')
        now = current_time()
        if self.heat_is_on():
            logging.getLogger('pyro').debug('heat is already on %s %s %s' %
                                            (now, self.heat_start, heat_duration))
            if now > self.heat_start + heat_duration:
                logging.getLogger('pyro').debug('turning it off')
                self.heat_source_off()
            else:
                logging.getLogger('pyro').debug('leaving it on')
        else:
            logging.getLogger('pyro').debug('heat is off %s %s %s' %
                                            (now, self.heat_end, cool_duration))
            if now > self.heat_end + cool_duration:
                logging.getLogger('pyro').debug('cool done period ended, turing heat on')
                self.heat_source_on()
            else:
                logging.getLogger('pyro').debug('still cooling down')

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

    def control_power(self):
        try:
            db = get_db()
            control_data = db.get_control_data()
            logging.getLogger('pyro').debug('using %s to control power' % control_data)
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
                self.turn_led_off(program_led)
                db.set_heat_source_status('off')
                logging.getLogger('pyro').debug('disabled turning off heat')
            else:
                self.turn_led_on(program_led)
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


