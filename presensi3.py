import cv2
import os
import time
import mysql.connector
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
import requests
import subprocess
from board import SCL, SDA
import busio
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306
import socket
from datetime import datetime

# Nonaktifkan peringatan GPIO
GPIO.setwarnings(False)

# Inisialisasi pembaca RFID
reader = SimpleMFRC522()

# Set the GPIO mode jika belum diatur
try:
    GPIO.setmode(GPIO.BCM)
except ValueError as e:
    print(f"Mode GPIO sudah diatur: {e}")

buzzer_pin = 11

if GPIO.getmode() is None:  
    GPIO.setmode(GPIO.BCM)

GPIO.setup(buzzer_pin, GPIO.OUT)

# Koneksi ke database MySQL
db = mysql.connector.connect(
    host="localhost",
    user="tefa",
    password="123",
    database="absensi"
)

# Cursor untuk menjalankan perintah SQL
cursor = db.cursor()

# Create an instance of the VideoCapture object for webcam
cap = cv2.VideoCapture(0)

# Parameters
font = cv2.FONT_HERSHEY_COMPLEX
height = 1
boxColor = (0, 0, 255)      # BGR- RED
nameColor = (255, 255, 255) # BGR- WHITE
confColor = (255, 255, 0)   # BGR- YELLOW

face_detector = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')

recognizer = cv2.face.LBPHFaceRecognizer_create()

def buzz(duration):
    GPIO.output(buzzer_pin, GPIO.HIGH)
    time.sleep(duration)
    GPIO.output(buzzer_pin, GPIO.LOW)

def check_server(address='10.10.0.157', port=8081):
    s = socket.socket()
    print(f"Mencoba menghubungkan ke {address} di port {port}")
    try:
        s.connect((address, port))
        print("Koneksi server sukses.")
        display_text_on_oled("Koneksi server sukses.", 16)
        time.sleep(1.5)
        clear_oled_display() 
    except Exception as e:
        print(f"Koneksi server gagal: {e}")
        display_text_on_oled("Koneksi server gagal.", 16)
        time.sleep(1.5)
        clear_oled_display() 
    finally:
        s.close()

def display_text_on_oled(text, font_size):
    i2c = busio.I2C(SCL, SDA)
    disp = adafruit_ssd1306.SSD1306_I2C(128, 32, i2c)
    disp.fill(0)
    disp.show()
    width = disp.width
    height = disp.height
    image = Image.new("1", (width, height))
    draw = ImageDraw.Draw(image)
    font_path = '/home/jtinova/Downloads/DejaVu_Sans/DejaVuSans-Bold.ttf'  # Adjust path to your TTF font file
    font = ImageFont.truetype(font_path, font_size)
    draw.rectangle((0, 0, width, height), outline=0, fill=0)
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    x = (width - text_width) // 2
    y = (height - text_height) // 2
    draw.text((x, y), text, font=font, fill=255)
    disp.image(image)
    disp.show()

def clear_oled_display():
    i2c = busio.I2C(SCL, SDA)
    disp = adafruit_ssd1306.SSD1306_I2C(128, 32, i2c)
    disp.fill(0)
    disp.show()

def read_rfid():
    print('Tempelkan RFID anda!')
    display_text_on_oled("Scan RFID anda!.", 16)
    time.sleep(1)
    clear_oled_display()   
    uid, text = reader.read()
    buzz(1)
    folder_uid = str(uid)
    folder_name = text.replace(" ", " ") 
    return folder_uid, folder_name

def check_rfid_registered(folder_uid):
    histogram_path = os.path.join(os.getcwd(), f"{folder_uid}.yml")
    if not os.path.exists(histogram_path):
        print("RFID belum terdaftar. Harap daftar terlebih dahulu.")
        display_text_on_oled("RFID tidak terdaftar.", 16)
        time.sleep(1)
        clear_oled_display()
        buzz(1)
        return False
    recognizer.read(histogram_path)
    return True

def face_recognition(folder_name, folder_uid, start_time, cap):
    status_sent = False
    while time.time() - start_time < 30:
        ret, frame = cap.read()
        frameGray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_detector.detectMultiScale(frameGray, scaleFactor=1.1, minNeighbors=5, minSize=(150, 150))
        for (x, y, w, h) in faces:
            namepos = (x + 5, y - 5)
            confpos = (x + 5, y + h - 5)
            cv2.rectangle(frame, (x, y), (x + w, y + h), boxColor, 3)
            id, confidence = recognizer.predict(frameGray[y:y+h, x:x+w])
            if confidence >= 55 and not status_sent:
                label_name = "Wajah Dikenali"
                confidence_text = f"{100 - confidence:.0f}%"
                timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
                display_text_on_oled("Wajah dikenali.", 16)
                time.sleep(1)
                clear_oled_display()
                send_to_database(folder_name, folder_uid, timestamp)
                send_to_api(folder_name, folder_uid, timestamp)
                status_sent = True
                break
            else:
                label_name = "Wajah Tidak Dikenali."
                confidence_text = f"{100 - confidence:.0f}%"
                display_text_on_oled("Wajah tidak dikenali.", 16)
                time.sleep(1)
                clear_oled_display()
                buzz(1)
            cv2.putText(frame, str(label_name), namepos, font, height, nameColor, 2)
            cv2.putText(frame, str(confidence_text), confpos, font, height, confColor, 1)
        cv2.imshow('Absensi', frame)
        if status_sent:
            break
        if cv2.waitKey(20) & 0xFF == ord('q'):
            break
    return status_sent

def send_to_database(folder_name, folder_uid, timestamp):
    sql = f"INSERT INTO {folder_name} (RFID, NIM, Status_kehadiran, Timestamp) VALUES (%s, %s, %s, %s)"
    val = (folder_uid, folder_name, "hadir", timestamp)
    cursor.execute(sql, val)
    db.commit()
    send_to_api(folder_name, folder_uid, timestamp)
    print("Status hadir telah dikirim ke database.")
    display_text_on_oled("Status hadir terkirim ke database.", 16)
    time.sleep(1.5)
    clear_oled_display()

def send_to_api(folder_name, folder_uid, timestamp):
    url = 'http://10.10.0.157:8081/api/presensi'
    data = {
        "rfid": folder_uid,
        "nim": folder_name,
        "status": "hadir",
        "timestamp": timestamp
    }
    response = requests.post(url, json=data)
    if response.status_code == 200:
        display_text_on_oled("Data terkirim ke server.", 16)
        time.sleep(1)
        clear_oled_display()
        print("Data berhasil dikirim ke server.")
        print("Response:", response.json())
    else:
        display_text_on_oled("Data presensi gagal dikirim.", 16)
        time.sleep(1)
        clear_oled_display()
        print("Data gagal dikirim ke server:", response.status_code)

def main():
    start_time = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0).time()
    end_time = datetime.now().replace(hour=9, minute=30, second=0, microsecond=0).time()

    while True:
        current_time = datetime.now().time()

        if current_time < start_time:
            display_text_on_oled("Presensi belum dimulai.", 16)
            time.sleep(1.5)
            clear_oled_display()
            continue
        elif current_time > end_time:
            display_text_on_oled("Anda terlambat.", 16)
            time.sleep(1.5)
            clear_oled_display()
            continue

        try:
            while True:
                check_server()
                folder_uid, folder_name = read_rfid()
                if not check_rfid_registered(folder_uid):
                    current_time = datetime.now().time()
                    if current_time > end_time:
                        display_text_on_oled("Anda terlambat.", 16)
                        time.sleep(1.5)
                        clear_oled_display()
                        continue
                    continue

                print(f"Nama: {folder_name}")
                print("RFID terdaftar. Melanjutkan ke proses pengenalan wajah.")
                display_text_on_oled("RFID terdaftar.", 16)
                time.sleep(1.5)
                clear_oled_display()
                buzz(0.2)
                start_time = time.time()
                status_sent = face_recognition(folder_name, folder_uid, start_time, cap)
                if not status_sent:
                    cv2.destroyAllWindows()
                    current_time = datetime.now().time()
                    if current_time > end_time:
                        display_text_on_oled("Anda terlambat.", 16)
                        time.sleep(1.5)
                        clear_oled_display()
                        continue
                    print("Gagal mengenali wajah dalam 30 detik. Silakan tempelkan RFID kembali.")
                    display_text_on_oled("Gagal mengenali wajah.", 16)
                    time.sleep(1.5)
                    clear_oled_display()
                    buzz(1)
                    continue
                if status_sent:
                    cv2.destroyAllWindows()
                    display_text_on_oled("Presensi selesai.", 16)
                    time.sleep(1)
                    clear_oled_display()
                    buzz(1)
                    print("\nPresensi telah selesai. Silakan tempelkan RFID kembali.")
        except Exception as e:
            print(e)
        finally:
            cap.release()
            GPIO.cleanup()
            cv2.destroyAllWindows()

if __name__ == "__main__":
    while True:
      main()
