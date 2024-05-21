# import os
# import time
# import mysql.connector
# from mfrc522 import SimpleMFRC522
# import RPi.GPIO as GPIO
# import cv2
# import numpy as np

# reader = SimpleMFRC522()

# # Membuat instance objek VideoCapture untuk webcam
# cap = cv2.VideoCapture(0)

# while True:
#     # Membaca UID dari RFID
#     # print('Tempelkan RFID anda.')
#     # uid, text = reader.read()
#     # print("UID dari RFID:", uid)
    
#     text = input("Nama anggota: ")
#     reader.write(text)
#     print("Scanning berhasil. Apakah data diri anda sebagai berikut?")
#     uid, text = reader.read()
    
#     # Membuat folder berdasarkan UID yang baru dibaca
#     folder_uid = str(uid)  # Menggunakan UID sebagai nama folder
#     folder_name = text.replace(" ", "_")
#     folder_path = os.path.join(os.getcwd(), "Datasets_User", folder_name)  # Mendapatkan path folder baru
    
#     # Validasi apakah folder dataset sudah ada
#     if os.path.exists(folder_path):
#         print("Gagal mendaftar, UID sudah terdaftar.")
#         continue

#     # Validasi apakah tabel di database sudah ada
#     db = mysql.connector.connect(
#         host="localhost",
#         user="tefa",
#         password="123",
#         database="absensi"
#     )
#     cursor = db.cursor()
#     cursor.execute(f"SHOW TABLES LIKE '{folder_name}'")
#     if cursor.fetchone():
#         print("Gagal mendaftar, UID sudah terdaftar.")
#         continue

#     # Membuat folder baru sesuai dengan UID RFID
#     os.makedirs(folder_path, exist_ok=True)  # Membuat folder baru jika belum ada
#     # Membuat folder 'image' di dalam folder anggota
#     os.makedirs(os.path.join(folder_path, 'image'), exist_ok=True)

#     print(f"Folder {folder_name} telah dibuat.")

#     # Validasi data yang diinputkan
#     validasi = input("Apakah data yang diinputkan sudah benar? (y/n): ")
#     if validasi.lower() != "y":
#         continue  # Ulangi proses input jika data tidak benar

#     #  Membuat tabel dengan nama folder_name di dalam database
#     create_table_query = f"CREATE TABLE IF NOT EXISTS {folder_name} (id INT AUTO_INCREMENT PRIMARY KEY, \
#                             nama VARCHAR(255), \
#                             status_kehadiran VARCHAR(50), \
#                             timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
#     cursor.execute(create_table_query)
#     db.commit()

#     print(f"Tabel {folder_name} telah dibuat di database.")
#     # Menanyakan apakah pengambilan foto bisa dimulai
#     while True:
#         start_capture = input("Apakah pengambilan foto bisa dimulai? (y/n): ")
#         if start_capture.lower() == "y":
#             break
#         elif start_capture.lower() == "n":
#             time.sleep(15)
#         else:
#             print("Input tidak valid.")

#     # Mengambil gambar wajah selama 15 detik dan menyimpannya di dalam folder baru
#     start_time = time.time()
#     capture_duration = 15  # Durasi pengambilan gambar dalam detik

#     images = []  # List untuk menyimpan gambar yang diambil

#     while time.time() - start_time < capture_duration:
#         ret, frame = cap.read()  # Baca frame dari kamera

#         # Convert frame dari BGR ke skala abu-abu
#         frameGray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

#         # Simpan gambar wajah berwarna ke dalam folder 'image' hanya jika file yang sama belum ada
#         file_path = os.path.join(folder_path, 'image', f"foto_{int(time.time())}.jpg")
#         if not os.path.exists(file_path):
#             cv2.imwrite(file_path, frameGray)
#             images.append(frameGray)  # Menambahkan gambar ke dalam list

#     print("\n [INFO] Pengambilan foto selesai, melanjutkan ke proses training....")

#     # Training recognizer menggunakan gambar yang telah diambil
#     recognizer = cv2.face.LBPHFaceRecognizer_create()
#     face_detector = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')

#     labels = [0] * len(images)  # Set label untuk setiap gambar
#     recognizer.train(images, np.array(labels))

#     # Simpan histogram di luar folder 'Datasets_User' dengan nama yang sesuai dengan NIM atau ID Pegawai
#     trained_path = os.path.join(os.getcwd(), f"{folder_uid}.yml")
#     recognizer.save(trained_path)

#     print("\n [INFO] Histogram berhasil disimpan.")

#     break

# # Bebaskan webcam
# cap.release()
# GPIO.cleanup()  # Membersihkan GPIO

import cv2
import os
import time
import mysql.connector
from mfrc522 import SimpleMFRC522

# Inisialisasi pembaca RFID
reader = SimpleMFRC522()

# Koneksi ke database MySQL
db = mysql.connector.connect(
    host="localhost",
    user="user",
    password="123",
    database="absensi"
)

# Cursor untuk menjalankan perintah SQL
cursor = db.cursor()

def main():
    # Parameters
    font = cv2.FONT_HERSHEY_COMPLEX
    height = 1
    boxColor = (0, 0, 255)      # BGR- RED
    nameColor = (255, 255, 255) # BGR- WHITE
    confColor = (255, 255, 0)   # BGR- YELLOW

    face_detector = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
    recognizer = cv2.face.LBPHFaceRecognizer_create()

    # Create an instance of the VideoCapture object for webcam
    cap = cv2.VideoCapture(0)

    while True:
        try:
            print('Tempelkan RFID anda.')
            uid, text = reader.read()
            folder_name = str(uid)  # Menggunakan UID sebagai nama folder

            # Check if RFID is registered
            histogram_path = os.path.join(os.getcwd(), f"{folder_name}.yml")
            if not os.path.exists(histogram_path):
                print("RFID belum terdaftar. Harap daftar terlebih dahulu")
                continue
            
            print("RFID terdaftar. Melanjutkan ke proses pengenalan wajah.")

            # Load the trained model
            recognizer.read(histogram_path)

            # Face recognition process
            start_time = time.time()
            while time.time() - start_time < 30:  # Maximum face recognition process for 30 seconds
                # Capture a frame from the camera
                ret, frame = cap.read()

                # Convert frame from BGR to grayscale
                frameGray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                # Detect faces in the grayscale frame
                faces = face_detector.detectMultiScale(
                    frameGray,
                    scaleFactor=1.1,
                    minNeighbors=5,
                    minSize=(150, 150)
                )

                for (x, y, w, h) in faces:
                    namepos = (x + 5, y - 5)
                    confpos = (x + 5, y + h - 5)
                    
                    # Create a bounding box across the detected face
                    cv2.rectangle(frame, (x, y), (x + w, y + h), boxColor, 3)

                    # Recognize face using the trained model
                    id, confidence = recognizer.predict(frameGray[y:y+h, x:x+w])

                    if confidence <= 100:
                        name = "Wajah Dikenali"
                        confidence_text = f"{100 - confidence:.0f}%"
                        # Send "hadir" status to MySQL database along with current timestamp
                        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
                        sql = f"INSERT INTO {folder_name} (nama, status_kehadiran, timestamp) VALUES (%s, %s, %s)"
                        val = (name, "hadir", timestamp)
                        cursor.execute(sql, val)
                        db.commit()
                        print("Status hadir telah dikirim ke database.")
                    else:
                        name = "Wajah Tidak Dikenali"
                        confidence_text = f"{100 - confidence:.0f}%"

                    # Display name and confidence of person who's face is recognized
                    cv2.putText(frame, str(name), namepos, font, height, nameColor, 2)
                    cv2.putText(frame, str(confidence_text), confpos, font, height, confColor, 1)

                cv2.imshow('Absensi', frame)  # Show Video
                if cv2.waitKey(20) & 0xFF == ord('q'):
                    break

        except Exception as e:
            print(e)
            break

        # Wait for a key event (extract sigfigs) and exit if 'ESC' or 'q' is pressed
        key = cv2.waitKey(100) & 0xff
        if key == 27 or key == 113:  # ESCAPE key or q key
            break

    # Release the webcam and close all windows
    print("\n Absensi telah selesai.")
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
