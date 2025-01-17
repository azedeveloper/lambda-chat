import socket
import threading
import random
import curses
import json

def receive_messages(client_socket, stdscr, messages):
    while True:
        try:
            message = client_socket.recv(1024).decode('utf-8')
            username = client_socket.recv(1024).decode('utf-8')
            if message:
                messages.append((username, message))
                refresh_chat(stdscr, messages)
            else:
                break
        except Exception as e:
            messages.append(("Error", "An error occurred!"))
            refresh_chat(stdscr, messages)
            client_socket.close()
            break

def refresh_chat(stdscr, messages):
    stdscr.clear()
    height, width = stdscr.getmaxyx()

    for i, (username, message) in enumerate(messages[-(height - 2):]):
        if username == "Error":
            stdscr.addstr(i, 0, message[:width - 1], curses.color_pair(3))
        else:
            try:
                stdscr.addstr(i, 0, f"{username}: ", curses.color_pair(2))
                stdscr.addstr(f"{message}", curses.color_pair(1))
            except curses.error:
                pass

    stdscr.addstr(height - 1, 0, "".ljust(width - 1), curses.color_pair(4))
    stdscr.addstr(height - 1, 0, "> ")
    stdscr.refresh()

def main(stdscr):
    curses.start_color()
    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_CYAN, curses.COLOR_BLACK)    
    curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)     
    curses.init_pair(4, curses.COLOR_BLACK, curses.COLOR_BLACK)  

    with open('client.json', 'r') as file:
        jsonData = json.load(file)

    host = jsonData['ip'] or "127.0.0.1"
    port = jsonData['port'] or 5000 
    username = jsonData['username'] or f"client{random.randint(1, 1000)}"  

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))

    messages = [("System", f"Connected to {host}:{port}"), ("System", f"You are: {username}")]

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
            client_socket.send(input_buffer.encode('utf-8'))
            client_socket.send(username.encode('utf-8'))
            input_buffer = ""
        elif key in (8, 127, curses.KEY_BACKSPACE):  
            input_buffer = input_buffer[:-1]
        elif 32 <= key <= 126:  
            if len(input_buffer) < width - 3: 
                input_buffer += chr(key)

if __name__ == "__main__":
    curses.wrapper(main)
