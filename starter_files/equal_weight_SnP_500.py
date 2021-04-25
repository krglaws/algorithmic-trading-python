# imports
import numpy as np
import pandas as pd
import requests
import xlsxwriter
import math

# get API key
from secrets import IEX_CLOUD_API_TOKEN

def chunks(lst, n):
  """Yield successive n-sized chunks from lst."""
  for i in range(0, len(lst), n):
    yield lst[i:i + n]

# create dataframe with header
my_columns = ['Ticker', 'Stock Price', 'Market Capitalization', 'Number of Shares to Buy']
final_dataframe = pd.DataFrame(columns = my_columns)

# grab S&P 500 list
stocks = pd.read_csv('sp_500_stocks.csv')
symbol_groups = list(chunks(stocks['Ticker'], 100))

symbol_strings = []
for i in range(0, len(symbol_groups)):
  symbol_strings.append(','.join(symbol_groups[i]))

for symbol_string in symbol_strings:
  batch_api_call_url = f'https://sandbox.iexapis.com/stable/stock/market/batch?symbols={symbol_string}&types=quote&token={IEX_CLOUD_API_TOKEN}'
  data = requests.get(batch_api_call_url).json()

  for symbol in symbol_string.split(','):
    final_dataframe = final_dataframe.append(
      pd.Series(
        [
          symbol,
          data[symbol]['quote']['latestPrice'],
          data[symbol]['quote']['marketCap'],
          'N/A'
        ],
        index=my_columns
      ),
      ignore_index=True
    )

# read in total value of your portfolio
portfolio_size = 10000000.0
"""
while True:

  try:
    portfolio_size = float(input('Enter the value of your portfolio: '))
    break
  except ValueError:
    print('Not a number, please try again.')
"""

# position size per ticker (portfolio value / number of tickers)
position_size = portfolio_size / len(final_dataframe.index)

for i in range(len(final_dataframe.index)):
  final_dataframe.loc[i, 'Number of Shares to Buy'] = math.floor(position_size/final_dataframe.loc[i, 'Stock Price'])

writer = pd.ExcelWriter('recommended_trades.xlsx', engine = 'xlsxwriter')
final_dataframe.to_excel(writer, 'Recommended Trades', index = False)

background_color = '#0a0a23'
font_color = '#ffffff'

string_format = writer.book.add_format(
  {
    'font_color': font_color,
    'bg_color': background_color,
    'border': 1
  }
)

dollar_format = writer.book.add_format(
  {
    'num_format': '$0.00',
    'font_color': font_color,
    'bg_color': background_color,
    'border': 1
  }
)

integer_format = writer.book.add_format(
  {
    'num_format': '0',
    'font_color': font_color,
    'bg_color': background_color,
    'border': 1
  }
)

column_formats = {
  'A': ['Ticker', string_format],
  'B': ['Stock Price', dollar_format],
  'C': ['Market Capitalization', dollar_format],
  'D': ['Number of Shares to Buy', integer_format]
}

for column in column_formats.keys():
  title, fmt = column_formats[column]
  writer.sheets['Recommended Trades'].set_column(f'{column}:{column}', 18, fmt)
  writer.sheets['Recommended Trades'].write(f'{column}1', title, fmt)

writer.save()
