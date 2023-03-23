import pandas as pd
import numpy as np

candles = pd.read_csv('assets/data.csv')


def lagged():
    tminuses = []
    volumes = []
    for i in range(1, 4):
        candles[f'tminus_{str(i)}'] = candles.change.shift(i)
        candles[f'vol_{str(i)}'] = candles.volume.shift(i)
        tminuses.append(f'tminus_{str(i)}')
        volumes.append(f'vol_{str(i)}')

    return [tminuses + volumes]


candles.rename(columns={'timestamp': 'Time'}, inplace=True)
candles.set_index('Time', inplace=True)

candles.drop_duplicates()

candles.open = candles.open.astype(float)
candles.close = candles.close.astype(float)
candles.high = candles.high.astype(float)
candles.low = candles.low.astype(float)
candles.volume = candles.volume.astype(float)

candles['change'] = candles.close.pct_change()

lagged()

candles['ema12'] = candles.close.ewm(span=12).mean()
candles['ema12_diff'] = candles[['ema12', 'close']].pct_change(axis=1)['close'] * 100.0
candles.ema12 = candles.ema12.apply(np.floor)

candles.dropna(inplace=True)

candles['signal'] = np.where(candles.change > 0, True, False)

candles.to_csv('assets/model.csv')
