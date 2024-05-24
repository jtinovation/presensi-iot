# import cv2
# import os
# import time
# import mysql.connector
# import RPi.GPIO as GPIO
# from mfrc522 import SimpleMFRC522

# # Inisialisasi pembaca RFID
# reader = SimpleMFRC522()

# # Koneksi ke database MySQL
# db = mysql.connector.connect(
#     host="localhost",
#     user="tefa",
#     password="123",
#     database="absensi"
# )

# # Cursor untuk menjalankan perintah SQL
# cursor = db.cursor()

# # Parameters
# font = cv2.FONT_HERSHEY_COMPLEX
# height = 1
# boxColor = (0, 0, 255)      # BGR- RED
# nameColor = (255, 255, 255) # BGR- WHITE
# confColor = (255, 255, 0)   # BGR- YELLOW

# face_detector = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
# recognizer = cv2.face.LBPHFaceRecognizer_create()

# # Create an instance of the VideoCapture object for webcam
# cap = cv2.VideoCapture(0)

# def read_rfid():
#     print('Tempelkan RFID anda.')
#     uid, text = reader.read()
#     folder_uid = str(uid)
#     folder_name = text.replace(" ", " ")  # Ganti spasi dengan underscore
#     return folder_uid, folder_name

# def check_rfid_registered(folder_uid):
#     histogram_path = os.path.join(os.getcwd(), f"{folder_uid}.yml")
#     if not os.path.exists(histogram_path):
#         print("RFID belum terdaftar. Harap daftar terlebih dahulu.")
#         return False
#     recognizer.read(histogram_path)
#     return True

# def face_recognition(folder_name, start_time, cap):
#     status_sent = False
#     while time.time() - start_time < 30:
#         ret, frame = cap.read()
#         frameGray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
#         faces = face_detector.detectMultiScale(
#             frameGray,
#             scaleFactor=1.1,
#             minNeighbors=5,
#             minSize=(150, 150)
#         )

#         for (x, y, w, h) in faces:
#             namepos = (x + 5, y - 5)
#             confpos = (x + 5, y + h - 5)
#             cv2.rectangle(frame, (x, y), (x + w, y + h), boxColor, 3)
#             id, confidence = recognizer.predict(frameGray[y:y+h, x:x+w])

#             if confidence >= 55 and not status_sent:
#                 label_name = "Wajah Dikenali"
#                 confidence_text = f"{100 - confidence:.0f}%"
#                 timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
#                 send_to_database(folder_name, timestamp)
#                 status_sent = True
#                 break
#             else:
#                 label_name = "Wajah Tidak Dikenali"
#                 confidence_text = f"{100 - confidence:.0f}%"

#             cv2.putText(frame, str(label_name), namepos, font, height, nameColor, 2)
#             cv2.putText(frame, str(confidence_text), confpos, font, height, confColor, 1)

#         cv2.imshow('Absensi', frame)
#         if status_sent:
#             break
#         if cv2.waitKey(20) & 0xFF == ord('q'):
#             break

#     return status_sent

# def send_to_database(folder_name, timestamp):
#     sql = f"INSERT INTO {folder_name} (nama, status_kehadiran, timestamp) VALUES (%s, %s, %s)"
#     val = (folder_name, "hadir", timestamp)
#     cursor.execute(sql, val)
#     db.commit()
#     print("Status hadir telah dikirim ke database.")

# def main():
#     while True:
#         try:
#             folder_uid, folder_name = read_rfid()
#             if not check_rfid_registered(folder_uid):
#                 continue

#             print(f"Nama: {folder_name}")
#             print("RFID terdaftar. Melanjutkan ke proses pengenalan wajah.")

#             start_time = time.time()
#             status_sent = face_recognition(folder_name, start_time, cap)

#             if not status_sent:
#                 cv2.destroyAllWindows()
#                 print("Gagal mengenali wajah dalam 30 detik. Silakan tempelkan RFID kembali.")
#                 continue  # Restart the process if no face is recognized

#             if status_sent:
#                 cv2.destroyAllWindows()
#                 print("\nAbsensi telah selesai. Silakan tempelkan RFID kembali.")
#                 continue  # Restart the process after successful attendance

#         except Exception as e:
#             print(e)
#             break

#         key = cv2.waitKey(100) & 0xff
#         if key == 27 or key == 113:  # ESCAPE key or q key
#             break

#     cap.release()
#     GPIO.cleanup()
#     cv2.destroyAllWindows()

# if __name__ == "__main__":
#     main()


import cv2
import os
import time
import mysql.connector
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522

# Inisialisasi buzzer
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

buzzer = 17
GPIO.setup(buzzer, GPIO.OUT)

# Inisialisasi pembaca RFID
reader = SimpleMFRC522()

# Koneksi ke database MySQL
db = mysql.connector.connect(
    host="localhost",
    user="tefa",
    password="123",
    database="absensi"
)

# Cursor untuk menjalankan perintah SQL
cursor = db.cursor()

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

def read_rfid():
    print('Tempelkan RFID anda.')
    uid, text = reader.read()
    folder_uid = str(uid)
    folder_name = text.replace(" ", " ")  # Ganti spasi dengan underscore
    return folder_uid, folder_name

def check_rfid_registered(folder_uid):
    histogram_path = os.path.join(os.getcwd(), f"{folder_uid}.yml")
    if not os.path.exists(histogram_path):
        print("RFID belum terdaftar. Harap daftar terlebih dahulu.")
        return False
    recognizer.read(histogram_path)
    return True

def face_recognition(folder_name, start_time, cap):
    status_sent = False
    while time.time() - start_time < 30:
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

            if confidence >= 55 and not status_sent:
                label_name = "Wajah Dikenali"
                confidence_text = f"{100 - confidence:.0f}%"
                timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
                send_to_database(folder_name, timestamp)
                status_sent = True
                break
            else:
                label_name = "Wajah Tidak Dikenali"
                confidence_text = f"{100 - confidence:.0f}%"

            cv2.putText(frame, str(label_name), namepos, font, height, nameColor, 2)
            cv2.putText(frame, str(confidence_text), confpos, font, height, confColor, 1)

        cv2.imshow('Absensi', frame)
        if status_sent:
            break
        if cv2.waitKey(20) & 0xFF == ord('q'):
            break

    return status_sent

def send_to_database(folder_name, timestamp):
    sql = f"INSERT INTO {folder_name} (nama, status_kehadiran, timestamp) VALUES (%s, %s, %s)"
    val = (folder_name, "hadir", timestamp)
    cursor.execute(sql, val)
    db.commit()
    print("Status hadir telah dikirim ke database.")

def main():
    while True:
        try:
            folder_uid, folder_name = read_rfid()
            if not check_rfid_registered(folder_uid):
                continue

            print(f"Nama: {folder_name}")
            print("RFID terdaftar. Melanjutkan ke proses pengenalan wajah.")

            start_time = time.time()
            status_sent = face_recognition(folder_name, start_time, cap)

            if not status_sent:
                cv2.destroyAllWindows()
                print("Gagal mengenali wajah dalam 30 detik. Silakan tempelkan RFID kembali.")
                continue  # Restart the process if no face is recognized

            if status_sent:
                cv2.destroyAllWindows()
                print("\nAbsensi telah selesai. Silakan tempelkan RFID kembali.")
                continue  # Restart the process after successful attendance

        except Exception as e:
            print(e)
            break

        key = cv2.waitKey(100) & 0xff
        if key == 27 or key == 113:  # ESCAPE key or q key
            break

    cap.release()
    GPIO.cleanup()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()

