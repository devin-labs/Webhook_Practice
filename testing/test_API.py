import requests
from dotenv import load_dotenv
from os import getenv
import hashlib
import hmac
import random
import json

WEBHOOK_URL = 'http://localhost:5000/webhook'
EVENTS_URL = 'http://localhost:5000/events'
HEALTH_URL = 'http://localhost:5000/health'
EVENT_TYPES = ('user.created', 'user.deleted', 'order.created')

load_dotenv('../main/.env')

def create_signature(json_body: bytes):
    secret = getenv('WEBHOOK_SECRET').encode('utf-8')
    digest = hmac.new(secret, json_body, hashlib.sha256).hexdigest()
    return digest

def create_payload(event_type: str) -> dict:
    event_id = f'evt_{random.randint(1, 100)}'
    if event_type in ['user.created', 'user.deleted']:
        data = {
            'name': 'Allison',
        }
    elif event_type == 'order.created':
        data = {
            'order_id': random.randint(1, 10000),
            'customer': 'Benson Boone',
            'amount': random.randint(1000, 200000) / 100,
        }
    payload = {
        'event_id': event_id,
        'event': event_type,
        'data': data,
    }
    return payload

def main():
    #body = json.dumps(create_payload(random.choice(EVENT_TYPES)))
    body = {
        "event_id": "evt_9198",
        "event": "order.created",
        "data": {
            "order_id": 8472,
            "customer": "Alice",
            "amount": 1499.99
        }
    }
    body = json.dumps(body)
    signature = create_signature(body.encode())
    headers = {
        'Content-Type': 'application/json',
        'X-Signature': signature,
    }
    response = requests.post(WEBHOOK_URL, data=body, headers=headers)
    try:
        print(json.loads(body)['event'])
    except KeyError:
        pass
    print(response.status_code)
    print(response.text)

if __name__ == '__main__':
    main()