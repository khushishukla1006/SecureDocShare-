import socket
import threading

def handle_client(conn, addr):
    print(f"Connection from {addr}")
    conn.sendall(b"Server is running!")
    conn.close()

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('192.168.212.9', 5004))
    server.listen(5)
    print("TCP test server running on port 5004...")
    
    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()

if __name__ == '__main__':
    start_server()
