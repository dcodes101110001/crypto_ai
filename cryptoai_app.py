#!/usr/bin/env python3
# Converted from: 6_final_stock_selection.ipynb

# ============================================================================== 
# Cell 1
# ============================================================================== 

from platform import python_version
print(python_version())

# ============================================================================== 
# Cell 2
# ============================================================================== 

import pandas as pd
import numpy as np
import math
import pickle # get the ML model from other notebook
from matplotlib import pyplot as plt # scatter plot
import matplotlib.lines as mlines # plot

# ============================================================================== 
# Cell 3
# ============================================================================== 

# Set the plotting DPI settings to be a bit higher.
plt.rcParams['figure.figsize'] = [7.0, 4.5]
plt.rcParams['figure.dpi'] = 150

# ============================================================================== 
# Cell 4
# ============================================================================== 
# # get_x_y_raw_data

# ============================================================================== 
# Cell 5
# ============================================================================== 

def getYPriceDataNearDate(ticker, date, modifier, dailySharePrices):
    '''
    Return just the y price and volume.
    Take the first day price/volume of the list of days,
    that fall in the window of accepted days.
    'modifier' just modifies the date to look between.
    Returns a list.
    '''
    windowDays=5
    rows = dailySharePrices[
        (dailySharePrices["Date"].between(pd.to_datetime(date)
                                          + pd.Timedelta(days=modifier),
                                          pd.to_datetime(date)
                                          + pd.Timedelta(days=windowDays
                                                         +modifier)
                                         )
        ) & (dailySharePrices["Ticker"]==ticker)]
    
    if rows.empty:
        return [ticker, np.nan,
                np.datetime64('NaT'),
                np.nan]
    else:
        return [ticker, rows.iloc[0]["Open"],
                rows.iloc[0]["Date"],
                rows.iloc[0]["Volume"]*rows.iloc[0]["Open"]]

# ============================================================================== 
# Cell 6
# ============================================================================== 

def getYPricesReportDateAndTargetDate(x, d, modifier=365):
    '''
    Takes in all fundamental data X, all stock prices over time y,
    and modifier (days), and returns the stock price info for the
    data report date, as well as the stock price one year from that date
    (if modifier is left as modifier=365)
    '''
    # Preallocation list of list of 2 
    # [(price at date) (price at date + modifier)]
    y = [[None]*8 for i in range(len(x))] 
    
    whichDateCol='Publish Date'# or 'Report Date', 
    # is the performance date from->to. Want this to be publish date.
    
    # Because of time lag between report date
    # (which can't be actioned on) and publish date
    # (data we can trade with)
    
    # In the end decided this instead of iterating through index.
    # Iterate through a range rather than index, as X might not have
    # monotonic increasing index 1, 2, 3, etc.
    i=0
    for index in range(len(x)):
        y[i]=(getYPriceDataNearDate(x['Ticker'].iloc[index],
                                    x[whichDateCol].iloc[index],0,d)
              +getYPriceDataNearDate(x['Ticker'].iloc[index],
                                     x[whichDateCol].iloc[index],
                                     modifier, d))
        i=i+1
        
    return y

# ============================================================================== 
# Cell 7
# ============================================================================== 

def getYRawData2024(my_path = 'stock_data\\'):
    d=pd.read_csv(my_path + 'us-shareprices-daily.csv', delimiter=';')
    d["Date"]=pd.to_datetime(d["Date"])
    print('Stock Price data matrix is: ',d.shape)
    return d

# ============================================================================== 
# Cell 8
# ============================================================================== 

def getYPricesReportDate(X, d, modifier=365):
    '''
    Get the stock prices for our X matrix to create Market Cap. column later.
    '''
    i=0
    y = [[None]*8 for i in range(len(X))] # Preallocation list of list of 2 [(price at date) (price at date + modifier)]
    whichDateCol='Publish Date'# or 'Report Date', is the performance date from->to. Want this to be publish date.
    # Because of time lag between report date (which can't be actioned on) and publish date (data we can trade with)
    for index in range(len(X)):
        y[i]=getYPriceDataNearDate(X['Ticker'].iloc[index], X[whichDateCol].iloc[index], 0, d)
        i=i+1
    return y

def getXFullDataMerged(myLocalPath='stock_data\\'):
    '''
    For combining fundamentals financial data from SimFin+ only,
    without API. 
    Download Income Statement, Balance Sheet and Cash Flow files,
    the -full versions, e.g. us-balance-annual-full.csv.
    Place in a directory and give the directory path to the function.
    Assumes standard filenames from SimFin.
    Returns a DataFrame of the combined result. 
    Prints file infos.
    '''
    incomeStatementData=pd.read_csv(myLocalPath+'us-income-annual-full-asreported.csv',
                                    delimiter=';')
    balanceSheetData=pd.read_csv(myLocalPath+'us-balance-annual-full-asreported.csv',
                                 delimiter=';')
    CashflowData=pd.read_csv(myLocalPath+'us-cashflow-annual-full-asreported.csv',
                             delimiter=';')
    
    print('Income Statement CSV data is(rows, columns): ',
          incomeStatementData.shape)
    print('Balance Sheet CSV data is: ',
          balanceSheetData.shape)
    print('Cash Flow CSV data is: ' ,
          CashflowData.shape)
    

    # Merge the data together
    result = pd.merge(incomeStatementData, balanceSheetData,\
                on=['Ticker','SimFinId','Currency',
                    'Fiscal Year','Report Date','Publish Date'])
    
    result = pd.merge(result, CashflowData,\
                on=['Ticker','SimFinId','Currency',
                    'Fiscal Year','Report Date','Publish Date'])
    
    # dates in correct format
    result["Report Date"] = pd.to_datetime(result["Report Date"]) 
    result["Publish Date"] = pd.to_datetime(result["Publish Date"])
    
    print('Merged X data matrix shape is: ', result.shape)
    
    return result

# ============================================================================== 
# Cell 9
# ============================================================================== 

X = getXFullDataMerged()

# ============================================================================== 
# Cell 10
# ============================================================================== 

# Get data only for 2024
PublishDateStart = "2024-01-01"
PublishDateEnd = "2024-04-01"
bool_list = X['Publish Date'].between(\
              pd.to_datetime(PublishDateStart),\
              pd.to_datetime(PublishDateEnd) )
X=X[bool_list]

# ============================================================================== 
# Cell 11
# ============================================================================== 

d=getYRawData2024()

# ============================================================================== 
# Cell 12
# ============================================================================== 

y = getYPricesReportDate(X, d) # Takes a min due to price lookups.
y = pd.DataFrame(y, columns=['Ticker', 'Open Price', 'Date', 'Volume'])

# ============================================================================== 
# Cell 13
# ============================================================================== 

import yfinance as yf

def analyze_crypto_data(crypto_data_dir):
    """
    Analyzes the data in the specified crypto_data directory.

    Parameters:
        crypto_data_dir (str): Path to the directory containing cryptocurrency data.

    Returns:
        pd.DataFrame: Dataframe containing analysis results.
    """
    import os
    crypto_analysis = []

    for filename in os.listdir(crypto_data_dir):
        if filename.endswith('.csv'): 
            file_path = os.path.join(crypto_data_dir, filename)
            data = pd.read_csv(file_path)

            # Simple analysis: Calculate average closing price
            avg_close_price = data['Close'].mean()
            crypto_analysis.append({
                'File': filename,
                'Average Close Price': avg_close_price
            })

    return pd.DataFrame(crypto_analysis)

if __name__ == "__main__":
    # Example usage of analyze_crypto_data
    crypto_data_directory = "crypto_data"  # Path to crypto data dir
    analysis_results = analyze_crypto_data(crypto_data_directory)

    print("Analysis Results:")
    print(analysis_results)