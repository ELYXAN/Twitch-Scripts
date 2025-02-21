import socket
import re
import time
import requests
import os
import webbrowser
from datetime import datetime

# OAuth-Token automatisch generieren mit chat:read, chat:edit und moderator:read:chatters
CLIENT_ID = ""
CLIENT_SECRET = ""
REDIRECT_URI = "http://localhost"
USERNAME_FILE = "username.txt"
STREAMER_FILE = "streamer.txt"
TOKEN_FILE = "token.txt"
EXCLUDED_USERS_FILE = "excluded_users.txt"

def get_oauth_token():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r") as file:
            return file.read().strip()
    
    print("Öffne den Browser zur Twitch-Authentifizierung...")
    auth_url = f"https://id.twitch.tv/oauth2/authorize?response_type=token&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope=chat:read+chat:edit+moderator:read:chatters"
    webbrowser.open(auth_url)
    
    token = input("Füge hier dein Twitch-OAuth-Token ein: ")
    with open(TOKEN_FILE, "w") as file:
        file.write(token)
    return token

def get_username():
    if os.path.exists(USERNAME_FILE):
        with open(USERNAME_FILE, "r") as file:
            return file.read().strip()
    username = input("Gib deinen Twitch-Benutzernamen ein: ")
    with open(USERNAME_FILE, "w") as file:
        file.write(username)
    return username

def get_streamer():
    if os.path.exists(STREAMER_FILE):
        with open(STREAMER_FILE, "r") as file:
            return file.read().strip()
    streamer = input("Gib den Twitch-Kanal ein, den du überwachen möchtest: ")
    with open(STREAMER_FILE, "w") as file:
        file.write(streamer)
    return streamer

def load_excluded_users():
    if os.path.exists(EXCLUDED_USERS_FILE):
        with open(EXCLUDED_USERS_FILE, "r") as file:
            return set(file.read().splitlines())
    return set()

def get_existing_chatters():
    return set()

NICKNAME = get_username()
STREAMER = get_streamer()
TOKEN = get_oauth_token()
EXCLUDED_USERS = load_excluded_users()

SERVER = "irc.chat.twitch.tv"
PORT = 6667
CHANNEL = f"#{STREAMER}"

greeted_users = get_existing_chatters()

sock = socket.socket()
sock.connect((SERVER, PORT))
sock.send(f"PASS oauth:{TOKEN}\r\n".encode("utf-8"))
sock.send(f"NICK {NICKNAME}\r\n".encode("utf-8"))
sock.send(f"JOIN {CHANNEL}\r\n".encode("utf-8"))

def send_message(message):
    sock.send(f"PRIVMSG {CHANNEL} :{message}\r\n".encode("utf-8"))

print(f"Bot ready. Listening for messages from: {STREAMER}")

while True:
    try:
        response = sock.recv(2048).decode("utf-8")
        
        if response.startswith("PING"):
            sock.send("PONG :tmi.twitch.tv\r\n".encode("utf-8"))
            continue
        
        match = re.search(r":(\w+)!\w+@\w+\.tmi\.twitch\.tv PRIVMSG #\w+ :(.*)", response)
        if match:
            username = match.group(1)
            message = match.group(2).lower()
            print(f"{username}: {message}")
            
            if username not in greeted_users and username not in EXCLUDED_USERS:
                time.sleep(7)
                send_message(f"@{username} MLADY")
                greeted_users.add(username)
        
        time.sleep(1)  
    
    except Exception as e:
        print(f"Fehler: {e}")
        break
