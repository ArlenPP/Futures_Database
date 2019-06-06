import pymysql
import inspect
import os
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey
from sqlalchemy.orm import sessionmaker
config = {
        'host': os.environ.get('stockdb_host'),
        'port': int(os.environ.get('stockdb_port')),
        'user': os.environ.get('stockdb_user'),
        'password': os.environ.get('stockdb_passwd'),
        'db': 'fitx',
    }


class stockDB(object):
    def __init__(self, host, port, user, password, db):
        self.db = pymysql.connect(host=host, port=port, user=user, password=password, db=db, charset='utf8')
        self.cursor = self.db.cursor()
        
        # ORM
        self.engine = create_engine("mysql+pymysql://{}:{}@{}:{}/{}".format(user, password, host, port, db))
        self.metadata = MetaData()
        self.metadata.reflect(bind=self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.day_ks = self.metadata.tables.get('day_ks')
        self.minute_ks = self.metadata.tables.get('minute_ks')

    def exe_query(self, query):
        caller = inspect.stack()[1].function
        try:
            self.cursor.execute(query)
            #提交修改
            self.db.commit()
            return self.cursor.fetchall()
            print(caller + ' success')
        except pymysql.InternalError as error:
            #發生錯誤時停止執行SQL
            code, message = error.args
            self.db.rollback()
            print(caller + '\n\n' + str(code) + ' ' + message)

    def insert_data(self, df, table):
        df.to_sql(name=table, if_exists='append', index=False, con=self.engine)

    def read_data(self, sDate, eDate, sTime=None, eTime=None):
        
        if(sTime == None or eTime == None):
            session = self.Session()
            day_ks = self.day_ks
            query = session.query(day_ks).filter(day_ks.columns.Date>=sDate,       
                                                 day_ks.columns.Date<=eDate)
            df = pd.read_sql(query.statement, query.session.bind)
            session.close()
            return df
        else:
            session = self.Session()
            minute_ks = self.minute_ks
            query = session.query(minute_ks).filter(minute_ks.columns.Date>=sDate, 
                                                minute_ks.columns.Date<=eDate,
                                                minute_ks.columns.Time>=sTime,
                                                minute_ks.columns.Time<=eTime)
            df = pd.read_sql(query.statement, query.session.bind)
            session.close()
            return df

if __name__ == "__main__":

    mydb = stockDB(**config)
    # df = mydb.read_data("2019/3/20", "2019/03/21")
    # df = mydb.read_data("2019/01/1", "2019/1/30", "00:00", "14:00")
    # mydb.exe_query("delete from day_ks where Date=\"2019/3/21\"")
    # df = pd.read_csv("./product/fitx.csv")
    # mydb.insert_data(df, "day_ks")
    mydb.db.close()
