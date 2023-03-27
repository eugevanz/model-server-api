import time
from os import getenv

import joblib as jb
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from requests import get
from sqlalchemy import create_engine, text

load_dotenv()
api_key_id = getenv('LUNO_API_KEY_ID')
api_key_secret = getenv('LUNO_API_KEY_SECRET')

since = int(time.time() * 1000) - 3 * 60 * 59 * 1000
duration = 300


def cleaning(pair):
    res_json = get(
        f'https://api.luno.com/api/exchange/1/candles?pair={pair}&duration=300&since={since}',
        auth=(api_key_id, api_key_secret),
    ).json()['candles']
    df = pd.DataFrame(res_json)

    def lagged():
        tminuses = []
        volumes = []
        for x in range(1, 4):
            df[f'tminus_{str(x)}'] = df.change.shift(x)
            df[f'vol_{str(x)}'] = df.volume.shift(x)
            tminuses.append(f'tminus_{str(x)}')
            volumes.append(f'vol_{str(x)}')

        return tminuses + volumes

    df.rename(columns={'timestamp': 'Time'}, inplace=True)

    df.Time = df.Time.astype(int)
    df.open = df.open.astype(float)
    df.close = df.close.astype(float)
    df.high = df.high.astype(float)
    df.low = df.low.astype(float)
    df.volume = df.volume.astype(float)

    df['change'] = df.close.pct_change()

    lagged()

    df['ema12'] = df.close.ewm(span=12).mean()
    df['ema12_diff'] = df[['ema12', 'close']].pct_change(axis=1)['close'] * 100.0
    df.ema12 = df.ema12.apply(np.floor)

    df.dropna(inplace=True)

    df['signal'] = np.where(df.change > 0, True, False)

    ind_vars = df[['tminus_1', 'tminus_2', 'tminus_3', 'vol_1', 'vol_2', 'vol_3', 'ema12_diff']]

    model = jb.load('assets/model.pkl')
    df['prediction'] = list(model.predict(ind_vars))

    derivatives = pd.DataFrame(
        [{
            'late_close': df.close.tolist()[-1],
            'late_ema': df.ema12.tolist()[-1],
            'late_signal': df.prediction.tolist()[-1] and (df.ema12.tolist()[-1] < df.close.tolist()[-1]),
            'max_high': df.high.idxmax(),
            'min_low': df.low.idxmin(),
            'max_close': df.close.idxmax(),
            'min_close': df.close.idxmin(),
            'avg_close': df.close.mean()
        }]
    )

    return df, derivatives


def add_to_database(df, tbl_name):
    status = 'add_to_database FAILED'
    try:
        # Create the SQLAlchemy engine
        engine = create_engine(getenv('RENDER_SQL_EXT'), echo=True, future=True)
        # Define the query to insert data into the table
        cursor_result = df.to_sql(tbl_name, con=engine, if_exists='replace', index=False)
        status = f'add_to_database Succeeded!, {cursor_result}'
    except Exception as error:
        print(error)

    return status


if __name__ == '__main__':
    xbtzar_df, xbtzar_deriv = cleaning('XBTZAR')
    ethzar_df, ethzar_deriv = cleaning('ETHZAR')

    print(add_to_database(xbtzar_df, 'xbtzar_df'))
    print(add_to_database(ethzar_df, 'ethzar_df'))
    print(add_to_database(xbtzar_deriv, 'xbtzar_deriv'))
    print(add_to_database(ethzar_deriv, 'ethzar_deriv'))

    # print(select_db('select * from xbtzar_df'))
    # print(select_db('select * from ethzar_df'))
    # print(select_db('select * from xbtzar_deriv'))
    # print(select_db('select * from ethzar_deriv'))
