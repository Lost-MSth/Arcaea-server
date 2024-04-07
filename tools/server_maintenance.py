from flask import Flask, jsonify

app = Flask(__name__)

HOST = '0.0.0.0'
PORT = '80'

@app.route('/favicon.ico', methods=['GET'])
def favicon():
    return ''

@app.route('/<path:p>')
def hello(p):
    r = {"success": False, "error_code": 2}
    return jsonify(r)


if __name__ == '__main__':
    app.run(host=HOST, port=PORT)
