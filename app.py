from os import getenv
from flask import Flask
from utilities.make_prediction import accounting, cleaning

api_key_id = getenv('LUNO_API_KEY_ID')
api_key_secret = getenv('LUNO_API_KEY_SECRET')

app = Flask(__name__)

accounts = accounting()


@app.route('/transaction/', methods=['GET'])
def transaction_desc():
    return accounts['description'][0]


@app.route('/bal/<string:asset>/', methods=['GET'])
def balance(asset):
    return str(accounts[asset][0])


@app.route('/candles/<string:pair>/', methods=['GET'])
def candles(pair):
    df, _ = cleaning(pair)
    return df.to_dict()


@app.route('/derives/<string:pair>/<string:deriv>/', methods=['GET'])
def derives(pair, deriv):
    _, derivatives = cleaning(pair)
    return str(derivatives[deriv][0])


@app.route('/', methods=['GET'])
def hello_world():
    return 'Hello from Model Server API'


if __name__ == '__main__':
    app.run()
