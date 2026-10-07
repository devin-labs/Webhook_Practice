import requests
from hashlib import sha256
from dotenv import load_dotenv
import os
import json
from datetime import datetime
import hmac
import random

SERVER_URL = 'http://127.0.0.1:8000'

def create_signature(data: str, timestamp: float):
    secret = os.getenv("WEBHOOK_SECRET")
    pre_digest = f"{str(timestamp)}.{data}"
    digest = hmac.new(
        secret.encode(), 
        pre_digest.encode(), 
        sha256
        ).hexdigest()
    return digest


def main():
    load_dotenv("/home/ubuntu/Web_App_Revision/Webhooks_Practice/env_vars_webhook.env")
    body = {
        "event_id": f"event_{random.randint(1, 500)}",
        "event": "user.created",
        "data": {
            "id": 123,
        },
    }
    timestamp = datetime.now().timestamp()

    headers = {
        "Content-Type": "application/json",
        "X-Signature": create_signature(body, timestamp),
        "X-Timestamp": str(timestamp),
    }
    retries = 0
    while True:
        response = requests.post(
            SERVER_URL + '/webhook', json.dumps(body), headers=headers
        )
        if response.status_code == 500 and retries <3:
            retries += 1
            print(f'Bad response received, trying again...({retries}/3)')
            continue
        elif response.status_code == 500 and retries == 3:
            print('Exceeded max number of retries, cancelling...')
            break
        elif response.status_code == 200:
            print(response.status_code, response.json())
            break


if __name__ == "__main__":
    main()
