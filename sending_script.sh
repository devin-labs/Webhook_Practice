#!/bin/bash

for i in {1..10}; do
    #python "/home/ubuntu/Web_App_Revision/Webhooks_Practice/webhook_sender.py" &
    curl http://localhost:8000/worker
done

wait

echo "All programs complete"