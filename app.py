import pandas as pd
import numpy as np
from requests import get
import time
from dotenv import load_dotenv
from os import getenv
import joblib as jb
from flask import Flask

load_dotenv()
api_key_id = getenv('LUNO_API_KEY_ID')
api_key_secret = getenv('LUNO_API_KEY_SECRET')

since = int(time.time() * 1000) - 3 * 60 * 59 * 1000
duration = 300


def get_candles(pair):
    res_json = get(
        f'https://api.luno.com/api/exchange/1/candles?pair={pair}&duration=300&since={since}',
        auth=(api_key_id, api_key_secret),
    ).json()['candles']

    df = pd.DataFrame(res_json)

    def lagged():
        tminuses = []
        volumes = []
        for i in range(1, 4):
            df[f'tminus_{str(i)}'] = df.change.shift(i)
            df[f'vol_{str(i)}'] = df.volume.shift(i)
            tminuses.append(f'tminus_{str(i)}')
            volumes.append(f'vol_{str(i)}')

        return tminuses + volumes

    df.rename(columns={'timestamp': 'Time'}, inplace=True)
    df.set_index('Time', inplace=True)

    df.open = df.open.astype(float)
    df.close = df.close.astype(float)
    df.high = df.high.astype(float)
    df.low = df.low.astype(float)
    df.volume = df.volume.astype(float)

    df['change'] = df.close.pct_change()

    features = lagged()

    df['EMA12'] = df.close.ewm(span=12).mean()
    df['EMA12_diff'] = df[['EMA12', 'close']].pct_change(axis=1)['close'] * 100.0
    features.append('EMA12_diff')

    df.dropna(inplace=True)

    df['signal'] = np.where(df.change > 0, True, False)

    model = jb.load('assets/model.pkl')

    df['prediction'] = list(model.predict(df[features]))

    late_close = df.close.tolist()[-1]
    late_ema = df.EMA12.tolist()[-1]
    late_signal = df.prediction.tolist()[-1] and (late_ema < late_close)

    max_high = df.high.idxmax()
    min_low = df.low.idxmin()
    max_close = df.close.idxmax()
    min_close = df.close.idxmin()
    avg_close = df.close.mean()

    return dict(
        candles=df,
        late_signal=late_signal,
        late_close=late_close,
        late_ema=late_ema,
        max_high=max_high,
        min_low=min_low,
        max_close=max_close,
        min_close=min_close,
        avg_close=avg_close,
    )


xbtzar = get_candles('XBTZAR')
ethzar = get_candles('ETHZAR')

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


@app.route('/candles/<string:currency>/', methods=['GET'])
def candles(currency):
    return xbtzar['candles'].to_dict() if currency == 'XBTZAR' else ethzar['candles'].to_dict()


@app.route('/late_signal/<string:currency>/', methods=['GET'])
def late_signal_x(currency):
    return ('BUY' if xbtzar['late_signal'] else 'SELL') if currency == 'XBTZAR' else (
        'BUY' if ethzar['late_signal'] else 'SELL')


@app.route('/late_close/<string:currency>/', methods=['GET'])
def late_close_x(currency):
    return str(xbtzar['late_close']) if currency == 'XBTZAR' else str(ethzar['late_close'])


@app.route('/late_ema/<string:currency>/', methods=['GET'])
def late_ema_x(currency):
    return str(xbtzar['late_ema']) if currency == 'XBTZAR' else str(ethzar['late_ema'])


@app.route('/max_high/<string:currency>/', methods=['GET'])
def max_high_x(currency):
    return str(xbtzar['max_high']) if currency == 'XBTZAR' else str(ethzar['max_high'])


@app.route('/min_low/<string:currency>/', methods=['GET'])
def min_low_x(currency):
    return str(xbtzar['min_low']) if currency == 'XBTZAR' else str(ethzar['min_low'])


@app.route('/max_close/<string:currency>/', methods=['GET'])
def max_close_x(currency):
    return str(xbtzar['max_close']) if currency == 'XBTZAR' else str(ethzar['max_close'])


@app.route('/min_close/<string:currency>/', methods=['GET'])
def min_close_x(currency):
    return str(xbtzar['min_close']) if currency == 'XBTZAR' else str(ethzar['min_close'])


@app.route('/avg_close/<string:currency>/', methods=['GET'])
def avg_close_x(currency):
    return str(xbtzar['avg_close']) if currency == 'XBTZAR' else str(ethzar['avg_close'])


@app.route('/', methods=['GET'])
def hello_world():
    return 'Hello from Model Server API'


if __name__ == '__main__':
    app.run()
