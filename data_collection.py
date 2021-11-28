from genericpath import exists
from requests.api import get
import yahoo_fin.stock_info as si 
import pandas as pd 
from tda import auth, client 
import json, config, os, time 
import datetime
import os.path 
from os import path

# establish td ameritrade api connection 
token_path = config.token_path
api_key = config.api_key
redirect_uri = config.redirect_url
c = auth.client_from_token_file(token_path, api_key)
# create daily report text file


def get_current_date():
    # returns the current date in '10-12-2021' format
    current_date = str(datetime.datetime.now()).split(' ')[0]
    current_date = current_date.split('-')
    current_date = current_date[1] + '-' + current_date[2] + '-' + current_date[0]
    return current_date

def sleep_until(intended_time):
    date = get_current_date()
    print (date)
    date_arr = date.split('-')
    year = int(date_arr[2])
    month = int(date_arr[0])
    day = int(date_arr[1])
    # intended_time string format = 9:00
    intended_arr = intended_time.split(':')
    intended_hours = int(intended_arr[0])
    intended_min = int(intended_arr[1])
    intended_time = datetime.datetime(year,month,day,intended_hours,intended_min,00,00)   
    now = datetime.datetime.now() 
    diff = str(intended_time - now)
    diff_arr = diff.split(':')
    hours = int(diff_arr[0])
    mins = int(diff_arr[1])
    sleep_time = (hours*60*60) + (mins*60) 
    print ('sleeping for ',sleep_time, ' seconds')
    time.sleep(sleep_time)

def get_er_within3():
    '''
    function will return a data frame which contains earnings report information
    for companies within 3 days of the current date
    '''
    print ("Fetching tickers that have an ER within 3 days of current date")
    current_date = datetime.date.today()
    start_range = current_date + datetime.timedelta(days=-3) # date 3 days before current day
    end_range = current_date + datetime.timedelta(days=3) # date 3 days after current day

    er_in_range = si.get_earnings_in_date_range(start_range,end_range) # dictionary with data
    df = pd.DataFrame(er_in_range)
    # add a column to the data frame the contains either 'AM' or 'PM' for the time of er
    am_or_pm = []
    for i in range(0,len(df)):
        hour = int(df.loc[i]['startdatetime'].split('T')[1].split(':')[0]) # the hour the er occurs at (0-23)
        if hour < 12:
            am_or_pm.append('AM')
        else:
            am_or_pm.append('PM')
    df['am_pm'] = am_or_pm  
    print ("Tickers Retrieved")
    return df

def get_er_tickers(df):
    # takes in a data frame, then returns a list of tickers that have an er within 3 days of the current date
    tickers = []
    for row in range(0,len(df)):
        tickers.append(df.loc[row]['ticker'])
    return tickers

def mkdirs(tickers):
    # function that makes the propery directories on my pc
    for ticker in tickers:
        if not os.path.exists(f'D:\IvCrushData\Options Data'):
            os.mkdir(f'D:\IvCrushData\Options Data')
        if not os.path.exists(f'D:\IvCrushData\ER_Daily_Data'):
            os.mkdir(f'D:\IvCrushData\ER_Daily_Data')
        if not os.path.exists(f'D:\IvCrushData\Stats'):
            os.mkdir(f'D:\IvCrushData\Stats')


def iter1():
    iter_1_start_time = time.time()
    # save data frame with er data for that day
    print ('Performing Iteration #1')
    er_data = get_er_within3()
    er_data.to_csv(f'D:\IvCrushData\ER_Daily_Data\{get_current_date()} report.csv')

    # collect option data 5 times a day, equal time intervals
    # datetime.datetime.now() returns the time in CST 
    # market opens at 8:30 am CST, closes at 3:00 pm CST -- market is open for 6 hours and 30 minutes (390 minutes)
    # so, collect data 30 minutes after open and 30 minutes before close, then equal intervals between (330/5)
    # start collection at 9 AM, collect option data every 80 minutes until 2:30 pm

    # separate liquid tickers from illiquid 
    print ("Creating New Data Frames")
    temp_symbols = get_er_tickers(er_data)
    symbols = []
    excluded = []
    for ticker in temp_symbols:
        try:
            test_chain = c.get_option_chain(ticker).json()
            time.sleep(0.35)
            if test_chain['status'] == 'SUCCESS':
                symbols.append(ticker)
            else:
                excluded.append(ticker)
        except:
            print (f'problem with {ticker}')
    

    # get a list of new tickers (no data collected yet)
    new_tickers = []
    exists_tickers = []
    for ticker in symbols:
        if not path.exists(f'D:\IvCrushData\Options Data\{ticker}_chain.csv'):
            new_tickers.append(ticker)
        else:
            exists_tickers.append(ticker)


    # write list of tickers to report file
    reportf = open(f"D:\IvCrushData\Reports\ report_{get_current_date()}.txt",'a')
    reportf.write(f'Tickers Included: \n{symbols}')
    reportf.write(f'\n\nTickers Excluded: \n{excluded}')
    reportf.write(f'\n\nNew Tickers: \n{new_tickers}')
    reportf.close()

    current_date = get_current_date()
    # initial iteration
    # --------------------------- factor in for already existing data frame
    # --------------------------- also, if there is an error with api, sleep for longer
    for ticker in new_tickers:
        chain = c.get_option_chain(ticker).json()
        time.sleep(0.35) # so api call limit ins't surpassed
        temp_exp = list(chain['callExpDateMap'].keys())[0]
        temp_strike = list(chain['callExpDateMap'][temp_exp].keys())[0]
        df = pd.DataFrame.from_dict(chain['callExpDateMap'][temp_exp][temp_strike])
        # collect call data and save in data frame
        for exp_date in chain['callExpDateMap']:
            temp_date = exp_date.split(':')[0]
            for strike in chain['callExpDateMap'][exp_date]:
                # set call data to call var
                call = list(chain['callExpDateMap'][exp_date][strike][0].values())
                # assign last row of data frame to call 
                df.loc[len(df)] = call 
        # collect put data and save in same data frame
        for exp_date in list(chain['putExpDateMap'].keys()):
            for strike in list(chain['putExpDateMap'][exp_date].keys()):
                put = list(chain['putExpDateMap'][exp_date][strike][0].values())
                df.loc[len(df)] = put 
        iter_num = []
        for i in range(len(df)):
            iter_num.append(1)
        df['iter_num'] = iter_num 
        current_dates = []
        for i in range(len(df)):
            current_dates.append(current_date)
        df['current_date'] = current_dates
        df.to_csv(f'D:\IvCrushData\Options Data\{ticker}_chain.csv')
        
    print ("New Data Frame Creation Complete")
    print ("Collecting Data For Existing Tickers")
    for ticker in exists_tickers:
        chain = c.get_option_chain(ticker).json()
        time.sleep(0.35)
        df = pd.read_csv(f'D:\IvCrushData\Options Data\{ticker}_chain.csv')
        for exp_date in chain['callExpDateMap']:
            temp_date = exp_date.split(':')[0]
            for strike in chain['callExpDateMap'][exp_date]:
                # set call data to call var
                call = list(chain['callExpDateMap'][exp_date][strike][0].values())
                call.append(1)
                call.append(current_date)
                # assign last row of data frame to call 
                df.loc[len(df)] = call 
        # collect put data and save in same data frame
        for exp_date in list(chain['putExpDateMap'].keys()):
            for strike in list(chain['putExpDateMap'][exp_date].keys()):
                put = list(chain['putExpDateMap'][exp_date][strike][0].values())
                put.append(1)
                put.append(current_date)
                df.loc[len(df)] = put


        df.to_csv(f'D:\IvCrushData\Options Data\{ticker}_chain.csv')
    print ("Existing Ticker Collection Complete")
    
    # initial iteration complete, now calculate time until next iteration, repeat 4x

    print ("Completed Iteration #1")
    iter_1_end_time = time.time()
    iter_1_duration = iter_1_end_time - iter_1_start_time 
    reportf2 = open(f"D:\IvCrushData\Reports\ report_{get_current_date()}.txt",'a')
    reportf2.write(f"\n\nIteration #1 Duration = {iter_1_duration}")
    reportf2.close()
    return symbols 

# make it so iteration num and date collected can be added to data frame 
def iter_2to5(symbols,iter_num):
    iter_duration_start = time.time()
    print (f"Performing Iteration #{iter_num}")
    current_date = get_current_date()
    for ticker in symbols:
        time.sleep(0.35) # so I don't surpass api call limit
        df = pd.read_csv(f'D:\IvCrushData\Options Data\{ticker}_chain.csv')
        df.drop('Unnamed: 0',inplace=True,axis=1)
        chain = c.get_option_chain(ticker).json()
        for exp_date in chain['callExpDateMap']:
            for strike in chain['callExpDateMap'][exp_date]:
                # set call data to call var
                call = list(chain['callExpDateMap'][exp_date][strike][0].values())
                call.append(iter_num)
                call.append(current_date)
                # assign last row of data frame to call 
                df.loc[len(df)] = call 
        # collect put data and save in same data frame
        for exp_date in list(chain['putExpDateMap'].keys()):
            for strike in list(chain['putExpDateMap'][exp_date].keys()):
                put = list(chain['putExpDateMap'][exp_date][strike][0].values())
                put.append(iter_num)
                put.append(current_date)
                df.loc[len(df)] = put
        # create an extra column for the iteration that data was collected for 


        df.to_csv(f'D:\IvCrushData\Options Data\{ticker}_chain.csv')
    print (f"Completed Iteration #{iter_num}")
    iter_duration = time.time() - iter_duration_start
    reportf2 = open(f"D:\IvCrushData\Reports\ report_{get_current_date()}.txt",'a')
    reportf2.write(f'iteration #{iter_num} duration = {iter_duration}')
    reportf2.close()



def get_stats(symbols):
    print ("Collecting Stats")
    for ticker in symbols:
        stats = si.get_stats(ticker)
        stats.to_csv(f'D:\IvCrushData\Stats\{ticker}_stats_{get_current_date()}.csv')
    print ("Stats Collection Complete")


# collect data at:
# 9:00 am - iter 1
# 10:20 am - iter 2
# 11:40 am - iter 3
# 1:00 pm - iter 4
# 2:25 pm (get stats too) - iter 5



sleep_until('9:00')
symbols = iter1()
sleep_until('10:20')
iter_2to5(symbols,2)
sleep_until('11:40')
iter_2to5(symbols,3)
sleep_until('13:00')
iter_2to5(symbols,4)
sleep_until('14:25')
iter_2to5(symbols,5)
get_stats(symbols)
