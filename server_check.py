import socket

def check_server(address, port):
    s = socket.socket()
    print(f"Attempting to connect to {address} on port {port}")
    try:
        s.connect((address, port))
        print("Connection successful")
    except Exception as e:
        print(f"Connection failed: {e}")
    finally:
        s.close()

check_server("10.10.0.157", 8081)
