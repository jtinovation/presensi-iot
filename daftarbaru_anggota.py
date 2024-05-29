import os
import time
import cv2
import numpy as np
import mysql.connector
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
import Adafruit_SSD1306

# Nonaktifkan peringatan GPIO
GPIO.setwarnings(False)

# Inisialisasi pembaca RFID
reader = SimpleMFRC522()

# GPIO pin configuration for the OLED display
OLED_RESET_PIN = None  # Set to GPIO pin if your display has a reset pin
OLED = Adafruit_SSD1306.SSD1306_128_64(rst=OLED_RESET_PIN)

# Initialize the OLED display
OLED.begin()

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

# Membuat instance objek VideoCapture untuk webcam
cap = cv2.VideoCapture(0)

def buzz(duration):
    # """Fungsi untuk menyalakan buzzer selama `duration` detik"""
    GPIO.output(buzzer_pin, GPIO.HIGH)
    time.sleep(duration)
    GPIO.output(buzzer_pin, GPIO.LOW)

def register_member():

    while True:
        
        text = input("Nama anggota: ")

        OLED.clear()
        OLED.draw.text((0, 0), "Masukkan nama anggota!", font=None, fill=255)
        OLED.display()
        
        print("Silahkan scan RFID anda.")

        OLED.clear()
        OLED.draw.text((0, 0), "Silahkan RFID anda.", font=None, fill=255)
        OLED.display()

        reader.write(text)

        print("Scanning berhasil. Apakah data diri anda berikut ini sudah benar?")
        
        OLED.clear()
        OLED.draw.text((0, 0), "Cek kembali data diri anda.", font=None, fill=255)
        OLED.display()

        buzz(0.2)

        uid, read_text = reader.read()
        
        print(f"UID: {uid}")
        print(f"Nama: {read_text}")
        
        validasi = input("Apakah data berikut sudah benar? (y/n): ")

        OLED.clear()
        OLED.draw.text((0, 0), "Apakah data berikut sudah benar?", font=None, fill=255)
        OLED.display()

        if validasi.lower() == 'y':
            
            buzz(0.2)
            
            return uid, read_text
        
        else:

            buzz(0.2)
            
            print("Ulangi proses penulisan nama anggota RFID.\n")

def create_dataset_and_db(uid, text):
    
    folder_uid = str(uid)
    folder_name = text.replace(" ", " ")
    folder_path = os.path.join(os.getcwd(), "Datasets_User", folder_name)

    if os.path.exists(folder_path):
        
        buzz(1.2)

        print("Gagal mendaftar, UID sudah terdaftar.")

        OLED.clear()
        OLED.draw.text((0, 0), "Gagal mendaftar.", font=None, fill=255)
        OLED.display()

        return False

    cursor.execute(f"SHOW TABLES LIKE '{folder_name}'")
    
    if cursor.fetchone():

        buzz(1.2)
        
        print("Gagal mendaftar, UID sudah terdaftar.")
        
        OLED.clear()
        OLED.draw.text((0, 0), "Gagal mendaftar.", font=None, fill=255)
        OLED.display()

        return False

    os.makedirs(folder_path, exist_ok=True)
    os.makedirs(os.path.join(folder_path, 'image'), exist_ok=True)

    print(f"Folder {folder_name} telah dibuat.")

    OLED.clear()
    OLED.draw.text((0, 0), "Gagal mendaftar.", font=None, fill=255)
    OLED.display()

    create_table_query = f"CREATE TABLE IF NOT EXISTS {folder_name} (id INT AUTO_INCREMENT PRIMARY KEY, \
                            nama VARCHAR(255), \
                            status_kehadiran VARCHAR(50), \
                            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
    cursor.execute(create_table_query)
    
    db.commit()

    print(f"Tabel {folder_name} telah dibuat di database.")

    OLED.clear()
    OLED.draw.text((0, 0), "Table data diri telah dibuat.", font=None, fill=255)
    OLED.display()

    return folder_path, folder_uid

def capture_images(folder_path):

    start_time = time.time()
    capture_duration = 20
    images = []

    while time.time() - start_time < capture_duration:
        
        ret, frame = cap.read()
        frameGray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        file_path = os.path.join(folder_path, 'image', f"foto_{int(time.time())}.jpg")

        if not os.path.exists(file_path):

            cv2.imwrite(file_path, frameGray)
            images.append(frameGray)

    print("\n [INFO] Pengambilan foto selesai, melanjutkan ke proses training....")

    OLED.clear()
    OLED.draw.text((0, 0), "Pengambilan foto selesai, melanjutkan ke proses training....", font=None, fill=255)
    OLED.display()    

    return images

def train_recognizer(images, folder_uid):

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    labels = [0] * len(images)
    recognizer.train(images, np.array(labels))
    trained_path = os.path.join(os.getcwd(), f"{folder_uid}.yml")
    recognizer.save(trained_path)
    
    buzz(1.3)
    
    print("\n [INFO] Histogram berhasil disimpan. Proses pendaftaran telah selesai.")

    OLED.clear()
    OLED.draw.text((0, 0), "Histogram berhasil disimpan. Proses pendaftaran telah selesai.", font=None, fill=255)
    OLED.display() 

def main():

    while True:

        try:

            uid, text = register_member()
            result = create_dataset_and_db(uid, text)
            
            if result:
                
                folder_path, folder_uid = result

                while True:
                    
                    start_capture = input("Apakah pengambilan foto bisa dimulai? (y/n): ")
                    
                    OLED.clear()
                    OLED.draw.text((0, 0), "Apakah pengambilan foto bisa dimulai?", font=None, fill=255)
                    OLED.display()

                    if start_capture.lower() == "y":

                        buzz(1.1)
                        
                        images = capture_images(folder_path)
                        
                        train_recognizer(images, folder_uid)
                        
                        break

                    elif start_capture.lower() == "n":
                        
                        buzz(0.2)

                        print("\n [INFO] Menunggu 15 detik. Silahkan bersiap-siap")

                        OLED.clear()
                        OLED.draw.text((0, 0), "Menunggu 15 detik..", font=None, fill=255)
                        OLED.display()

                        time.sleep(15)

                    else:

                        print("\n [INFO] Input tidak valid.")

                        OLED.clear()
                        OLED.draw.text((0, 0), "Input tidak valid", font=None, fill=255)
                        OLED.display()

        except Exception as e:

            print(e)
            
            break

    cap.release()

    GPIO.cleanup()

if __name__ == "__main__":

    main()
