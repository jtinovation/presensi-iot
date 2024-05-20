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

while True:
    # Membaca UID dari RFID
    print('Tempelkan RFID anda.')
    uid = reader.read()
    print("UID dari RFID:", uid)
    
    # Membuat folder berdasarkan UID yang baru dibaca
    folder_name = str(uid)  # Menggunakan UID sebagai nama folder
    folder_path = os.path.join(os.getcwd(), "Datasets_User", folder_name)  # Mendapatkan path folder baru
    
    # Validasi apakah folder dataset sudah ada
    if os.path.exists(folder_path):
        print("Gagal mendaftar, UID sudah terdaftar.")
        continue

    # Validasi apakah tabel di database sudah ada
    db = mysql.connector.connect(
        host="localhost",
        user="tefa",
        password="123",
        database="absensi"
    )
    cursor = db.cursor()
    cursor.execute(f"SHOW TABLES LIKE '{folder_name}'")
    if cursor.fetchone():
        print("Gagal mendaftar, UID sudah terdaftar.")
        continue

    # Membuat folder baru sesuai dengan UID RFID
    os.makedirs(folder_path, exist_ok=True)  # Membuat folder baru jika belum ada
    # Membuat folder 'image' di dalam folder anggota
    os.makedirs(os.path.join(folder_path, 'image'), exist_ok=True)

    print(f"Folder {folder_name} telah dibuat.")

    # Validasi data yang diinputkan
    validasi = input("Apakah data yang diinputkan sudah benar? (y/n): ")
    if validasi.lower() != "y":
        continue  # Ulangi proses input jika data tidak benar

    #  Membuat tabel dengan nama folder_name di dalam database
    create_table_query = f"CREATE TABLE IF NOT EXISTS {folder_name} (id INT AUTO_INCREMENT PRIMARY KEY, \
                            nama VARCHAR(255), \
                            status_kehadiran VARCHAR(50), \
                            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
    cursor.execute(create_table_query)
    db.commit()

    print(f"Tabel {folder_name} telah dibuat di database.")
    # Menanyakan apakah pengambilan foto bisa dimulai
    while True:
        start_capture = input("Apakah pengambilan foto bisa dimulai? (y/n): ")
        if start_capture.lower() == "y":
            break
        elif start_capture.lower() == "n":
            time.sleep(15)
        else:
            print("Input tidak valid.")

    # Mengambil gambar wajah selama 15 detik dan menyimpannya di dalam folder baru
    start_time = time.time()
    capture_duration = 15  # Durasi pengambilan gambar dalam detik

    images = []  # List untuk menyimpan gambar yang diambil

    while time.time() - start_time < capture_duration:
        ret, frame = cap.read()  # Baca frame dari kamera

        # Convert frame dari BGR ke skala abu-abu
        frameGray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Simpan gambar wajah berwarna ke dalam folder 'image' hanya jika file yang sama belum ada
        file_path = os.path.join(folder_path, 'image', f"foto_{int(time.time())}.jpg")
        if not os.path.exists(file_path):
            cv2.imwrite(file_path, frameGray)
            images.append(frameGray)  # Menambahkan gambar ke dalam list

    print("\n [INFO] Pengambilan foto selesai, melanjutkan ke proses training....")

    # Training recognizer menggunakan gambar yang telah diambil
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    face_detector = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')

    labels = [0] * len(images)  # Set label untuk setiap gambar
    recognizer.train(images, np.array(labels))

    # Simpan histogram di luar folder 'Datasets_User' dengan nama yang sesuai dengan NIM atau ID Pegawai
    trained_path = os.path.join(os.getcwd(), f"{folder_name}.yml")
    recognizer.save(trained_path)

    print("\n [INFO] Histogram berhasil disimpan.")

    break

# Bebaskan webcam
cap.release()
GPIO.cleanup()  # Membersihkan GPIO
