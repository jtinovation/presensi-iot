# SPDX-FileCopyrightText: 2017 Tony DiCola for Adafruit Industries
# SPDX-FileCopyrightText: 2017 James DeVito for Adafruit Industries
# SPDX-License-Identifier: MIT

# This example is for use on (Linux) computers that are using CPython with
# Adafruit Blinka to support CircuitPython libraries. CircuitPython does
# not support PIL/pillow (python imaging library)!

import time
import subprocess

from board import SCL, SDA
import busio
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306


# Create the I2C interface.
i2c = busio.I2C(SCL, SDA)

# Create the SSD1306 OLED class.
# The first two parameters are the pixel width and pixel height.  Change these
# to the right size for your display!
disp = adafruit_ssd1306.SSD1306_I2C(128, 32, i2c)

# Clear display.
disp.fill(0)
disp.show()

# Create blank image for drawing.
# Make sure to create image with mode '1' for 1-bit color.
width = disp.width
height = disp.height
image = Image.new("1", (width, height))

# Get drawing object to draw on image.
draw = ImageDraw.Draw(image)

# Draw a black filled box to clear the image.
draw.rectangle((0, 0, width, height), outline=0, fill=0)

# Draw some shapes.
# First define some constants to allow easy resizing of shapes.
padding = -2
top = padding
bottom = height - padding
# Move left to right keeping track of the current x position for drawing shapes.
x = 0


# Load default font.
font = ImageFont.load_default()

# Alternatively load a TTF font.  Make sure the .ttf font file is in the
# same directory as the python script!
# Some other nice fonts to try: http://www.dafont.com/bitmap.php
# font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 9)

while True:
    # Draw a black filled box to clear the image.
    draw.rectangle((0, 0, width, height), outline=0, fill=0)

    # Shell scripts for system monitoring from here:
    # https://unix.stackexchange.com/questions/119126/command-to-display-memory-usage-disk-usage-and-cpu-load
    cmd = "hostname -I | cut -d' ' -f1"
    IP = subprocess.check_output(cmd, shell=True).decode("utf-8")
    cmd = 'cut -f 1 -d " " /proc/loadavg'
    CPU = subprocess.check_output(cmd, shell=True).decode("utf-8")
    cmd = "free -m | awk 'NR==2{printf \"Mem: %s/%s MB  %.2f%%\", $3,$2,$3*100/$2 }'"
    MemUsage = subprocess.check_output(cmd, shell=True).decode("utf-8")
    cmd = 'df -h | awk \'$NF=="/"{printf "Disk: %d/%d GB  %s", $3,$2,$5}\''
    Disk = subprocess.check_output(cmd, shell=True).decode("utf-8")

    # Write four lines of text.

    draw.text((x, top + 0), "IP: " + IP, font=font, fill=255)
    draw.text((x, top + 8), "CPU load: " + CPU, font=font, fill=255)
    draw.text((x, top + 16), MemUsage, font=font, fill=255)
    draw.text((x, top + 25), Disk, font=font, fill=255)

    image = image.rotate(180)
    
    # Display image.
    disp.image(image)
    disp.show()
    time.sleep(0.1)


import time
import board
import busio
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306

def display_text(text_lines, font_size=12, sleep_time=5):
    # Setup I2C connection
    i2c = busio.I2C(board.SCL, board.SDA)

    # Define the display parameters
    WIDTH = 128
    HEIGHT = 32  # Change to 64 if you have a 128x64 display
    BORDER = 5

    # Create the SSD1306 OLED class
    # The first two parameters are the pixel width and pixel height. Change these
    # to the right size for your display!
    oled = adafruit_ssd1306.SSD1306_I2C(WIDTH, HEIGHT, i2c, addr=0x3C)

    # Clear display.
    oled.fill(0)
    oled.show()

    # Create blank image for drawing.
    # Make sure to create image with mode '1' for 1-bit color.
    image = Image.new("1", (oled.width, oled.height))

    # Get drawing object to draw on image.
    draw = ImageDraw.Draw(image)

    # Load default font with custom size
    font = ImageFont.load_default(size=font_size)

    # Define text starting position
    x = 0
    y = 0

    # Clear the image
    draw.rectangle((0, 0, oled.width, oled.height), outline=0, fill=0)

    # Draw each line of text
    for line in text_lines:
        draw.text((x, y), line, font=font, fill=255)
        y += font_size + 2  # Move to the next line (2 pixels space)

    # Display image
    oled.image(image)
    oled.show()

    time.sleep(sleep_time)

# Contoh pemanggilan fungsi dengan teks yang berbeda, ukuran huruf yang berbeda, dan waktu tidur yang berbeda
display_text(["Ini", "adalah", "contoh", "penggunaan", "fungsi"], font_size=16, sleep_time=3)

# sudo i2cdetect -y 1
# sudo pip3 install adafruit-circuitpython-ssd1306 adafruit-circuitpython-framebuf pillow

import time
import board
import busio
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306

# Setup I2C connection
i2c = busio.I2C(board.SCL, board.SDA)

# Define the display parameters
WIDTH = 128
HEIGHT = 32  # Change to 64 if you have a 128x64 display
BORDER = 5

# Create the SSD1306 OLED class
# The first two parameters are the pixel width and pixel height. Change these
# to the right size for your display!
oled = adafruit_ssd1306.SSD1306_I2C(WIDTH, HEIGHT, i2c, addr=0x3C)

# Clear display.
oled.fill(0)
oled.show()

# Create blank image for drawing.
# Make sure to create image with mode '1' for 1-bit color.
image = Image.new("1", (oled.width, oled.height))

# Get drawing object to draw on image.
draw = ImageDraw.Draw(image)

# Load default font.
font = ImageFont.load_default()

# Define some text to display
text_lines = [
    "Hello, World!",
    "Raspberry Pi",
    "OLED Display",
    "SSD1306"
]

# Define text starting position
x = 0
y = 0

# Clear the image
draw.rectangle((0, 0, oled.width, oled.height), outline=0, fill=0)

# Draw each line of text
for line in text_lines:
    draw.text((x, y), line, font=font, fill=255)
    y += 10  # Move to the next line (10 pixels down)

# Display image
oled.image(image)
oled.show()

time.sleep(5)

