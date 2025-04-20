import asyncio
from datetime import datetime, timedelta
from configparser import ConfigParser
from twikit import Client, TooManyRequests

# Load credentials from config.ini
config = ConfigParser()
config.read('config1.ini')
username = config['X']['username']
email = config['X']['email']
password = config['X']['password']

# Async function to log in
async def login_and_save_cookies():
    client = Client(language='en-US')
    await client.login(auth_info_1=username, auth_info_2=email, password=password)  # Await the coroutine
    client.save_cookies('cookies1.json')
    print("✅ Cookies saved successfully!")

# Run the async function
asyncio.run(login_and_save_cookies())
