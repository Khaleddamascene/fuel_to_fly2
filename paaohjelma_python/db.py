import mysql.connector

def get_connection():
    return mysql.connector.connect(
        host='127.0.0.1',
        port=3306,
        database='fuel_to_fly',
        user='andrei',
        password='1234',

        autocommit=True
    )
