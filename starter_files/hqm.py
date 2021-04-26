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
  'One-Month Return Percentile',
  'HQM Score'
]

hqm_dataframe = pd.DataFrame(columns = hqm_columns)

for symbol_string in symbol_strings:
  batch_api_call_url = f'https://sandbox.iexapis.com/stable/stock/market/batch?symbols={symbol_string}&types=stats,price&token={IEX_CLOUD_API_TOKEN}'
  data = requests.get(batch_api_call_url).json()

  for symbol in symbol_string.split(','):
    price = data[symbol]['price']

    y1cp = data[symbol]['stats']['year1ChangePercent']
    y1cp = 0.0 if y1cp == None else y1cp

    m6cp = data[symbol]['stats']['month6ChangePercent']
    m6cp = 0.0 if m6cp == None else m6cp

    m3cp = data[symbol]['stats']['month3ChangePercent']
    m3cp = 0.0 if m3cp == None else m3cp

    m1cp = data[symbol]['stats']['month1ChangePercent']
    m1cp = 0.0 if m1cp == None else m1cp

    hqm_dataframe = hqm_dataframe.append(
      pd.Series(
      [
        symbol,
        price,
        'N/A',
        y1cp,
        'N/A',
        m6cp,
        'N/A',
        m3cp,
        'N/A',
        m1cp,
        'N/A',
        'N/A'
      ],
      index = hqm_columns
      ),
      ignore_index = True
    )

time_periods = [
                'One-Year',
                'Six-Month',
                'Three-Month',
                'One-Month'
               ]

# fill in growth rate for each time period column
for row in hqm_dataframe.index:
  for time_period in time_periods:
    change_col = f'{time_period} Price Return'
    percentile_col = f'{time_period} Return Percentile'
    hqm_dataframe.loc[row, percentile_col] = stats.percentileofscore(np.asarray(hqm_dataframe[change_col]), hqm_dataframe.loc[row, change_col])/100


# find HQM (mean of each ticker's growth rates for each period)
from statistics import mean

for row in hqm_dataframe.index:
  momentum_percentiles = []
  for time_period in time_periods:
    momentum_percentiles.append(hqm_dataframe.loc[row, f'{time_period} Return Percentile'])
  hqm_dataframe.loc[row, 'HQM Score'] = mean(momentum_percentiles)

# grab top 50 tickers
hqm_dataframe.sort_values('HQM Score', ascending = False, inplace = True)
hqm_dataframe = hqm_dataframe[:50]
hqm_dataframe.reset_index(inplace = True, drop = True)

# calculate number of shares to buy
portfolio_size = 10000000
position_size = float(portfolio_size)/len(hqm_dataframe.index)
for i in hqm_dataframe.index:
  hqm_dataframe.loc[i, 'Number of Shares to Buy'] = math.floor(position_size/hqm_dataframe.loc[i, 'Price'])

writer = pd.ExcelWriter('momentum_strategy.xlsx', engine='xlsxwriter')
hqm_dataframe.to_excel(writer, sheet_name = 'Momentum Strategy', index = False)

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

percent_format = writer.book.add_format(
  {
    'num_format': '0.0%',
    'font_color': font_color,
    'bg_color': background_color,
    'border': 1
  }
)

column_formats = {
  'A': ['Ticker', string_format],
  'B': ['Price', dollar_format],
  'C': ['Number of Shares to Buy', integer_format],
  'D': ['One-Year Price Return', percent_format],
  'E': ['One-Year Return Percentile', percent_format],
  'F': ['Six-Month Price Return', percent_format],
  'G': ['Six-Month Return Percentile', percent_format],
  'H': ['Three-Month Price Return', percent_format],
  'I': ['Three-Month Return Percentile', percent_format],
  'J': ['One-Month Price Return', percent_format],
  'K': ['One-Month Return Percentile', percent_format],
  'L': ['HQM Score', percent_format]
}

for column in column_formats.keys():
  title, fmt = column_formats[column]
  writer.sheets['Momentum Strategy'].set_column(f'{column}:{column}', 25, fmt)
  writer.sheets['Momentum Strategy'].write(f'{column}1', title, fmt)

writer.save()


