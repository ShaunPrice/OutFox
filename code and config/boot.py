
import sensor, image, lcd, time, utime, uos,sys, math, ujson
import KPU as kpu
from Maix import GPIO, FPIOA
from board import board_info
from fpioa_manager import fm
from machine import UART, I2C

version = "1.0.0"
animals = ['red fox','kit fox','dingo','dog', 'wolf','grey fox','coyote']
timeout_duration = 30 # How long the camera is on for in seconds
timeout_extended_duration = 30 # How long to keep the camera on after a detection

# I2C Addresses
RTC_I2C_ADDR  = 0x68
SECONDS_ADDR  = 0x00
MINUTES_ADDR  = 0x01
HOURS_ADDR    = 0x02
WEEKDAY_ADDR  = 0x03
MONTHDAY_ADDR = 0x04
MONTH_ADDR    = 0x05
YEAR_ADDR     = 0x06
TEMP_MSB_ADDR = 0x11
TEMP_LSB_ADDR = 0x12

# Calendar variables
year = 19
month = 1
day = 1
hour = 0
minute = 0
second = 0
daylight = True
temperature = 0

# Sunrise and sunset times for each month
# Assumes Lat/Lon of -31:30:00/152:30:00
# Times were calculated using:
# https://www.esrl.noaa.gov/gmd/grad/solcalc/sunrise.html
# Sunrise and sunset are in hours.
# Fractional part are in hours (e.g. 0.5 = 30 mins)
# Format (sunrise,sunset)
DAYLIGHT_TIMES = ((5.4,19.2), \
             (5.8,19.0), \
             (6.2,18.5), \
             (6.5,17.8), \
             (6.8,17.4), \
             (7.1,17.3), \
             (7.1,17.4), \
             (6.8,17.7), \
             (6.2,18.1), \
             (5.3,18.3), \
             (5.1,18.7), \
             (5.0,19.1))

# Set defaults
DAYLIGHT_START = 7
DAYLIGHT_END = 5

# Pins
'''
Function    Physical    Label       PIN     GPIO
====================================================
PWR_OFF      5          ISP_RX      PIN6    GPIO6
UC_SDA       6          ISP_TX      PIN7    GPIOHS9
UC_SCL       7          WIFI_TX     PIN8    GPIOHS10
SIREN        8          WIFI_RX     PIN7    GPIO7
RTC_PROG     9          WIFI_EN     PIN8    GPIOHS0
LED_3W      10          PIN9        PIN9    GPIOHS1
IR_LEDS     11          PIN10       PIN10   GPIOHS2
RTC SCL     17          SPI0_CLK    PIN14   GPIOHS8
RTC SDA     18          MICBCK      PIN15   GPIOHS7

###################################################
For the daughter board version:
========================
PWR_OFF      7          WIFI_TX     PIN6    GPIO6
SIREN        8          WIFI_RX     PIN7    GPIO7
RTC_PROG     9          WIFI_EN     PIN8    GPIOHS0
LED_3W      10          PIN9        PIN9    GPIOHS1
IR_LEDS     11          PIN10       PIN10   GPIOHS2
RTC SDA     33          MIC0_BCK    PIN32   GPIOHS7
RTC SCL     34          I2S_WS      PIN33   GPIOHS8
UC_SDA      35          I2S_DA      PIN34   GPIOHS9
UC_SCL      36          I2S_BCK     PIN35   GPIOHS10
###################################################
'''

# GPIO Pin Mapping
PWR_OFF  = board_info.WIFI_TX
SIREN    = board_info.WIFI_RX
RTC_PROG = board_info.WIFI_EN
LED_3W   = board_info.PIN9
IR_LEDS  = board_info.PIN10
RTC_SDA  = board_info.MIC0_BCK
RTC_SCL  = board_info.I2S_WS

# Turns the RGB LED on and Red
def redLED ():
    led_r.value(0)
    led_g.value(1)
    led_b.value(1)

# Turns the RGB LED on and gREEN
def greenLED ():
    led_r.value(1)
    led_g.value(0)
    led_b.value(1)

# Turns the RGB LED on and bLUE
def blueLED ():
    led_r.value(1)
    led_g.value(1)
    led_b.value(0)

# Displays text on the LCD and the serial console
def lcd_display_text(x,y,text):
    print(text)
    if lcd_display == 1:
        lcd_display_blank(x,y)
        lcd.draw_string(x,y,text)

# Blanks out previous text on the LCD
def lcd_display_blank(x,y):
    if lcd_display == 1:
        lcd.draw_string(x,y,"                         ")

# Display image on the LCD
def lcd_display_image(img):
    if lcd_display == 1:
        lcd.display(img, oft=(50,0))

# Converts BCD to Decimal number coding
def bcd_2_dec(bcd):
    return (((bcd & 0xF0) >> 4) * 10) + (bcd & 0x0F)

# Converts Decimal to BCD Coding
def dec_2_bcd(dec):
    decade = int(dec / 10)
    LSB = dec - (decade * 10)
    MSB =  decade << 4
    BYTE = MSB + LSB
    return MSB + LSB 

# Read from I2C address of teh RTC 
def readData(address):
    data = rtc_i2c.readfrom_mem(RTC_I2C_ADDR,address,1)
    return data[0]

# Write to I2C address of the RTC
def writeData(address, data):
    rtc_i2c.writeto_mem(RTC_I2C_ADDR,address,data)

# Get the year from the RTC
def getYear():
    data = readData(YEAR_ADDR)
    return bcd_2_dec(data)

# Get the month from the RTC
def getMonth():
    data = readData(MONTH_ADDR)  & 0b0111111
    return bcd_2_dec(data)

# Get the month day from the RTC
def getDay():
    data = readData(MONTHDAY_ADDR)
    return bcd_2_dec(data)

# Get the hour from the RTC
def getHour():
    data = readData(HOURS_ADDR)
    return bcd_2_dec(data)

# Get the miunute from the RTC
def getMinute():
    data = readData(MINUTES_ADDR)
    return bcd_2_dec(data)

# Get the seconds from the RTC
def getSeconds():
    data = readData(SECONDS_ADDR)
    return bcd_2_dec(data)

# Set the year of the RTC
def setYear(_year):
    data = dec_2_bcd(_year)
    writeData(YEAR_ADDR, data)

# Set the month of the RTC
def setMonth(_month):
    data = dec_2_bcd(_month) + 0b1000000
    writeData(MONTH_ADDR, data)

# Set the month day of the RTC
def setDay(_day):
    data = data = dec_2_bcd(_day)
    writeData(MONTHDAY_ADDR, data)

# Set the hour of the RTC
def setHour(_hour):
    data = data = dec_2_bcd(_hour)
    writeData(HOURS_ADDR, data)

# Set the minute of the RTC
def setMinute(_minute):
    data = data = dec_2_bcd(_minute)
    writeData(MINUTES_ADDR, data)

# Set the seconds of the RTC
def setSeconds(_second):
    data = data = dec_2_bcd(_second)
    writeData(SECONDS_ADDR, data)

# Get the temperature from the RTC
def getTemperature():
    tempMSB = readData(TEMP_MSB_ADDR)
    tempLSB = (readData(TEMP_LSB_ADDR) >> 6) * 0.25
    tempFloat = float(tempMSB & 0b01111111) + tempLSB
    if (tempMSB & 0b10000000) > 0: # If nexagive temp
        return (float(tempMSB & 0b01111111) + tempLSB) * -1
    else:
        return tempFloat

# Get all the date and timne data from the RTC
# Returns a formated date/time string
def getDateTime():
    year =  getYear()
    month = getMonth()
    day =   getDay()
    hour =  getHour()
    minute = getMinute()
    second = getSeconds()

    return "20{:0>2d}".format(year)+"-" \
           +"{:0>2d}".format(month)+"-" \
           +"{:0>2d}".format(day)+" " \
           +"{:0>2d}".format(hour)+":" \
           +"{:0>2d}".format(minute)+":" \
           +"{:0>2d}".format(second)

# Checks if the sun is up.
# Currently set for mid to north coast of NSW Australia
# Future versions will calculate the times based on the geoloacation 
# The board also has an LDR that can be used for this purpose
def checkDaylight():
    print(getDateTime())
    hours_as_fraction = hour + (minute / 60) 

    if hours_as_fraction > DAYLIGHT_START and hours_as_fraction < DAYLIGHT_END:
        daylight = True
    else:
        daylight = False

# Used to display messages and convert terminal input to integers
def rtcInput(text):
    print(text)
    return int(input())

# Set up folders
if "images" not in uos.listdir("/sd"):
    uos.mkdir("/sd/images")
    
# Init Sensor
sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)
sensor.set_windowing((224, 224))
sensor.set_vflip(1)
sensor.run(1)

# Init LEDs
fm.register(board_info.LED_B, fm.fpioa.GPIO0)
fm.register(board_info.LED_G, fm.fpioa.GPIO1)
fm.register(board_info.LED_R, fm.fpioa.GPIO2)

led_r = GPIO(GPIO.GPIO1, GPIO.OUT) 
led_g = GPIO(GPIO.GPIO0, GPIO.OUT) 
led_b = GPIO(GPIO.GPIO2, GPIO.OUT) 

led_r.value(1)
led_g.value(1)
led_b.value(1)

# Init GPIO
fm.register(PWR_OFF, fm.fpioa.GPIO6)
fm.register(SIREN, fm.fpioa.GPIO7)
fm.register(RTC_PROG, fm.fpioa.GPIOHS0)
fm.register(LED_3W, fm.fpioa.GPIOHS1)
fm.register(IR_LEDS, fm.fpioa.GPIOHS2)

pwr_off = GPIO(GPIO.GPIO6, GPIO.OUT)
siren = GPIO(GPIO.GPIO7, GPIO.OUT)
rtc_prog = GPIO(GPIO.GPIOHS0, GPIO.IN)
led_3w = GPIO(GPIO.GPIOHS1, GPIO.OUT)
ir_leds = GPIO(GPIO.GPIOHS2, GPIO.OUT)

pwr_off.value(0)
siren.value(0)
led_3w.value(0)
ir_leds.value(0)

# Turn the LED blue
blueLED()

# Init I2C for RTC
fm.register(RTC_SDA, fm.fpioa.GPIOHS7,force=True)
fm.register(RTC_SCL, fm.fpioa.GPIOHS8,force=True)

rtc_i2c = I2C(I2C.I2C0, mode=I2C.MODE_MASTER, freq=400000,scl=RTC_SCL, sda=RTC_SDA)
devices = rtc_i2c.scan()
print ("RTC Devices:")
for device in devices:  
    print(hex(device))

# Initialises the RTC so it can be read
not_used = rtc_i2c.readfrom(RTC_I2C_ADDR,7)
print("RTC I2C Initialised...")

# Init LCD
lcd.init()
lcd.clear()
lcd_display = 1
#lcd_display = 0
       
lcd_display_text(200,224,"OutFox "+version)

# wait for input
print("Enable RTC_PROG to set the time.")

if rtc_prog.value() == 1:
    year = rtcInput("Enter year (y)")
    month = rtcInput("Enter month (m)")
    day =  rtcInput("Enter day (d)")
    hour = rtcInput("Enter hour 24 hrs (h)")
    minute = rtcInput("Enter minute (m)")
    second = rtcInput("Enter second (s)")

    # set the external RTC
    setYear(year)
    setMonth(month)
    setDay(day)
    setHour(hour)
    setMinute(minute)
    setSeconds(second)

time.sleep(2) # Wait for update before reading

# Calculate the daylight hours
DAYLIGHT_START = DAYLIGHT_TIMES[month][0]
DAYLIGHT_END = DAYLIGHT_TIMES[month][1]

checkDaylight()

# Get the current temperature
temperature = getTemperature()
print ("Temperature: "+"{:4.2f}".format(temperature)+"C")

# Set the internal RTC so files have the correct date and time
time.set_time((year,month,day,hour,minute,second))

# Open the index number for the last image
lcd_display_text(0,224,"Loading Image Index...")

index = open('index.txt')

imgId = 0
try:
    imgId = int(index.read())
except:
    print("Resetting image index...")
    index = open('index.txt',"w+")
    index.write("0")

index.close()

# Save the triggered image to help with identifying false trigers
# Increment the image index
imgId += 1
index = open('index.txt','w')
index.write(str(imgId))
index.close()

# Log the detection results
log=open('fox.csv','a+')
logText = getDateTime()+"," \
    +"'TRIGGERED',0.0," \
    +str(imgId)+".jpg," \
    +str(daylight)+"," \
    +"{:4.2f}".format(temperature)+"\r\n"

log.write(logText)
log.close()
# Capture and save the image
if daylight: ir_leds.value(1)
img = sensor.snapshot()
ir_leds.value(0)
imgPath = "images/"+str(imgId)+".jpg"
img.save(imgPath)

# Load the labels
lcd_display_text(0,224,"Loading labels...")
f=open('labels.txt','r')
lcd_display_text(0,224,"labels opened...")
labels=f.readlines()
lcd_display_text(0,224,"Labels loaded...")
f.close()

# Load the AI model
lcd_display_text(0,224,"Loading model...")
task = kpu.load(0x200000) 
lcd_display_text(0,224,"Model loaded...")

# Set the time for timeout
timeout = utime.ticks_add(utime.ticks_ms(),timeout_duration * 1000)
lcd_display_text(0,224,"Timeout set...")
detectTime = 0

# Run fox detection loop
lcd_display_text(0,224,"FoxCAM Running...")
while(True):
    # If timeout exit and power down
    if utime.ticks_diff(utime.ticks_ms(),timeout) > 0:
        lcd_display_text(0,224,"TIMEOUT!!!")
        blueLED()
        break
    
    fox = False
    logText = ""
    greenLED()

    # Check if IR and LED Lights are required
    getDateTime()
    hours_as_fraction = hour + (minute / 60) 

    # Take image
    if daylight: ir_leds.value(1)
    img = sensor.snapshot()
    ir_leds.value(0)
    
    # Get the trip time from the RTC
    localtime = utime.localtime()
    
    # Detect foxes
    fmap = kpu.forward(task, img)
    plist=fmap[:]

    # Display the image on the LCD
    lcd_display_image(img)

    # Retrieve the top five predictions
    mlist = sorted(plist, reverse=True)[:5]
    # Loop through the top five results
    for detection in mlist:
        for animal in animals:
            # If its a red fox or another dog like animal with 15% or higher probability
            item = plist.index(detection)
            if 'red fox' in labels[item] or (animal in labels[item] and detection >= 0.15):
                fox = True
                lcd_display_text(0, 224, "Fox Detected")
                redLED()
                logText += "'"+animal+"',"+str(detection)
                
                # Extend the timeout
                timeout = utime.ticks_add(utime.ticks_ms(), timeout_extended_duration*1000)

                # Pulse siren and LED if dark
                loop = 0
                while loop < 2:
                    siren.value(1)
                    if not daylight:
                        led_3w.value(1)
                    time.sleep(0.5)
                    led_3w.value(0)
                    time.sleep(0.5)
                    siren.value(0)
                    if not daylight:
                        led_3w.value(1)
                    time.sleep(0.5)
                    led_3w.value(0)
                    time.sleep(0.5)
                    loop += 1

                break
            else:
                lcd_display_blank(0, 224)
        # Log data if fox detected
        if fox:
            imgId += 1
            index=open('index.txt','w')
            index.write(str(imgId))
            index.close()

            # Log the detection results
            log=open('fox.csv','a+')
            temperature = getTemperature()
            logText = getDateTime()+"," \
                +logText+"," \
                +str(imgId)+".jpg," \
                +str(daylight)+"," \
                +"{:4.2f}".format(temperature)+"\r\n"
            log.write(logText)
            log.close()
            # Save the image
            imgPath = "/sd/images/"+str(imgId)+".jpg"
            img.save(imgPath)
            break

# Deinitialising was causing the program to crash
#lcd_display_text(0, 224, "Deinitialising KPU...")
#kpu.deinit(task)

# Turn alarms and lights off
lcd_display_text(0, 224, "Turning off GPIO...")
led_r.value(1)
led_g.value(1)
led_b.value(1)
siren.value(0)
led_3w.value(0)
ir_leds.value(0)

# Unregister GPIO
fm.unregister(board_info.LED_R, fm.fpioa.GPIO2)
fm.unregister(board_info.LED_G, fm.fpioa.GPIO1)
fm.unregister(board_info.LED_B, fm.fpioa.GPIO0)

fm.unregister(board_info.WIFI_RX , fm.fpioa.GPIO7)
fm.unregister(board_info.WIFI_EN , fm.fpioa.GPIOHS0)
fm.unregister(board_info.PIN9 , fm.fpioa.GPIOHS1)
fm.unregister(board_info.PIN10 , fm.fpioa.GPIOHS2)

# Power down after time
lcd_display_text(0, 224, "Powering Down...")
pwr_off.value(1)
time.sleep(5)
pwr_off.value(0)
fm.unregister(board_info.WIFI_TX , fm.fpioa.GPIO6)
lcd_display_text(0, 224, "Powered Down...")
