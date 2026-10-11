from flask import Flask, request, jsonify
from dotenv import load_dotenv
from os import getenv
from hashlib import sha256
from hmac import new, compare_digest
import processing_functions
from datetime import datetime
import logging

#---events:
'''order.created	Process a new order using the data provided
user.created	Process a newly created user
user.deleted	Process a deleted user'''
app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

processed_events = {} #index by event ID
load_dotenv('.env')

def validate_signature(received_signature, body_bytes: bytes) -> bool:
    webhook_secret = getenv('WEBHOOK_SECRET').encode('utf-8')
    if webhook_secret is None:
        logger.critical('Webhook secret could not be retrieved')
        return jsonify('Internal server error'), 500
    digest = new(webhook_secret, body_bytes, sha256).hexdigest()
    return compare_digest(received_signature, digest)    

@app.post('/webhook')
def post_webhook():
    #---check content type
    logger.info('Checking content type')
    content_type = request.headers.get('Content-Type')
    if 'application/json' not in content_type:
        logger.warning('Invalid content type')
        return jsonify('Request not valid JSON'), 415

    #---check for missing fields
    logger.info('Checking for missing fields')
    body = request.get_json(silent=True)
    if body is None:
        return jsonify('Invalid JSON'), 400
    try:
        event_id = body['event_id']
        event = body['event']
        data = body['data']
    except KeyError:
        logger.warning('Invalid data formatting')
        return jsonify('Invalid data formatting'), 400

    #---verify valid data
    logger.info('Verifying data is valid')
    if not event_id.strip():
        return jsonify('Invalid event id'), 400
    if not event.strip():
        return jsonify('Invalid event type'), 400
    if not isinstance(data, dict):
        return jsonify('Data field is invalid'), 400

    #---verify signature is valid
    logger.info(f'Verifying signature for {event_id}')
    body_bytes = request.get_data()
    received_signature = request.headers.get('X-Signature')
    if received_signature is None or not received_signature.strip():
        return jsonify('No signature sent'), 400
    if not validate_signature(received_signature, body_bytes):
        logger.warning(f'Signature invalid for {event_id}')
        return jsonify('Invalid signature'), 400

    #---check if already processed
    logger.info(f'Running idempotency check on {event_id}')
    if event_id in processed_events.keys():
        logger.warning(f'{event_id} already processed')
        return jsonify('Event already processed'), 200

    #---route events
    logger.info(f'Handling {event_id}')
    if event.strip().lower() == 'order.created':
        logger.info(f'Order created for {event_id}')
        processing_functions.process_new_order(body, event_id)
    elif event.strip().lower() == 'user.created':
        try:
            logger.info(f'Creating user for {event_id}')
            processing_functions.create_user(body)
        except KeyError:
            logging.warning(f'No username for {event_id}')
            return jsonify('No username included'), 400
    elif event.strip().lower() == 'user.deleted':
        try:
            logger.info(f'Deleting user for {event_id}')
            processing_functions.delete_user(body)
        except KeyError:
            logging.warning(f'No username for {event_id}')
            return jsonify('No username included'), 400
    else:
        logger.warning(f'Unexpected event type for {event_id}')
        return jsonify('Invalid event'), 400

    #---storing new data
    logger.info(f'Storing new data for {event_id}')
    saved_data = {
        'event': event,
        'received_at': datetime.now().isoformat(),
        'processed': True,
    }
    processed_events[event_id] = saved_data

    logger.info(f'Processing complete for {event_id}')
    return jsonify('Data received'), 201       

@app.get('/events')
def get_events():
    logger.info('Returning all saved events')
    return jsonify(processed_events), 200

@app.get('/health')
def get_health():
    return jsonify('Service is alive'), 200

if __name__ == '__main__':
    app.run(port=5000)