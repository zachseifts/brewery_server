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
app.config['BOOTSTRAP_JQUERY_VERSION'] = '2.0.0'
app.config['BOOTSTRAP_HTML5_SHIM'] = True
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

    def timestamp(self):
        ''' Converts timestamp.
        '''
        return self.created.strftime("%m/%d/%Y %l:%M %p").lstrip('0').lower()


@app.template_filter('reverse')
def reverse_filter(s):
    return reversed(s)

@app.route('/', methods=['GET'])
def home():
    now = datetime.datetime.now()
    half = [obj for obj in Reading.objects(created__gte=now - datetime.timedelta(minutes=30)).order_by('created__date')[:1440]][::-1]
    hour = [obj for obj in Reading.objects(created__gte=now - datetime.timedelta(hours=1)).order_by('created__date')[:1440]][::-1]
    hour_3 = [obj for obj in Reading.objects(created__gte=now - datetime.timedelta(hours=3)).order_by('created__date')[:1440]][::-1]
    day = [obj for obj in Reading.objects(created__gte=now - datetime.timedelta(hours=24)).order_by('created__date')[:1440]][::-1]
    temps = [o.as_fahrenheit() for o in day]
    return render_template('homepage.html',
        day=day,
        current=day[0].as_fahrenheit(),
        hour=hour,
        hour_3=hour_3,
        half=half,
        average=sum(temps) / float(len(temps)),
        max_24=max(temps),
        min_24=min(temps),
    )

@app.route('/sensors/', methods=['GET'])
def sensors():
    sensors = Reading.objects().distinct('key')
    return render_template('sensors.html', sensors=sensors)

@app.route('/sersor/<string:key>/', methods=['GET'])
def sensor(key):
    objects = [obj for obj in Reading.objects(key=key).order_by('created__date')][::-1]
    temps = [o.as_fahrenheit() for o in objects]
    return render_template('sensor.html',
        sensor=key,
        objects=objects,
        current=objects[0].as_fahrenheit(),
        average=sum(temps) / float(len(temps)),
        max_24=max(temps),
        min_24=min(temps)
    )

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

