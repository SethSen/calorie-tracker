import sqlite3

conn = sqlite3.connect('calorie_tracker.sqlite')

c = conn.cursor()

# Dropping food_log table
c.execute('''
          DROP TABLE IF EXISTS food_log
          ''')

# Dropping personal_info table
c.execute('''
          DROP TABLE IF EXISTS personal_info
          ''')

conn.commit()
conn.close()
