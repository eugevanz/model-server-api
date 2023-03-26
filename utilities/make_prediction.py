import time
from os import getenv

# import joblib as jb
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from requests import get
from sqlalchemy import create_engine
from sqlalchemy.sql import text
# import sqlite3

# import make_tables

load_dotenv()
api_key_id = getenv('LUNO_API_KEY_ID')
api_key_secret = getenv('LUNO_API_KEY_SECRET')

since = int(time.time() * 1000) - 3 * 60 * 59 * 1000
duration = 300

# Create the SQLAlchemy engine
engine = create_engine(getenv('RENDER_SQL_EXT'), echo=True)


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
    # df.set_index('Time', inplace=True)

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

    # ind_vars = df[['tminus_1', 'tminus_2', 'tminus_3', 'vol_1', 'vol_2', 'vol_3', 'ema12_diff']]

    # model = jb.load('assets/model.pkl')
    # df['prediction'] = list(model.predict(ind_vars))

    derivatives = pd.DataFrame(
        {
            'late_close': [df.close.tolist()[-1]],
            'late_ema': [df.ema12.tolist()[-1]],
            # 'late_signal': [df.prediction.tolist()[-1] and (late_ema > late_close)],
            'max_high': [df.high.idxmax()],
            'min_low': [df.low.idxmin()],
            'max_close': [df.close.idxmax()],
            'min_close': [df.close.idxmin()],
            'avg_close': [df.close.mean()]
        }
    )

    return df, derivatives


def add_to_database(pair):
    df, derivatives = cleaning(pair)
    # Write the dataframe to the tables
    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        df.to_sql(pair, con=conn, if_exists='append', index=False)
        derivatives.to_sql(pair + 'deriv', con=conn, if_exists='append', index=False)


def select_db(pair):
    # Define the query to select data from the table
    with engine.connect().execution_options(autocommit=True) as conn:
        # derivatives = pd.read_sql(text(f'''SELECT * FROM {pair}deriv'''), con=conn)
        candles = pd.read_sql(text(f'''SELECT * FROM {pair}'''), con=conn)
        # print(derivatives)
        print(candles)


if __name__ == '__main__':
    try:
        # make_tables.create(engine)
        # add_to_database('XBTZAR')
        add_to_database('ETHZAR')
        # select_db('XBTZAR')
        select_db('ETHZAR')
    except Exception as e:
        print(e)
    finally:
        engine.dispose()
