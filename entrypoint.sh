#!/bin/bash

# Start ngrok in the background
ngrok http 8000 &

# Wait for ngrok to start and be accessible
sleep 10

# Update the .env file with the ngrok URL
# /usr/local/bin/update_ngrok_link.sh

# Start the Django application
exec python manage.py runserver 0.0.0.0:8000
