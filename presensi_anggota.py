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
import Adafruit_SSD1306

# Nonaktifkan peringatan GPIO
GPIO.setwarnings(False)

# Inisialisasi pembaca RFID
reader = SimpleMFRC522()

# GPIO pin configuration for the OLED display
OLED_RESET_PIN = None  # Set to GPIO pin if your display has a reset pin

OLED = Adafruit_SSD1306.SSD1306_128_64(rst=OLED_RESET_PIN) #OLED specification configuration. 

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


def read_rfid():
    
    print('Tempelkan RFID anda!')

    OLED.clear()
    OLED.draw.text((0, 0), "Tempelkan RFID anda!", font=None, fill=255)
    OLED.display()

    uid, text = reader.read()

    buzz(1)

    folder_uid = str(uid)
    folder_name = text.replace(" ", " ")  # Ganti spasi dengan underscore
    
    return folder_uid, folder_name

def check_rfid_registered(folder_uid):

    histogram_path = os.path.join(os.getcwd(), f"{folder_uid}.yml")
    
    if not os.path.exists(histogram_path):

        print("RFID belum terdaftar. Harap daftar terlebih dahulu.")

        OLED.clear()
        OLED.draw.text((0, 0), "RFID belum terdaftar. Harap daftar terlebih dahulu.", font=None, fill=255)
        OLED.display()

        buzz(1)
        
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
                
                buzz(1)

                OLED.clear()
                OLED.draw.text((0, 0), "Wjah tidak dikenali.", font=None, fill=255)
                OLED.display()

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

    OLED.clear()
    OLED.draw.text((0, 0), "Status hadir telah dikirim ke database.", font=None, fill=255)
    OLED.display()


def main():

    while True:
        
        try:

            folder_uid, folder_name = read_rfid()
            
            if not check_rfid_registered(folder_uid):

                continue

            print(f"Nama: {folder_name}")
            print("RFID terdaftar. Melanjutkan ke proses pengenalan wajah.")
    
            OLED.clear()
            OLED.draw.text((0, 0), "RFID terdaftar. Melanjutkan ke proses pengenalan wajah.", font=None, fill=255)
            OLED.display()

            buzz(0.2)

            start_time = time.time()
            status_sent = face_recognition(folder_name, start_time, cap)

            if not status_sent:

                cv2.destroyAllWindows()

                print("Gagal mengenali wajah dalam 30 detik. Silakan tempelkan RFID kembali.")

                OLED.clear()
                OLED.draw.text((0, 0), "Wajah tidak dikenali.", font=None, fill=255)
                OLED.display()
                
                buzz(1)
                
                continue  # Restart the process if no face is recognized

            if status_sent:

                cv2.destroyAllWindows()
                
                buzz(1)
                
                print("\nPresensi telah selesai. Silakan tempelkan RFID kembali.")

                OLED.clear()
                OLED.draw.text((0, 0), "Proses presensi berhasil.", font=None, fill=255)
                OLED.display()
                
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

