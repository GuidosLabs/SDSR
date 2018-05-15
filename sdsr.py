#!/usr/bin/env python
# -*- coding: utf-8 -*-

# sdsr.py
# Something Doesn't Sound Right - Detects Unusual Departures from Normal Sounds in a Production Environment
# Designed by David Guidos, April 2017

import sys  
import numpy
import time
import json
import pyaudio
import pygame
import wave
from sense_hat import SenseHat
#import paho.mqtt.client as mqtt
#from socketIO_client import SocketIO
import argparse
#from urllib.parse import urlencode
import requests
# for emails
import smtplib
from email.mime.text import MIMEText

mic = None

# audio set up  
FS = 44100                  # sampling frequency; standard CD rate
SAMPLES = 2048              # size of sound sample
SAMPLE_BUFFER_SIZE = 8192   # number of frames in the buffer
NUMBER_OF_SAMPLES = 100     # number of samples in the profile
MIC_DEVICE = 1              # TODO: enumerate to find mic device?

# get command line arguments
parser = argparse.ArgumentParser(description='SDSR')
parser.add_argument('-b', action='store', dest='buildNormalProfile', default=1,
                    help='Number of this device')
parser.add_argument('-d', action='store', dest='deviceNumber', default=1,
                    help='Number of this device')
parser.add_argument('-g', action='store_true', default=False,
                    dest='usePyGame', help='Display grahical data?')
parser.add_argument('-s', action='store_true', default=False,
                    dest='useSenseHat', help='Display to SenseHat?')
parser.add_argument('-w',action='store_true', default=False,
                    dest='useWebServer', help='Send data to web server?')
parser.add_argument('-p',action='store_true', default=False,
                    dest='usePost', help='Send data as post?')

args = parser.parse_args()
buildNormalProfile = args.buildNormalProfile
deviceNumber = int(args.deviceNumber)
usePyGame = args.usePyGame
useSenseHat = args.useSenseHat
useWebServer = args.useWebServer
usePost = args.usePost

buildNormalProfile = True
usePyGame = True
deviceNumber = 1
useSenseHat = False
useWebServer = True
usePost = False

print ("deviceNumber: " + str(deviceNumber))
print ("usePyGame: " + str(usePyGame))
print ("useSenseHat: " + str(useSenseHat))
print ("useWebServer: " + str(useWebServer))
print ("usePost: " + str(usePost))
print ("sampleSize: " + str(SAMPLES))
#time.sleep(5.000)   # wait for 1 sec

# TCP request definitions
postURL = 'http://guidoslabs.com/SDSR/eventAlert.py'
putURL = 'http://guidoslabs.com/SDSR/eventAlert.py'

# normal sound profile
sampleData = [[] for i in range(NUMBER_OF_SAMPLES)]
meanPower = [-1 for i in range(int(SAMPLES / 2))]
stdDevPower = [-1 for i in range(int(SAMPLES / 2))]

# monitored sound levels and deviations


#   P Y G A M E
#
# set canvas parameters
screen = pygame.Surface
size = width, height = 1100, 900
speed = [100, 100]

redColor = pygame.Color(255, 0, 0)
blueColor = pygame.Color(0, 0, 255)
greenColor = pygame.Color(0, 255, 0)
yellowColor = pygame.Color(0, 255, 255)
blackColor = pygame.Color(0, 0, 0)
whiteColor = pygame.Color(255, 255, 255)
greyColor = pygame.Color(150, 150, 150)

#   S E N S E   H A T
#
# sense hat rainbow pixel pattern
rainbowPixels = [
    [255, 0, 0], [255, 0, 0], [255, 87, 0], [255, 196, 0], [205, 255, 0], [95, 255, 0], [0, 255, 13], [0, 255, 122],
    [255, 0, 0], [255, 96, 0], [255, 205, 0], [196, 255, 0], [87, 255, 0], [0, 255, 22], [0, 255, 131], [0, 255, 240],
    [255, 105, 0], [255, 214, 0], [187, 255, 0], [78, 255, 0], [0, 255, 30], [0, 255, 140], [0, 255, 248], [0, 152, 255],
    [255, 223, 0], [178, 255, 0], [70, 255, 0], [0, 255, 40], [0, 255, 148], [0, 253, 255], [0, 144, 255], [0, 34, 255],
    [170, 255, 0], [61, 255, 0], [0, 255, 48], [0, 255, 157], [0, 243, 255], [0, 134, 255], [0, 26, 255], [83, 0, 255],
    [52, 255, 0], [0, 255, 57], [0, 255, 166], [0, 235, 255], [0, 126, 255], [0, 17, 255], [92, 0, 255], [201, 0, 255],
    [0, 255, 66], [0, 255, 174], [0, 226, 255], [0, 117, 255], [0, 8, 255], [100, 0, 255], [210, 0, 255], [255, 0, 192],
    [0, 255, 183], [0, 217, 255], [0, 109, 255], [0, 0, 255], [110, 0, 255], [218, 0, 255], [255, 0, 183], [255, 0, 74]
]
pixels = rainbowPixels  #current pixels for display

def clearPixels(pixels, pixelColor):
    for pix in pixels:
        pix = pixelColor    



#   A U D I O
#
def record_audio():
	CHUNK = 8192
	FORMAT = pyaudio.paInt16
	CHANNELS = 1
	RATE = 44100
	RECORD_SECONDS = 5
	WAVE_OUTPUT_FILENAME = "normalSound.wav"
	console = True

	p = pyaudio.PyAudio()

	stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK)

	if console:
		print ("* Recording audio...")

	frames = []

	for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
		data = stream.read(CHUNK)
		frames.append(data)

	if console:
		print ("* done\n") 

	stream.stop_stream()
	stream.close()
	p.terminate()

	wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
	wf.setnchannels(CHANNELS)
	wf.setsampwidth(p.get_sample_size(FORMAT))
	wf.setframerate(RATE)
	wf.writeframes(b''.join(frames))
	wf.close()

def get_audioSample():
    global mic
    if mic is None:
        pa = pyaudio.PyAudio()
        mic = pa.open(format = pyaudio.paInt16, channels = 1, rate = FS,
                      input_device_index = MIC_DEVICE, input = True,
                      frames_per_buffer = SAMPLE_BUFFER_SIZE)
    audioSample = mic.read(SAMPLES)
    flush = mic.read(SAMPLE_BUFFER_SIZE - SAMPLES)   # clear rest of buffer to prevent overflow
    return numpy.fromstring(audioSample, dtype=numpy.short)

# get power spectrum from the amplitudes
def get_powerSpectrum(amplitudes):
    return abs(numpy.fft.fft(amplitudes / 32768.0))[:SAMPLES/2]

# normalize the power spectrum by eliminating the background
def normalized_powerSpectrum(powerSpectrum):
    nps = []
    return nps

def plot_sound(amplitudes):
    # determine canvas positions
    yUsable = (height / 3) - 60
    yRange = yUsable / 2
    yBase = 10
    x = -0.5
    maxAmplitude = max(max(amplitudes), -min(amplitudes))
    previousY = 0
    for amplitude in amplitudes:
        x += 0.5
        #y = (-float(amplitude) / float(maxAmplitude)) * yRange   # for automatic scaling
        y = (-float(amplitude) / 4096.0) * yRange   # fixed scaling
        # plot this amplitude
        #lineRect = pygame.draw.line(screen, blueColor, (x + 10, yRange + y + 10), (x + 10, yRange - y + 10), 1)
        lineRect = pygame.draw.line(screen, blueColor, (x + 10, yBase + yRange + previousY), (x + 10, yBase + yRange + y), 1)
        previousY = y
    #print max(amplitudes)
    # show title
    gameFont = pygame.font.SysFont("monospace", 15)
    screen.blit(gameFont.render("Sound data", 1, blackColor), (20, 10))

def plot_powerSpectrum(powerArray):  
    # determine canvas positions
    yUsable = (height / 3) - 60
    yBase = 10 + yUsable * 2 + 60
    x = -1
    freqIndex = powerArray.argmax(axis=0)   # primary frequency
    maximumPower = max(powerArray)
    print ("Freq Index: " + str(freqIndex))
    for powerValue in powerArray:
        x += 1
        y = powerValue / maximumPower * yUsable
        if (x == freqIndex):
            # show power level for primary sample frequency in red
            lineColor = redColor
        else:
            # normal power levels in black
            lineColor = blackColor
        # plot the power level for this sample value
        lineRect = pygame.draw.line(screen, lineColor, (x + 10, yBase), (x + 10, yBase - y), 1)
    # show title
    screen.blit(spectrumLabel, (20, 330))
    screen.blit(spectrumFrequencies, (10, yBase + 20))

def plot_deviationLevels(levels):
    yUsable = (height / 3) - 60
    yBase = height - 40
    xBase = 0
    x = 10
    maximumLevel = 50 # max(levels)
    lineColor = redColor
    previousY = -1
    for level in levels:
        x += 1
        y = float(level) / float(maximumLevel) * float(yUsable)
        if previousY == -1:
            previousY = y
        # plot the detection level for this sample value 
        lineRect = pygame.draw.line(screen, lineColor, (xBase + (x - 1) * 2, yBase - previousY), (xBase + x * 2, yBase - y), 1)       
        previousY = y
    screen.blit(gameFont.render("Deviation Levels", 1, blackColor), (20, height - yUsable))

def captureNormalSoundData():
    record_audio()

def capturedNormalSoundData(profileName):
    sampleData = []
    for i in range(NUMBER_OF_SAMPLES):
        amplitudes = get_audioSample()
        sampleData.append(amplitudes)
        print("Capturing ", i)
        screen.fill(whiteColor)
        plot_sound(amplitudes)          # show the waveform as it's captured
        displayMessage("Capturing Normal Sound Data", blueColor, "Creating Profile: " + profileName, blackColor)
            
        # update the display
        pygame.display.flip()

        #time.sleep(.01)
        
    return sampleData

def analyzeSoundProfile(soundData):
    screen.fill(whiteColor)
    displayMessage("Analyzing Sound Data", blueColor, "Creating Profile", blackColor)
    pygame.display.flip()
    soundPower = [] #numpy.array([])
    i = 0
    for amplitudes in soundData:
        print("Analyzing ", i)
        power = get_powerSpectrum(amplitudes)
        soundPower.append(power)
        i += 1

    means = numpy.mean(soundPower, 0)
    mins = numpy.min(soundPower, 0)
    maxs = numpy.max(soundPower, 0)
    stds = numpy.std(soundPower, axis = 0)
    print("Means ", means)
    print("Mins ", mins)
    print("Maxs ", maxs)
    print("Std Devs ", stds)
    
    soundProfile = [means, mins, maxs, stds]
    return soundProfile

def deviationOfSoundFromProfile(soundPowerLevels, soundProfile):
    numberOfFrequencies = len(soundPowerLevels) 
    deviationLevel = 1
    for i in range(numberOfFrequencies):
        if ( (soundPowerLevels[i] < soundProfile[1][i]) | (soundPowerLevels[i] > soundProfile[2][i]) ):    # outside of min/max range
            deviationLevel += 1
    deviationLevelPercent = float(deviationLevel) * 100.0 / float(numberOfFrequencies)
    return deviationLevelPercent

# integrate the deviations and compare to threshold
def deviationsExceedThreshold(deviations, threshold):
    return (sum(deviations) > threshold)   
    
def plotSoundProfile(soundProfile):
    # get profile data arrays
    means = soundProfile[0]
    mins = soundProfile[1]
    maxs = soundProfile[2]
    stds = soundProfile[3]
    # show title
    screen.fill(whiteColor)
    gameFont = pygame.font.SysFont("monospace", 15)
    screen.blit(gameFont.render("Normal Sound Profile", 1, blackColor), (10, 10))
    # determine canvas positions
    yUsable = height - 60
    yRange = yUsable
    yBase = 10
    for x in range(0, len(means)):
        # draw min/max range in blue
        yMin = (-float(mins[x]) / 10.0) * yRange
        yMax = (-float(maxs[x]) / 10.0) * yRange
        lineRect = pygame.draw.line(screen, blueColor, (x + 10, yBase + yRange + yMin), (x + 10, yBase + yRange + yMax), 1)
        # show mean in yellow
        yMean = (-float(means[x]) / 10.0) * yRange
        pygame.draw.line(screen, yellowColor, (x, yMean), (x, yMean)) 
            
    # update the display
    pygame.display.flip()


# display message area
def displayMessage(message1, color1, message2, color2):
    fontsize = 30
    gameFont = pygame.font.SysFont("monospace", fontsize)
    screen.blit(gameFont.render(message1, 1, color1), (width / 2 + 10, height * 3 / 4))
    gameFont = pygame.font.SysFont("monospace", int(fontsize * 0.65))
    screen.blit(gameFont.render(message2, 1, color2), (width / 2 + 10, height * 3 / 4 + fontsize * 1.5))



#   P O S T   R E Q U E S T
#

def postRequestToURL(urlString, postData):
    headers = {'content-type' : 'application/json'}
    request = requests.post(urlString, data=json.dumps(postData), headers=headers)


def putRequestToURL(urlString, putData):
    headers = {'content-type' : 'application/json'}
    request = requests.put(urlString, data=json.dumps(putData), headers=headers)



#   E M A I L
#

def sendAnomalyTextMessage(currentProfileName):
    # Create a text/plain message
    msg = MIMEText("Something doesn't sound right for profile " + currentProfileName)

    # me == the sender's email address
    # you == the recipient's email address
    # Credentials (if needed)
    username = 'daveguidos'
    password = 'DontPanic42!'
    msg['Subject'] = "SDSR Anomaly"
    msg['From'] = "daveguidos@gmail.com"
    msg['To'] = "3107954241@vtext.com"

    # Send the message via our own SMTP server, but don't include the
    # envelope header.
    s = smtplib.SMTP('smtp.gmail.com:587')
    s.starttls()
    s.login(username,password)
    s.sendmail(msg['From'], [msg['To']], msg.as_string())
    s.quit()


#   M A I N

# init sense-hat
if useSenseHat:
    sense = SenseHat()
    sense.set_rotation(180)
    sense.set_pixels(pixels)
    time.sleep(2.0) #Wait for 2s
    clearPixels(pixels,(0,0,255))
    sense.set_pixels(pixels)
    sense.clear((255,255,0))

# init the game engine
if usePyGame:
    pygame.init( )

    # display title on canvas and clear the display
    pygame.display.set_caption("SDSR")
    screen = pygame.display.set_mode(size)
    screen.fill(whiteColor)

    gameFont = pygame.font.SysFont("monospace", 15)
    gameFont2 = pygame.font.SysFont("monospace", 30)

    # create text
    #soundLabel = gameFont.render("Sound data", 1, blackColor)
    spectrumLabel = gameFont.render("Power spectrum", 1, blackColor)
    spectrumFrequencies = gameFont.render("0Hz        5kHz       10kHz       15kHz       20kHz       25kHz       30kHz       35kHz       40kHz       45kHz", 1, blueColor)

    # render the surface
    pygame.display.flip()

# build normal sound profile
currentProfileName = "Default"
if buildNormalProfile:
    normalSoundData = capturedNormalSoundData(currentProfileName)
    normalSoundProfile = analyzeSoundProfile(normalSoundData)
    plotSoundProfile(normalSoundProfile)

# loop monitoring for deviations from the normal sound profile
start = time.time()
abort = False                   # abort requested
soundDeviationLevels = []       # array of most current sound deviation levels
textMessageSent = False
while not abort:
    try:
        amplitudes = get_audioSample()
        soundPowerLevels = get_powerSpectrum(amplitudes)
        primaryFrequencyIndex = soundPowerLevels.argmax(axis=0)
        # detect deviation from normal sounds
        soundDeviationLevel = deviationOfSoundFromProfile(soundPowerLevels, normalSoundProfile)
        previousFrequencyIndex = primaryFrequencyIndex
        
        # limits the deviation chart size to 200 elements
        soundDeviationLevels.append(soundDeviationLevel)
        if len(soundDeviationLevels) > 200:
            soundDeviationLevels.pop(0)

    except (IOError):
        #print("IOError: " + str(IOError))
        continue

    if usePyGame:
        
        # check for keyboard activity
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_n:
                    print ('Key pressed: n')
                elif event.key == pygame.K_q:
                    abort = True
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_n:
                    print ('Key released: n')
        
        # clear the canvas
        screen.fill(whiteColor)
    
        # display the sound data
        plot_sound(amplitudes)
    
        # display the sound spectrum
        plot_powerSpectrum(soundPowerLevels)

        # display the sound deviation level history
        print("Sum of Deviations: ")
        print(sum(soundDeviationLevels))
        plot_deviationLevels(soundDeviationLevels)

        # check for anomaly beyond threshold
        if (deviationsExceedThreshold(soundDeviationLevels, 1000)):
            # display monitoring message
            displayMessage("WARNING! Anomaly Detected", redColor, "Deviation Threshold Exceeded! Profile: " + currentProfileName, blackColor)
            # update the display
            pygame.display.flip()
            if (not textMessageSent):
                sendAnomalyTextMessage(currentProfileName)
                textMessageSent = True
        else:
            # display monitoring message
            displayMessage("Monitoring Environment", greenColor, "Using Profile: " + currentProfileName, blackColor)
            # update the display
            pygame.display.flip()
            textMessageSent = False


    # update the sense-hat
    #if useSenseHat:
        # TODO: display warning image

    # check whether to send an alert
    soundOutOfNormalRange = False
    if soundOutOfNormalRange:
        
        # put to url
        if usePost:
            putRequestToURL(putURL + str(deviceNumber), {
                'name' : "Device " + str(deviceNumber),
                'value': "Abnormal sound detected"
                }
            )

        #time.sleep(publishing_period / 1000.)

        # put data to apache server area
        if useWebServer:
            # TODO:
            print ("Normal Sound Deviation: ", deviationLevel)
            with open("/var/www/html/soundProfile.txt", "w") as text_file:
                text_file.write(str("TODO:"))
            with open("/var/www/html/soundProfile.json", "w") as text_file:
                text_file.write(json.dumps(message))

        # clear data for next publishing period
        sampleCount = 0

    #abort = True






#   b o n e y a r d
#

#pygame.draw.rect(screen,redColor,(30,90,150,75))

#ball = pygame.image.load("beeSH.png")
#ballrect = ball.get_rect()


#while True:
#    for pix in pixels:
#        next_colour(pix)
#
#    sense.set_pixels(pixels)
#    msleep(2)


#def next_colour(pix):
#   r = pix[0]
#    g = pix[1]
#    b = pix[2]
#
#    if (r == 255 and g < 255 and b == 0):
#        g += 1
#
#    if (g == 255 and r > 0 and b == 0):
#        r -= 1
#
#    if (g == 255 and b < 255 and r == 0):
#        b += 1
#
#    if (b == 255 and g > 0 and r == 0):
#        g -= 1
#
#    if (b == 255 and r < 255 and g == 0):
#        r += 1
#
#    if (r == 255 and b > 0 and g == 0):
#        b -= 1
#
#    pix[0] = r
#    pix[1] = g
#    pix[2] = b

#sense.set_rotation(180)
#red = (255, 0, 0)
#sense.show_message("One small step for Pi!", text_colour=red)

#sense = SenseHat()
#sense.clear()
#sense.load_image("bee.png")

#time.sleep(0.1)#Wait for 100ms
