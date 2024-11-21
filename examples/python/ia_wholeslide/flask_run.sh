#!/bin/bash
export FLASK_APP=src/dpat_wholeslide/webserver
export FLASK_RUN_PORT=5006
export FLASK_RUN_HOST=0.0.0.0
export FLASK_DEBUG=1
uv run -- flask run
