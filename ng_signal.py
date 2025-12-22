import yfinance as yf
import pandas as pd
from ta import add_all_ta_features
from ta.utils import dropna
from twilio.rest import Client
from ng_signal import data, strat
from datetime import datetime
import os
import dotenv

dotenv.load_dotenv()

sid, token = os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN")

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

def msg():

    print("Checking technical signals for Natural Gas...")
    try:
        # Get latest signal
        df_data = data('NG=F')
        signals = strat(df_data)
        
        active_signal = None
        if signals['buy_1']: active_signal = "STRONGLY BUY"
        elif signals['sell_1']: active_signal = "STRONGLY SELL"
        elif signals['buy_0.5']: active_signal = "MODERATELY BUY"
        elif signals['sell_0.5']: active_signal = "MODERATELY SELL"

        if not active_signal:
            print("No actionable signal detected in ng_signal.py logic.")
            return

        print(f"Signal detected: {active_signal}. Sending WhatsApp notification...")

        client = Client(sid, token)

        # Get current time for the message
        now = datetime.now().strftime("%H:%M")
        today = datetime.now().strftime("%d/%m")

        message = client.messages.create(
            from_='whatsapp:+14155238886',
            content_sid='HXb5b62575e6e4ff6129ad7c8efe1f983e',
            content_variables=f'{{"1":"{active_signal}","2":"{now} on {today}"}}',
            to='whatsapp:+917828374376'
        )

        print(f"Message sent successfully! SID: {message.sid}")
    except Exception as e:
        print(f"Error in msg() notification logic: {e}")

if __name__ == "__main__":
  msg()