import pandas as pd
import pymysql
import os
from sqlalchemy import create_engine

config = {
        'host': os.environ.get('stockdb_host'),
        'port': int(os.environ.get('stockdb_port')),
        'user': os.environ.get('stockdb_user'),
        'password': os.environ.get('stockdb_passwd'),
        'db': 'fitx',
    }

if __name__ == "__main__":
    #not ORM

    # fitxdb = database.stockDB(**config)
    # df = pd.read_csv("./product/fitx.csv")
    # for index, row in df.iterrows():
    #     fitxdb.insert_data(row['Date'], row['Open'], row['High'], row['Low'], row['Close'], int(row['Volume']))

    # fitxdb.db.close()
    
    # USE ORM

    ## create connect to AWS sql
    engine = create_engine("mysql+pymysql://{}:{}@{}:{}/{}".format(config['user'], config['password'], config['host'], config['port'], config['db']))
    con = engine.connect()

    ## read fitx.1m.csv
    df = pd.read_csv("./product/fitx.1m.csv")
    df['Volume'].fillna(0, inplace=True)

    ## insert_data
    df.to_sql(name='minute_ks', con=con, if_exists='append', index=False)
    