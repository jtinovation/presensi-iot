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
    user="tefa",
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
            folder_uid = str(uid)
            folder_name = text.replace(" ", " ")
            print(f"Nama: {folder_name}")
            print("RFID terdaftar. Melanjutkan ke proses pengenalan wajah.")

            # Load the trained model
            recognizer.read(f"{folder_uid}.yml")

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

                    if confidence >= 55:
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
