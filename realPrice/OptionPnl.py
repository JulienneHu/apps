import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import requests
import time
from realPrice.realStock import get_realtime_stock_price
from realPrice.realOption import main as get_realtime_option_price

def get_historical_data(ticker, start_date):
    api_key = 'C6ig1sXku2yKl_XEIvSvc_OWCwB8ILLn'
    base_url = 'https://api.polygon.io/v2/aggs/ticker/'
    end_date = datetime.now()  

    ticker = f'O:{ticker}'
    if isinstance(start_date, datetime):
        start_date = start_date.strftime('%Y-%m-%d')

    url = f"{base_url}{ticker}/range/1/day/{start_date}/{end_date.strftime('%Y-%m-%d')}?apiKey={api_key}"

    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if 'results' in data:
            df = pd.DataFrame(data['results'])
            df['t'] = pd.to_datetime(df['t'], unit='ms')
            df['date'] = df['t'].dt.date  
            return df[['date', 'c']]
        else:
            print("No results found in the data.")
            return pd.DataFrame()  
    else:
        print(f"Failed to retrieve data: {response.status_code}")
        return None

def calls_or_puts(company, date, strike):
    options = [] 
    ticker = yf.Ticker(company)
    expiration_dates = ticker.options

    if date in expiration_dates:
        opts = ticker.option_chain(date)
        
        call_option = opts.calls[opts.calls['strike'] == strike]
        put_option = opts.puts[opts.puts['strike'] == strike]
        
        if not call_option.empty:
            call_option_names = call_option['contractSymbol'].tolist()
            options.extend(call_option_names)
            print(f"Call option(s) for strike price {strike} on {date}: {', '.join(call_option_names)}")
        else:
            print(f"No call option with a strike price of {strike} for {date}.")
            
        if not put_option.empty:
            put_option_names = put_option['contractSymbol'].tolist()
            options.extend(put_option_names)
            print(f"Put option(s) for strike price {strike} on {date}: {', '.join(put_option_names)}")
        else:
            print(f"No put option with a strike price of {strike} for {date}.")
    else:
        print(f"No options available for {date}.")
    return options

def get_stock_price(symbol, start_date, end_date):
    stock = yf.Ticker(symbol)
    hist = stock.history(start=start_date, end=end_date)
    hist.reset_index(inplace=True)
    hist['date'] = hist['Date'].dt.date
    hist.rename(columns={'Close': 'stock_close_price'}, inplace=True)
    hist['stock_close_price'] = hist['stock_close_price'].round(2)
    return hist[['date', 'stock_close_price']]

def main(company='AAPL', strike_date='2024-06-21', strike=180, trade_date='2024-05-02'):
    options = calls_or_puts(company, strike_date, strike)
    if options:
        data_frames = []
        for i, option in enumerate(options):
            price_data = get_historical_data(option, trade_date)
            time.sleep(1)
            if price_data is not None:
                if i == 0:
                    price_data.rename(columns={'c': 'call_close_price'}, inplace=True)
                else:    
                    price_data.rename(columns={'c': 'put_close_price'}, inplace=True)
                data_frames.append(price_data)
            else:
                print(f"Failed to retrieve data for option: {option}")

        if len(data_frames) == 2:
            df = pd.merge(data_frames[0], data_frames[1], on='date')
            
            # Get the stock price data
            start_date = datetime.strptime(trade_date, '%Y-%m-%d')
            end_date = datetime.now()
            stock_prices = get_stock_price(company, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
            df = pd.merge(df, stock_prices, on='date', how='left')
            print(df)
            
            # Get today's stock price, call price, and put price
            current_price = get_realtime_stock_price(company)[0]
            current_call_price = get_realtime_option_price(company, strike_date, strike)[0]
            current_put_price = get_realtime_option_price(company, strike_date, strike)[1]
            
            # Add today's data to the DataFrame
            df.loc[len(df)] = [datetime.now().date(), current_call_price, current_put_price, current_price]
            return df
        else:
            print("Could not retrieve data for one or more options.")
            return None
    else:
        print("No options found.")
        return None

