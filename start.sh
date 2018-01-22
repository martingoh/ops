#!/bin/bash

PID=$(ps -eaf | grep uwsgi | grep -v grep | awk '{print $2}')
if [ "$PID" != '' ]; then
	kill -9 $PID
fi
source .venv/bin/activate
uwsgi --ini ./uwsgi/uwsgi.ini
