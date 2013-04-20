from __future__ import with_statement
from contextlib import closing
import sqlite3
from flask import Flask, request, jsonify, json, Response, abort, g, render_template
from flask.ext.bootstrap import Bootstrap
from werkzeug.contrib.fixers import ProxyFix

app = Flask(__name__)
Bootstrap(app)
app.config.from_envvar('FLASK_SETTINGS', silent=True)

app.config['BOOTSTRAP_USE_MINIFIED'] = True
app.config['BOOTSTRAP_USE_CDN'] = True
app.config['BOOTSTRAP_FONTAWESOME'] = True

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
    cur = g.db.execute('select created, temp/1000.0, key from entries order by id desc')
    entries = [dict(created=row[0], temp=row[1], key=row[2]) for row in cur.fetchall()]
    return render_template('entries.html', entries=entries, graph=reversed(entries))

@app.route('/temp/<key>/<int:temp>', methods=['POST'])
def temps(key, temp):
    if request.method == 'POST':
        auth = request.authorization
        if not auth or (auth.username != app.config['DEFAULT_USERNAME'] or auth.password != app.config['DEFAULT_PASSWORD']):
            abort(401)
        g.db.execute('insert into entries (temp, key) values (?, ?)', [temp, key])
        g.db.commit()
        return jsonify(status='ok', temp=temp, key=key)

app.wsgi_app = ProxyFix(app.wsgi_app)

if __name__ == '__main__':
    app.run()

