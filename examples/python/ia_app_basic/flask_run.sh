#!/bin/bash
export FLASK_APP=pcaddemo/webserver
export FLASK_RUN_PORT=5005
export FLASK_RUN_HOST=0.0.0.0
export FLASK_DEBUG=1
flask run
