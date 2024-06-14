import os
import time
import cv2
import numpy as np
import mysql.connector
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
import shutil
from PIL import Image, ImageDraw, ImageFont
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

# Membuat instance objek VideoCapture untuk webcam
cap = cv2.VideoCapture(0)

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
    oled.clear()

def register_member():
    while True:
        text = input("Masukkan NIM atau ID anggota anda: ")
        print("Silahkan scan RFID anda.")
        oled_display("Scan RFID!", 2)
        reader.write(text)
        print("Scanning berhasil. Apakah data diri anda berikut ini sudah benar?")
        buzz(0.1)
        uid, read_text = reader.read()
        print(f"UID: {uid}")
        print(f"Nama: {read_text}")
        oled_display(read_text, 3)
        validasi = input("Apakah data berikut sudah benar? (y/n): ")
        if validasi.lower() == 'y':
            buzz(0.1)
            return uid, read_text
        else:
            buzz(0.1)
            print("Ulangi proses penulisan NIM atau ID anggota pada RFID.\n")
            oled_display("Ulangi pendaftaran.", 2)

def create_dataset_and_db(uid, text):
    folder_uid = str(uid)
    folder_name = text.replace(" ", "")  # Ganti spasi dengan underscore
    folder_path = os.path.join(os.getcwd(), "Datasets_User", folder_name)
    histogram_path = os.path.join(os.getcwd(), f"{folder_uid}.yml")

    while os.path.exists(histogram_path):
        buzz(0.6)
        print("UID sudah terdaftar.")
        delete_histogram = input("Apakah anda ingin menghapus data lama yang ada pada RFID? (y/n): ")
        if delete_histogram.lower() == "y":
            buzz(1)
            shutil.rmtree(histogram_path)
            oled_display("Menghapus data RFID.", 2)
            print("Data RFID dihapus. Lanjutkan pendaftaran.")
            break
        elif delete_histogram.lower() == "n":
            buzz(0.1)
            print("Menunggu 15 detik. Silahkan bersiap-siap")
            oled_display("Menunggu 15 detik..", 2)
            time.sleep(15)
            return False
        else:
            print("Input tidak valid. Ulangi.")
            oled_display("Input tidak valid.", 2)

    cursor.execute(f"SHOW TABLES LIKE {folder_name}")
    if cursor.fetchone():
        buzz(0.6)
        print("Gagal mendaftar, Table sudah dibuat.")
        oled_display("RFID terdaftar.", 2)
        return False

    os.makedirs(folder_path, exist_ok=True)
    os.makedirs(os.path.join(folder_path, 'image'), exist_ok=True)

    print(f"Folder {folder_name} telah dibuat.")
    oled_display("Folder dibuat.", 1)

    create_table_query = f"CREATE TABLE IF NOT EXISTS {folder_name} (id INT AUTO_INCREMENT PRIMARY KEY, \
                            RFID BIGINT(255), \
                            NIM VARCHAR(255), \
                            Status_kehadiran VARCHAR(50), \
                            Timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
    cursor.execute(create_table_query)
    db.commit()

    print(f"Tabel {folder_name} telah dibuat di database.")
    oled_display("Database dibuat.", 1)

    return folder_path, folder_uid

def create_dataset_and_db(uid, text):
    folder_uid = str(uid)
    folder_name = text.replace(" ", "")  # Ganti spasi dengan underscore
    folder_path = os.path.join(os.getcwd(), "Datasets_User", folder_name)
    histogram_path = os.path.join(os.getcwd(), f"{folder_uid}.yml")

    while os.path.exists(histogram_path):
        buzz(0.6)
        print("UID sudah terdaftar.")
        delete_histogram = input("Apakah anda ingin menghapus data lama yang ada pada RFID? (y/n): ")
        if delete_histogram.lower() == "y":
            try:
                buzz(1)
                os.remove(histogram_path)
                oled_display("Menghapus data RFID.", 2)
                print("Data RFID dihapus. Lanjutkan pendaftaran.")
                break
            except OSError as e:
                print(f"Terjadi kesalahan saat menghapus file: {e}")
                oled_display("Gagal menghapus data.", 2)
                return False  # Menghentikan proses jika penghapusan gagal
        elif delete_histogram.lower() == "n":
            buzz(0.1)
            print("Proses pendaftaran dibatalkan. Menunggu 15 detik sebelum mengulangi.")
            oled_display("Menunggu 15 detik..", 2)
            time.sleep(15)
            return False  # Keluar dari fungsi untuk kembali ke proses utama
        else:
            buzz(0.1)
            print("Input tidak valid. Ulangi.")
            oled_display("Input tidak valid.", 2)

    os.makedirs(folder_path, exist_ok=True)
    os.makedirs(os.path.join(folder_path, 'image'), exist_ok=True)

    print(f"Folder {folder_name} telah dibuat.")
    oled_display("Folder dibuat.", 1)

    create_table_query = f"CREATE TABLE IF NOT EXISTS {folder_name} (id INT AUTO_INCREMENT PRIMARY KEY, \
                            RFID BIGINT(255), \
                            NIM VARCHAR(255), \
                            Status_kehadiran VARCHAR(50), \
                            Timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
    cursor.execute(create_table_query)
    db.commit()

    print(f"Tabel {folder_name} telah dibuat di database.")
    oled_display("Database dibuat.", 1)

    return folder_path, folder_uid

def capture_images(folder_path):
    start_time = time.time()
    capture_duration = 60
    images = []

    while time.time() - start_time < capture_duration:
        ret, frame = cap.read()
        frameGray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        file_path = os.path.join(folder_path, 'image', f"foto_{int(time.time())}.jpg")

        if not os.path.exists(file_path):
            cv2.imwrite(file_path, frameGray)
            images.append(frameGray)

        remaining_time = int(capture_duration - (time.time() - start_time))
        oled_display(f"Sisa waktu: {remaining_time} detik", 1)

    print("Pengambilan foto selesai, melanjutkan ke proses training....")
    oled_display("Lanjut ke training...", 10)

    return images

def train_recognizer(images, folder_uid):
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    labels = [0] * len(images)
    recognizer.train(images, np.array(labels))
    trained_path = os.path.join(os.getcwd(), f"{folder_uid}.yml")
    recognizer.save(trained_path)
    
    buzz(1)
    
    print("Histogram berhasil disimpan. Proses pendaftaran telah selesai.")
    oled_display("Data wajah sukses diambil.", 2)

    return trained_path

def datasets_purge():
    folder_path = os.path.join(os.getcwd(), "Datasets_User")
    if os.path.exists(folder_path):
        shutil.rmtree(folder_path)
    else:
        print("Datasets_User tidak ditemukan.")

def main():
    while True:
        try:
            uid, text = register_member()
            result = create_dataset_and_db(uid, text)
            
            if result:
                folder_path, folder_uid = result
                while True:
                    start_capture = input("Apakah pengambilan foto bisa dimulai? (y/n): ")
                    if start_capture.lower() == "y":
                        buzz(1)
                        oled_display("Pengambilan foto...", 2)
                        images = capture_images(folder_path)
                        train_recognizer(images, folder_uid)
                        datasets_purge()
                        break
                    elif start_capture.lower() == "n":
                        buzz(0.1)
                        print("Menunggu 15 detik. Silahkan bersiap-siap")
                        oled_display("Menunggu 15 detik..", 2)
                        time.sleep(15)
                    else:
                        print("Input tidak valid.")

        except Exception as e:
            print(e)
            break

    cap.release()
    GPIO.cleanup()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
