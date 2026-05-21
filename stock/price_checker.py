from alpha_vantage.timeseries import TimeSeries
from pykrx import stock
from datetime import datetime, timedelta
import pandas as pd
from settings import ALPHA_VANTAGE_API_KEY
import config
import time
from utils.enums import Market

class PriceChecker:
    def __init__(self):
        self._api_key = ALPHA_VANTAGE_API_KEY
        self.symbols = config.STOCK_SYMBOLS
        self.threshold = config.ALERT_THRESHOLD

    def _get_krx_close_prices(self) -> dict[str, dict | None]:
        '''pykrx로 국내 주식 종가 조회'''
        result = {}
        today = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=7)).strftime('%Y%m%d') # 공휴일 버퍼 포함

        for i, symbol in enumerate(self.symbols.get('KRX', [])):
            try:
                df = stock.get_market_ohlcv(start_date, today, symbol)
                
                result[symbol] = {
                    'yesterday_date': df.index[-1].strftime('%Y-%m-%d'),
                    'yesterday_close':    df.iloc[-1]['종가'],
                    'two_days_ago_close': df.iloc[-2]['종가']
                }
            except Exception as e:
                print(f'{symbol} KRX 조회 실패: {e}')
                result[symbol] = None
            
            if i < len(symbol) - 1:
                time.sleep(12)

        return result

    def _get_us_close_prices(self) -> dict[str, dict : None]:
        '''Alpha Vantage로 미국 주식 종가 조회'''
        result = {}
        ts = TimeSeries(key=self._api_key, output_format='pandas')

        for i, symbol in enumerate(self.symbols.get('US', [])):
            try:
                data, _ = ts.get_daily(symbol=symbol, outputsize='compact')
                data.index = pd.to_datetime(data.index)
                data = data.sort_index(ascending=False)

                result[symbol] = {
                    'yesterday_date': data.index[0].strftime('%Y-%m-%d'),
                    'yesterday_close':    data.iloc[0]['4. close'],
                    'two_days_ago_close': data.iloc[1]['4. close']
                }
            except Exception as e:
                print(f'{symbol} US 조회 실패: {e}')
                result[symbol] = None

            if i > 0:
                time.sleep(12)

        return result

    @staticmethod
    def _calc_change_rate(prev: float, curr: float) -> float:
        if prev == 0:
            return 0.0
        
        return ((curr - prev) / prev) * 100

    def get_change_rate(self, market) -> dict:
        '''각 종목의 임계값 계산'''
        close_prices = self._get_krx_close_prices() if market == Market.KRX else self._get_us_close_prices()
        result = {}

        for symbol, data in close_prices.items():
            if data is None:
                result[symbol] = None
                continue

            curr = float(data['yesterday_close'])
            prev = float(data['two_days_ago_close'])

            result[symbol] = {
                'date': data['yesterday_date'],
                'change_rate': self._calc_change_rate(prev, curr)
            }

        return result
    
    def is_above_volatility_threshold(self) -> dict:
        '''각 종목의 임계값(예: ±5%) 초과 여부 반환'''
        change_rates = self.get_change_rate()
        result = {}

        for symbol, data in change_rates.items():
            if data is None:
                result[symbol] = {'is_alert': False}
                continue

            rate = data['change_rate']
            result[symbol] = {
                'date': data['yesterday_date'],
                'is_alert': abs(rate) >= self.threshold
            }

        return result
            
