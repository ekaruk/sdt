
import os
import requests
from dotenv import load_dotenv

load_dotenv()


OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

if not OPENAI_API_KEY:
    print('ERROR: Set the OPENAI_API_KEY environment variable.')
    exit(1)

url = 'https://api.openai.com/v1/models'
headers = {
    'Authorization': f'Bearer {OPENAI_API_KEY}'
}

response = requests.get(url, headers=headers)

if response.ok:
    data = response.json()
    print('Available OpenAI models:')
    for model in data.get('data', []):
        print(f"- {model.get('id')}")
else:
    print('Error:', response.status_code, response.text)
