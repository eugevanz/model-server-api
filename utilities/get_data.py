import pandas as pd
from requests import get
from dotenv import load_dotenv
from os import getenv

load_dotenv()
api_key_id = getenv('LUNO_API_KEY_ID')
api_key_secret = getenv('LUNO_API_KEY_SECRET')

start = int(pd.Timestamp('2022-01-01T12').timestamp()) * 1000
end = int(pd.Timestamp.now().timestamp()) * 1000

df_list = []
timestamp = start

while timestamp < end:
    res_json = get(
        f'https://api.luno.com/api/exchange/1/candles?pair=XBTZAR&duration=300&since={timestamp}',
        auth=(api_key_id, api_key_secret)
    ).json()['candles']
    df_list = df_list + res_json
    timestamp = timestamp + (5000 * 60000)
    print(timestamp)

print('Completed')
df = pd.DataFrame(df_list)
df.to_csv('assets/data.csv')
