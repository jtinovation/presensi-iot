import cv2
import os
import time
import mysql.connector
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
import requests
import subprocess
from PIL import Image, ImageDraw, ImageFont
import socket
import json
from datetime import datetime
from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1306

# Nonaktifkan peringatan GPIO
GPIO.setwarnings(False)

# Inisialisasi pembaca RFID
reader = SimpleMFRC522()

serial = i2c(port=1, address=0x3C)
oled = ssd1306(serial, width=128, height=32)

font_path = "DejaVuSans-Bold.ttf"
font_size = 14  # Sesuaikan ukuran font untuk layar 128x32
font_oled = ImageFont.truetype(font_path, font_size)

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

def oled_display(text, duration):

    with canvas(oled) as draw:

        max_chars_per_line = 10
        lines = [text[i:i+max_chars_per_line] for i in range(0, len(text), max_chars_per_line)]
        y = 0
        for line in lines:
            
            draw.text((0, y), line, font=font_oled, fill="white")
            y += font_size
    
    time.sleep(duration)

def check_server(address, port):

    s = socket.socket()
    print(f"Mencoba menghubungkan ke {address} di port {port}")

    try:

        s.connect((address, port))
        print("Koneksi server sukses.")
        oled_display("Server terhubung.", 2)
        oled.clear()
        return True
    
    except Exception as e:

        print(f"Koneksi server gagal: {e}")
        oled_display("Server terputus.", 2)
        oled.clear()
        return False
    
    finally:
        s.close()

def read_rfid():

    print('Tempelkan RFID anda!')
    oled_display("Scan RFID!.", 2)
    oled.clear()
    uid, text = reader.read()
    buzz(0.1)
    folder_uid = str(uid)
    folder_name = text.replace(" ", "")
    return folder_uid, folder_name

def check_rfid_registered(folder_uid):

    histogram_path = os.path.join(os.getcwd(), f"{folder_uid}.yml")

    if not os.path.exists(histogram_path):

        print("RFID belum terdaftar. Harap daftar terlebih dahulu.")
        oled_display("RFID belum terdaftar.", 2)
        oled.clear()
        buzz(1)
        return False
    
    recognizer.read(histogram_path)

    return True

def face_recognition(folder_name, folder_uid, start_time, cap):

    status_sent = False

    while time.time() - start_time < 60:

        status_sent = False
        ret, frame = cap.read()
        frameGray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_detector.detectMultiScale(
            frameGray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(150, 150)
        )

        for (x, y, w, h) in faces:

            namepos = (x + 5, y - 5)
            confpos = (x + 5, y + h - 5)
            cv2.rectangle(frame, (x, y), (x + w, y + h), boxColor, 3)
            id, confidence = recognizer.predict(frameGray[y:y+h, x:x+w])

            if confidence <= 40 and not status_sent:

                label_name = "Wajah Dikenali"
                confidence_text = f"{100 - confidence:.0f}%"
                timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
                oled_display("Wajah dikenali.", 1)
                oled.clear()
                send_to_database(folder_name, folder_uid, timestamp)
                status_sent = True
                break

            else:

                label_name = "Wajah Tidak Dikenali."
                confidence_text = f"{100 - confidence:.0f}%"
                oled_display("Wajah tidak dikenali.", 1)
                oled.clear()
                status_sent = False

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
    save_data_locally(folder_name, folder_uid, timestamp)
    send_to_api(folder_name, folder_uid, timestamp)
    print("Status hadir telah dikirim ke database.")

def save_data_locally(folder_name, folder_uid, timestamp):

    local_data = {
        "rfid": folder_uid,
        "nim": folder_name,
        "status": "hadir",
        "timestamp": timestamp
    }
    with open("local_data.json", "a") as file:
        file.write(json.dumps(local_data) + "\n")

def send_to_api(folder_name, folder_uid, timestamp):
    url = 'http://10.10.0.157:8081/api/presensi'
    data = {
        "rfid": folder_uid,
        "nim": folder_name,
        "status": "hadir",
        "timestamp": timestamp
    }

    try:
        response = requests.post(url, json=data)

        if response.status_code == 200:
            print("Data berhasil dikirim ke server.")
            print("Response:", response.json())
            return True
        else:
            print(f"Gagal mengirim data ke server. Status code: {response.status_code}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"Request ke server gagal: {e}")
        return False

def send_local_data_to_api():
    try:
        with open("local_data.json", "r") as file:
            lines = file.readlines()

        for line in lines:
            data = json.loads(line)
            success = send_to_api(data['nim'], data['rfid'], data['timestamp'])
            
            if not success:
                # Jika gagal mengirim, hentikan proses dan biarkan data lokal tetap ada
                print("Gagal mengirim data lokal ke server.")
                return
        
        # Jika semua data berhasil terkirim, hapus file local_data.json
        os.remove("local_data.json")

    except FileNotFoundError:
        print("Tidak ada data lokal yang perlu dikirim.")

    except Exception as e:
        print(f"Terjadi kesalahan saat mengirim data lokal: {e}")

def main():

    server_connected = False
    while True:
        
        current_time = datetime.now()
        start_time = current_time.replace(hour=9, minute=0, second=0, microsecond=0)
        end_time = current_time.replace(hour=15, minute=0, second=0, microsecond=0)

        address = "10.10.0.157"
        port = 8081

        if current_time < start_time:

            send_local_data_to_api()
            continue
         
        elif current_time > end_time:

            oled_display("Anda terlambat.", 32340)
            oled.clear()
            continue

        try:

            while True:

                if not server_connected:

                    server_connected = check_server(address, port)

                if server_connected:

                    folder_uid, folder_name = read_rfid()

                    if not check_rfid_registered(folder_uid):
                        continue

                    print(f"Nama: {folder_name}")
                    print("RFID terdaftar. Melanjutkan ke proses pengenalan wajah.")
                    oled_display("RFID terdaftar.", 2)
                    oled.clear()

                    buzz(0.1)

                    start_time = time.time()
                    status_sent = face_recognition(folder_name, folder_uid, start_time, cap)

                    if not status_sent:

                        time.sleep(10)
                        cv2.destroyAllWindows()
                        print("Gagal mengenali wajah dalam 30 detik. Silakan tempelkan RFID kembali.")
                        oled_display("Wajah tidak dikenali.", 2)
                        oled.clear()
                        buzz(1)
                        cap.release()
                        GPIO.cleanup()
                        cv2.destroyAllWindows()
                        continue

                    if status_sent:

                        time.sleep(10)
                        cv2.destroyAllWindows()
                        oled_display("Presensi sukses.", 2)
                        oled.clear()
                        buzz(1)
                        print("\nPresensi telah selesai. Silakan tempelkan RFID kembali.")
                        cap.release()
                        GPIO.cleanup()
                        cv2.destroyAllWindows()

                else:

                    folder_uid, folder_name = read_rfid()

                    if not check_rfid_registered(folder_uid):
                        continue

                    print(f"Nama: {folder_name}")
                    print("RFID terdaftar. Melanjutkan ke proses pengenalan wajah.")
                    oled_display("RFID terdaftar.", 2)
                    oled.clear()

                    buzz(0.1)

                    start_time = time.time()
                    status_sent = face_recognition(folder_name, folder_uid, start_time, cap)

                    if not status_sent:

                        time.sleep(10)
                        cv2.destroyAllWindows()
                        print("Gagal mengenali wajah dalam 30 detik. Silakan tempelkan RFID kembali.")
                        oled_display("Wajah tidak dikenali.", 2)
                        oled.clear()
                        buzz(1)
                        cap.release()
                        GPIO.cleanup()
                        cv2.destroyAllWindows()
                        continue

                    if status_sent:

                        time.sleep(10)
                        oled_display("Presensi sukses.", 2)
                        oled.clear()
                        buzz(1)
                        print("\nPresensi telah selesai. Silakan tempelkan RFID kembali.")
                        cap.release()
                        GPIO.cleanup()
                        cv2.destroyAllWindows()

        except Exception as e:
            print(e)

        finally:

            cap.release()
            GPIO.cleanup()
            cv2.destroyAllWindows()

if __name__ == "__main__":

    main()
