# price_checker.py
import time
from datetime import datetime, timedelta

from pykrx import stock
import FinanceDataReader as fdr

import config
from settings import ALPHA_VANTAGE_API_KEY
from utils.enums import Market
from utils.logger import get_logger

logger = get_logger(__name__)

class PriceChecker:
    def __init__(self):
        self.stock_tickers = config.STOCK_TICKERS
        self.threshold = config.ALERT_THRESHOLD

    def _get_krx_close_prices(self) -> dict[str, dict | None]:
        result = {}

        today = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=7)).strftime('%Y%m%d')

        for ticker, name in self.stock_tickers.get('KRX', {}).items():
            try:
                df = stock.get_market_ohlcv(
                    start_date,
                    today,
                    ticker
                )

                if df.empty:
                    logger.warning("[%s] 데이터가 없습니다.", ticker)
                    continue

                if len(df) < 2:
                    logger.warning("[%s] 데이터가 부족합니다.", ticker)
                    continue

                result[name] = {
                    'yesterday_date': df.index[-1].strftime('%Y-%m-%d'),
                    'yesterday_close': df.iloc[-1]['종가'],
                    'two_days_ago_close': df.iloc[-2]['종가']
                }

                logger.debug(
                    "%s KRX 조회 완료 (종가: %s)",
                    name,
                    result[name]['yesterday_close']
                )

            except Exception as e:
                logger.error(
                    "%s(%s) KRX 조회 실패: %s",
                    name,
                    ticker,
                    e,
                    exc_info=True
                )

                result[name] = None

            time.sleep(1)

        return result

    def _get_us_close_prices(self) -> dict[str, dict | None]:
        '''FinanceDataReader로 미국 주식 종가 조회'''
        result = {}

        # 최근 영업일 포함 넉넉하게 조회 (주말/공휴일 대비 10일)
        start_date = (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d')

        for ticker, name in self.stock_tickers.get('US', {}).items():
            try:
                df = fdr.DataReader(ticker, start_date)

                if df.empty or len(df) < 2:
                    raise ValueError(f'데이터 부족 (rows={len(df)})')

                latest_two = df.sort_index(ascending=False).iloc[:2]
                yesterday = latest_two.index[0]
                two_days_ago = latest_two.index[1]

                result[name] = {
                    'yesterday_date': yesterday,
                    'yesterday_close': float(latest_two.loc[yesterday]['Close']),
                    'two_days_ago_close': float(latest_two.loc[two_days_ago]['Close'])
                }

                logger.debug("%s US 조회 완료 (종가: %s)", name, result[name]['yesterday_close'])
            except Exception as e:
                logger.error("%s US 조회 실패: %s", name, e, exc_info=True)
                result[name] = None
            
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
    
    def is_above_volatility_threshold(self, market) -> dict:
        '''각 종목의 임계값(예: ±5%) 초과 여부 반환'''
        change_rates = self.get_change_rate(market)
        result = {}

        for symbol, data in change_rates.items():
            if data is None:
                continue

            rate = data['change_rate']
            if abs(rate) >= self.threshold:
                logger.warning(
                    "%s 변동률 임계값 초과: %.2f%% (기준: ±%.1f%%)",
                    symbol, rate, self.threshold
                )
                result[symbol] = {'date': data['date'], 'rate': rate}

        return result
            
