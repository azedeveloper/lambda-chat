#TODO: SAVE PUBLIC KEYS OF ALL CLIENTS SERVER-SIDE AND WHEN A CLIENT JOINS SEND THEM THE PUBLIC KEYS OF THE OTHER CONNECTED CLIENTS SO THEY CAN ADD THEM LOCALLY
#TODO: ALSO A WAY FOR CLIENTS TO SEE WHAT USERS ARE ONLINE (WITH THEIR USERNAME) EG /ONLINE

import socket
import threading
import json
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization, hashes

clients = []
client_info = {}  # Store client information including username and public key

# ANSI color codes
RESET = "\033[0m"
RED = "\033[31m"
GREEN = "\033[32m"
BLUE = "\033[34m"
YELLOW = "\033[33m"
CYAN = "\x1b[96m"
BOLD = "\u001b[1m"

# Remove a client socket from the list of clients
def remove(client_socket, client_address, username):
    if client_socket in clients:           
        print(f"{RED}Client {BOLD}{username}{RESET}{RED} at {BOLD}{client_address}{RESET}{RED} disconnected and removed{RESET}")
        clients.remove(client_socket)
        del client_info[client_socket]
        broadcast_online_users()

# Handle individual client connections
def handle_client(client_socket, auth_key, print_messages, client_address, username):
    try:
        while True:
            message = client_socket.recv(2048).decode('utf-8')
            if message:
                parsed_message = json.loads(message)
                username = parsed_message.get("username", "Unknown")
                content = parsed_message.get("message", "")
                recipient = parsed_message.get("recipient", None)

                if content.lower() == "/online":
                    send_online_users(client_socket)
                else:
                    if recipient:
                        recipient_socket = next((sock for sock, info in client_info.items() if info["username"] == recipient), None)
                        if recipient_socket:
                            decrypted_message = decrypt_message(content, client_info[recipient_socket]["private_key"])
                            if print_messages: print(f"{CYAN}{username} to {recipient}: {RESET}{decrypted_message}")
                            broadcast(decrypted_message, username, client_socket, client_address, recipient_socket)
                    else:
                        if print_messages: print(f"{CYAN}{username}: {RESET}{content}")
                        broadcast(content, username, client_socket, client_address)
            else:
                break
    except Exception as e:
        if e.errno == 10054:
            return
        print(f"{RED}Error: {e}{RESET}")
    finally:
        remove(client_socket, client_address, username)
        client_socket.close()

def decrypt_message(encrypted_message, private_key_pem):
    private_key = serialization.load_pem_private_key(private_key_pem.encode('utf-8'), password=None)
    return private_key.decrypt(
        bytes.fromhex(encrypted_message),
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    ).decode('utf-8')

# Broadcast a message to all clients
def broadcast(message, username, sender_socket, client_address, recipient_socket=None):
    payload = json.dumps({"username": username, "message": message})
    if recipient_socket:
        try:
            recipient_socket.send(payload.encode('utf-8'))
        except:
            remove(recipient_socket, client_address, username)
    else:
        for client in clients:
            try:
                client.send(payload.encode('utf-8'))
            except:
                remove(client, client_address, username)

# Authenticate the client on connection
def authenticate_client(client_socket):
    try:
        auth_response = client_socket.recv(1024 + 2048).decode('utf-8')
        auth_data = json.loads(auth_response)
        provided_key = auth_data.get("auth_key")
        distribute_public_key(auth_data.get("username"), auth_data.get("public_key"), auth_data.get("private_key"), client_socket)

        if provided_key == AUTH_KEY:
            return True, auth_data.get("username", "Unknown")
        else:
            error_message = json.dumps({"username": "System", "message": "Authentication failed. Disconnecting..."}).encode('utf-8')
            client_socket.send(error_message)
            return False, None
    except Exception as e:
        print(f"{RED}Authentication error: {e}{RESET}")
        return False, None
    
def distribute_public_key(username, public_key, private_key, client_socket):
    client_info[client_socket] = {"username": username, "public_key": public_key, "private_key": private_key}
    broadcast_public_keys()

def broadcast_public_keys():
    payload = json.dumps({"type": "public_keys", "data": {info["username"]: info["public_key"] for info in client_info.values()}})
    for client in clients:
        try:
            client.send(payload.encode('utf-8'))
        except:
            remove(client, client_info[client]["address"], client_info[client]["username"])

def send_online_users(client_socket):
    online_users = [info["username"] for info in client_info.values()]
    payload = json.dumps({"type": "online_users", "data": online_users})
    client_socket.send(payload.encode('utf-8'))

def broadcast_online_users():
    online_users = [info["username"] for info in client_info.values()]
    payload = json.dumps({"type": "online_users", "data": online_users})
    for client in clients:
        try:
            client.send(payload.encode('utf-8'))
        except:
            remove(client, client_info[client]["address"], client_info[client]["username"])

# Start the server and listen for incoming connections
def start_server():
    with open('server.json', 'r') as file:
        jsonData = json.load(file)

    global AUTH_KEY
    HOST = jsonData["ip"]
    PORT = jsonData["port"]
    MAX_CLIENTS = jsonData["max_clients"]
    PRINT_MESSAGES = jsonData["print_messages"]
    AUTH_KEY = jsonData["authentication"]

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(MAX_CLIENTS)
    print(f"{GREEN}Server started on {BOLD}{HOST}:{PORT}{RESET}")

    while True:
        client_socket, client_address = server.accept()

        if len(clients) < MAX_CLIENTS:
            authenticated, username = authenticate_client(client_socket)
            if authenticated:
                clients.append(client_socket)
                print(f"{BLUE}Client {BOLD}{username}{RESET}{BLUE} at {BOLD}{client_address}{RESET}{BLUE} connected and authenticated!{RESET}")
                threading.Thread(target=handle_client, args=(client_socket, AUTH_KEY, PRINT_MESSAGES, client_address, username)).start()
            else:
                print(f"{RED}Authentication failed for client {BOLD}{username}{RESET}{RED} at {BOLD}{client_address}{RESET}")
                client_socket.close()
        else:
            client_socket.send(json.dumps({"username": "System", "message": "Server is full. Try again later."}).encode('utf-8'))
            client_socket.close()

if __name__ == "__main__":
    start_server()
