import pymysql
import inspect
import os

class stockDB(object):
    def __init__(self, host, port, user, password, db):
        self.db = pymysql.connect(host=host, port=port, user=user, passwd=password, db=db, charset='utf8')
        self.cursor = self.db.cursor()

    def exe_query(self, query):
        caller = inspect.stack()[1].function
        try:
            self.cursor.execute(query)
            #提交修改
            self.db.commit()
            print(caller + ' success')
        except pymysql.InternalError as error:
            #發生錯誤時停止執行SQL
            code, message = error.args
            self.db.rollback()
            print(caller + '\n\n' + str(code) + ' ' + message)

    def insert_data(self, Date, Open, High, Low, Close, Volume, Time=None):
        # Date = '%Y-%m-%d'
        # Time = '%H:%M:%S'
        # Open, High, Low, Close, Volume are int
        
        table = 'day_ks'
        # Day k
        if(None == Time):
            #check is this data already in database
            if(len(self.read_data(sDate=Date, eDate=Date)) != 0):
                print("%s already in DataBase" % (Date))
                return
            
            #SQL query
            sql_query = "INSERT INTO %s VALUES(\"%s\", %s, %s, %s, %s, %s)" % (table ,Date, Open, High, Low, Close, Volume)

            print(sql_query)
            self.exe_query(sql_query)

        # minute k
        else:
            #check is this data and time already in database
            if(len(self.read_data(sDate=Date, eDate=Date, sTime=Time, eTime=Time)) != 0):
                print("%s %s already in DataBase" % (Date, Time))
                return
            table = 'minute_ks'
            #SQL query
            sql_query = "INSERT INTO %s VALUES(%s, %s, %s, %s, %s, %s)" % (table ,Date, Time, Open, High, Low, Close, Volume)
            self.exe_query(sql_query)

    def read_data(self, sDate, eDate, sTime=None, eTime=None):
        
        table = 'day_ks'
        # Day k
        if(None == sTime and None == eTime):        
            #SQL query
            sql_query = "select * from %s where Date>=\"%s\" and Date<=\"%s\""% (table ,sDate, eDate)
            self.exe_query(sql_query)
            return self.cursor.fetchall()

        # minute k
        else:
            #check is this data and time already in database
            table = 'minute_ks'
            #SQL query
            sql_query = "select * from %s where Date=\"%s\", Time>=\"%s\" and Time<=\"%s\" "% (table ,Date, sTime, eTime)
            self.exe_query(sql_query)
            return self.cursor.fetchall()

    # Read Data

if __name__ == "__main__":

    mydb = stockDB(**config)
    # mydb.insert_data("1999-01-07",6150,6430,6074,6120, 0)
    result = mydb.read_data("1999-01-05", "1999-01-07")
    if(0 == len(result)):
        print("Nothing")
    else:
        print(result)
    # mydb.exe_query("delete from day_ks where Date=\"1999-01-07\"")
    mydb.db.close()
