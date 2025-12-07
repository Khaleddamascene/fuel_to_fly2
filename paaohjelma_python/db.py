# ansenna pip install python-dotenv 

import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv()  # Lataa .env-tiedoston

def get_connection():
    return mysql.connector.connect(
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT'),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        autocommit=True
    )
