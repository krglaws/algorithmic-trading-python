import numpy as np
import pandas as pd
import requests
import math
from scipy import stats
import xlsxwriter
import pprint


def chunks(lst, n):
  """Yield successive n-sized chunks from lst."""
  for i in range(0, len(lst), n):
    yield lst[i:i + n]


# get API key
from secrets import IEX_CLOUD_API_TOKEN

# get ticker list
stocks = pd.read_csv('sp_500_stocks.csv')

# move tickers into string groups for api batching
symbol_groups = list(chunks(stocks['Ticker'], 100))
symbol_strings = []
for i in range(len(symbol_groups)):
  symbol_strings.append(','.join(symbol_groups[i]))

# set up dataframe
my_columns = ['Ticker', 'Price', 'One Year Price Return', 'Number of Shares to Buy']
final_dataframe = pd.DataFrame(columns = my_columns)

# request and store into dataframe
for symbol_string in symbol_strings:
  batch_api_call_url = f'https://sandbox.iexapis.com/stable/stock/market/batch?symbols={symbol_string}&types=stats,price&token={IEX_CLOUD_API_TOKEN}'
  data = requests.get(batch_api_call_url).json()

  for symbol in symbol_string.split(','):
    final_dataframe = final_dataframe.append(
      pd.Series(
        [
          symbol,
          data[symbol]['price'],
          data[symbol]['stats']['year1ChangePercent'],
          'N/A'
        ],
        index = my_columns
      ),
      ignore_index = True
    )

final_dataframe.sort_values('One Year Price Return', ascending=False, inplace = True)
final_dataframe = final_dataframe[:50]
final_dataframe.reset_index(inplace = True)

portfolio_size = 0.0
def portfolio_input():
  global portfolio_size
  portfolio_size = input('Enter the size of your portfolio:')

  try:
    float(portfolio_size)
  except:
    print('That is not a number!')
    print('Please try again:')
    portfolio_size = input('Enter the size of your portfolio:')

portfolio_input()

position_size = float(portfolio_size) / len(final_dataframe.index)
for i in range(len(final_dataframe.index)):
  final_dataframe.loc[i, 'Number of Shares to Buy'] = math.floor(position_size/final_dataframe.loc[i,'Price'])


hqm_columns = [
  'Ticker',
  'Price',
  'Number of Shares to Buy',
  'One-Year Price Return',
  'One-Year Return Percentile',
  'Six-Month Price Return',
  'Six-Month Return Percentile',
  'Three-Month Price Return',
  'Three-Month Return Percentile',
  'One-Month Price Return',
  'One-Month Return Percentile'
]




