import time
from machine import Pin, I2C, PWM
import adafruit_adxl34x

class Knuckleblaster:
    def __init__(self,
                 servo_pin=26,
                 i2c_id=0, scl_pin=4, sda_pin=8,
                 solenoid_pin=21,
                 lighter_pin=48,
                 IMUdelayMS=250,
                 solenoidDelayMS=100,
                 lighterDelayMS=100,
                 releaseAng=90,
                 latchAng=0,
                 imu_threshold=2.5,
                 earthGravity=9.8,
                 servoClosed=0):
        
        self.i2c = I2C(i2c_id, scl=Pin(scl_pin), sda=Pin(sda_pin), freq=400000)
        self.accelerometer = adafruit_adxl34x.ADXL343(self.i2c)
        
        self.servo = PWM(Pin(servo_pin), freq=50)
        self.solenoid = Pin(solenoid_pin, Pin.OUT)
        self.lighter = Pin(lighter_pin, Pin.OUT)
        
        self.IMUdelayMS = IMUdelayMS
        self.solenoidDelayMS = solenoidDelayMS
        self.lighterDelayMS = lighterDelayMS
        self.releaseAng = releaseAng
        self.latchAng = latchAng
        self.imu_threshold = imu_threshold
        self.earthGravity = earthGravity
        self.servoClosed = servoClosed

    def imuCheck(self, axis_value):
        triggered = 0
        start_time = time.ticks_ms()
        
        # Use ticks_diff and '<' to prevent infinite loop bugs
        while time.ticks_diff(time.ticks_ms(), start_time) < self.IMUdelayMS:
            x, y, z = self.accelerometer.acceleration
            if abs(axis_value - self.earthGravity) >= self.imu_threshold:
                triggered = 1
                break
        return triggered

    def servo_angle(self, angle):
        angle = max(0, min(180, angle))
        pulse_us = 1000 + (angle * 1000 // 100)
        self.servo.duty_ns(pulse_us * 1000)

    def fire_solenoid(self):
        # Turn on once, wait safely using class attribute delay
        self.solenoid.value(1)
        start_time = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), start_time) < self.solenoidDelayMS:
            pass
        self.solenoid.value(0)

    def fire_lighter(self):
        # Turn on once, use correct lighter pin and delay
        self.lighter.value(1)
        start_time = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), start_time) < self.lighterDelayMS:
            pass
        self.lighter.value(0)

kb = Knuckleblaster()
kb.servo_angle(kb.releaseAng)
kb.servoClosed = 0

while True:
    x, y, z = kb.accelerometer.acceleration
    
    if kb.imuCheck(z):
        time.sleep(1)
        kb.servo_angle(kb.releaseAng)
        kb.fire_solenoid()
        kb.fire_lighter()
        
    if kb.imuCheck(y): 
        if kb.servoClosed == 0:
            kb.servo_angle(kb.latchAng)
            kb.servoClosed = 1
        if kb.servoClosed == 1:
            kb.servo_angle(kb.releaseAng)
            kb.servoClosed = 0