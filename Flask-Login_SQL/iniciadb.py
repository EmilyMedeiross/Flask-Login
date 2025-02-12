import sqlite3

database = "database.db"
conn = sqlite3.connect(database)

with open('sqlite.sql') as f:
    conn.executescript(f.read())