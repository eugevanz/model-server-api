import pandas as pd
import numpy as np
from requests import get
import time
from dotenv import load_dotenv
from os import getenv
import joblib as jb
import psycopg2 as psql

load_dotenv()
api_key_id = getenv('LUNO_API_KEY_ID')
api_key_secret = getenv('LUNO_API_KEY_SECRET')

since = int(time.time() * 1000) - 3 * 60 * 59 * 1000
duration = 300


def get_candles(pair):
    conn = None
    cur = None

    try:
        conn = psql.connect(
            host=getenv('RENDER_SQL_HOST'),
            database=getenv('RENDER_SQL_DATABASE'),
            user=getenv('RENDER_SQL_USER'),
            password=getenv('RENDER_SQL_PASS')
        )
        cur = conn.cursor()

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

        ind_vars = df[['tminus_1', 'tminus_2', 'tminus_3', 'vol_1', 'vol_2', 'vol_3', 'ema12_diff']]

        model = jb.load('assets/model.pkl')
        df['prediction'] = list(model.predict(ind_vars))

        add_dataset_script = '''
            create table if not exists Candles (
                Time int, 
                open varchar(255),
                close varchar(255),
                high varchar(255),
                low varchar(255),
                volume varchar(255),
                change varchar(255),
                ema12 varchar(255),
                ema12_diff varchar(255),
                signal varchar(255),
                tminus_1 varchar(255),
                tminus_2 varchar(255),
                tminus_3 varchar(255),
                vol_1 varchar(255),
                vol_2 varchar(255),
                vol_3 varchar(255),
                prediction varchar(255)
            )
        '''
        cur.execute(add_dataset_script)
        conn.commit()
        # supabase.table(
        #     'xbt_modelled_dataset' if pair == 'XBTZAR' else 'eth_modelled_dataset'
        # ).upsert(df.to_dict('records')).execute()

        late_close = df.close.tolist()[-1]
        late_ema = df.ema12.tolist()[-1]
        late_signal = df.prediction.tolist()[-1] and (late_ema > late_close)

        max_high = df.high.idxmax()
        min_low = df.low.idxmin()
        max_close = df.close.idxmax()
        min_close = df.close.idxmin()
        avg_close = df.close.mean()

        # data, _ = supabase.table(
        #     'xbt_aggregated_text' if pair == 'XBTZAR' else 'eth_aggregated_text'
        # ).upsert(
        #     {
        #         'late_close': late_close, 'late_ema': late_ema,
        #         'late_signal': late_signal, 'max_high': max_high, 'min_low': min_low,
        #         'max_close': max_close, 'min_close': min_close, 'avg_close': avg_close
        #     }
        # ).execute()

        # return f'{pair} has {len(data)} records'
    except Exception as e:
        print(e)
    finally:
        if cur is not None:
            cur.close()
        if conn is not None:
            conn.close()


if __name__ == '__main__':
    print(f'XBTZAR count - : {get_candles("XBTZAR")}\nETHZAR count - : {get_candles("ETHZAR")}')
