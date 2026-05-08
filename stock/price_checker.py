from alpha_vantage.timeseries import TimeSeries
from datetime import datetime, timedelta
import pandas as pd
import settings
import time

class PriceChecker():
    def __init__(self):
        self.api_key = settings.ALPHA_VANTAGE_API_KEY

    def get_close_price(self, symbols):
        ts = TimeSeries(key= self.api_key, output_format='pandas')

        now = datetime.now()
        yesterday = (now - timedelta(days=1)).strftime('%Y-%m-%d')

        result = {}

        for i, symbol in enumerate(symbols):
            if i > 0:
                time.sleep(12)

            try:
                data, meta = ts.get_daily(symbol=symbol, outputsize='compact')
                data, index = pd.to_datetime(data.index)

                recent = data.loc[data.index <= yesterday].iloc[:2]

                result[symbol] = {
                    'yesterday_close': recent.iloc[0]['4. close'],
                    'two_days_ago_close': recent.iloc[1]['4. close']
                }
            except Exception as e:
                print(f'{symbol} 데이터 조회 실패: {e}')
                result[symbol] = None

        return result

    def calc_change_rate(prev, curr):
        return ((curr - prev) / prev) * 100

    def get_change_rate(self, symbols):
        pass