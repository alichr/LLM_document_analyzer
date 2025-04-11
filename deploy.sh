#!/bin/bash

echo "Stopping old Flask app (if running)..."
pkill -f "flask run" || true

echo "Starting new Flask app..."
export FLASK_APP=app/web_page.py  # Change if your entry point is different
export FLASK_ENV=development
nohup flask run --host=0.0.0.0 --port=8080 > flask.log 2>&1 &
