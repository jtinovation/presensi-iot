import os
import time
import mysql.connector
from mfrc522 import SimpleMFRC522
import RPi.GPIO as GPIO
import cv2
import numpy as np

reader = SimpleMFRC522()

# Membuat instance objek VideoCapture untuk webcam
cap = cv2.VideoCapture(0)

# Koneksi ke database MySQL
db = mysql.connector.connect(
    host="localhost",
    user="tefa",
    password="123",
    database="absensi"
)
cursor = db.cursor()

def register_member():
    while True:
        text = input("Nama anggota: ")
        print("Silahkan scan RFID anda.")
        reader.write(text)
        print("Scanning berhasil. Apakah data diri anda sebagai berikut?")
        uid, read_text = reader.read()
        
        print(f"UID: {uid}")
        print(f"Nama: {read_text}")
        
        validasi = input("Apakah data yang diinputkan sudah benar? (y/n): ")
        if validasi.lower() == 'y':
            return uid, read_text
        else:
            print("Ulangi proses penulisan nama anggota RFID.\n")

def create_dataset_and_db(uid, text):
    folder_uid = str(uid)
    folder_name = text.replace(" ", " ")
    folder_path = os.path.join(os.getcwd(), "Datasets_User", folder_name)

    if os.path.exists(folder_path):
        print("Gagal mendaftar, UID sudah terdaftar.")
        return False

    cursor.execute(f"SHOW TABLES LIKE '{folder_name}'")
    if cursor.fetchone():
        print("Gagal mendaftar, UID sudah terdaftar.")
        return False

    os.makedirs(folder_path, exist_ok=True)
    os.makedirs(os.path.join(folder_path, 'image'), exist_ok=True)

    print(f"Folder {folder_name} telah dibuat.")

    create_table_query = f"CREATE TABLE IF NOT EXISTS {folder_name} (id INT AUTO_INCREMENT PRIMARY KEY, \
                            nama VARCHAR(255), \
                            status_kehadiran VARCHAR(50), \
                            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
    cursor.execute(create_table_query)
    db.commit()

    print(f"Tabel {folder_name} telah dibuat di database.")

    return folder_path, folder_uid

def capture_images(folder_path):
    start_time = time.time()
    capture_duration = 15
    images = []

    while time.time() - start_time < capture_duration:
        ret, frame = cap.read()
        frameGray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        file_path = os.path.join(folder_path, 'image', f"foto_{int(time.time())}.jpg")
        if not os.path.exists(file_path):
            cv2.imwrite(file_path, frameGray)
            images.append(frameGray)

    print("\n [INFO] Pengambilan foto selesai, melanjutkan ke proses training....")
    return images

def train_recognizer(images, folder_uid):
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    labels = [0] * len(images)
    recognizer.train(images, np.array(labels))
    trained_path = os.path.join(os.getcwd(), f"{folder_uid}.yml")
    recognizer.save(trained_path)
    print("\n [INFO] Histogram berhasil disimpan.")

def main():
    while True:
        try:
            uid, text = register_member()
            result = create_dataset_and_db(uid, text)
            if result:
                folder_path, folder_uid = result
                start_capture = input("Apakah pengambilan foto bisa dimulai? (y/n): ")
                if start_capture.lower() == "y":
                    images = capture_images(folder_path)
                    train_recognizer(images, folder_uid)
                    break
                elif start_capture.lower() == "n":
                    time.sleep(15)
                else:
                    print("Input tidak valid.")
        except Exception as e:
            print(e)
            break

    cap.release()
    GPIO.cleanup()

if __name__ == "__main__":
    main()
