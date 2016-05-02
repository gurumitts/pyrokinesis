from w1thermsensor import W1ThermSensor
import Adafruit_MAX31855.MAX31855 as MAX31855
import logging

# Supported units
DEGREES_F = 'TEMP_UNIT_F'
DEGREES_C = 'TEMP_UNIT_C'

# Function to convert from celsius to fahrenheit
c_to_f = lambda c: c * 9.0 / 5.0 + 32.0


class BaseSensor:
    def __init__(self, temp_unit=DEGREES_F):
        self._temperature_unit = temp_unit

    def get_temperature(self):
        pass

    def is_ready(self):
        try:
            temp = self.get_temperature()
            logging.getLogger('pyro').debug('Probing...' % self)
            logging.getLogger('pyro').debug('Ready check - temperature reading:  %s'
                                            % temp)
            if temp is not None and 40 < temp < 280:
                return True
            else:
                return False
        except Exception, err:
            logging.getLogger('pyro').debug('%s sensor cannot be loaded' % self)
            return False

    def __str__(self):
        return self.__class__.__name__


class Wire1Sensor(BaseSensor):
    def __init__(self, temp_unit=DEGREES_F):
        BaseSensor.__init__(self, temp_unit=temp_unit)
        try:
            self.sensor = W1ThermSensor()
        except Exception, err:
            self.sensor = None

    def get_temperature(self):
        if self.sensor is not None:
            if self._temperature_unit == DEGREES_F:
                return self.sensor.get_temperature(W1ThermSensor.DEGREES_F)
            else:
                return self.sensor.get_temperature(W1ThermSensor.DEGREES_C)
        else:
            return None


class KTypeSensor(BaseSensor):
    # Raspberry Pi software SPI configuration.
    CLK = 25
    CS = 24
    DO = 18

    def __init__(self, temp_unit=DEGREES_F):
        BaseSensor.__init__(self, temp_unit=temp_unit)
        self.sensor = MAX31855.MAX31855(self.CLK, self.CS, self.DO)

    def get_temperature(self):
        if self._temperature_unit == DEGREES_F:
            return c_to_f(self.sensor.readTempC())
        else:
            return self.sensor.readTempC()


class Sensor:
    def __init__(self, temp_unit=DEGREES_F):
        logging.getLogger('pyro').debug('Sensor initialization...')
        self.active_sensor = None
        self._temp_unit = temp_unit

    def initialize(self):

        wire1 = Wire1Sensor(temp_unit=self._temp_unit)
        if wire1.is_ready():
            logging.getLogger('pyro').info("1 wire sensor is ready")
            self.active_sensor = wire1

        ktype = KTypeSensor(temp_unit=self._temp_unit)
        if ktype.is_ready():
            logging.getLogger('pyro').info("K-type sensor is ready")
            self.active_sensor = ktype

        logging.getLogger('pyro').info("%s is the active sensor" % self.active_sensor)
        logging.getLogger('pyro').info("Sensor initialization complete!")

    def ready(self):
        return self.active_sensor is not None

    def get_active_sensor(self):
        return self.active_sensor

    def get_temperature(self):
        return self.active_sensor.get_temperature()


if __name__ == '__main__':
    import time

    sensor = Sensor()
    while True:
        print(sensor.get_temperature())
        time.sleep(2)
