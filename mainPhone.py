#!/usr/bin/python

# Grateful Dead PayPhone Main Script 
# MikeyBreeze X-mas 2022


from pad4pi import rpi_gpio
import RPi.GPIO as GPIO
import signal
import datetime
import time
import sys
import mariadb
import os
import subprocess
import random


#Global Phone Number
PHONENO = ""

# Global DIALTONE
DIALTONE = False

#GLOBAL HUNGUP
HUNGUP = True

#Global KEYPAD and PINS DEF
KEYPAD = [
    [1, 2, 3, "A"],
    [4, 5, 6, "B"],
    [7, 8, 9, "C"],
    ["*", 0, "#", "D"]
]

ROW_PINS = [4, 14, 15, 25] # BCM numbering
COL_PINS = [18, 27, 22] # BCM numbering

#Coin Release/Flash on keypad
FLASHBUTTON = 23

#PhoneHook microswitch
HOOKSWITCH = 5

def keyPressed(key):
    global PHONENO
    global DIALTONE
    global HUNGUP
    
    if DIALTONE:
        killMPG()
        time.sleep(0.25)
        DIALTONE = False
    
    if HUNGUP == False:
        print(f"Received key from interrupt:: {key}")
        PHONENO += str(key)
        if key == 0:
            os.system('mpg123 -q ' + '/home/pi/Music/PhoneSounds/DTMF-0.mp3')
        elif  key == 1:
            os.system('mpg123 -q ' + '/home/pi/Music/PhoneSounds/DTMF-1.mp3')
        elif  key == 2:
            os.system('mpg123 -q ' + '/home/pi/Music/PhoneSounds/DTMF-2.mp3')
        elif  key == 3:
            os.system('mpg123 -q ' + '/home/pi/Music/PhoneSounds/DTMF-3.mp3')
        elif  key == 4:
            os.system('mpg123 -q ' + '/home/pi/Music/PhoneSounds/DTMF-4.mp3')
        elif  key == 5:
            os.system('mpg123 -q ' + '/home/pi/Music/PhoneSounds/DTMF-5.mp3')
        elif  key == 6:
            os.system('mpg123 -q ' + '/home/pi/Music/PhoneSounds/DTMF-6.mp3')
        elif  key == 7:
            os.system('mpg123 -q ' + '/home/pi/Music/PhoneSounds/DTMF-7.mp3')
        elif  key == 8:
            os.system('mpg123 -q ' + '/home/pi/Music/PhoneSounds/DTMF-8.mp3')
        elif  key == 9:
            os.system('mpg123 -q ' + '/home/pi/Music/PhoneSounds/DTMF-9.mp3')    
        elif key == "#":
            os.system('mpg123 -q ' + '/home/pi/Music/PhoneSounds/DTMF-pound.mp3')
        elif key == "*":
            os.system('mpg123 -q ' + '/home/pi/Music/PhoneSounds/DTMF-star.mp3')
        
        print(PHONENO)
        if len(PHONENO) == 10:
            try:    
                listOfSongs = getSongList(PHONENO)
                playSong(listOfSongs)
                time.sleep(1)

            except (IOError,TypeError) as e:
                print("keyPressed::ERROR:" + str(e))
                print("Exiting...")
        
        if len(PHONENO) > 10:
            print("ERROR: Phone Number > 10")
            PHONENO = PHONENO[-1:]

        
        #0 was first key pressed...call "Operator"
        #Operator was only played live 4 times, 
        #this will randomly choose one of those 4 shows
        elif len(PHONENO) == 1 and key == 0:
            opint = random.randint(0,3)
            print("Operator Called")
            if opint == 0:
                opath = QueryTrack('1970081807')
                os.system('mpg123 -q ' + opath + ' &')
            elif opint == 1:
                opath = QueryTrack('1970091802')
                os.system('mpg123 -q ' + opath + ' &')
            elif opint == 2:
                opath = QueryTrack('1970110705')
                os.system('mpg123 -q ' + opath + ' &')
            elif opint == 3:
                opath = QueryTrack('1970110807')
                os.system('mpg123 -q ' + opath + ' &')



# Routine to QueryDB:
def QueryTrack(dateAndTrack):
    # Settings for database connection
    hostname = 'localhost'
    username = 'guser'
    password = 'dead'
    database = 'gratefuldb'
    
    #Query for Path to mp3 based on date & track
    query = "SELECT Folder_path, Filename FROM deadtracks WHERE DateAndTrack=%s" % (dateAndTrack)
    args = (dateAndTrack)
    try:
       	conn = mariadb.connect( host=hostname, user=username, passwd=password, db=database )
        cursor = conn.cursor()
        cursor.execute(query, args)
        
        
        result = cursor.fetchone();
        if result is not None:
            songPath = result[0] + "/" + result[1]
        else:
            songPath = ""
            
        return songPath
    except Exception as error:
       	print("QueryTrack:ERROR: " + str(error))
       
    finally:
       	cursor.close()
       	conn.close()

#Gets a list of by calling QueryTrack function
def getSongList(pnum):
    try:
        
        songList = QueryTrack(pnum)
        print(songList)
        if songList == "":
            print("getSongList: No Song Returned")
            os.system('mpg123 -f -3000 /home/pi/Music/PhoneSounds/cannot-be-completed.mp3 &')
        else:
            songList = '"' + songList + '"'
            #Increment Phone number until there are no more tracks returned
            while True:
                pnum = int(pnum)
                pnum += 1 
                pnum = str(pnum)

                songToAdd = QueryTrack(pnum)
                print(songToAdd)
                if songToAdd == "":
                    break
                else:
                    songList = songList + ' "' + songToAdd + '"'
        return songList
    except Exception as error:
        print("getSongList:ERROR: " + str(error))
    


def playSong(songToPlay):

    try:     
        
        if songToPlay == "":
            print("playSong: No Song Returned")
            os.system('mpg123 -f -3000 /home/pi/Music/PhoneSounds/cannot-be-completed.mp3 &')
        print(songToPlay)
        os.system('mpg123 ' + songToPlay + ' &')

        # wait a little
        time.sleep(1)

    except Exception as error:
        print("playSong:ERROR: " + str(error))
    
#Press Flash Button to reset
def flash_pressed_callback(pin):
    global DIALTONE
    global PHONENO
    global HUNGUP
    
    print("Flash Pressed")
    
    if HUNGUP == False:
        time.sleep(.5)
        DIALTONE = True
        PHONENO = ""
        
        #Kill all mpg123s
        killMPG()
        time.sleep(.5)
        
        #play dialTone
        os.system('mpg123 -f -10000 /home/pi/Music/PhoneSounds/dialToneLong.mp3 &')


#Interrupt check for phone up or down
def hook_check(pin):
    global PHONENO
    global DIALTONE
    global HUNGUP
    
    time.sleep(0.25)
    if GPIO.input(HOOKSWITCH):
        #Phone Picked Up
        print("Phone Picked UP")
        HUNGUP = False
        DIALTONE = True
        PHONENO = ""    
        #play dialTone
        os.system('mpg123 -f -10000 /home/pi/Music/PhoneSounds/dialToneLong.mp3 &')
    else:
        #Phone Hung Up
        print ("Phone Hung Up")
        HUNGUP = True
        PHONENO = ""
        #Kill all mpg123s
        killMPG()
        time.sleep(.5)




#kill active MPG123 proccesses to stop any mp3s playing
def killMPG():
    os.system('pidof mpg123 | xargs kill -9 &')

try:
    now = str(datetime.datetime.now())
    print("SCRIPT STARTED " + now)
    #Set Up keypad Inputs
    factory = rpi_gpio.KeypadFactory()
    keypad = factory.create_keypad(keypad=KEYPAD,row_pins=ROW_PINS, col_pins=COL_PINS) # makes assumptions about keypad layout and GPIO pin numbers
    
    #Set Up Phone Hook MicroSwitch Input
    GPIO.setup(HOOKSWITCH, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    
    #Set Up Flash Button Input
    GPIO.setup(FLASHBUTTON, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    #Interrupt for Phone Hook
    GPIO.add_event_detect(HOOKSWITCH, GPIO.BOTH, callback=hook_check, bouncetime=1000)
    
    
    #Interrupt for Flash Button 
    GPIO.add_event_detect(FLASHBUTTON, GPIO.FALLING, callback=flash_pressed_callback, bouncetime=1500)
    
    #Interrupt for KeyPad
    keypad.registerKeyPressHandler(keyPressed)
    


    print("Press buttons on your keypad. Ctrl+C to exit.")
    while True:
        time.sleep(.5)
            
except KeyboardInterrupt:
    print("Goodbye")
except Exception as error:
    print("MAIN:ERROR: " + str(error))
finally:
    keypad.cleanup()
    os.system('pidof mpg123 | xargs kill -9 &')
    sys.exit()