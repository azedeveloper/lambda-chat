import socket
import threading
import json

HOST = '127.0.0.1'
PORT = 5000
MAX_CLIENTS = 10

clients = []

def handle_client(client_socket):
    while True:
        try:
            message = client_socket.recv(1024).decode('utf-8')
            if message:
                parsed_message = json.loads(message)
                username = parsed_message.get("username", "Unknown")
                content = parsed_message.get("message", "")
                broadcast(content, username, client_socket)
            else:
                remove(client_socket)
                break
        except:
            remove(client_socket)
            break

def broadcast(message, username, sender_socket):
    payload = json.dumps({"username": username, "message": message})
    for client in clients:
        try:
            client.send(payload.encode('utf-8'))
        except:
            remove(client)

def remove(client_socket):
    if client_socket in clients:
        clients.remove(client_socket)

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(MAX_CLIENTS)
    print(f"Server started on {HOST}:{PORT}")

    while True:
        client_socket, client_address = server.accept()
        if len(clients) < MAX_CLIENTS:
            clients.append(client_socket)
            print(f"Client {client_address} connected")
            threading.Thread(target=handle_client, args=(client_socket,)).start()
        else:
            client_socket.send(json.dumps({"username": "System", "message": "Server is full. Try again later."}).encode('utf-8'))
            client_socket.close()

if __name__ == "__main__":
    start_server()
