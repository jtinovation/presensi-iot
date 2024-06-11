# import requests
# import time

# def send_to_api():
#     url = "http://10.10.0.157:8081/api/presensi"
#     timestamp = int(time.time())  # Mengambil timestamp saat ini
#     payload = {
#         "rfid": "0fosdjf9",
#         "nim": "E928349823",
#         "status": "hadir",
#         "timestamp": timestamp
#     }
#     headers = {'Content-Type': 'application/json'}

#     try:
#         response = requests.post(url, json=payload, headers=headers)
#         response.raise_for_status()

#         print("Data berhasil dikirim ke API.")

#     except requests.exceptions.RequestException as e:
#         print(f"Gagal ngirim: {e}")

# def main():
#     try:
#         while True:
#             send_to_api()
#             time.sleep(5)  # Delay 5 detik sebelum mengirim data lagi
#     except KeyboardInterrupt:
#         print("Pengiriman data dihentikan oleh pengguna.")

# if __name__ == "__main__":
#     main()









# import requests
# import time

# def send_to_api():
#     url = "http://10.10.0.157:8081/api/presensi"
#     timestamp = int(time.time())  # Mengambil timestamp saat ini
#     payload = {
#         "rfid": "0fosdjf9",
#         "nim": "E928349823",
#         "status": "hadir",
#         "timestamp": timestamp
#     }
#     headers = {'Content-Type': 'application/json'}

#     try:
#         response = requests.post(url, json=payload, headers=headers)
#         response.raise_for_status()
#         print("Data berhasil dikirim ke API.")
#     except requests.exceptions.RequestException as e:
#         print(f"Gagal mengirim data ke API: {e}")

# def main():
#     try:
#         while True:
#             send_to_api()
#             time.sleep(5)  # Delay 5 detik sebelum mengirim data lagi
#     except KeyboardInterrupt:
#         print("Pengiriman data dihentikan oleh pengguna.")

# if __name__ == "__main__":
#     main()




# import requests
# import time

# timestamp = int(time.time())  
# payload = {"rfid": "0fosdjf9", "nim":"E928349823", "status": "hadir", "timestamp":timestamp}
# r = requests.post("http://10.10.0.157:8081/api/presensi", data=payload)
# print(r.text)




import requests
import time

# URL dari API yang akan diposting
url = 'http://10.10.0.157:8081/api/presensi'

# Data yang akan diposting (dalam format JSON)
timestamp = int(time.time())  # Mengambil timestamp saat ini
data = {
        "rfid": "0fosdjf9",
        "nim": "E928349823",
        "status": "hadir",
        "timestamp": timestamp
    }

response = requests.post(url, json=data)

# Mendapatkan respons dari API
if response.status_code == 200:
    print("Data berhasil diposting!")
    print("Response:", response.json())
else:
    print("Gagal melakukan posting data. Status code:", response.status_code)
