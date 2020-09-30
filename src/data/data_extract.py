#!/usr/bin/env python
# coding: utf-8

# importing
import pandas as pd

import yfinance as yf
import pandas_datareader as pdr

import requests
from bs4 import BeautifulSoup
from time import sleep
from datetime import date, timedelta


# getting s&p price data from yahoo finance

def get_yahoo_data(start, end):
    # overriding with pandas datareader
    yf.pdr_override()
    standard_and_poor = '^GSPC'

    # finding s&p index ticker and getting 5 years of data
    sp_df = pdr.get_data_yahoo(standard_and_poor, start=start, end=end).reset_index()

    return sp_df


def get_edgar_data(start, end):
    # getting CIK for every company in the s&p 500 from wikipedia

    wiki_url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    cik_df = pd.read_html(wiki_url, header=0, index_col=0)[0]
    cik_list = list(cik_df['CIK'])

    # creating empty dataframe to append all other dataframes with 8-k links
    doc_df = pd.DataFrame()

    for cik in cik_list:

        try:

            # defining endpoint and parameters for every company in the s&p
            url = 'https://www.sec.gov/cgi-bin/browse-edgar'
            params = {'action': 'getcompany',
                      'CIK': cik,
                      'type': '8-K',
                      'output': 'xml',
                      'dateb': end,
                      'datea': start,
                      'start': '',
                      'count': '100'}

            # getting response from EDGAR database
            sec_response = requests.get(url=url, params=params)

            # creating soup to parse xml
            soup = BeautifulSoup(sec_response.content, 'xml')

            # getting link to 8-k document
            urls = soup.findAll('filingHREF')
            html_list = []

            # html version of links
            for url in urls:
                url = url.string

                if url.split('.')[len(url.split('.')) - 1] == 'htm':
                    txt_link = url + 'l'
                    html_list.append(txt_link)

            html_list = pd.Series(html_list).astype(str)

            # list of links
            doc_list = html_list.str.replace('-index.html', '.txt').values.tolist()

            # creating dataframe to append the link of each company
            df = pd.DataFrame({'cik': [cik] * len(doc_list),
                               'txt_link': doc_list})

            doc_df = doc_df.append(df)

        except requests.exceptions.ConnectionError:
            sleep(.1)

    return doc_df


def get_current_date(extract_method):
    # function that returns correctly format date inputs given required function params

    current_date = date.today()
    if extract_method == 'edgar':
        # calculates a 15-day date range to search for 8-ks

        start = current_date.strftime('%Y%m%d')
        end = current_date - timedelta(days=15)
        end = end.strftime('%Y%m%d')
        return [start, end]

    elif extract_method == 'yahoo':
        # yahoo finance only needs one date input

        return current_date.strftime('%Y-%m-%d')
