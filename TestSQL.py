import sqlite3
def get_db_connection():
    conn = sqlite3.connect("data.db")
    conn.row_factoruy = sqlite3.Row
    return conn



