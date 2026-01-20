import os
import psycopg2

conn = psycopg2.connect(
        host="localhost",
        port="5432",
        database="moodyai",
        user='postgres',
        password='admin123'
)
