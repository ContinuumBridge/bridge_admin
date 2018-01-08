from flask import Flask, jsonify
import os
import ssl

ASSETS_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__)


@app.route('/')
def index():
    return 'Flask is running!'


@app.route('/data')
def names():
    data = {"names": ["John", "Jacob", "Julie", "Jennifer"]}
    return jsonify(data)


if __name__ == '__main__':
    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    context.load_cert_chain('/home/ubuntu/bridge_admin/flask/cbclient.pem', '/home/ubuntu/bridge_admin/flask/cbclient.key')
    #app.run(debug=True, ssl_context=context)
    app.run(host = '0.0.0.0', port=5005, ssl_context=context)
    #app.run(debug=True)
