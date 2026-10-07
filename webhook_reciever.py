from flask import Flask, request, url_for, jsonify, redirect
from dotenv import load_dotenv
import hashlib
import hmac
from datetime import datetime, timedelta
import os
import requests
import json

app = Flask(__name__)

users_data = {}
users_transactions = []
processed_event_ids = []
processed_events = []
load_dotenv('/home/ubuntu/Web_App_Revision/Webhooks_Practice/env_vars_webhook.env')

def save_new_user(user_id: int, user_name: str): 
    new_user = {
        'user_name': user_name,
    }
    users_data[user_id] = new_user

def delete_user(user_id: int):
    _ = users_data.pop(user_id)

def process_payment(user_id: int, user_name: str, amount: float=10.00):
    new_transaction = {
        'user_id': user_id,
        'user_name': user_name,
        'transaction_amount': amount,
    }
    users_transactions.append(new_transaction)

def create_signature(json_data:str, timestamp: str):
    pre_digest = f'{timestamp}.{json_data}'
    secret_key = os.getenv('WEBHOOK_SECRET')
    return hmac.new(
        secret_key.encode(), 
        pre_digest.encode(), 
        hashlib.sha256
    ).hexdigest()

@app.route('/')
def home():
    return 'This website does not have a homepage', 404

@app.post('/webhook')
def webhook():
    raw_body = request.json
    timestamp = request.headers['X-Timestamp']

    #check for data validity
    signature = create_signature(raw_body, timestamp)
    sent_signature = request.headers.get('X-Signature')
    if not hmac.compare_digest(signature, sent_signature):
        return {'message': 'Request suspected of tampering'}, 400

    #check for replay attack
    sent_time = datetime.fromtimestamp(float(timestamp))
    if (datetime.now() - sent_time) > timedelta(minutes=5):
        return {'message': 'Request rejected, too delayed'}, 400

    #check if content type is valid
    content_type = request.headers.get('Content-Type')
    if content_type == 'application/json':
        body = request.get_json()
        try:
            event_id = body['event_id']
            event = body['event']
            user_data = body['data']
        except KeyError:
            return {'message': 'Invalid body formatting'}, 400
    else:
        return {'message': 'Data sent must be in JSON'}, 400

    #check event_id for idempotency
    if event_id in processed_event_ids:
        return {'message': 'Event already processed'}, 200
    
    #check event validity
    supported_events = [
        'user.created',
        'user.deleted',
        'payment.completed',
    ]
    if not event.strip().lower() in supported_events:
        return {'message': 'Event not supported'}, 400

    #check presence of user id and name
    try:
        user_id = user_data['id']
    except KeyError:
        return {'message': 'Sent data must include user ID'}, 400
    
    try:
        user_name = user_data['name']
    except KeyError:
        user_name = ''

    #---handle event processing
    if event == 'user.created':
        save_new_user(user_id, user_name)
    elif event == 'user.deleted':
        delete_user(user_id)
    elif event == 'payment.completed':
        amount = user_data['amount']
        process_payment(user_id, user_name, amount)

    #---log event
    processed_event_ids.append(event_id)
    processed_events.append({
        'event_id': event_id,
        'event': event,
        'data': 'Not Available',
        'received_at': datetime.now().isoformat(sep=' '),
        'processed': True,
    })
    return {'message': 'Data received successfully'}, 200

@app.post('/trigger')
def trigger(): 
    body = request.get_json()
    try:
        event = body['event']
        data = body['data']
    except KeyError:
        return {'message': 'Invalid request format'}, 400
    headers = {
        'Content-Type': 'application/json',
    }
    endpoint_url = url_for('receiver', _external=True)
    response = requests.post(endpoint_url, json.dumps(body), headers=headers)
    return response.json(), response.status_code

@app.post('/receiver')
def receiver():
    global return_counter
    body = request.get_json()
    try:
        body = body['data']
    except KeyError:
        return {'message': 'Invalid request format'}, 400
    if return_counter < 3:
        return_counter += 1
        return {'message': 'Next time champ, try again later'}, 500
    elif return_counter == 3:
        return_counter = 1
        return {'message': f'Return to sender!: \'{body}\''}, 200
    
#-----reciever endpoint infrastructure
return_counter = 1

@app.get('/webhook/events')
def get_events():
    return processed_events, 200

@app.get('/worker')
def get_worker():
    return {'message': f'Current PID: {os.getpid()}'}, 200

if __name__ == '__main__':
    app.run()