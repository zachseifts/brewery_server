from __future__ import with_statement
from contextlib import closing
import sqlite3
from flask import Flask, request, jsonify, json, Response, abort, g, render_template
from werkzeug.contrib.fixers import ProxyFix

app = Flask(__name__)
app.config.from_envvar('FLASK_SETTINGS', silent=True)

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

@app.route('/temp/', methods=['POST', 'GET'])
def temps():
    if request.method == 'GET':
        cur = g.db.execute('select created, temp, key from entries order by id desc')
        entries = [dict(created=row[0], temp=float(row[1] / 1000), key=row[2]) for row in cur.fetchall()]
        return render_template('entries.html', entries=entries)
    if request.method == 'POST':
        auth = request.authorization
        if not auth or (auth.username != app.config['DEFAULT_USERNAME'] or auth.password != app.config['DEFAULT_PASSWORD']):
            abort(401)
        data = json.loads(request.data)
        g.db.execute('insert into entries (temp, key) values (?, ?)',
            [data['temp'], data['key']])
        g.db.commit()
        return jsonify(status='ok', temp=data['temp'], key=data['key'])

app.wsgi_app = ProxyFix(app.wsgi_app)

if __name__ == '__main__':
    app.run(host='0.0.0.0')

