import socket
import threading
import random
import curses
import json

# Receive and parse incoming messages from the server
def receive_messages(client_socket, stdscr, messages):
    while True:
        try:
            message = client_socket.recv(1024).decode('utf-8')
            if message:
                parsed_message = json.loads(message)
                username = parsed_message.get("username", "Unknown")
                content = parsed_message.get("message", "")
                messages.append((username, content))
                refresh_chat(stdscr, messages)
            else:
                break
        except Exception as e:
            messages.append(("Error", "An error occurred!"))
            refresh_chat(stdscr, messages)
            client_socket.close()
            break

# Refresh the chat with new messages
def refresh_chat(stdscr, messages):
    stdscr.clear()
    height, width = stdscr.getmaxyx()
    chat_lines = []

    for username, message in messages:
        lines = message.split('\n')
        for line in lines:
            wrapped_lines = [line[i:i + width - 1] for i in range(0, len(line), width - 1)]
            for wrapped_line in wrapped_lines:
                chat_lines.append((username, wrapped_line))

    for i, (username, line) in enumerate(chat_lines[-(height - 2):]):
        if username == "Error":
            stdscr.addstr(i, 0, line, curses.color_pair(3))
        elif username == "System": 
            stdscr.addstr(i, 0, f"{username}: ", curses.color_pair(5))
            stdscr.addstr(line, curses.color_pair(1))
        else:
            stdscr.addstr(i, 0, f"{username}: ", curses.color_pair(2))
            stdscr.addstr(line, curses.color_pair(1))

    stdscr.addstr(height - 1, 0, "".ljust(width - 1), curses.color_pair(4))
    stdscr.addstr(height - 1, 0, "> ")
    stdscr.refresh()

# Rendering with curses and connecting to the server
def main(stdscr):
    curses.start_color()
    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_CYAN, curses.COLOR_BLACK)    
    curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)     
    curses.init_pair(4, curses.COLOR_BLACK, curses.COLOR_BLACK)  
    curses.init_pair(5, curses.COLOR_MAGENTA, curses.COLOR_BLACK)  

    with open('client.json', 'r') as file:
        jsonData = json.load(file)

    host = jsonData['ip'] or "127.0.0.1"
    port = jsonData['port'] or 5000 
    username = jsonData['username'] or f"client{random.randint(1, 1000)}"
    auth_key = jsonData['authentication']

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))

    # Send authentication
    auth_payload = json.dumps({"auth_key": auth_key, "username": username})
    client_socket.send(auth_payload.encode('utf-8'))


    ascii_art = (
        "\u200B"
        """
    __   ___   __  ______  ___  ___     _______ _____ ______
   / /  / _ | /  |/  / _ )/ _ \/ _ |   / ___/ // / _ /_  __/
  / /__/ __ |/ /|_/ / _  / // / __ |  / /__/ _  / __ |/ /   
 /____/_/ |_/_/  /_/____/____/_/ |_|  \___/_//_/_/ |_/_/    
        """
        "\u200B"
    )

    messages = [
        ("System", ascii_art.strip()),
        ("System", f"Connected to {host}:{port}"),
        ("System", f"You are: {username}")
    ]

    threading.Thread(target=receive_messages, args=(client_socket, stdscr, messages), daemon=True).start()

    height, width = stdscr.getmaxyx()
    input_buffer = ""

    while True:
        refresh_chat(stdscr, messages)
        stdscr.addstr(height - 1, 2, input_buffer[:width - 3])
        key = stdscr.getch()

        if key == curses.KEY_RESIZE:
            height, width = stdscr.getmaxyx()
        elif key in (10, 13):  
            if input_buffer.strip().lower() == "exit":
                client_socket.close()
                break
            payload = json.dumps({
                "auth_key": auth_key,
                "username": username,
                "message": input_buffer
            })
            client_socket.send(payload.encode('utf-8'))
            input_buffer = ""
        elif key in (8, 127, curses.KEY_BACKSPACE):  
            input_buffer = input_buffer[:-1]
        elif 32 <= key <= 126:  
            if len(input_buffer) < width - 3: 
                input_buffer += chr(key)

if __name__ == "__main__":
    curses.wrapper(main)
