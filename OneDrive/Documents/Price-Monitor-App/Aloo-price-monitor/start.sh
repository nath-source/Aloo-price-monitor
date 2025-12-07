#!/bin/bash
# Start the Celery Worker in the background
celery -A make_celery_app worker --beat --loglevel=info --concurrency=2 &

# Start the Web Server
gunicorn run:app