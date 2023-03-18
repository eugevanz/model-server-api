import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
import joblib as jb
from requests import get
import time

candles = pd.read_csv('assets/model.csv')
candles = candles.drop('Unnamed: 0', axis=1)

candles = candles.drop_duplicates()

candles.open = candles.open.astype(float)
candles.close = candles.close.astype(float)
candles.high = candles.high.astype(float)
candles.low = candles.low.astype(float)
candles.volume = candles.volume.astype(float)
candles.change = candles.change.astype(float)
candles.tminus_1 = candles.tminus_1.astype(float)
candles.tminus_2 = candles.tminus_2.astype(float)
candles.tminus_3 = candles.tminus_3.astype(float)
candles.vol_1 = candles.vol_1.astype(float)
candles.vol_2 = candles.vol_2.astype(float)
candles.vol_3 = candles.vol_3.astype(float)
candles.EMA12 = candles.EMA12.astype(float)

ind_vars = candles[['tminus_1', 'tminus_2', 'tminus_3', 'vol_1', 'vol_2', 'vol_3']]
dep_vars = candles.signal

model = LogisticRegression(class_weight='balanced')

ind_train, ind_test, dep_train, dep_test = train_test_split(
    ind_vars, dep_vars, test_size=0.3, shuffle=False
)

model.fit(ind_vars, dep_vars)

jb.dump(model, 'assets/model.pkl')
