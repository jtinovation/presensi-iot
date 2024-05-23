# import os
# import time
# import mysql.connector
# from mfrc522 import SimpleMFRC522
# import RPi.GPIO as GPIO
# import cv2
# import numpy as np

# reader = SimpleMFRC522()

# def register_member():
#     while True:
#         print("[INFO] INI ADALAH PROSES PENGHAPUSAN DAFTAR ANGGOTA")
#         print("Tempelkan kartu RFID.")
#         uid, read_text = reader.read()
        
#         print(f"UID: {uid}")
#         print(f"Nama: {read_text}")
        
#         validasi = input("Apakah data yang diinputkan sudah yakin akan dihapus? (y/n): ")
#         if validasi.lower() == 'y':
#             return 
#         else:
#             print("Ulangi proses penulisan nama anggota RFID.\n")


import os
import time
import mysql.connector
from mfrc522 import SimpleMFRC522
import RPi.GPIO as GPIO

# Koneksi ke database MySQL
db = mysql.connector.connect(
    host="localhost",
    user="tefa",
    password="123",
    database="absensi"
)

# Cursor untuk menjalankan perintah SQL
cursor = db.cursor()

def delete_all_datasets_and_tables():
    # Ambil semua folder dalam "Datasets_User" dan hapus satu per satu
    datasets_folder = os.path.join(os.getcwd(), "Datasets_User")
    for folder_name in os.listdir(datasets_folder):
        folder_path = os.path.join(datasets_folder, folder_name)
        if os.path.isdir(folder_path):
            delete_folder(folder_path)

    # Ambil semua tabel dalam database dan hapus satu per satu
    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()
    for table in tables:
        table_name = table[0]
        cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
        db.commit()
        print(f"Tabel {table_name} telah dihapus dari database.")

    print("Semua dataset dan tabel telah dihapus.")

def delete_folder(folder_path):
    for root, dirs, files in os.walk(folder_path, topdown=False):
        for name in files:
            os.remove(os.path.join(root, name))
        for name in dirs:
            os.rmdir(os.path.join(root, name))
    os.rmdir(folder_path)
    print(f"Folder {folder_path} telah dihapus.")

# Penggunaan fungsi untuk menghapus semua dataset dan tabel
delete_all_datasets_and_tables()
delete_folder()
