def process_new_order(data: dict, event_id: str):
    print(f'Processing order for event {event_id}')

def create_user(data: dict):
    name = data['data']['name']
    print(f'Creating user {name}...')

def delete_user(data: dict):
    name = data['data']['name']
    print(f'Deleting user {name}')