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
        return [ticker, np.nan,\
                np.datetime64('NaT'),\
                np.nan]
    else:
        return [ticker, rows.iloc[0]["Open"],\
                rows.iloc[0]["Date"],\
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

# Replace 'AAPL' with the ticker symbol of the stock you want to fetch data for
ticker_symbol = 'WMT'

# Create a yfinance object for the specified stock
stock = yf.Ticker(ticker_symbol)

# Get historical data for the stock with the 'history' method
# By default, it will return data for the last available trading day
historical_data = stock.history(period="1d")

# Extract the open price from the historical data
open_price = historical_data['Open'].iloc[0]

print(f"Open price for {ticker_symbol}: {open_price}")


# ==============================================================================
# Cell 14
# ==============================================================================

import yfinance as yf
openPrices = {}
for sym in y['Ticker']:
    # Replace 'AAPL' with the ticker symbol of the stock you want to fetch data for
    ticker_symbol = sym

    # Create a yfinance object for the specified stock
    stock = yf.Ticker(ticker_symbol)
    # Get historical data for the stock with the 'history' method
    # By default, it will return data for the last available trading day
    historical_data = stock.history(period="1d")
    if not historical_data.empty:
        # Extract the open price from the historical data
        open_price = historical_data['Open'].iloc[0]

        print(f"Open price for {ticker_symbol}: {open_price}")
        openPrices[ticker_symbol] = open_price


# ==============================================================================
# Cell 15
# ==============================================================================

y2 = pd.DataFrame(list(openPrices.items()), columns=['Ticker', 'Open Price'])
y2['Date']='2024-03-22'
y2


# ==============================================================================
# Cell 16
# ==============================================================================

y2=y2.reset_index(drop=True)
X=X.reset_index(drop=True)

# Issue where no share price
bool_list1 = ~y["Open Price"].isnull()
# Issue where there is low/no volume
#bool_list2 = ~(y['Volume']<1e4)

y2=y2[bool_list1]
X=X[bool_list1]

# Issues where no listed number of shares
bool_list4 = ~X["Shares (Diluted)_x"].isnull()
y2=y2[bool_list4]
X=X[bool_list4]
               
y2=y2.reset_index(drop=True)
X=X.reset_index(drop=True)

X["Market Cap"] = y2["Open Price"]*X["Shares (Diluted)_x"]


# ==============================================================================
# Cell 17
# ==============================================================================

X.to_csv("stock_data\\Annual_Stock_Price_Fundamentals_Filtered_2024_present.csv")
y2.to_csv("stock_data\\Tickers_Dates_2024_present.csv")


# ==============================================================================
# Cell 18
# ==============================================================================
# # process_x_y_learning_data


# ==============================================================================
# Cell 19
# ==============================================================================

def fixNansInX(x):
    '''
    Takes in x DataFrame, edits it so that important keys
    are 0 instead of NaN.
    '''
    keyCheckNullList = ["Short Term Debt" ,\
            "Long Term Debt" ,\
            "Interest Expense, Net",\
            "Income Tax (Expense) Benefit, Net",\
            "Cash, Cash Equivalents & Short Term Investments",\
            "Property, Plant & Equipment, Net",\
            "Revenue",\
            "Gross Profit",\
            "Total Current Liabilities"]
    x[keyCheckNullList]=x[keyCheckNullList].fillna(0)
    x['Property, Plant & Equipment, Net'] = x['Property, Plant & Equipment, Net'].fillna(0)
    
def addColsToX(x):
    '''
    Takes in x DataFrame, edits it to include:
        Enterprise Value.
        Earnings before interest and tax.
    
    '''
    x["EV"] = x["Market Cap"] \
    + x["Long Term Debt"] \
    + x["Short Term Debt"] \
    - x["Cash, Cash Equivalents & Short Term Investments"]

    x["EBIT"] = x["Net Income (Common)"] \
    - x["Interest Expense, Net"] \
    - x["Income Tax (Expense) Benefit, Net"]


# ==============================================================================
# Cell 20
# ==============================================================================

# Make new X with ratios to learn from.
def getXRatios(x_):
    '''
    Takes in x_, which is the fundamental stock DataFrame raw. 
    Outputs X, which is the data encoded into stock ratios.
    '''
    X=pd.DataFrame()
    
    # EV/EBIT
    X["EV/EBIT"] = x_["EV"] / x_["EBIT"]
    
    # Op. In./(NWC+FA)
    X["Op. In./(NWC+FA)"] = x_["Operating Income (Loss)"] \
    / (x_["Total Current Assets"] - x_["Total Current Liabilities"] \
       + x_["Property, Plant & Equipment, Net"])
    
    # P/E
    X["P/E"] = x_["Market Cap"] / x_["Net Income (Common)"]
    
    # P/B
    X["P/B"] = x_["Market Cap"] / x_["Total Equity"] 
    
    # P/S
    X["P/S"] = x_["Market Cap"] / x_["Revenue"] 
    
    # Op. In./Interest Expense
    X["Op. In./Interest Expense"] = x_["Operating Income (Loss)"]\
    / - x_["Interest Expense, Net"]
    
    # Working Capital Ratio
    X["Working Capital Ratio"] = x_["Total Current Assets"]\
    / x_["Total Current Liabilities"]
    
    # Return on Equity
    X["RoE"] = x_["Net Income (Common)"] / x_["Total Equity"]
    
    # Return on Capital Employed
    X["ROCE"] = x_["EBIT"]\
    / (x_["Total Assets"] - x_["Total Current Liabilities"] )
    
    # Debt/Equity
    X["Debt/Equity"] = x_["Total Liabilities"] / x_["Total Equity"]
    
    # Debt Ratio
    X["Debt Ratio"] = x_["Total Assets"] / x_["Total Liabilities"]
    
    # Cash Ratio
    X["Cash Ratio"] = x_["Cash, Cash Equivalents & Short Term Investments"]\
    / x_["Total Current Liabilities"]
    
    # Asset Turnover
    X["Asset Turnover"] = x_["Revenue"] / \
                            x_["Property, Plant & Equipment, Net"]
    
    # Gross Profit Margin
    X["Gross Profit Margin"] = x_["Gross Profit"] / x_["Revenue"]
    
    ### Altman ratios ###
    # (CA-CL)/TA
    X["(CA-CL)/TA"] = (x_["Total Current Assets"]\
                       - x_["Total Current Liabilities"])\
                        /x_["Total Assets"]
    
    # RE/TA
    X["RE/TA"] = x_["Retained Earnings"]/x_["Total Assets"]
    
    # EBIT/TA
    X["EBIT/TA"] = x_["EBIT"]/x_["Total Assets"]
    
    # Book Equity/TL
    X["Book Equity/TL"] = x_["Total Equity"]/x_["Total Liabilities"]
    
    X.fillna(0, inplace=True)
    return X

def fixXRatios(X):
    '''
    Takes in X, edits it to have the distributions clipped.
    The distribution clippings are done manually by eye,
    with human judgement based on the information.
    '''
    X["RoE"].clip(-5, 5, inplace=True)
    X["Op. In./(NWC+FA)"].clip(-5, 5, inplace=True)
    X["EV/EBIT"].clip(-500, 500, inplace=True)
    X["P/E"].clip(-1000, 1000, inplace=True)
    X["P/B"].clip(-50, 100, inplace=True)    
    X["P/S"].clip(0, 500, inplace=True)
    X["Op. In./Interest Expense"].clip(-600, 600, inplace=True)#-600, 600
    X["Working Capital Ratio"].clip(0, 30, inplace=True)  
    X["ROCE"].clip(-2, 2, inplace=True)
    X["Debt/Equity"].clip(0, 100, inplace=True)
    X["Debt Ratio"].clip(0, 50, inplace=True)  
    X["Cash Ratio"].clip(0, 30, inplace=True)
    X["Gross Profit Margin"].clip(0, 1, inplace=True) #how can be >100%?
    X["(CA-CL)/TA"].clip(-1.5, 2, inplace=True)
    X["RE/TA"].clip(-20, 2, inplace=True)
    X["EBIT/TA"].clip(-2, 1, inplace=True)
    X["Book Equity/TL"].clip(-2, 20, inplace=True)
    X["Asset Turnover"].clip(-2000, 2000, inplace=True)# 0, 500


# ==============================================================================
# Cell 21
# ==============================================================================

X=pd.read_csv("stock_data\\Annual_Stock_Price_Fundamentals_Filtered_2024_present.csv", 
              index_col=0)

# Net Income fix, checked annual reports.
X['Net Income (Common)'] = X['Net Income_x'] 

fixNansInX(X)
addColsToX(X)
X=getXRatios(X)
fixXRatios(X)
X.to_csv("stock_data\\Annual_Stock_Price_Fundamentals_Ratios_2024.csv")


# ==============================================================================
# Cell 22
# ==============================================================================
# # final_stock_selection


# ==============================================================================
# Cell 23
# ==============================================================================

def calcZScores(X):
    '''
    Calculate Altman Z'' scores 1995
    '''
    Z = pd.DataFrame()
    Z['Z score'] = 3.25 \
    + 6.51 * X['(CA-CL)/TA']\
    + 3.26 * X['RE/TA']\
    + 6.72 * X['EBIT/TA']\
    + 1.05 * X['Book Equity/TL']
    return Z


# ==============================================================================
# Cell 24
# ==============================================================================

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.preprocessing import PowerTransformer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LinearRegression
from sklearn.linear_model import ElasticNet
from sklearn.neighbors import KNeighborsRegressor
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.svm import SVR
import pickle


# ==============================================================================
# Cell 25
# ==============================================================================

# Linear model pipeline
def trainLinearModel(X_train, y_train):
    pl_linear = Pipeline([('Power Transformer', PowerTransformer()),
        ('linear', LinearRegression())])
    pl_linear.fit(X_train, y_train)
    return pl_linear

# ElasticNet model pipeline
def trainElasticNetModel(X_train, y_train):
    pl_ElasticNet = Pipeline([('Power Transformer', PowerTransformer()),
        ('ElasticNet', ElasticNet(l1_ratio=0.00001))])
    pl_ElasticNet.fit(X_train, y_train)
    return pl_ElasticNet

# KNeighbors regressor
def trainKNeighborsModel(X_train, y_train):
    pl_KNeighbors = Pipeline([('Power Transformer', PowerTransformer()),
        ('KNeighborsRegressor', KNeighborsRegressor(n_neighbors=40))])
    pl_KNeighbors.fit(X_train, y_train)
    return pl_KNeighbors

# DecisionTreeRegressor
def traindecTreeModel(X_train, y_train):
    pl_decTree = Pipeline([
        ('DecisionTreeRegressor',\
         DecisionTreeRegressor(max_depth=20, random_state=42))
    ])
    pl_decTree.fit(X_train, y_train)
    return pl_decTree

# RandomForestRegressor
def trainrfregressorModel(X_train, y_train):
    pl_rfregressor = Pipeline([
        ('RandomForestRegressor',\
         RandomForestRegressor(max_depth=10, random_state=42))
    ])
    pl_rfregressor.fit(X_train, y_train)
    
    return pl_rfregressor

# GradientBoostingRegressor
def traingbregressorModel(X_train, y_train):
    pl_GradBregressor = Pipeline([
        ('GradBoostRegressor',\
         GradientBoostingRegressor(n_estimators=100,\
                                   learning_rate=0.1,\
                                   max_depth=14,\
                                   random_state=42,\
                                   loss='absolute_error'))  ])
    pl_GradBregressor.fit(X_train, y_train)
    
    return pl_GradBregressor

# SVM
def trainsvmModel(X_train, y_train):
    pl_svm = Pipeline([('Power Transformer', PowerTransformer()),
        ('SVR', SVR(kernel='rbf', C=100, gamma=0.1, epsilon=.1))])
    pl_svm.fit(X_train, y_train)
    return pl_svm


# ==============================================================================
# Cell 26
# ==============================================================================

import pandas as pd

def pickStockForMe():
    '''
    Pick stocks.
    Reads Annual_Stock_Price_Fundamentals_Ratios.csv,
    and Annual_Stock_Price_Performance_Percentage.csv,
    trains the AI with the best model/parameters,
    Then picks stocks using outputs from Notebooks 1 and 2:
    Annual_Stock_Price_Fundamentals_Ratios_2021.csv,
    and Tickers_Dates_2021.csv.
    Outputs a DataFrame of best picks.
    '''
    # Training X and Y of all previous year data
    X=pd.read_csv("stock_data\\Annual_Stock_Price_Fundamentals_Ratios.csv", 
                  index_col=0)
    # annual stock performances
    yperf=pd.read_csv("stock_data\\Annual_Stock_Price_Performance_Percentage.csv", 
                      index_col=0)
    
    yperf=yperf["Perf"]

    # Stock selection ratios for 2024 X
    X_2024=pd.read_csv("stock_data\\Annual_Stock_Price_Fundamentals_Ratios_2024.csv"
                       , index_col=0)
    # And the row tickers
    tickers=pd.read_csv("stock_data\\Tickers_Dates_2024_present.csv", index_col=0)
    
    # Gradient Boosted tree
    #model_pl = traingbregressorModel(X, yperf)
    #y_pred=model_pl.predict(X_2024)
    #y_pred=pd.DataFrame(y_pred)
    
    # Random Forest
    #model_pl = trainrfregressorModel(X, yperf)
    #y_pred=model_pl.predict(X_2024)
    #y_pred=pd.DataFrame(y_pred)
    
    
    # KNN
    model_pl = trainKNeighborsModel(X, yperf)
    y_pred=model_pl.predict(X_2024)
    y_pred=pd.DataFrame(y_pred)
    
    

    # FINAL STOCK PICKS
    # Separate out stocks with low Z scores
    # 3.75 is approx. B- rating
    z = calcZScores(X_2024)
    zbl = (z['Z score'].reset_index(drop=True) > 3) 

    # Final_Predictions = pd.DataFrame()
    Final_Predictions=tickers[['Ticker','Date']].reset_index(drop=True)\
                                                [zbl].reset_index(drop=True)
    
    Final_Predictions['Perf'] = y_pred.reset_index(drop=True)\
                                                [zbl].reset_index(drop=True)

    return Final_Predictions.sort_values(by='Perf', ascending=False)\
                                                .reset_index(drop=True)


# ==============================================================================
# Cell 27
# ==============================================================================

# What it's all about.
res = pickStockForMe()


# ==============================================================================
# Cell 28
# ==============================================================================

# RF
pd.set_option('display.max_rows', 10000)
res


# ==============================================================================
# Cell 29
# ==============================================================================

# KNN (apparent 2nd best)
pd.set_option('display.max_rows', 10000)
res


# ==============================================================================
# Cell 30
# ==============================================================================

# GBST (apparent best)
pd.set_option('display.max_rows', 10000)
res
