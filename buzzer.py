import RPi.GPIO as GPIO
import time
from mfrc522 import SimpleMFRC522

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
        buzz(1)  # Nyalakan buzzer selama 1 detik
    except Exception as e:
        print(f"Error membaca RFID: {e}")
    finally:
        GPIO.cleanup()

if __name__ == "__main__":
    read_rfid_and_buzz()
