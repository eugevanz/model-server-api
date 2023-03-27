import pandas as pd
from requests import get
from os import getenv
from flask import Flask
from sqlalchemy import create_engine, text

api_key_id = getenv('LUNO_API_KEY_ID')
api_key_secret = getenv('LUNO_API_KEY_SECRET')

app = Flask(__name__)


@app.route('/transaction/', methods=['GET'])
def transaction_desc():
    res_json = get(
        'https://api.luno.com/api/1/accounts/5177208153100163675/transactions?min_row=1&max_row=2',
        auth=(api_key_id, api_key_secret),
    ).json()['transactions']

    return res_json[0]['description'] if res_json is not None else '---'


@app.route('/bal/<string:asset>', methods=['GET'])
def balance(asset):
    res_json = get(
        f'https://api.luno.com/api/1/balance?assets={asset}',
        auth=(api_key_id, api_key_secret),
    ).json()['balance']

    return res_json[0]['balance']


@app.route('/candles/<string:tbl_name>/', methods=['GET'])
def candles(tbl_name):
    result = []
    query = text('SELECT * FROM :tbl_name')
    try:
        # Create the SQLAlchemy engine
        engine = create_engine(getenv('RENDER_SQL_EXT'), echo=True, future=True)
        # Define the query to select data from the table
        with engine.connect() as connection:
            result = connection.execute(query, {'tbl_name': tbl_name})
            result = pd.DataFrame(result.fetchall())
    except Exception as error:
        print(error)

    return result


@app.route('/derives/<string:col_name>/<string:tbl_name>/', methods=['GET'])
def derives(col_name, tbl_name):
    result = '/derives/<string:col_name>/<string:tbl_name>'
    query = text('SELECT :col_name FROM :tbl_name')
    try:
        # Create the SQLAlchemy engine
        engine = create_engine(getenv('RENDER_SQL_EXT'), echo=True, future=True)
        # Define the query to select data from the table
        with engine.connect() as connection:
            result = connection.execute(query, {'col_name': col_name, 'tbl_name': tbl_name})
            result = result.fetchone()[0]
    except Exception as error:
        print(error)

    return result


@app.route('/', methods=['GET'])
def hello_world():
    return 'Hello from Model Server API'


if __name__ == '__main__':
    app.run()
