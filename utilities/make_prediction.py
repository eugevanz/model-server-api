import time
from os import getenv

import joblib as jb
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from requests import get, post

# Load environment variables
load_dotenv()
api_key_id = getenv('LUNO_API_KEY_ID')
api_key_secret = getenv('LUNO_API_KEY_SECRET')

since = int(time.time() * 1000) - 3 * 60 * 59 * 1000
duration = 300


def cleaning(pair):
    """
    Downloads candlestick data from the Luno API for a given currency pair,
    cleans the data, generates lagged features, makes a prediction using a pre-trained model,
    and returns a DataFrame of the cleaned and lagged data along with a DataFrame of derivatives.

    Args:
        pair (str): The currency pair to download data for, e.g. 'XBTZAR'.

    Returns:
        A tuple of two DataFrames: the cleaned and lagged data, and a DataFrame of derivatives.
    """

    try:
        # Download data
        res_json = get(
            f'https://api.luno.com/api/exchange/1/candles?pair={pair}&duration=300&since={since}',
            auth=(api_key_id, api_key_secret),
        ).json()['candles']
        df = pd.DataFrame(res_json)

        def lagged(num_lags=3):
            """
            Creates lagged features for a given DataFrame.

            Args:
                num_lags (int): Number of lags to create.

            Returns:
                A tuple of two lists: tminuses and volumes, where tminuses contains
                the names of the tminus columns and volumes contains the names of
                the volume columns.
            """
            tminuses = [f'tminus_{i}' for i in range(1, num_lags + 1)]
            volumes = [f'vol_{i}' for i in range(1, num_lags + 1)]

            for lag in range(1, num_lags + 1):
                df[f'tminus_{lag}'] = df.change.shift(lag)
                df[f'vol_{lag}'] = df.volume.shift(lag)

            return tminuses + volumes

        # Clean data
        df.rename(columns={'timestamp': 'Time'}, inplace=True)

        df.Time = df.Time.astype(int)
        df.open = df.open.astype(float)
        df.close = df.close.astype(float)
        df.high = df.high.astype(float)
        df.low = df.low.astype(float)
        df.volume = df.volume.astype(float)

        df['change'] = df.close.pct_change()

        # Generate lagged features
        lagged()

        # Calculate EMA and EMA difference
        df['ema12'] = df.close.ewm(span=12).mean()
        df['ema12_diff'] = df[['ema12', 'close']].pct_change(axis=1)['close'] * 100.0
        df.ema12_diff = df.ema12_diff.shift(1)

        df.dropna(inplace=True)

        df['signal'] = np.where(df.change > 0, True, False)

        ind_vars = df[['tminus_1', 'tminus_2', 'tminus_3', 'vol_1', 'vol_2', 'vol_3', 'ema12_diff']]

        model = jb.load('assets/model.pkl')
        df['prediction'] = list(model.predict(ind_vars))

        derivatives = pd.DataFrame(
            [{
                'late_close': df.close.values[-1],
                'late_ema': df.ema12.values[-1],
                'late_signal': df.prediction.values[-1],
                'max_high': df.high.idxmax(),
                'min_low': df.low.idxmin(),
                'max_close': df.close.idxmax(),
                'min_close': df.close.idxmin(),
                'avg_close': df.close.mean()
            }]
        )

        return df, derivatives
    except Exception as ex:
        print(ex)


def accounting():
    try:
        transactions = get(
            'https://api.luno.com/api/1/accounts/5177208153100163675/transactions?min_row=1&max_row=2',
            auth=(api_key_id, api_key_secret),
        ).json()['transactions']

        description = transactions[0]['description']

        balance = get(
            f'https://api.luno.com/api/1/balance?assets=XBT&assets=ETH&assets=ZAR',
            auth=(api_key_id, api_key_secret),
        ).json()['balance']

        df = pd.DataFrame(
            [{
                'description': description,
                'xbt': balance[0]['balance'],
                'eth': balance[2]['balance'],
                'zar': balance[-1]['balance']
            }]
        )

        return df
    except Exception as ex:
        print(ex)


def post_market_order(late_signal, counter=None, base=None):
    late_signal = 'BUY' if late_signal else 'SELL'
    volume = f'&counter_volume={counter}' if late_signal else f'&base_volume={base}'

    try:
        res_json = post(
            f'https://api.luno.com/api/1/marketorder?pair=XBTZAR&type={late_signal}{volume}',
            auth=(api_key_id, api_key_secret),
        ).json()
        return res_json['error'] if 'error' in res_json else res_json['order_id']
    except Exception as error:
        return error


if __name__ == '__main__':
    xbtzar_df, xbtzar_deriv = cleaning('XBTZAR')
    accounts = accounting()

    print(
        post_market_order(
            xbtzar_deriv.late_signal[0],
            counter=accounts.zar[0],
            base=accounts.xbt[0]
        )
    )
