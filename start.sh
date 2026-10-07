#!/bin/bash

echo "Starting Flask application..."
gunicorn -c /home/ubuntu/Web_App_Revision/Webhooks_Practice/gunicorn.conf.py wsgi:app