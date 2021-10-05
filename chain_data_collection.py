import pandas as pd
from yahoo_fin import options
from yahoo_fin import stock_info as yf
import os

file = open("liquid_symbols.txt" , "r")
symbols = list(file)
# this makes it so the list is properly formatted? 
symbols = symbols[0].split(' ')
symbols.pop(len(symbols)-1)
symbols.pop(len(symbols)-1)
symbols.append('TSLA')
symbols.append('SPY')
symbols.append('QQQ')
file2 = open("error_tickers_for_chain(10-5-2021).txt","w+")

# let the data collection begin...
for ticker in symbols:
    try:
        print(f'COLLECTING DATA FOR ---------- {ticker}')
        exp_dates = options.get_expiration_dates(ticker)
        if len(exp_dates) < 1:
            print (f"EMPTY EXPIRATION DATES FOR --- {ticker}")
        #print (exp_dates)
        for date in exp_dates:
            chain = options.get_options_chain(ticker, date)
            calls = pd.DataFrame.from_dict(chain['calls'])
            puts = pd.DataFrame.from_dict(chain['puts'])
            calls.to_csv(f'D:\Options Data\{ticker}\ 10-5-2021_option_chain_calls_{date}.csv')
            puts.to_csv(f'D:\Options Data\{ticker}\ 10-5-2021_option_chain_puts_{date}.csv')
    except:
        print (f'ERROR -------------------------------------------------------------------- {ticker}')
        file2.write(f'{ticker}\n')

#CSV FILE FORMAT = (date collected)_option_chain_(puts or calls)_(option chain expiration date)

file.close()
file2.close()