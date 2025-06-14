import sqlite3
conn = sqlite3.connect("matches.db")
cursor = conn.cursor()
cursor.execute("SELECT * FROM matches")
rows = cursor.fetchall()
for row in rows:
    print(row)
conn.close()