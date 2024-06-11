
import time
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1306
from PIL import ImageFont

def display_oled(text, size, duration):
  serial = i2c(port=1, address=0x3C)
  oled = ssd1306(serial, width=128, height=32)

  font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
  font_size = size  # Sesuaikan ukuran font untuk layar 128x32
  font = ImageFont.truetype(font_path, font_size)

  with canvas(oled) as draw:
      draw.text((0, 0), text, font=font, fill="white")
      draw.text((0, 16), text, font=font, fill="white")

  time.sleep(duration)

  oled.clear()
  oled.display()
  GPIO.cleanup()

