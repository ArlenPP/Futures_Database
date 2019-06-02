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
config = {
    'taifex_fname': 'Daily_%s_%s_%s.zip',
    'taifex_path': './taifex/',
    'taifex_url': 'http://www.taifex.com.tw/DailyDownload/DailyDownloadCSV/',
    'day_ks_path': './fitx.csv',
    'minute_ks_path': './minute_ks/',

}
config = namedtuple('Config', config.keys())(**config)

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
    minute_k = { 'minute': False }
    minute_ks = []
    for line in lines:
        # 0        1        2              3        4        5             6        7        8
        # 成交日期,商品代號,到期月份(週別),成交時間,成交價格,成交數量(B+S),近月價格,遠月價格,開盤集合競價
        cells = line.split(',')
        if cells[3] < '084500' or cells[3] > '134500' or int(cells[4]) < 0: continue
        minute = cells[3][:4]
        
        if minute == minute_k['minute'] or minute == '1345':
            price = int(cells[4])
            minute_k['close'] = price
            minute_k['volume'] = minute_k['volume'] + int(cells[5])/2
            if price > minute_k['high']: minute_k['high'] = price
            elif price < minute_k['low']: minute_k['low'] = price
        else: # new minute
            minute_ks.append(minute_k)
            minute_k = { 'minute': minute }
            minute_k['close'] = minute_k['high'] = minute_k['low'] = minute_k['open'] = int(cells[4])
            minute_k['volume'] = int(cells[5])/2
    minute_ks.append(minute_k)
    minute_ks.pop(0)
    # }}}
    day_ks = {
        'Date': [year +'/'+ month +'/'+ day],
        'Open': [minute_ks[0]['open']],
        'High': [max([v['high'] for v in minute_ks])],
        'Low': [min([v['low'] for v in minute_ks])],
        'Close': [minute_ks[-1]['close']],
        'Volume': [sum([v['volume'] for v in minute_ks])],
    }
    return day_ks, minute_ks


if '__main__' == __name__:
    day_list = day_list()
    for day in day_list:
        day_ks, minute_ks = taifex(day)

        if(day_ks != None and minute_ks != None):
            split = ","
            #  if min_k exit then day_k was done so continue
            if os.path.exists(config.minute_ks_path+day.strftime('%Y%m%d')+'.csv'):
                continue
            df = pd.DataFrame(day_ks, columns=day_ks.keys())
            # order the columns to what we want
            df = df[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']]        
            day_path = config.day_ks_path
            if os.path.exists(day_path):
                df.to_csv(day_path, mode='a', header=False, index=False)
            else:
                df.to_csv(day_path, mode='w', header=True, index=False)
                               
            with open(config.minute_ks_path+day.strftime('%Y%m%d')+'.csv', 'w') as f:
                f.write('Date,Time,Open,High,Low,Close,Volume\n')
                for line in minute_ks:
                    data_minute = [day.strftime('%Y%m%d'), str(line['minute']), str(line['open']), str(line['high']), str(line['low']), str(line['close']), str(line['volume'])+'\n']
                    f.write(split.join(data_minute))
    print(day_list[-1].strftime('%Y/%m/%d')+' done!')
# vi:et:sw=4:ts=4
