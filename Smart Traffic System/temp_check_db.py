import sqlite3
from config import DB_PATH
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()
c.execute("SELECT COUNT(*) FROM violations WHERE image_path IS NULL OR image_path=''")
print(c.fetchone()[0])
conn.close()
