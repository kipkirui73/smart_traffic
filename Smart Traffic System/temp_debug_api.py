import sqlite3
from config import DB_PATH
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()
c.execute('SELECT id, image_path FROM violations ORDER BY id DESC LIMIT 10')
for r in c.fetchall():
    print(r)
conn.close()
