import time
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1306
from PIL import ImageFont

# Nonaktifkan peringatan GPIO
GPIO.setwarnings(False)

# Inisialisasi pembaca RFID
reader = SimpleMFRC522()

# Set the GPIO mode jika belum diatur
try:
    GPIO.setmode(GPIO.BCM)
except ValueError as e:
    print(f"Mode GPIO sudah diatur: {e}")

# Set up GPIO pin 17 as an output for buzzer
buzzer_pin = 11
if GPIO.getmode() is None:
    GPIO.setmode(GPIO.BCM)
GPIO.setup(buzzer_pin, GPIO.OUT)

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

def buzz(duration):
    """Fungsi untuk menyalakan buzzer selama `duration` detik"""
    GPIO.output(buzzer_pin, GPIO.HIGH)
    time.sleep(duration)
    GPIO.output(buzzer_pin, GPIO.LOW)

def read_rfid_and_buzz():
    print('Tempelkan RFID anda.')
    try:
        uid, text = reader.read()
        print(f"RFID terbaca. UID: {uid}, Text: {text}")
        display_oled("Terbaca", 14, 3)
        buzz(1)  # Nyalakan buzzer selama 1 detik
    except Exception as e:
        print(f"Error membaca RFID: {e}")
        display_oled("Tidak terbaca", 14, 3)
    finally:
        GPIO.cleanup()

if __name__ == "__main__":
    read_rfid_and_buzz()
