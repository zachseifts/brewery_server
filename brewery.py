from __future__ import with_statement
import os
import datetime
from contextlib import closing
from flask import Flask, request, jsonify, json, Response, abort, g, render_template, send_from_directory
from flask.ext.bootstrap import Bootstrap
from flask.ext.mongoengine import MongoEngine
from werkzeug.contrib.fixers import ProxyFix

app = Flask(__name__)

app.config.from_envvar('FLASK_SETTINGS', silent=True)
app.config['BOOTSTRAP_USE_MINIFIED'] = True
app.config['BOOTSTRAP_USE_CDN'] = True
app.config['BOOTSTRAP_FONTAWESOME'] = True
app.config['MONGODB_SETTINGS'] = {'DB': 'brewery_server'}

Bootstrap(app)
db = MongoEngine()
db.init_app(app)

class Reading(db.Document):
    ''' A record of the reading from the sensor.
    '''
    created = db.DateTimeField(default=datetime.datetime.now)
    key = db.StringField(max_length=60)
    value = db.IntField()

    def as_celsus(self):
        ''' Returns the temperature as celsus.
        '''
        return self.value / 1000.0

    def as_fahrenheit(self):
        ''' Returns the temperature as fahrenheit.
        '''
        return (self.as_celsus() * 1.8) + 32


@app.template_filter('reverse')
def reverse_filter(s):
    return reversed(s)

@app.route('/', methods=['GET'])
def home():
    readings = list()
    objects = Reading.objects.order_by('created')[:1440]
    for reading in list(objects):
        readings.append({
            'created': reading.created,
            'temp': reading.as_fahrenheit(),
            'c': reading.as_celsus(),
            'key': reading.key
        })
    temps = [o.as_fahrenheit() for o in list(objects)]
    return render_template('homepage.html',
        daily_average=reduce(lambda x, y: x + y, temps) / len(temps),
        hourly_average=reduce(lambda x, y: x + y, temps[60:]) / len(temps[60:]),
        current=readings[0]['temp'], 
        hour=readings[60:],
        half=readings[30:],
        day=readings)

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
        Reading(key=key, value=temp).save()
        return jsonify(status='ok', temp=temp, key=key)

app.wsgi_app = ProxyFix(app.wsgi_app)

if __name__ == '__main__':
    app.run()

