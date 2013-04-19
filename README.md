# A flask based brewery server.

Uses flask to log stuff.

# Setup

Create a settings.cfg file and add the following to it:

    DEFAULT_USERNAME = 'username'
    DEFAULT_PASSWORD = 'password'
    SECRET_KEY = 'secret key'
    DATABASE = '/path/to/database.db'

Installing everything

    pip install -r requirements.txt

# Running the server

    export FLASK_SETTINGS=./settings.cfg
    python app.py

# Communicating to the server

    curl -H "Accept: application/json" -H "Content-type: application/json" -X POST -d '{"temp":2554}' --user username:password http://localhost:5000/temp/

