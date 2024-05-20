import os
import time
import mysql.connector
from mfrc522 import SimpleMFRC522
import RPi.GPIO as GPIO
import cv2
import buzzer 

reader = SimpleMFRC522()

led_green_pin = 11  
led_red_pin = 15
buzzer_pin = 13

GPIO.setmode(GPIO.BCM)
GPIO.setup(led_green_pin, GPIO.OUT)
GPIO.setup(led_red_pin, GPIO.OUT)
GPIO.setup(buzzer_pin, GPIO.OUT) 

# Membuat instance objek VideoCapture untuk webcam
cap = cv2.VideoCapture(0)

while True:
    text1 = input("Nama anggota: ")
    text2 = input("NIM atau ID Pegawai: ")
    
    # Membuat folder berdasarkan NIM yang baru diinputkan
    folder_name = text2.replace(" ", "_")  # Mengganti spasi dengan underscore untuk nama folder
    folder_path = os.path.join(os.getcwd(), "Datasets_User", folder_name)  # Mendapatkan path folder baru
    
    # Validasi apakah folder dataset sudah ada
    if os.path.exists(folder_path):
        print("Gagal mendaftar, NIM sudah terdaftar.")
        continue

    # Validasi apakah tabel di database sudah ada
    db = mysql.connector.connect(
        host="localhost",
        user="user",
        password="123",
        database="absensi"
    )
    cursor = db.cursor()
    cursor.execute(f"SHOW TABLES LIKE '{folder_name}'")
    if cursor.fetchone():
        print("Gagal mendaftar, NIM sudah terdaftar.")
        continue
    
    print("Silahkan scan RFID anda.")
    reader.write(text1 + "," + text2)
    print("Scanning berhasil.")

    # Membuat folder baru
    os.makedirs(folder_path, exist_ok=True)  # Membuat folder baru jika belum ada
    # Membuat folder 'image' dan 'trained' di dalam folder anggota
    os.makedirs(os.path.join(folder_path, 'image'), exist_ok=True)
    os.makedirs(os.path.join(folder_path, 'trained'), exist_ok=True)

    print(f"Folder {folder_name} telah dibuat.")

    # Validasi data yang diinputkan
    validasi = input("Apakah data yang diinputkan sudah benar? (y/n): ")
    if validasi.lower() != "y":
        continue  # Ulangi proses input jika data tidak benar

    # Membuat tabel dengan nama folder_name di dalam database
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

    while time.time() - start_time < capture_duration:
        ret, frame = cap.read()  # Baca frame dari kamera

        # Convert frame dari BGR ke skala abu-abu
        frameGray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Simpan gambar wajah berwarna ke dalam folder 'image' hanya jika file yang sama belum ada
        file_path = os.path.join(folder_path, 'image', f"foto_{int(time.time())}.jpg")
        if not os.path.exists(file_path):
            cv2.imwrite(file_path, frameGray)

    print("\n [INFO] Pengambilan foto selesai.")
    break

# Bebaskan webcam
cap.release()
GPIO.cleanup()  # Membersihkan GPIO
