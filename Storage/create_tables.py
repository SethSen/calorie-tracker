import sqlite3

conn = sqlite3.connect('calorie_tracker.sqlite')
c = conn.cursor()

# Creating the personal_info table
c.execute('''
CREATE TABLE personal_info (
id INTEGER PRIMARY KEY,
trace_id TEXT UNIQUE NOT NULL,
user_id INTEGER NOT NULL,
age INTEGER NOT NULL,
sex VARCHAR(10) NOT NULL,
height INTEGER NOT NULL,
weight INTEGER NOT NULL,
activity_level VARCHAR(50) NOT NULL,
nutritional_goal VARCHAR(50) NOT NULL,
date_created VARCHAR(100) NOT NULL)
''')

# Creating the food_log table
c.execute('''
CREATE TABLE food_log (
id INTEGER PRIMARY KEY,
trace_id TEXT UNIQUE NOT NULL,
user_id INTEGER NOT NULL,
timestamp VARCHAR(100) NOT NULL,
food_name VARCHAR(250) NOT NULL,
quantity INTEGER NOT NULL,
calories INTEGER NOT NULL,
carbohydrates INTEGER NOT NULL,
fats INTEGER NOT NULL,
proteins INTEGER NOT NULL,
date_created VARCHAR(100) NOT NULL)
''')

conn.commit()
conn.close()
