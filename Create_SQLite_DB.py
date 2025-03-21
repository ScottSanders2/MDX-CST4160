
import sqlite3

def createdb():
  print(f"SqLite version {sqlite3.sqlite_version}")
  conn = sqlite3.connect("FinApp.db")
  cursor = conn.cursor()

  sql_script = """CREATE TABLE transactions (
              tid TEXT PRIMARY KEY,
              date TEXT,
              dc TEXT, amount REAL);"""
  cursor.executescript(sql_script)
  conn.commit()

  conn.close()

def insertdata():
    conn = sqlite3.connect("FinApp.db")
    cursor = conn.cursor()

    sql_script = """INSERT INTO transactions (tid, date, dc, amount) VALUES
    ('82345a', '2025-01-15', 'c', '2000.00'),
     ('8937db', '2025-01-18', 'c', '13500.10'),
      ('9997cc', '2025-02-10', 'd', '7500.85'),
      ('1232ss', '2025-02-20', 'c', '44500.50');"""
    cursor.executescript(sql_script)
    conn.commit()

    conn.close()

if __name__ == '__main__':
  insertdata()


