from __future__ import with_statement
import os
import sqlite3
import datetime
from contextlib import closing
from flask import Flask, request, jsonify, json, Response, abort, g, render_template, send_from_directory
from flask.ext.bootstrap import Bootstrap
from flask.ext.mongoengine import MongoEngine
from werkzeug.contrib.fixers import ProxyFix

app = Flask(__name__)
Bootstrap(app)
app.config.from_envvar('FLASK_SETTINGS', silent=True)

app.config['BOOTSTRAP_USE_MINIFIED'] = True
app.config['BOOTSTRAP_USE_CDN'] = True
app.config['BOOTSTRAP_FONTAWESOME'] = True

app.config['MONGODB_SETTINGS'] = {'DB': 'brewery_server'}

db = MongoEngine()
db.init_app(app)

class Reading(db.Document):
    ''' A record of the reading from the sensor.
    '''
    created = db.DateTimeField(default=datetime.datetime.now)
    key = db.StringField(max_length=60)
    value = db.IntField()


def connect_db():
    ''' Connects to the database.
    '''
    return sqlite3.connect(app.config['DATABASE'])

def init_db():
    ''' Creates the database from sql.
    '''
    with closing(connect_db()) as db:
        with app.open_resource('database.sql') as f:
            db.cursor().executescript(f.read())
        db.commit()

@app.before_request
def before_request():
    g.db = connect_db()

@app.after_request
def after_request(response):
    g.db.close()
    return response

@app.route('/', methods=['GET'])
def home():
    cur = g.db.execute('select created, ((temp/1000.0) * 1.8) + 32, temp/1000.0, key from entries order by id desc limit 1440')
    entries = [dict(created=row[0], temp=row[1], c=row[2], key=row[3]) for row in cur.fetchall()]
    return render_template('homepage.html',
        entries=entries[:60],
        current=entries[0]['temp'], 
        half=reversed(entries[:30]),
        hour=reversed(entries[:60]),
        day=reversed(entries))

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
        'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/temp/<key>/<int:temp>', methods=['POST'])
def temps(key, temp):
    if request.method == 'POST':
        auth = request.authorization
        if not auth or (auth.username != app.config['DEFAULT_USERNAME'] or auth.password != app.config['DEFAULT_PASSWORD']):
            abort(401)
        g.db.execute('insert into entries (temp, key) values (?, ?)', [temp, key])
        g.db.commit()
        r = Reading(key=key, value=temp).save()
        return jsonify(status='ok', temp=temp, key=key)

app.wsgi_app = ProxyFix(app.wsgi_app)

if __name__ == '__main__':
    app.run()

