#!/bin/sh

python init_db.py

exec gunicorn --bind 0.0.0.0:5000 --log-level 'debug'  wsgi:app 
