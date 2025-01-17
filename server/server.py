import socket
import threading

HOST = '127.0.0.1'
PORT = 5000
MAX_CLIENTS = 10

clients = []

class ANSI:
    RESET = "\033[0m"
    BOLD = "\033[1m"

    # Text colors
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

def handle_client(client_socket):
    while True:
        try:
            message = client_socket.recv(1024).decode('utf-8')
            username = client_socket.recv(1024).decode('utf-8')

            if message:
                broadcast(message, username, client_socket)
            else:
                remove(client_socket)
                break
        except:
            continue

def broadcast(message, username, client_socket):
    for client in clients:
        try:
            client.send(message.encode('utf-8'))
            client.send(username.encode('utf-8'))
        except:
                remove(client)

def remove(client_socket):
    if client_socket in clients:
        clients.remove(client_socket)

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(MAX_CLIENTS)
    print(f"{ANSI.GREEN}Server started on {ANSI.BOLD}{HOST}:{PORT}{ANSI.RESET}")

    while True:
        client_socket, client_address = server.accept()
        if len(clients) < MAX_CLIENTS:
            clients.append(client_socket)
            print(f"Client {client_address} connected")
            threading.Thread(target=handle_client, args=(client_socket,)).start()
        else:
            client_socket.send("Server is full. Try again later.".encode('utf-8'))
            client_socket.close()

if __name__ == "__main__":
    start_server()