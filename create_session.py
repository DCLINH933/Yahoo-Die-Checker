import requests
import re
import os
import time
import random
import json
from requests.exceptions import RequestException
from concurrent.futures import ThreadPoolExecutor
from urllib3.exceptions import InsecureRequestWarning
from urllib3 import disable_warnings

disable_warnings(InsecureRequestWarning)

# Global proxy list
proxies_list = []

def load_proxies(file_path):
    global proxies_list
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Proxy file not found: {file_path}")

    with open(file_path, "r") as file:
        # Filter valid proxy lines based on format
        proxies_list = [
            line.strip() for line in file
            if re.match(r'^(([^:@\s]+:[^:@\s]+@)?[^:@\s]+:[0-9]+)$', line.strip())
        ]

    if not proxies_list:
        raise ValueError("Proxy file does not contain valid proxies.")

def get_random_proxy():
    if not proxies_list:
        raise ValueError("Proxy list is empty. Make sure to load proxies first.")

    return random.choice(proxies_list)

def fetch_yahoo_hidden_inputs(url, proxies=None):
    try:
        # Initialize a session
        with requests.Session() as session:
            # Sending a GET request to the URL
            response = session.get(url, proxies=proxies, verify=False, timeout=10)

            # Checking if the request was successful
            if response.status_code == 200:
                # Extracting hidden input values from the response text
                response_text = response.text

                # Using original regex patterns to ensure proper matching
                crumb = re.search(r'<input[^>]*value=["\'](.*?)["\'][^>]*name=["\']crumb["\']', response_text)
                acrumb = re.search(r'<input[^>]*value=["\'](.*?)["\'][^>]*name=["\']acrumb["\']', response_text)
                session_index = re.search(r'<input[^>]*value=["\'](.*?)["\'][^>]*name=["\']sessionIndex["\']', response_text)

                crumb_value = crumb.group(1) if crumb else None
                acrumb_value = acrumb.group(1) if acrumb else None
                session_index_value = session_index.group(1) if session_index else None

                cookies = session.cookies.get_dict()

                # Returning the extracted values and cookies
                return {
                    "crumb": crumb_value,
                    "acrumb": acrumb_value,
                    "sessionIndex": session_index_value,
                    "cookies": cookies
                }
            else:
                return {"error": f"Failed to fetch page. Status code: {response.status_code}"}

    except RequestException as e:
        return {"error": f"An error occurred: {str(e)}"}

def task(url):
    while True:
        try:
            selected_proxy = get_random_proxy()
            proxies = {"http": f"http://{selected_proxy}", "https": f"http://{selected_proxy}"}
        except ValueError as e:
            print({"error": f"Proxy selection failed: {str(e)}"})
            continue

        result = fetch_yahoo_hidden_inputs(url, proxies=proxies)

        # Save result to a file in the "session" folder only if all values are found
        if result.get("crumb") and result.get("acrumb") and result.get("sessionIndex"):
            if not os.path.exists("session"):
                os.makedirs("session")

            current_time = int(time.time())
            random_number = random.randint(1, 999999)
            file_name = f"session/Session_{current_time}_{random_number}.json"

            with open(file_name, "w") as file:
                json.dump(result, file, indent=4)

            print(f"Saved result to file: {file_name}")
        else:
            print({"error": "Failed to fetch required inputs."})

def main():
    global proxies_list

    url = "https://login.yahoo.com/account/create"
    proxy_file = "proxy.txt"

    try:
        load_proxies(proxy_file)
    except (FileNotFoundError, ValueError) as e:
        print({"error": f"Failed to load proxies: {str(e)}"})
        return

    try:
        num_threads = int(input("Enter the number of threads: "))
    except ValueError:
        print("Invalid input. Using 1 thread by default.")
        num_threads = 1

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        for _ in range(num_threads):
            executor.submit(task, url)

if __name__ == "__main__":
    main()
