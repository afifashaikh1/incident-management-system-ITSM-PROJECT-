import mysql.connector

def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",              # apna mysql username
        password="Afifa@04", # apna mysql password
        database="incident_db"
    )