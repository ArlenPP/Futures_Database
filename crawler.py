#!/usr/bin/env python3
# encoding: utf-8

from datetime import date, timedelta, datetime
from dateutil import relativedelta
from collections import namedtuple
from io import BytesIO
import pandas as pd
import numpy as np
import requests
import zipfile
import os
from database import stockDB

config = {
    'taifex_fname': 'Daily_%s_%s_%s.zip',
    'taifex_path': './taifex/',
    'taifex_url': 'http://www.taifex.com.tw/DailyDownload/DailyDownloadCSV/',
}
config = namedtuple('Config', config.keys())(**config)

db_config = {
        'host': os.environ.get('stockdb_host'),
        'port': int(os.environ.get('stockdb_port')),
        'user': os.environ.get('stockdb_user'),
        'password': os.environ.get('stockdb_passwd'),
        'db': 'fitx',
    }

def day_list(buffer = 40):
    today = date.today()
    day_list = [(today - timedelta(i)) for i in range(buffer, -1, -1)]
    return day_list

def taifex(today):
    year = today.strftime('%Y')
    month = today.strftime('%m')
    day = today.strftime('%d')

    # read zip # {{{
    fname = config.taifex_fname % (year, month, day)
    path = config.taifex_path + fname
    if zipfile.is_zipfile(path):
        zf = zipfile.ZipFile(path)
    else:
        # download
        url = config.taifex_url + fname
        r = requests.get(url)
        if('index' in str((r.content))):
            return None,None
        with open(path, 'wb') as f:
            f.write(r.content)
        zf = zipfile.ZipFile(BytesIO(r.content))
    raw_lines = zf.read(zf.namelist()[0]).split(b'\r\n')
    # }}}

    # filter
    nextmonth = today + relativedelta.relativedelta(months=1)

    pattern1 = '%s%s%s,TX     ,%s%s     ,' % (year, month, day, year, month)
    pattern1 = pattern1.encode('big5')

    pattern2 = '%s%s%s,TX     ,%s%s     ,' % (year, month, day, nextmonth.strftime('%Y'), nextmonth.strftime('%m'))
    pattern2 = pattern2.encode('big5')

    lines = []
    flag = False
    for pattern in [pattern1,pattern2]:
        for v in raw_lines:
            if -1 != v.find(pattern):
                flag = True
                lines.append(v.decode('big5'))
        if(flag == True):
            break

    # 1-minute k # {{{
    minute_k = { 'Time': False, }
    minute_ks = []
    for line in lines:
        # 0        1        2              3        4        5             6        7        8
        # 成交日期,商品代號,到期月份(週別),成交時間,成交價格,成交數量(B+S),近月價格,遠月價格,開盤集合競價
        cells = line.split(',')
        if cells[3] < '084500' or cells[3] > '134500' or int(cells[4]) < 0: continue
        minute = cells[3][:2] + ':' + cells[3][2:4]
        
        if minute == minute_k['Time'] or minute == '13:45':
            price = int(cells[4])
            minute_k['Close'] = price
            minute_k['Volume'] = minute_k['Volume'] + int(cells[5])/2
            if price > minute_k['High']: minute_k['High'] = price
            elif price < minute_k['Low']: minute_k['Low'] = price
        else: # new minute
            minute_ks.append(minute_k)
            minute_k = { 'Time': minute }
            minute_k['Close'] = minute_k['High'] = minute_k['Low'] = minute_k['Open'] = int(cells[4])
            minute_k['Volume'] = int(cells[5])/2
            minute_k['Date'] = year +'/'+ month +'/'+ day
    minute_ks.append(minute_k)
    minute_ks.pop(0)


    minute_ks_df = pd.DataFrame.from_dict(minute_ks)

    minute_ks_df['DateTime'] = pd.to_datetime(minute_ks_df['Date'] + ' ' + minute_ks_df['Time'])
    minute_ks_df.fillna(0, inplace=True)

    # day_ks
    day_ks = {
        'Date': [year +'/'+ month +'/'+ day],
        'Open': [minute_ks[0]['Open']],
        'High': [max([v['High'] for v in minute_ks])],
        'Low': [min([v['Low'] for v in minute_ks])],
        'Close': [minute_ks[-1]['Close']],
        'Volume': [sum([v['Volume'] for v in minute_ks])],
    }
    day_ks_df = pd.DataFrame.from_dict(day_ks)
    
    return day_ks_df, minute_ks_df


if '__main__' == __name__:
    
    # connect to DB
    mydb = stockDB(**db_config)
    prev_df = mydb.read_data(day_list[0], day_list[-1], True)
    
    # 先取得爬蟲要爬的日期
    day_list = day_list()

    # 確認這個日期的day_k是不是已經存在了
    already = pd.to_datetime(prev_df['Date']).tolist()
    already = [day.date() for day in already[-40:]]

    need = set(day_list) - set(already)

    for day in need:
        day_ks, minute_ks = taifex(day)
        if(day_ks is None or minute_ks is None):
            continue
        mydb.insert_data(day_ks, "day_ks")
        mydb.insert_data(minute_ks, "minute_ks")

    print(day_list[-1].strftime('%Y/%m/%d')+' done!')
# vi:et:sw=4:ts=4
