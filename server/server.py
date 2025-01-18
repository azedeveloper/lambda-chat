import socket
import threading
import json

HOST = '127.0.0.1'
PORT = 5000
MAX_CLIENTS = 10

clients = []

# ANSI color codes
RESET = "\033[0m"
RED = "\033[31m"
GREEN = "\033[32m"
BLUE = "\033[34m"
YELLOW = "\033[33m"

# Broadcast a message to all clients
def broadcast(message, username, sender_socket):
    payload = json.dumps({"username": username, "message": message})
    for client in clients:
        try:
            client.send(payload.encode('utf-8'))
        except:
            remove(client)

# Remove a client socket from the list of clients
def remove(client_socket):
    if client_socket in clients:
        clients.remove(client_socket)
        print(f"{RED}Client disconnected and removed{RESET}")

# Handle individual client connections
def handle_client(client_socket):
    try:
        while True:
            message = client_socket.recv(1024).decode('utf-8')
            if message:
                parsed_message = json.loads(message)
                username = parsed_message.get("username", "Unknown")
                content = parsed_message.get("message", "")
                print(f"{BLUE}{username}: {content}{RESET}")
                broadcast(content, username, client_socket)
            else:
                break
    except Exception as e:
        print(f"{RED}Error: {e}{RESET}")
    finally:
        remove(client_socket)
        client_socket.close()

# Start the server and listen for incoming connections
def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(MAX_CLIENTS)
    print(f"{GREEN}Server started on {HOST}:{PORT}{RESET}")

    while True:
        client_socket, client_address = server.accept()
        if len(clients) < MAX_CLIENTS:
            clients.append(client_socket)
            print(f"{BLUE}Client {client_address} connected{RESET}")
            threading.Thread(target=handle_client, args=(client_socket,)).start()
        else:
            client_socket.send(json.dumps({"username": "System", "message": "Server is full. Try again later."}).encode('utf-8'))
            client_socket.close()

if __name__ == "__main__":
    start_server()