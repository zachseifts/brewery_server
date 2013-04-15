from flask import Flask, request, jsonify, json, Response, abort

app = Flask(__name__)
app.config.from_envvar('FLASK_SETTINGS')

@app.route('/temp/', methods=['POST', 'GET'])
def temps():
    if request.method == 'GET':
        return 'foo'
    if request.method == 'POST':
        auth = request.authorization
        if not auth or (auth.username != app.config['DEFAULT_USERNAME'] or auth.password != app.config['DEFAULT_PASSWORD']):
            abort(401)
        data = json.loads(request.data)
        return jsonify(items=[{'data': data}])

if __name__ == '__main__':
    app.run()

