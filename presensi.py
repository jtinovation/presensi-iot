import cv2
import os
import time
import mysql.connector
from mfrc522 import SimpleMFRC522
import RPi.GPIO as GPIO
import buzzer 

reader = SimpleMFRC522()

led_green_pin = 11
led_red_pin = 15
buzzer_pin = 13 

GPIO.setmode(GPIO.BCM)
GPIO.setup(led_green_pin, GPIO.OUT)
GPIO.setup(led_red_pin, GPIO.OUT)
GPIO.setup(buzzer_pin, GPIO.OUT) 

# Koneksi ke database MySQL
db = mysql.connector.connect(
    host="localhost",
    user="user",
    password="123",
    database="absensi"
)

# Cursor untuk menjalankan perintah SQL
cursor = db.cursor()

def rfid_check(text2):
    folder_name = text2.replace(" ", "_")  # Mengganti spasi dengan underscore untuk nama folder
    folder_path = os.path.join(os.getcwd(), "Datasets_User", folder_name)  # Mendapatkan path folder
    return os.path.exists(folder_path), folder_name  # Mengembalikan status keberadaan folder dan nama folder

def main():
    # Parameters
    font = cv2.FONT_HERSHEY_COMPLEX
    height = 1
    boxColor = (0, 0, 255)      # BGR- GREEN
    nameColor = (255, 255, 255) # BGR- WHITE
    confColor = (255, 255, 0)   # BGR- TEAL

    face_detector = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')

    # Membaca model yang dilatih dari folder trainedp
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read(os.path.join('Datasets_User', folder_name, 'trained', 'trained.yml'))

    # Create an instance of the VideoCapture object for webcam
    cap = cv2.VideoCapture(0)

    while True:
        # Read RFID
        try:
            id, text1, text2 = reader.read()
            print(id, "|", text1, "|", text2)

            # Check if RFID is registered
            rfid_status, folder_name = rfid_check(text2)
            if not rfid_status:
                print("RFID belum terdaftar. Harap daftar terlebih dahulu")
                GPIO.output(led_red_pin, GPIO.HIGH)
                GPIO.output(buzzer_pin, GPIO.HIGH) 
                time.sleep(2)
                GPIO.output(led_red_pin, GPIO.LOW)
                GPIO.output(buzzer_pin, GPIO.LOW) 
                continue
            else:
                GPIO.output(led_green_pin, GPIO.HIGH)
                GPIO.output(buzzer_pin, GPIO.HIGH) 
                time.sleep(1)
                GPIO.output(led_green_pin, GPIO.LOW)
                GPIO.output(buzzer_pin, GPIO.LOW) 

            # Mengambil waktu saat ini
            current_time = time.localtime()
            current_hour = current_time.tm_hour
            current_minute = current_time.tm_min

            # Membatasi rentang waktu antara jam 9 pagi hingga jam 9:15 pagi
            if 9 <= current_hour < 9.15:
                print("Maaf, absen hanya bisa dilakukan di luar jam 9 pagi hingga 9:15 pagi.")
                continue

            # If RFID is valid, proceed to face recognition process
            start_time = time.time()
            while time.time() - start_time < 30:  # Maximum face recognition process for 30 seconds
                # Capture a frame from the camera
                ret, frame = cap.read()

                # Convert frame from BGR to grayscale
                frameGray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                # Create a DS faces- array with 4 elements- x,y coordinates top-left corner), width and height
                faces = face_detector.detectMultiScale(
                    frameGray,      # The grayscale frame to detect
                    scaleFactor=1.1,# how much the image size is reduced at each image scale-10% reduction
                    minNeighbors=5, # how many neighbors each candidate rectangle should have to retain it
                    minSize=(150, 150)# Minimum possible object size. Objects smaller than this size are ignored.
                )

                for (x, y, w, h) in faces:
                    namepos = (x + 5, y - 5) # shift right and up/outside the bounding box from top
                    confpos = (x + 5, y + h - 5) # shift right and up/intside the bounding box from bottom

                    # Create a bounding box across the detected face
                    cv2.rectangle(frame, (x, y), (x + w, y + h), boxColor, 3)

                    # Recognize face using the trained model
                    id, confidence = recognizer.predict(frameGray[y:y+h, x:x+w])

                    # If confidence is less than 100, it is considered a perfect match
                    if confidence < 100:
                        id = "Wajah Dikenali."
                        confidence = f"{100 - confidence:.0f}%"
                        GPIO.output(led_green_pin, GPIO.HIGH)
                        GPIO.output(buzzer_pin, GPIO.HIGH)
                        time.sleep(2)
                        GPIO.output(led_green_pin, GPIO.LOW)                   
                        GPIO.output(buzzer_pin, GPIO.LOW)
                    else:
                        id = "Wajah Tidak Dikenali."
                        confidence = f"{100 - confidence:.0f}%"
                        GPIO.output(led_red_pin, GPIO.HIGH)
                        GPIO.output(buzzer_pin, GPIO.HIGH)
                        time.sleep(1)
                        GPIO.output(led_red_pin, GPIO.LOW)
                        GPIO.output(buzzer_pin, GPIO.LOW)

                    # Display name and confidence of person who's face is recognized
                    cv2.putText(frame, str(id), namepos, font, height, nameColor, 2)
                    cv2.putText(frame, str(confidence), confpos, font, height, confColor, 1)

                    if confidence >= 100:
                        # Send "hadir" status to MySQL database along with current timestamp
                        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
                        sql = f"INSERT INTO {folder_name} (nama, status_kehadiran, timestamp) VALUES (%s, %s, %s)"
                        val = (folder_name, "hadir", timestamp)
                        cursor.execute(sql, val)
                        db.commit()

                        print("Status hadir telah dikirim ke database.")

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
