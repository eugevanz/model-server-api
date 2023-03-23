import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
import numpy as np
from sklearn.model_selection import GridSearchCV
import joblib as jb

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
candles.ema12 = candles.ema12.astype(float)
candles.ema12_diff = candles.ema12_diff.astype(float)
candles.signal = candles.signal.astype(bool)

ind_vars = candles[['tminus_1', 'tminus_2', 'tminus_3', 'vol_1', 'vol_2', 'vol_3', 'ema12_diff']]
dep_vars = candles.signal

ind_train, ind_test, dep_train, dep_test = train_test_split(
    ind_vars, dep_vars, test_size=0.3, shuffle=False
)

estimator = GridSearchCV(
    LogisticRegression(),
    param_grid=[{
        'penalty': ['l1', 'l2', 'elasticnet', None],
        'C': np.logspace(-4, 4, 20),
        'solver': ['lbfgs', 'newton-cg', 'liblinear', 'sag', 'saga'],
        'max_iter': [100, 1000, 2500, 5000]
    }],
    cv=3,
    verbose=True,
    n_jobs=-1
).fit(ind_train, dep_train)

print(f'Accuracy - {(estimator.score(ind_test, dep_test) * 100.0):.2f}')
jb.dump(estimator.best_estimator_, 'assets/model.pkl')
