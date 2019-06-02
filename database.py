import pymysql

# Create Table

# Insert Data

# Read Data

if __name__ == "__main__":
    config = {
        'host': '',
        'user': '',
        'password': '',
        'database': '',
    }
    sqlConnection = pymysql.createConnect( **config)
