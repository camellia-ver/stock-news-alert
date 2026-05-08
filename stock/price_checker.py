from alpha_vantage.timeseries import TimeSeries
from datetime import datetime, timedelta
import pandas as pd
import settings
import config
import time

class PriceChecker():
    def __init__(self):
        self.api_key = settings.ALPHA_VANTAGE_API_KEY
        self.symbols = config.STOCK_SYMBOLS
        self.threshold = config.ALERT_THRESHOLD

    def get_close_price(self):
        ts = TimeSeries(key= self.api_key, output_format='pandas')

        result = {}

        for i, symbol in enumerate(self.symbols):
            try:
                data, meta = ts.get_daily(symbol=symbol, outputsize='compact')
                data.index = pd.to_datetime(data.index)
                data = data.sort_index(ascending=False)

                result[symbol] = {
                    'yesterday_close': data.iloc[0]['4. close'],
                    'two_days_ago_close': data.iloc[1]['4. close']
                }
            except Exception as e:
                print(f'{symbol} 데이터 조회 실패: {e}')
                result[symbol] = None

            if i > 0:
                    time.sleep(12)

        return result

    def calc_change_rate(self, prev, curr):
        return ((curr - prev) / prev) * 100

    def get_change_rate(self):
        close_prices = self.get_close_price()
        change_rate = {}

        for symbol, data in close_prices.items():
            if data is None:
                change_rate[symbol] = None
                continue

            yesterday = float(data['yesterday_close'])
            two_day_ago = float(data['two_days_ago_close'])

            change_rate[symbol] = {'change_rate': self.calc_change_rate(two_day_ago, yesterday)}

        return change_rate
    
    def is_above_volatility_threshold(self):
        change_rates = self.get_change_rate()

        result = {}

        for symbol, data in change_rates.items():
            rate = data['change_rate'] if data else None
            result[symbol] = {'is_alert_news': abs(rate) > self.threshold if rate is not None else False}

        return result
            