import cv2
import os
import time
import mysql.connector
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
import requests
import subprocess
from board import SCL, SDA
import busio
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306
import socket
from datetime import datetime

# Nonaktifkan peringatan GPIO
GPIO.setwarnings(False)

# Inisialisasi pembaca RFID
reader = SimpleMFRC522()

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

def check_server(address, port):
    s = socket.socket()
    print(f"Mencoba menghubungkan ke {address} di port {port}")
    try:
    
        s.connect((address, port))
    
        print("Koneksi server sukses.")
    
    except Exception as e:
    
        print(f"Koneksi server gagal: {e}")
    
        # Mengembalikan timestamp saat ini dalam format yang sama dengan format timestamp MySQL
        # timestamp_threshold = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # return timestamp_threshold
    
    finally:

        s.close()

def display_text_on_oled(text, font_size):

    # Create the I2C interface.
    i2c = busio.I2C(SCL, SDA)

    # Create the SSD1306 OLED class.
    disp = adafruit_ssd1306.SSD1306_I2C(128, 32, i2c)

    # Clear display.
    disp.fill(0)
    disp.show()

    # Create blank image for drawing.
    width = disp.width
    height = disp.height
    image = Image.new("1", (width, height))

    # Get drawing object to draw on image.
    draw = ImageDraw.Draw(image)
    # Load a TTF font.
    font_path = '/home/jtinova/Downloads/DejaVu_Sans/DejaVuSans-Bold.ttf'  # Adjust path to your TTF font file
    font = ImageFont.truetype(font_path, font_size)

    # Draw a black filled box to clear the image.
    draw.rectangle((0, 0, width, height), outline=0, fill=0)

    # Calculate bounding box of the text
    text_bbox = draw.textbbox((0, 0), text, font=font)

    # Calculate width and position to center the text
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    x = (width - text_width) // 2
    y = (height - text_height) // 2

    # Draw the text
    draw.text((x, y), text, font=font, fill=255)
    # image = image.rotate(180)

    # Display image.
    disp.image(image)
    disp.show()

def clear_oled_display():
    # Create the I2C interface.
    i2c = busio.I2C(SCL, SDA)
    # Create the SSD1306 OLED class.
    disp = adafruit_ssd1306.SSD1306_I2C(128, 32, i2c)
    # Clear display.
    disp.fill(0)
    disp.show()

def read_rfid():

    print('Tempelkan RFID anda!')

    display_text_on_oled("Scan RFID anda!.", 16)
    time.sleep(1)
    clear_oled_display()   
     
    uid, text = reader.read()

    buzz(1)

    folder_uid = str(uid)
    folder_name = text.replace(" ", " ") 

    return folder_uid, folder_name

def check_rfid_registered(folder_uid):
    
    histogram_path = os.path.join(os.getcwd(), f"{folder_uid}.yml")
    if not os.path.exists(histogram_path):
    
        print("RFID belum terdaftar. Harap daftar terlebih dahulu.")

        display_text_on_oled("RFID tidak terdaftar.", 16)
        time.sleep(1)
        clear_oled_display()    

        buzz(1)
    
        return False
    
    recognizer.read(histogram_path)

    return True

def face_recognition(folder_name, folder_uid, start_time, cap):

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
                
                display_text_on_oled("Wajah dikenali.", 16)
                time.sleep(1)
                clear_oled_display()    
                
                send_to_database(folder_name, folder_uid, timestamp)
                
                send_to_api()

                status_sent = True

                break
            
            else:

                label_name = "Wajah Tidak Dikenali."
                confidence_text = f"{100 - confidence:.0f}%"
                display_text_on_oled("Wajah tidak dikenali.", 16)
                time.sleep(1)
                clear_oled_display()    
                buzz(1)

            cv2.putText(frame, str(label_name), namepos, font, height, nameColor, 2)
            cv2.putText(frame, str(confidence_text), confpos, font, height, confColor, 1)

        cv2.imshow('Absensi', frame)
        
        if status_sent:
            break

        if cv2.waitKey(20) & 0xFF == ord('q'):
            break

    return status_sent

def send_to_database(folder_uid, folder_name, timestamp):

    sql = f"INSERT INTO {folder_name} (RFID, NIM, Status_kehadiran, Timestamp) VALUES (%s, %s, %s, %s)"
    val = (folder_uid, folder_name, "hadir", timestamp)
    cursor.execute(sql, val)

    db.commit()

    send_to_api(folder_name, folder_uid, timestamp) 
    
    print("Status hadir telah dikirim ke database.")

    display_text_on_oled("Status hadir terkirim ke database.", 16)
    time.sleep(1)
    clear_oled_display() 

def fetch_backup_data_from_database(timestamp_now):
    # Mendapatkan daftar tabel di database absensi
    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()

    for table in tables:
        table_name = table[0]
        # Query untuk mengambil semua record dari tabel
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        for row in rows:
            id, RFID, NIM, Status_kehadiran,Timestamp = row
            # Bandingkan timestamp dengan timestamp_threshold
            if Timestamp > timestamp_now:
                # Kirim data ke API
                data = {

                    "rfid": RFID,
                    "nim": NIM,
                    "status": Status_kehadiran,
                    "timestamp": Timestamp,
                    
                }

                send_to_api(data)

def send_backup_to_api(data):
    # URL dari API yang akan diposting
    url = 'http://10.10.0.157:8081/api/presensi'

    # Mengirim data dalam format JSON
    response = requests.post(url, json=data)

    # Mendapatkan respons dari API
    if response.status_code == 200:

        print("Data backup berhasil diposting ke API!")

    else:

        print("Gagal mengirim data backup", response.status_code)

def send_to_api(folder_name, folder_uid, timestamp):

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


            buzz(0.2)

            start_time = time.time()
            status_sent = face_recognition(folder_name, start_time, cap)

            if not status_sent:

                cv2.destroyAllWindows()

                print("Gagal mengenali wajah dalam 30 detik. Silakan tempelkan RFID kembali.")

                
                buzz(1)
                
                continue  # Restart the process if no face is recognized

            if status_sent:

                cv2.destroyAllWindows()
                
                buzz(1)
                
                print("\nPresensi telah selesai. Silakan tempelkan RFID kembali.")


                
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