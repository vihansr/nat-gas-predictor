import yfinance as yf
import pandas as pd
from ta import add_all_ta_features
from ta.utils import dropna

def data(tick, period="60d", invl="15m"):
  cols = ['Open', 'High', 'Low', 'Close', 'volatility_bbm', 'volatility_bbh', 'volatility_bbl', 'volume_vwap', 'momentum_rsi', 'ema_100']

  ticker = yf.Ticker(tick)
  data = ticker.history(period=period, interval=invl)

  df = pd.DataFrame(data)
  df = add_all_ta_features(
      df, open="Open", high="High", low="Low", close="Close", volume="Volume"
  )

  df.index = df.index.tz_convert('Asia/Kolkata')
  df['ema_100'] = df['Close'].ewm(span=100, adjust=False).mean()

  df = df[cols].iloc[-1]

  return df

def strat(df):
  o,h,l,c = df['Open'], df['High'], df['Low'], df['Close']
  bbl, bbm, bbh = df['volatility_bbl'], df['volatility_bbm'], df['volatility_bbh']
  vwap, ema = df['volume_vwap'], df['ema_100']
  rsi = df['momentum_rsi']

  df['buy_condition_1'] = (c > bbl) & (l <= bbl) & (c < vwap) & (c < ema) & (rsi < 50)
  df['sell_condition_1'] = (c < bbl) & (l >= bbl) & (c > vwap) & (c > ema) & (rsi > 50)

  df['buy_condition_0.5'] = (c > bbm) & (l <= bbm) & (c < vwap) & (rsi < 50)
  df['sell_condition_0.5'] = (c < bbm) & (l >= bbm) & (c > vwap) & (rsi > 50)

  signal = {
      'buy_1': bool(df['buy_condition_1']),
      'sell_1': bool(df['sell_condition_1']),
      'buy_0.5': bool(df['buy_condition_0.5']),
      'sell_0.5': bool(df['sell_condition_0.5']),
  }

  return signal

d = strat(data('NG=F'))
print(d)