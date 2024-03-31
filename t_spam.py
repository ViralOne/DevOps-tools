import requests
import random
import time
import string
import datetime
import os

# Load words from file
def load_words(file_path):
    with open(file_path, 'r') as file:
        words = [word.strip() for word in file]
    return words

# Generate random text
def generate_random_text(words, char_limit):
    text = ""
    while len(text) < char_limit:
        word = random.choice(words)
        if len(text) != 0 and len(text) + len(word) + 1 <= char_limit:
            text += " "
        elif len(text) + len(word) > char_limit:
            break
        text += word
    return text

words = load_words('words.txt')

def generate_random_filename():
    random_word = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    current_time = datetime.datetime.now()
    formatted_time = current_time.strftime("%Y_%m_%d_%H_%M_%S")
    return f"PW_{random_word}_{formatted_time}.html"

def create_random_file(words, char_limit, directory="."):
    filename = generate_random_filename()
    file_path = os.path.join(directory, filename)
    random_text = generate_random_text(words, char_limit)
    with open(file_path, 'w') as file:
        file.write(random_text)
    return file_path

def send_telegram_message(bot_token, chat_id, message):
    send_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = {"chat_id": chat_id, "text": message}
    response = requests.post(send_url, data=data)
    return response

def send_telegram_file(bot_token, chat_id, file_path, caption=None):
    send_url = f"https://api.telegram.org/bot{bot_token}/sendDocument"
    data = {"chat_id": chat_id}
    files = {'document': open(file_path, 'rb')}
    if caption:
        data['caption'] = caption
    response = requests.post(send_url, data=data, files=files)
    return response

# Define your chat IDs and bot tokens in lists
chat_ids = []
bot_tokens = []

# Message details
max_messages = 1000
char_limit = 1000
directory = "."
count = 0

start_time = time.time()

while count < max_messages:
    random_text = generate_random_text(words, 4013)
    captation_text = ""
    for chat_id, bot_token in zip(chat_ids, bot_tokens):
        created_file = create_random_file(words, char_limit, directory)
        time.sleep(2)
        result = send_telegram_file(bot_token, chat_id, created_file, captation_text)
        # result = send_telegram_message(bot_token, chat_id, random_text)
        if result.status_code == 429 or result.status_code == 400:
            print(f"{chat_id} - Error:", result.status_code)
            # If error 429, print time to wait and sleep that time
            if result.status_code == 429:
                retry_after = int(result.headers.get('Retry-After', '10'))
                print(f"Too many requests. Waiting for {retry_after} seconds before trying the next chat ID.")
                time.sleep(retry_after)
                break
            break
        elif result.status_code != 200:
            print("Unexpected error:", result.status_code)
        else:
            print(f"Message sent successfully to {chat_id}")
        
        os.remove(created_file)
    count += 1
    # Adjust the sleep time as needed to respect Telegram's rate limits

    print(f"Sent {count} messages in {time.time() - start_time} seconds.")