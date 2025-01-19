import socket
import threading
import json

clients = []

# ANSI color codes
RESET = "\033[0m"
RED = "\033[31m"
GREEN = "\033[32m"
BLUE = "\033[34m"
YELLOW = "\033[33m"

# Remove a client socket from the list of clients
def remove(client_socket):
    if client_socket in clients:
        clients.remove(client_socket)
        print(f"{RED}Client disconnected and removed{RESET}")

# Handle individual client connections
def handle_client(client_socket, auth_key):
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

# Broadcast a message to all clients
def broadcast(message, username, sender_socket):
    payload = json.dumps({"username": username, "message": message})
    for client in clients:
        try:
            client.send(payload.encode('utf-8'))
        except:
            remove(client)

# Authenticate the client on connection
def authenticate_client(client_socket):
    try:
        auth_response = client_socket.recv(1024 + 2048).decode('utf-8')
        auth_data = json.loads(auth_response)
        provided_key = auth_data.get("auth_key")
        distribute_public_key(auth_data.get("username"),auth_data.get("public_key"), client_socket)

        if provided_key == AUTH_KEY:
            return True, auth_data.get("username", "Unknown")
        else:
            error_message = json.dumps({"username": "System", "message": "Authentication failed. Disconnecting..."}).encode('utf-8')
            client_socket.send(error_message)
            return False, None
    except Exception as e:
        print(f"{RED}Authentication error: {e}{RESET}")
        return False, None
    
def distribute_public_key(username, public_key, client_socket):
    try:
        send_key = json.dumps({"username": username, "public_key": public_key})
        client_socket.send(send_key.encode('utf-8'))
    except Exception as e:
        print(f"{RED}Key error: {e}{RESET}")
        return False, None

# Start the server and listen for incoming connections
def start_server():
    with open('server.json', 'r') as file:
        jsonData = json.load(file)

    global AUTH_KEY
    HOST = jsonData["ip"]
    PORT = jsonData["port"]
    MAX_CLIENTS = jsonData["max_clients"]
    AUTH_KEY = jsonData["authentication"]

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(MAX_CLIENTS)
    print(f"{GREEN}Server started on {HOST}:{PORT}{RESET}")

    while True:
        client_socket, client_address = server.accept()
        print(f"{BLUE}Client {client_address} connected{RESET}")

        if len(clients) < MAX_CLIENTS:
            authenticated, username = authenticate_client(client_socket)
            if authenticated:
                clients.append(client_socket)
                print(f"{GREEN}Authentication successful for {username}{RESET}")
                threading.Thread(target=handle_client, args=(client_socket, AUTH_KEY)).start()
            else:
                print(f"{RED}Authentication failed for client at {client_address}{RESET}")
                client_socket.close()
        else:
            client_socket.send(json.dumps({"username": "System", "message": "Server is full. Try again later."}).encode('utf-8'))
            client_socket.close()

if __name__ == "__main__":
    start_server()
