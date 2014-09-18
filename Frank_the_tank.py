#!/usr/bin/env python

'''controls a dual motor driver with pwm support
via PS3 SIXAXIS or keyboard input. press <space> to
toggle between PS3 SIXAXIS and keyboard. in keyboard
mode, press <f> to toggle HEAD_LIGHTS, <c> to
SNAP_PHOTO, <w> <a> <s> <d> for movement, <q> <e>
to pivot, <1 - 9> sets speed of motors, or press <esc>
at any time to exit program. raspicam is used for
streaming video feed'''

import RPi.GPIO as GPIO
import pygame
import time
import os
import sys
from pygame.locals import *

IP_ADDRESS = "192.168.0.2" # ip address of host used for video stream
RASPICAM_ON = "raspivid -t 999999 -w 1280 -h 720 -sa -50 -br 60 -co 20 -fps 24 -b 3000000 -o - | gst-launch-1.0 -e -vvv fdsrc ! h264parse ! rtph264pay pt=96 config-interval=5 ! udpsink host=" + IP_ADDRESS + " port=8160&"
RASPICAM_OFF = "sudo killall -9 gst-launch-1.0"
PHOTOS_DIR = "/home/pi/Desktop/Tank_photos" # save photos to a any directory
SNAP_PHOTO = "raspistill -w 1920 -h 1080 -t 500 -o " + PHOTOS_DIR + "/"
IMAGE_NUMBERS_TXT_FILE = "image_numbers.txt" # text file to append number to 'image.jpg'
EMAIL_TO = "someone@gmail.com"

pygame.init()
pygame.joystick.init()
try:
    joyStick = pygame.joystick.Joystick(0)
    joyStick.init()
except:
    pass
screen = pygame.display.set_mode((240, 240))
pygame.display.set_caption('Frank the Tank')

"""this sets up the GPIO pins (GPIO.BOARD) to be used
with a TB6612FNG motor controller as labeled"""
AIN1 = 3 # left side motor
AIN2 = 5 # left side motor
BIN1 = 8 # right side motor
BIN2 = 10 # right side motor
PWMA = 11 # left side PWM
PWMB = 12 # right side PWM
STBY = 7 # standby pin

HEAD_LIGHTS = 13
speed = 50

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)

GPIO.setup(AIN1, GPIO.OUT)
GPIO.setup(AIN2, GPIO.OUT)
GPIO.setup(BIN1, GPIO.OUT)
GPIO.setup(BIN2, GPIO.OUT)
GPIO.setup(PWMA, GPIO.OUT)
GPIO.setup(PWMB, GPIO.OUT)
GPIO.setup(STBY, GPIO.OUT)
GPIO.setup(HEAD_LIGHTS, GPIO.OUT)
GPIO.output(STBY, 1)

PWM_A = GPIO.PWM(PWMA, 100)
PWM_B = GPIO.PWM(PWMB, 100)

PWM_A.start(0)
PWM_B.start(0)

def stopAll():
    GPIO.output(AIN1, 0)
    GPIO.output(AIN2, 0)
    GPIO.output(BIN1, 0)
    GPIO.output(BIN2, 0)

def moveFwd(speed):
    PWM_A.ChangeDutyCycle(int(speed * .95)) #calibrated to drive straight
    PWM_B.ChangeDutyCycle(speed)
    GPIO.output(AIN1, 1)
    GPIO.output(AIN2, 0)
    GPIO.output(BIN1, 1)
    GPIO.output(BIN2, 0)

def moveBack(speed):
    PWM_A.ChangeDutyCycle(speed)
    PWM_B.ChangeDutyCycle(speed)
    GPIO.output(AIN1, 0)
    GPIO.output(AIN2, 1)
    GPIO.output(BIN1, 0)
    GPIO.output(BIN2, 1)

def turnLeft(speed):
    PWM_A.ChangeDutyCycle(speed)
    PWM_B.ChangeDutyCycle(speed)
    GPIO.output(AIN1, 0)
    GPIO.output(AIN2, 0)
    GPIO.output(BIN1, 1)
    GPIO.output(BIN2, 0)

def turnRight(speed):
    PWM_A.ChangeDutyCycle(speed)
    PWM_B.ChangeDutyCycle(speed)
    GPIO.output(AIN1, 1)
    GPIO.output(AIN2, 0)
    GPIO.output(BIN1, 0)
    GPIO.output(BIN2, 0)

def pivotLeft(speed):
    PWM_A.ChangeDutyCycle(speed)
    PWM_B.ChangeDutyCycle(speed)
    GPIO.output(AIN1, 0)
    GPIO.output(AIN2, 1)
    GPIO.output(BIN1, 1)
    GPIO.output(BIN2, 0)

def pivotRight(speed):
    PWM_A.ChangeDutyCycle(speed)
    PWM_B.ChangeDutyCycle(speed)
    GPIO.output(AIN1, 1)
    GPIO.output(AIN2, 0)
    GPIO.output(BIN1, 0)
    GPIO.output(BIN2, 1)

def leftTrack(speed):
    """sets GPIO pins to drive left motor either fwd
    or rev depending on the value input from
    joystick axis"""

    if speed < -.2: # left track fwd
        PWM_A.ChangeDutyCycle(speed * -95)
        GPIO.output(AIN1, 1)
        GPIO.output(AIN2, 0)

    elif speed > .2: # left track rev
        PWM_A.ChangeDutyCycle(speed * 100)
        GPIO.output(AIN1, 0)
        GPIO.output(AIN2, 1)

    else:
        GPIO.output(AIN1, 0)
        GPIO.output(AIN2, 0)

def rightTrack(speed):
    """sets GPIO pins to drive right motor either fwd
    or rev depending on the value input from
    joystick axis"""

    if speed < -.2: # right track fwd
        PWM_B.ChangeDutyCycle(speed * -100)
        GPIO.output(BIN1, 1)
        GPIO.output(BIN2, 0)

    elif speed > .2: # right track rev
        PWM_B.ChangeDutyCycle(speed * 100)
        GPIO.output(BIN1, 0)
        GPIO.output(BIN2, 1)

    else:
        GPIO.output(BIN1, 0)
        GPIO.output(BIN2, 0)

def getSpeedLeft(axis0, axis1):
    """returns a float from -1.0 to 1.0 using joystick position"""

    if axis1 <= 0 and axis0 <= 0: # upper left js quadrant
        speed_left = axis1 - axis0
    elif axis1 <= 0 and axis0 >= 0: # upper right js quadrant
        if abs(axis1) > abs(axis0):
            speed_left = axis1
        else:
            speed_left = -axis0
    elif axis1 >= 0 and axis0 <= 0: # lower left js quadrant
        if abs(axis1) > abs(axis0):
            speed_left = axis1
        else:
            speed_left = -axis0
    elif axis1 >= 0 and axis0 >= 0: # lower right js quadrant
        speed_left = axis1 - axis0
    else:
        speed_left = 0

    return(speed_left)

def getSpeedRight(axis0, axis1):
    """returns a float from -1.0 to 1.0 using joystick position"""

    if axis1 <= 0 and axis0 >= 0: # upper right js quadrant
        speed_right = axis1 + axis0
    elif axis1 <= 0 and axis0 <= 0: # upper left js quadrant
        if abs(axis1) > abs(axis0):
            speed_right = axis1
        else:
            speed_right = axis0
    elif axis1 >= 0 and axis0 >= 0: # lower right js quadrant
        if abs(axis1) > abs(axis0):
            speed_right = axis1
        else:
            speed_right = axis0
    elif axis1 >= 0 and axis0 <= 0: # lower left js quadrant
        speed_right = axis1 + axis0
    else:
        speed_right = 0

    return(speed_right)

def dualShock(axis0, axis1):
    '''values passed from joystick axes are used for speed'''

    leftTrack(getSpeedLeft(axis0, axis1))
    rightTrack(getSpeedRight(axis0, axis1))

def getFileNum(txt_file):
    """returns a sequential number that reads and writes to
    image_numbers.txt"""

    read_number = open(txt_file, 'r')
    num = int(read_number.read()) + 1
    read_number.close()

    write_number = open(txt_file, 'w')
    str_num = str(num)
    write_number.write(str_num)
    write_number.close()

    read_number = open(txt_file, 'r')
    number = read_number.read()
    read_number.close()

    return number

def getFileName(txt_file):
    """returns a sequential file name to photos taken"""

    number = str(getFileNum(txt_file))
    return "image_" + number + ".jpg"

def takePic(file_name):

    os.system(RASPICAM_OFF)
    time.sleep(.5)
    os.system(SNAP_PHOTO + file_name)
    os.system(RASPICAM_ON)
    return file_name

def emailPic(email):

    file_name = takePic(getFileName(IMAGE_NUMBERS_TXT_FILE))
    os.system("/home/pi/email_attach.py " + PHOTOS_DIR + file_name + " " + email + "&")
    print file_name + " emailed to " + email

def headLights(lights):
    if lights == 0:
        GPIO.output(HEAD_LIGHTS, 1)
        lights = 1
    else:
        GPIO.output(HEAD_LIGHTS, 0)
        lights = 0

    return lights

MOVE_IT = {
    119: moveFwd,
    115: moveBack,
    97: turnLeft,
    100: turnRight,
    113: pivotLeft,
    101: pivotRight
    }

SPEED = {
    49: 25,
    50: 30,
    51: 40,
    52: 50,
    53: 60,
    54: 70,
    55: 80,
    56: 90,
    57: 100
    }

def main():
    '''the main loop can be toggled between joystick and keyboard
    controls by pressing the <space> key. while using keyboard controls,
    speed can be set using number keys 1 - 9'''

    os.system(RASPICAM_ON)
    stop = False
    while True:
        if stop == True:
            break
        running = True
        lights = 0
        while running:
            time.sleep(.02)
            if stop == True:
                break
            for event in pygame.event.get():
                if event.type == pygame.JOYAXISMOTION:
                    axis0 = joyStick.get_axis(2)
                    axis1 = joyStick.get_axis(3)
                    dualShock(axis0, axis1)
                elif event.type == pygame.JOYBUTTONDOWN:
                    if event.button == 12:
                        takePic()
                    elif event.button == 15:
                        lights = headLights(lights)
                elif event.type == pygame.KEYDOWN:
                    if event.key == 32:
                        running = False
                    elif event.key == K_ESCAPE:
                        stop = True
            
        stopAll()

        running = True
        speed = 50
        while running:
            time.sleep(.02)
            if stop == True:
                break
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key in MOVE_IT: # keys <w> <a> <s> <d>
                        MOVE_IT[event.key](speed)
                    elif event.key == 102: # key <f>
                        lights = headLights(lights)
                    elif event.key in SPEED: # keys <1 - 9>
                        speed = SPEED[event.key]
                    elif event.key == 99: # key <c>
                        takePic(getFileName(IMAGE_NUMBERS_TXT_FILE))
                    elif event.key == 118: # key <v>
                        emailPic(EMAIL_TO)
                    elif event.key == 32: # key <space>
                        running = False
                    elif event.key == K_ESCAPE: # key <escape>
                        stop = True
                elif event.type == pygame.KEYUP:
                    stopAll()

def quit():
    """shuts down all running components of program"""

    try:
        joyStick.quit()
    except:
        pass
    stopAll()
    GPIO.output(HEAD_LIGHTS, 0)
    os.system(RASPICAM_OFF)
    print "Goodbye!"

main()
quit()