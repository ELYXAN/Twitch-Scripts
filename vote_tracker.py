import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from fuzzywuzzy import process
import time

# Constants
VOTE_ID_FILE = 'Vote_IDs.csv'
INACCURATE_GAMES_FILE = 'inacurate_games.csv'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID = 'ID'
CLIENT_ID = 'CLIENT_ID'
CLIENT_SECRET = 'CLIENT_SECRET'
TOKEN = 'TOKEN'
TWITCH_USERNAME = 'Twitch Channel name'
NORMAL_VOTE_ID = 'VOTE_ID'
SUPER_VOTE_ID = 'VOTE_ID'

# Google API Authentication
creds = ServiceAccountCredentials.from_json_keyfile_name('Vote tracking.json', SCOPES)
client = gspread.authorize(creds)
sheet = client.open_by_key(SPREADSHEET_ID)
worksheet = sheet.get_worksheet(0)

# Twitch API Headers
headers = {
    'Client-ID': CLIENT_ID,
    'Authorization': f'Bearer {TOKEN}'
}

def banner():
    print("██╗   ██╗ ██████╗ ████████╗███████╗    ████████╗██████╗  █████╗  ██████╗██╗  ██╗███████╗██████╗ ")
    print("██║   ██║██╔═══██╗╚══██╔══╝██╔════╝    ╚══██╔══╝██╔══██╗██╔══██╗██╔════╝██║ ██╔╝██╔════╝██╔══██╗")
    print("██║   ██║██║   ██║   ██║   █████╗         ██║   ██████╔╝███████║██║     █████╔╝ █████╗  ██████╔╝")
    print("██║   ██║██║   ██║   ██║   ██╔══╝         ██║   ██╔═██║ ██╔══██║██║     ██╔═██╗ ██╔══╝  ██╔══██╗")
    print("╚██████╔╝╚██████╔╝   ██║   ███████╗       ██║   ██║  ██║██║  ██║╚██████╗██║  ██╗███████╗██║  ██║")
    print(" ╚═════╝  ╚═════╝    ╚═╝   ╚══════╝       ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝")
    print("\nMade by: ELYXAN")

def load_list(file_name):
    try:
        with open(file_name, 'r') as f:
            return [line.strip() for line in f.readlines()]
    except FileNotFoundError:
        return []

def save_list(file_name, items):
    with open(file_name, 'w') as f:
        for item in items:
            f.write(str(item) + '\n')

def get_broadcaster_id():
    endpoint = f'https://api.twitch.tv/helix/users?login={TWITCH_USERNAME}'
    response = requests.get(endpoint, headers=headers)
    if response.status_code == 200:
        data = response.json()
        return data['data'][0]['id']
    return None

def process_vote(reward_id, vote_weight):
    endpoint = f'https://api.twitch.tv/helix/channel_points/custom_rewards/redemptions?broadcaster_id={broadcaster_id}&reward_id={reward_id}&status=UNFULFILLED'
    response = requests.get(endpoint, headers=headers)
    if response.status_code == 200:
        rewards_data = response.json()
        for entry in rewards_data.get('data', []):
            vote_id = entry.get('id')
            title = entry.get('reward', {}).get('title', '')
            if vote_id not in vote_ids and title == 'Playlist name':
                vote_ids.append(vote_id)
                save_list(VOTE_ID_FILE, vote_ids)
                user_input = entry.get('user_input')
                match, score = process.extractOne(user_input, games_list, score_cutoff=70)
                if match:
                    update_votes(match, vote_weight, vote_id, title)
                else:
                    log_inaccurate_game(user_input, vote_id)

def update_votes(game, vote_weight, vote_id, title):
    try:
        cell = worksheet.find(game, in_column=2)
        current_votes = int(worksheet.cell(cell.row, 1).value)
        new_votes = current_votes + vote_weight
        worksheet.update_cell(cell.row, 1, new_votes)
        print(f"Vote für {game} erfolgreich hinzugefügt. {current_votes} Neue Anzahl der Votes: {new_votes} Vote ID: {vote_id} Titel: {title}")
        fulfill_vote(vote_id, NORMAL_VOTE_ID if vote_weight == 1 else SUPER_VOTE_ID)
    except gspread.exceptions.WorksheetNotFound:
        print(f"Spiel {game} nicht in der Tabelle gefunden.")

def log_inaccurate_game(game, vote_id):
    with open(INACCURATE_GAMES_FILE, 'a') as f:
        f.write(f"{game} Vote Anzahl: 1\n")
    print(f"Eintrag in CSV Datei: {game}, Vote ID: {vote_id}")

def fulfill_vote(vote_id, reward_id):
    url = 'https://api.twitch.tv/helix/channel_points/custom_rewards/redemptions'
    params = {
        'broadcaster_id': broadcaster_id,
        'reward_id': reward_id,
        'id': vote_id
    }
    payload = {'status': 'FULFILLED'}
    response = requests.patch(url, headers=headers, json=payload, params=params)
    print(response.json())

# Main Execution
banner()
vote_ids = load_list(VOTE_ID_FILE)
inaccurate_games = load_list(INACCURATE_GAMES_FILE)
broadcaster_id = get_broadcaster_id()
games_list = worksheet.col_values(2)

while True:
    process_vote(NORMAL_VOTE_ID, 1)
    process_vote(SUPER_VOTE_ID, 10)
    time.sleep(5)
