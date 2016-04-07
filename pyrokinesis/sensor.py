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
            print "Probing..." % self
            print 'Ready check - temperature reading:  %s' % temp
            if temp is not None and 30 < temp < 130:
                return True
            else:
                return False
        except Exception, err:
            print "%s sensor cannot be loaded" % self
            return False

    def __str__(self):
        return self.__class__.__name__


class Wire1Sensor(BaseSensor):
    def __init__(self, temp_unit=DEGREES_F):
        BaseSensor.__init__(self, temp_unit=temp_unit)
        self.sensor = W1ThermSensor()

    def get_temperature(self):
        if self._temperature_unit == DEGREES_F:
            return self.sensor.get_temperature(W1ThermSensor.DEGREES_F)
        else:
            return self.sensor.get_temperature(W1ThermSensor.DEGREES_C)


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
        print "Sensor initialization..."

        self.active_sensor = None

        wire1 = Wire1Sensor(temp_unit=temp_unit)
        if wire1.is_ready():
            logging.info("1 wire sensor is ready")
            self.active_sensor = wire1

        ktype = KTypeSensor(temp_unit=temp_unit)
        if ktype.is_ready():
            logging.info("K-type sensor is ready")
            self.active_sensor = ktype

        if self.active_sensor is None:
            raise RuntimeError('No temperature sensor found')
        logging.info("%s is the active sensor" % self.active_sensor)
        logging.info("Sensor initialization complete!")

    def get_temperature(self):
        return self.active_sensor.get_temperature()


if __name__ == '__main__':
    import time

    sensor = Sensor()
    while True:
        print(sensor.get_temperature())
        time.sleep(2)
